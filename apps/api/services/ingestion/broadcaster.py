"""Real-time ingestion pipeline progress tracking and broadcast service.

Provides multi-worker synchronization via Redis pub/sub with an automatic
resilient in-memory async fallback for single-instance or test environments.
Guarantees monotonic progress percentage reporting [0, 100].
"""

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class IngestionBroadcaster:
    """Manages real-time ingestion stage transitions and progress broadcasting."""

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or settings.redis_url
        self._subscribers: dict[str, set[tuple[asyncio.Queue[dict[str, Any]], asyncio.AbstractEventLoop]]] = (
            defaultdict(set)
        )
        self._last_progress: dict[str, int] = {}
        self._latest_state: dict[str, dict[str, Any]] = {}
        self._redis_client: Any = None
        self._redis_available: bool | None = None

    def _utcnow_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    def get_latest(self, repo_id: str) -> dict[str, Any] | None:
        """Retrieve most recent broadcast progress state for repository."""
        return self._latest_state.get(repo_id)

    async def _get_redis(self) -> Any:
        if self._redis_available is False:
            return None

        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis

                client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=0.1,
                )
                await asyncio.wait_for(client.ping(), timeout=0.1)
                self._redis_client = client
                self._redis_available = True
                logger.info("Connected to Redis pub/sub for ingestion progress tracking")
            except Exception as e:
                logger.debug("Redis unavailable (%s), using in-memory pub/sub fallback", e)
                self._redis_available = False
                self._redis_client = None

        return self._redis_client

    def _enforce_monotonic_progress(self, task_id: str, new_progress: int) -> int:
        clamped = max(0, min(100, int(new_progress)))
        previous = self._last_progress.get(task_id, 0)
        monotonic = max(previous, clamped)
        self._last_progress[task_id] = monotonic
        return monotonic

    async def publish(self, repo_id: str, event: dict[str, Any]) -> None:
        """Publish a progress event to local listeners and Redis channel."""
        event.setdefault("timestamp", self._utcnow_iso())
        event.setdefault("repo_id", repo_id)
        self._latest_state[repo_id] = event

        # 1. Distribute to in-memory subscribers safely across event loops
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        listeners = list(self._subscribers.get(repo_id, set()))
        for queue, loop in listeners:
            def _put(q=queue, evt=event):
                try:
                    q.put_nowait(evt)
                except asyncio.QueueFull:
                    logger.warning("Subscriber queue full for repo %s; dropping event", repo_id)

            if current_loop is loop:
                _put()
            elif loop.is_running():
                loop.call_soon_threadsafe(_put)

        # 2. Distribute to Redis pub/sub channel for cross-worker broadcast
        try:
            r = await self._get_redis()
            if r is not None:
                channel = f"ingest:progress:{repo_id}"
                await r.publish(channel, json.dumps(event))
        except Exception as e:
            logger.debug("Failed publishing event to Redis: %s", e)

    async def publish_stage_transition(
        self,
        repo_id: str,
        task_id: str,
        stage: str,
        progress: int,
        files_total: int = 0,
        files_processed: int = 0,
        stage_timings: dict[str, float] | None = None,
    ) -> None:
        """Broadcast transition to a new ingestion stage."""
        monotonic_pct = self._enforce_monotonic_progress(task_id, progress)
        event = {
            "type": "stage_transition",
            "repo_id": repo_id,
            "task_id": task_id,
            "stage": stage,
            "progress": monotonic_pct,
            "files_total": files_total,
            "files_processed": files_processed,
            "stage_timings": stage_timings or {},
        }
        await self.publish(repo_id, event)

    async def publish_progress(
        self,
        repo_id: str,
        task_id: str,
        stage: str,
        progress: int,
        files_total: int,
        files_processed: int,
        stage_timings: dict[str, float] | None = None,
    ) -> None:
        """Broadcast granular file-level progress within the current stage."""
        monotonic_pct = self._enforce_monotonic_progress(task_id, progress)
        event = {
            "type": "progress",
            "repo_id": repo_id,
            "task_id": task_id,
            "stage": stage,
            "progress": monotonic_pct,
            "files_total": files_total,
            "files_processed": files_processed,
            "stage_timings": stage_timings or {},
        }
        await self.publish(repo_id, event)

    async def publish_completed(
        self,
        repo_id: str,
        task_id: str,
        nodes_created: int,
        edges_created: int,
        stage_timings: dict[str, float] | None = None,
    ) -> None:
        """Broadcast successful completion of pipeline."""
        monotonic_pct = self._enforce_monotonic_progress(task_id, 100)
        event = {
            "type": "completed",
            "repo_id": repo_id,
            "task_id": task_id,
            "stage": "completed",
            "progress": monotonic_pct,
            "nodes_created": nodes_created,
            "edges_created": edges_created,
            "stage_timings": stage_timings or {},
        }
        await self.publish(repo_id, event)
        self._last_progress.pop(task_id, None)

    async def publish_failed(
        self,
        repo_id: str,
        task_id: str,
        stage: str,
        error_message: str,
        diagnostic_log: str | None = None,
        stage_timings: dict[str, float] | None = None,
    ) -> None:
        """Broadcast failure event with detailed diagnostic logs."""
        last_pct = self._last_progress.get(task_id, 0)
        event = {
            "type": "failed",
            "repo_id": repo_id,
            "task_id": task_id,
            "stage": stage,
            "progress": last_pct,
            "error": error_message,
            "diagnostic_log": diagnostic_log,
            "stage_timings": stage_timings or {},
        }
        await self.publish(repo_id, event)
        self._last_progress.pop(task_id, None)

    async def subscribe(
        self, repo_id: str, timeout: float = 300.0
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to progress events for a given repository."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        entry = (queue, loop)
        self._subscribers[repo_id].add(entry)

        try:
            start_time = loop.time()
            while True:
                remaining = timeout - (loop.time() - start_time)
                if remaining <= 0:
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=min(remaining, 5.0))
                    yield event
                    if event.get("type") in ("completed", "failed"):
                        break
                except TimeoutError:
                    continue
        finally:
            self._subscribers[repo_id].discard(entry)
            if not self._subscribers[repo_id]:
                self._subscribers.pop(repo_id, None)


progress_broadcaster = IngestionBroadcaster()
