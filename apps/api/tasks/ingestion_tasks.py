import asyncio
import logging
import time
from datetime import UTC
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal
from models import CodeEdge, CodeNode, IngestionTask, Repository

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

            files = await _clone_repository(repo, branch)
            task.files_total = len(files)
            stage_timings["clone"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["clone"]
            task.progress = cumulative
            await db.commit()

            # ── Stage 2: Parse ──
            stage_start = time.time()
            task.current_stage = "parse"
            await db.commit()

            parsed = await _parse_files(files, repo.settings)
            stage_timings["parse"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["parse"]
            task.progress = cumulative
            await db.commit()

            # ── Stage 3: Extract ──
            stage_start = time.time()
            task.current_stage = "extract"
            await db.commit()

            nodes, edges = await _extract_graph(parsed, str(repo.id))
            stage_timings["extract"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["extract"]
            task.progress = cumulative
            await db.commit()

            # ── Stage 4: Embed ──
            stage_start = time.time()
            task.current_stage = "embed"
            await db.commit()

            await _generate_embeddings(nodes)
            stage_timings["embed"] = time.time() - stage_start
            cumulative += STAGE_WEIGHTS["embed"]
            task.progress = cumulative
            await db.commit()

            # ── Stage 5: Persist ──
            stage_start = time.time()
            task.current_stage = "persist"
            await db.commit()

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
            logger.info(
                "Ingestion completed: task=%s repo=%s nodes=%d edges=%d",
                task_id, repo_id, created_nodes, created_edges,
            )

        except Exception as e:
            logger.exception("Ingestion failed: task=%s", task_id)
            task.status = "failed"
            task.error = str(e)
            task.error_stage = task.current_stage
            task.stage_timings = stage_timings
            task.completed_at = _utcnow()
            repo.status = "error"
            repo.error_message = str(e)
            await db.commit()
            raise


async def _clone_repository(repo: Repository, branch: str | None) -> list[dict[str, Any]]:
    import tempfile

    target_branch = branch or repo.default_branch
    url = repo.clone_url

    tmp_dir = Path(tempfile.mkdtemp(prefix="codeatlas_"))
    try:
        import asyncio

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth=1", "--filter=blob:none",
            "--branch", target_branch, url, str(tmp_dir / "repo"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Git clone failed: {stderr.decode()}")

        repo_path = tmp_dir / "repo"
        files = _scan_files(repo_path, repo.settings.get("ignored_paths", []))
        return files
    except Exception:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


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
    if not nodes:
        return

    try:
        import httpx

        batch_size = 32
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i : i + batch_size]
            for node in batch:
                text = _build_embedding_text(node)
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            f"{settings.ollama_url}/api/embeddings",
                            json={"model": settings.ollama_embed_model, "prompt": text},
                            timeout=15.0,
                        )
                        if resp.status_code == 200:
                            node["embedding"] = resp.json().get("embedding")
                except Exception as e:
                    logger.warning("Embedding failed for %s: %s", node.get("name"), e)
    except ImportError:
        logger.warning("httpx not available, skipping embeddings")


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
    await db.execute(delete(CodeEdge).where(CodeEdge.repo_id == repo_id))
    await db.execute(delete(CodeNode).where(CodeNode.repo_id == repo_id))
    await db.flush()

    path_to_id: dict[str, str] = {}
    db_nodes = []

    for n in nodes:
        node = CodeNode(
            id=n["id"],
            repo_id=repo_id,
            type=n["type"],
            name=n["name"],
            path=n["path"],
            language=n.get("language"),
            meta=n.get("metadata", {}),
            summary=n.get("summary"),
            content_hash=n.get("content_hash"),
            embedding=n.get("embedding"),
        )
        db_nodes.append(node)
        key = f"{n['path']}::{n['name']}::{n['type']}"
        path_to_id[key] = n["id"]

    db.add_all(db_nodes)
    await db.flush()

    db_edges = []
    for e in edges:
        source_key = e.get("source_key")
        target_key = e.get("target_key")
        source_id = path_to_id.get(source_key)
        target_id = path_to_id.get(target_key)

        if source_id and target_id:
            db_edges.append(
                CodeEdge(
                    id=e["id"],
                    repo_id=repo_id,
                    source_id=source_id,
                    target_id=target_id,
                    type=e["type"],
                    weight=e.get("weight", 1.0),
                    meta=e.get("metadata", {}),
                )
            )

    db.add_all(db_edges)
    await db.flush()

    return len(db_nodes), len(db_edges)


async def trigger_incremental_update(repo_id: str, branch: str, sha: str) -> None:
    import uuid as uuid_mod

    async with AsyncSessionLocal() as db:
        task = IngestionTask(
            id=str(uuid_mod.uuid4()),
            repo_id=repo_id,
            mode="webhook",
            status="queued",
            branch=branch,
            commit_sha=sha,
        )
        db.add(task)
        await db.commit()

        task_id = task.id

    task = asyncio.create_task(run_ingestion_pipeline(task_id, repo_id, "incremental", branch))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _utcnow():
    from datetime import datetime
    return datetime.now(UTC)
