import asyncio
import logging
import time
import traceback
from datetime import UTC
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import IngestionError, IngestionTask, Repository
from services.ingestion.broadcaster import progress_broadcaster

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()

STAGE_WEIGHTS = {
    "clone": 10,
    "parse": 30,
    "extract": 25,
    "embed": 25,
    "persist": 10,
}

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx",
    ".mp3", ".mp4", ".avi", ".mov",
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".lock", ".min.js", ".min.css",
    ".map", ".log", ".tmp", ".cache",
}

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "coverage",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "target", "vendor",
    ".idea", ".vscode", ".turbo", ".cache",
}


async def run_ingestion_pipeline(
    task_id: str,
    repo_id: str,
    mode: str,
    branch: str | None,
) -> None:
    async with AsyncSessionLocal() as db:
        task = await db.get(IngestionTask, task_id)
        repo = await db.get(Repository, repo_id)
        if task is None or repo is None:
            logger.error("Task %s or repo %s not found", task_id, repo_id)
            return

        task.status = "running"
        task.started_at = _utcnow()
        await db.commit()

        stage_start = time.time()
        stage_timings: dict[str, float] = {}
        cumulative = 0

        try:
            # ── Stage 1: Clone ──
            task.current_stage = "clone"
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="clone",
                progress=0,
                files_total=0,
                files_processed=0,
            )

            files = await _clone_repository(repo, branch)
            task.files_total = len(files)
            stage_timings["clone"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["clone"]
            task.progress = cumulative
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="clone",
                progress=cumulative,
                files_total=len(files),
                files_processed=0,
                stage_timings=stage_timings,
            )

            # ── Stage 2: Parse ──
            stage_start = time.time()
            task.current_stage = "parse"
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="parse",
                progress=cumulative,
                files_total=len(files),
                files_processed=0,
                stage_timings=stage_timings,
            )

            parsed = await _parse_files(files, repo.settings)
            # Explicit garbage collection to release Tree-sitter C memory and AST nodes
            import gc
            gc.collect()

            task.files_processed = len(parsed)
            stage_timings["parse"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["parse"]
            task.progress = cumulative
            await db.commit()
            await progress_broadcaster.publish_progress(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="parse",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            # ── Stage 3: Extract ──
            stage_start = time.time()
            task.current_stage = "extract"
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="extract",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            nodes, edges = await _extract_graph(parsed, str(repo.id))
            stage_timings["extract"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["extract"]
            task.progress = cumulative
            await db.commit()
            await progress_broadcaster.publish_progress(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="extract",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            # ── Stage 4: Embed ──
            stage_start = time.time()
            task.current_stage = "embed"
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="embed",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            await _generate_embeddings(nodes)
            stage_timings["embed"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["embed"]
            task.progress = cumulative
            await db.commit()
            await progress_broadcaster.publish_progress(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="embed",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            # ── Stage 5: Persist ──
            stage_start = time.time()
            task.current_stage = "persist"
            await db.commit()
            await progress_broadcaster.publish_stage_transition(
                repo_id=str(repo.id),
                task_id=task_id,
                stage="persist",
                progress=cumulative,
                files_total=len(files),
                files_processed=len(parsed),
                stage_timings=stage_timings,
            )

            created_nodes, created_edges = await _persist_graph(db, str(repo.id), nodes, edges)
            stage_timings["persist"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["persist"]

            task.status = "completed"
            task.progress = 100
            task.nodes_created = created_nodes
            task.edges_created = created_edges
            task.stage_timings = stage_timings
            task.completed_at = _utcnow()

            repo.status = "ready"
            repo.node_count = created_nodes
            repo.edge_count = created_edges
            repo.last_analyzed_at = _utcnow()
            repo.error_message = None

            await db.commit()
            await progress_broadcaster.publish_completed(
                repo_id=str(repo.id),
                task_id=task_id,
                nodes_created=created_nodes,
                edges_created=created_edges,
                stage_timings=stage_timings,
            )
            logger.info(
                "Ingestion completed: task=%s repo=%s nodes=%d edges=%d",
                task_id, repo_id, created_nodes, created_edges,
            )

        except Exception as e:
            logger.exception("Ingestion failed: task=%s", task_id)
            err_msg = str(e)
            tb_str = traceback.format_exc()

            # Record failure in task
            task.status = "failed"
            task.error = err_msg
            task.error_stage = task.current_stage
            task.stage_timings = stage_timings
            task.completed_at = _utcnow()

            # Two-phase commit rollback: preserve previous active graph if one existed
            # If repo already had nodes, it remains functional in degraded state
            if repo.node_count > 0:
                repo.status = "ready"
            else:
                repo.status = "error"
            repo.error_message = err_msg

            # Log root-cause error trace to ingestion_errors table
            error_log = IngestionError(
                repo_id=str(repo.id),
                task_id=task_id,
                error_stage=task.current_stage or "unknown",
                error_message=err_msg,
                traceback=tb_str,
                details={
                    "stage": task.current_stage,
                    "progress": cumulative,
                    "files_total": task.files_total,
                },
            )
            db.add(error_log)

            await db.commit()
            await progress_broadcaster.publish_failed(
                repo_id=str(repo.id),
                task_id=task_id,
                stage=task.current_stage or "unknown",
                error_message=err_msg,
                diagnostic_log=tb_str,
                stage_timings=stage_timings,
            )
            raise


async def _clone_repository(repo: Repository, branch: str | None) -> list[dict[str, Any]]:
    from services.ingestion.cloner import ShallowRepositoryCloner

    target_branch = branch or repo.default_branch
    url = repo.clone_url

    # Check for installation token in repo settings or auth context if available
    token = repo.settings.get("github_token") or repo.settings.get("installation_token")
    cloner = ShallowRepositoryCloner(token=token)

    return await cloner.clone_and_scan(
        clone_url=url,
        branch=target_branch,
        ignored_patterns=repo.settings.get("ignored_paths", []),
    )


def _scan_files(base_path: Path, ignored_patterns: list[str]) -> list[dict[str, Any]]:
    import fnmatch

    files = []
    for path in base_path.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(base_path)
        rel_str = str(rel).replace("\\", "/")

        parts = rel.parts
        if any(p in IGNORED_DIRS for p in parts):
            continue
        if path.suffix.lower() in IGNORED_EXTENSIONS:
            continue
        if any(fnmatch.fnmatch(rel_str, pat) for pat in ignored_patterns):
            continue

        try:
            if path.stat().st_size > 1_000_000:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        files.append({
            "path": rel_str,
            "content": content,
            "language": _detect_language(path.suffix),
        })

    return files


def _detect_language(suffix: str) -> str | None:
    mapping = {
        ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
        ".py": "python",
        ".go": "go",
        ".rs": "rust",
        ".prisma": "prisma",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".swift": "swift",
        ".c": "c", ".h": "c",
        ".cpp": "cpp", ".hpp": "cpp",
    }
    return mapping.get(suffix.lower())


async def _parse_files(
    files: list[dict[str, Any]],
    repo_settings: dict,
) -> list[dict[str, Any]]:
    from parsers import get_parser

    parsed = []
    for f in files:
        language = f.get("language")
        if language is None:
            continue

        try:
            parser = get_parser(language)
            if parser is None:
                continue
            result = parser.parse(f["content"], f["path"])
            f["parsed"] = result
            parsed.append(f)
        except Exception as e:
            logger.warning("Parse failed for %s: %s", f["path"], e)
            f["parsed"] = None
            parsed.append(f)

    return parsed


async def _extract_graph(
    parsed_files: list[dict[str, Any]],
    repo_id: str,
) -> tuple[list[dict], list[dict]]:
    from services.ingestion.extractor import GraphExtractor

    extractor = GraphExtractor(repo_id)
    return extractor.extract(parsed_files)


async def _generate_embeddings(nodes: list[dict]) -> None:
    from services.ingestion.embeddings import vector_embedding_pipeline

    await vector_embedding_pipeline.generate_embeddings_for_nodes(nodes)


def _build_embedding_text(node: dict) -> str:
    parts = [
        f"Type: {node.get('type', '')}",
        f"Name: {node.get('name', '')}",
        f"Path: {node.get('path', '')}",
    ]
    meta = node.get("metadata", {})
    if meta.get("docstring"):
        parts.append(f"Doc: {meta['docstring']}")
    if meta.get("exports"):
        parts.append(f"Exports: {', '.join(meta['exports'])}")
    if meta.get("http_method"):
        parts.append(f"Route: {meta['http_method']} {meta.get('route_path', '')}")
    if node.get("summary"):
        parts.append(f"Summary: {node['summary']}")
    return " | ".join(parts)


async def _persist_graph(
    db: AsyncSession,
    repo_id: str,
    nodes: list[dict],
    edges: list[dict],
) -> tuple[int, int]:
    from services.ingestion.persistence import batch_graph_persistence

    return await batch_graph_persistence.persist_graph(db, repo_id, nodes, edges)


async def trigger_incremental_update(
    repo_id: str,
    branch: str,
    sha: str,
    before_sha: str | None = None,
    diff_payload: str | None = None,
) -> None:
    import uuid as uuid_mod

    async with AsyncSessionLocal() as db:
        task = IngestionTask(
            id=str(uuid_mod.uuid4()),
            repo_id=repo_id,
            mode="incremental",
            status="queued",
            branch=branch,
            commit_sha=sha,
        )
        db.add(task)
        await db.commit()

        task_id = task.id

    task_coro = asyncio.create_task(
        run_incremental_pipeline(task_id, repo_id, branch, sha, before_sha, diff_payload)
    )
    _background_tasks.add(task_coro)
    task_coro.add_done_callback(_background_tasks.discard)


async def run_incremental_pipeline(
    task_id: str,
    repo_id: str,
    branch: str,
    sha: str,
    before_sha: str | None = None,
    diff_payload: str | None = None,
) -> None:
    from services.ingestion.diff_parser import IncrementalDiffEngine, parse_git_diff_name_status

    async with AsyncSessionLocal() as db:
        task = await db.get(IngestionTask, task_id)
        repo = await db.get(Repository, repo_id)
        if task is None or repo is None:
            return

        task.status = "running"
        task.started_at = _utcnow()
        await db.commit()

        try:
            changes = parse_git_diff_name_status(diff_payload or "")
            engine = IncrementalDiffEngine(repo_id)
            result = await engine.apply_incremental_diff(
                db=db,
                changes=changes,
                file_contents={},
                commit_sha=sha,
            )

            task.status = "completed"
            task.progress = 100
            task.completed_at = _utcnow()
            task.nodes_created = result.get("nodes_count", 0)
            task.edges_created = result.get("edges_count", 0)
            await db.commit()

        except Exception as e:
            logger.exception("Incremental ingestion failed: task=%s", task_id)
            task.status = "failed"
            task.error = str(e)
            task.completed_at = _utcnow()
            await db.commit()
            raise


def _utcnow():
    from datetime import datetime
    return datetime.now(UTC)
