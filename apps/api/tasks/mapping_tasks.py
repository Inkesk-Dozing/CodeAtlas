"""Celery-wrapped issue mapping task (used when settings.use_celery is true)."""
from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from sqlalchemy import select

from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.mapping_tasks.map_issue")
def map_issue(mapping_id: str, repo_id: str, issue_number: int) -> dict:
    import asyncio

    return asyncio.get_event_loop().run_until_complete(
        _map_issue_async(mapping_id, repo_id, issue_number)
    )


async def _map_issue_async(mapping_id: str, repo_id: str, issue_number: int) -> dict:
    from database import AsyncSessionLocal
    from models import Issue, IssueMapping
    from schemas import CodeMapping, CodeNodeResponse
    from services.mapping.ranker import MODEL_VERSION, IssueMapper

    started = time.time()
    async with AsyncSessionLocal() as session:
        mapping = await session.get(IssueMapping, mapping_id)
        issue = await session.scalar(
            select(Issue).where(Issue.repo_id == repo_id, Issue.number == issue_number)
        )
        if mapping is None or issue is None:
            return {"status": "not_found"}

        try:
            mapper = IssueMapper(session, repo_id)
            results = await mapper.analyze(issue)

            payload = [
                CodeMapping(
                    node=CodeNodeResponse.model_validate(r.pop("node")), **r
                ).model_dump(mode="json")
                for r in results
            ]

            mapping.mappings = payload
            mapping.status = "completed"
            mapping.model_version = MODEL_VERSION
            mapping.generation_ms = int((time.time() - started) * 1000)
            mapping.generated_at = datetime.now(UTC)
            await session.commit()
            return {"status": "completed", "mappings": len(payload)}
        except Exception as exc:
            logger.exception("celery mapping failed")
            mapping.status = "failed"
            await session.commit()
            return {"status": "failed", "error": str(exc)}
