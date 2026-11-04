"""Incremental git diff parser and re-indexing engine for push webhooks.

Parses 'git diff --name-status' payloads, classifies file modifications (Added,
Modified, Deleted, Renamed), performs targeted graph mutations (cascade-deleting
nodes/edges and re-parsing changed files), purges orphaned dependencies, bumps
graph version, and broadcasts real-time updates via WebSocket.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CodeEdge, CodeNode, Repository
from services.ingestion.broadcaster import progress_broadcaster

logger = logging.getLogger(__name__)

FileChangeStatus = Literal["added", "modified", "deleted", "renamed"]


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: FileChangeStatus
    old_path: str | None = None


def parse_git_diff_name_status(diff_output: str) -> list[ChangedFile]:
    """Parse 'git diff --name-status' output into structured ChangedFile entries.

    Supported status flags:
      - 'A' / 'A100': Added
      - 'M' / 'M100': Modified
      - 'D': Deleted
      - 'R' / 'R100': Renamed (tab-separated: R100 <old_path> <new_path>)
    """
    changes: list[ChangedFile] = []
    if not diff_output:
        return changes

    for line in diff_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            # Fallback for whitespace-split diff output
            parts = line.split()

        if len(parts) < 2:
            continue

        raw_status = parts[0].upper()
        if raw_status.startswith("A"):
            changes.append(ChangedFile(path=parts[1].replace("\\", "/"), status="added"))
        elif raw_status.startswith("M"):
            changes.append(ChangedFile(path=parts[1].replace("\\", "/"), status="modified"))
        elif raw_status.startswith("D"):
            changes.append(ChangedFile(path=parts[1].replace("\\", "/"), status="deleted"))
        elif raw_status.startswith("R"):
            old_p = parts[1].replace("\\", "/")
            new_p = (parts[2] if len(parts) > 2 else parts[1]).replace("\\", "/")
            changes.append(ChangedFile(path=new_p, status="renamed", old_path=old_p))

    return changes


class IncrementalDiffEngine:
    """Applies incremental AST updates and graph diff mutations to repository nodes."""

    def __init__(self, repo_id: str) -> None:
        self.repo_id = repo_id

    async def apply_incremental_diff(
        self,
        db: AsyncSession,
        changes: list[ChangedFile],
        file_contents: dict[str, str],
        commit_sha: str | None = None,
    ) -> dict[str, Any]:
        """Apply incremental changes for changed files in a commit."""
        from parsers import get_parser
        from services.ingestion.extractor import GraphExtractor
        from tasks.ingestion_tasks import _detect_language

        repo = await db.get(Repository, self.repo_id)
        if repo is None:
            raise ValueError(f"Repository {self.repo_id} not found")

        paths_to_delete: set[str] = set()
        files_to_index: list[dict[str, Any]] = []

        for ch in changes:
            if ch.status == "deleted":
                paths_to_delete.add(ch.path)
            elif ch.status == "renamed":
                if ch.old_path:
                    paths_to_delete.add(ch.old_path)
                if ch.path in file_contents:
                    files_to_index.append(
                        {
                            "path": ch.path,
                            "content": file_contents[ch.path],
                            "language": _detect_language("." + ch.path.split(".")[-1]) if "." in ch.path else None,
                        }
                    )
            elif ch.status == "modified":
                paths_to_delete.add(ch.path)
                if ch.path in file_contents:
                    files_to_index.append(
                        {
                            "path": ch.path,
                            "content": file_contents[ch.path],
                            "language": _detect_language("." + ch.path.split(".")[-1]) if "." in ch.path else None,
                        }
                    )
            elif ch.status == "added" and ch.path in file_contents:
                files_to_index.append(
                    {
                        "path": ch.path,
                        "content": file_contents[ch.path],
                        "language": _detect_language("." + ch.path.split(".")[-1]) if "." in ch.path else None,
                    }
                )

        # 1. Cascade delete existing nodes and connected edges for affected paths
        if paths_to_delete:
            existing_nodes = await db.execute(
                select(CodeNode.id).where(
                    CodeNode.repo_id == self.repo_id,
                    CodeNode.path.in_(list(paths_to_delete)),
                )
            )
            deleted_node_ids = existing_nodes.scalars().all()

            if deleted_node_ids:
                # Delete incoming and outgoing edges for deleted nodes
                await db.execute(
                    delete(CodeEdge).where(
                        CodeEdge.repo_id == self.repo_id,
                        (CodeEdge.source_id.in_(deleted_node_ids)) | (CodeEdge.target_id.in_(deleted_node_ids)),
                    )
                )
                # Delete the nodes themselves
                await db.execute(
                    delete(CodeNode).where(
                        CodeNode.repo_id == self.repo_id,
                        CodeNode.id.in_(deleted_node_ids),
                    )
                )
                await db.flush()

        # 2. Parse and index newly added or modified files
        parsed_files = []
        for f in files_to_index:
            lang = f.get("language")
            if not lang:
                continue
            parser = get_parser(lang)
            if parser is None:
                continue
            try:
                parse_result = parser.parse(f["content"], f["path"])
                f["parsed"] = parse_result
                parsed_files.append(f)
            except Exception as e:
                logger.warning("Incremental parse error for %s: %s", f["path"], e)

        if parsed_files:
            extractor = GraphExtractor(self.repo_id)
            extracted_nodes, extracted_edges = extractor.extract(parsed_files)

            path_to_id: dict[str, str] = {}
            db_nodes = []
            for n in extracted_nodes:
                node = CodeNode(
                    id=n["id"],
                    repo_id=self.repo_id,
                    type=n["type"],
                    name=n["name"],
                    path=n["path"],
                    language=n.get("language"),
                    meta=n.get("metadata", {}),
                    summary=n.get("summary"),
                    content_hash=n.get("content_hash"),
                )
                db_nodes.append(node)
                key = f"{n['path']}::{n['name']}::{n['type']}"
                path_to_id[key] = n["id"]

            db.add_all(db_nodes)
            await db.flush()

            db_edges = []
            for e in extracted_edges:
                source_key = e.get("source_key")
                target_key = e.get("target_key")
                source_id = path_to_id.get(source_key)
                target_id = path_to_id.get(target_key)
                if source_id and target_id:
                    db_edges.append(
                        CodeEdge(
                            id=e["id"],
                            repo_id=self.repo_id,
                            source_id=source_id,
                            target_id=target_id,
                            type=e["type"],
                            weight=e.get("weight", 1.0),
                            meta=e.get("metadata", {}),
                        )
                    )
            db.add_all(db_edges)
            await db.flush()

        # 3. Purge orphaned edges where dependencies were deleted
        active_nodes_subq = select(CodeNode.id).where(CodeNode.repo_id == self.repo_id)
        await db.execute(
            delete(CodeEdge)
            .where(CodeEdge.repo_id == self.repo_id)
            .where(
                (~CodeEdge.source_id.in_(active_nodes_subq))
                | (~CodeEdge.target_id.in_(active_nodes_subq))
            )
        )
        await db.flush()

        # 4. Recompute total repository graph metrics & bump graph version
        total_nodes = (
            await db.execute(select(func.count(CodeNode.id)).where(CodeNode.repo_id == self.repo_id))
        ).scalar() or 0
        total_edges = (
            await db.execute(select(func.count(CodeEdge.id)).where(CodeEdge.repo_id == self.repo_id))
        ).scalar() or 0

        repo_settings = dict(repo.settings or {})
        current_version = repo_settings.get("graph_version", 1)
        new_version = current_version + 1
        repo_settings["graph_version"] = new_version
        repo.settings = repo_settings
        repo.node_count = total_nodes
        repo.edge_count = total_edges
        repo.last_analyzed_at = datetime.now(UTC)
        if commit_sha:
            repo.last_analyzed_sha = commit_sha

        await db.commit()

        # 5. Notify connected WebSocket clients of graph update
        update_event = {
            "type": "graph_updated",
            "repo_id": self.repo_id,
            "graph_version": new_version,
            "commit_sha": commit_sha,
            "nodes_count": total_nodes,
            "edges_count": total_edges,
            "files_changed": len(changes),
            "files_added": len([c for c in changes if c.status == "added"]),
            "files_modified": len([c for c in changes if c.status == "modified"]),
            "files_deleted": len([c for c in changes if c.status == "deleted"]),
            "files_renamed": len([c for c in changes if c.status == "renamed"]),
        }
        await progress_broadcaster.publish(self.repo_id, update_event)

        return update_event
