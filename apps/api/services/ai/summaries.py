"""Repository and node summary generation with hash-based caching."""
from __future__ import annotations

import hashlib
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CodeEdge, CodeNode, NodeSummary, Repository
from services.ai.llm import chat_completion

logger = logging.getLogger(__name__)

SUMMARY_INSTRUCTION = (
    "Summarize the following {kind} for a developer new to this repository. "
    "Cover: purpose, key responsibilities, notable dependencies/callers, and any "
    "gotchas. Max 180 words. Plain markdown, no preamble."
)


def source_hash(*parts: str) -> str:
    return hashlib.sha256("||".join(parts).encode()).hexdigest()


async def generate_node_summary(
    db: AsyncSession, node: CodeNode, *, force: bool = False
) -> NodeSummary:
    node_hash = source_hash(node.path, node.name, node.content_hash or "")

    cached = await db.scalar(
        select(NodeSummary).where(
            NodeSummary.node_id == node.id, NodeSummary.summary_type == "node"
        )
    )
    if cached and not force and cached.source_hash == node_hash:
        return cached

    context = (
        f"path: {node.path}\n"
        f"type: {node.type}\n"
        f"language: {node.language or 'unknown'}\n"
        f"metadata: {node.meta}\n"
        f"existing summary: {node.summary or 'n/a'}"
    )
    result = await chat_completion(
        SUMMARY_INSTRUCTION.format(kind=f"{node.type} `{node.name}`") + "\n\n" + context
    )

    if cached:
        cached.content = result.text
        cached.source_hash = node_hash
        cached.model_used = result.model
        cached.input_tokens = result.input_tokens
        cached.output_tokens = result.output_tokens
        node.summary = result.text
        return cached

    summary = NodeSummary(
        node_id=node.id,
        summary_type="node",
        content=result.text,
        model_used=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        source_hash=node_hash,
    )
    db.add(summary)
    node.summary = result.text
    return summary


async def generate_repo_summary(db: AsyncSession, repo: Repository) -> str:
    cached = await db.scalar(
        select(NodeSummary)
        .join(CodeNode, CodeNode.id == NodeSummary.node_id)
        .where(CodeNode.repo_id == repo.id, NodeSummary.summary_type == "repo")
        .limit(1)
    )

    stats = await db.execute(
        select(CodeNode.type, func.count(CodeNode.id))
        .where(CodeNode.repo_id == repo.id)
        .group_by(CodeNode.type)
        .order_by(func.count(CodeNode.id).desc())
    )
    by_type = {row[0]: row[1] for row in stats.all()}

    languages = await db.execute(
        select(CodeNode.language, func.count(CodeNode.id))
        .where(CodeNode.repo_id == repo.id, CodeNode.language.isnot(None))
        .group_by(CodeNode.language)
        .order_by(func.count(CodeNode.id).desc())
        .limit(8)
    )
    by_language = {row[0]: row[1] for row in languages.all()}

    entry_nodes = await db.execute(
        select(CodeNode)
        .where(CodeNode.repo_id == repo.id, CodeNode.type.in_(["page", "route", "entry", "main"]))
        .limit(15)
    )
    entries = [f"- {n.type}: {n.name} ({n.path})" for n in entry_nodes.scalars().all()]

    context = (
        f"repository: {repo.full_name}\n"
        f"description: {repo.description or 'n/a'}\n"
        f"primary language: {repo.language or 'n/a'}\n"
        f"node counts by type: {by_type}\n"
        f"node counts by language: {by_language}\n"
        f"entry points:\n" + ("\n".join(entries) or "- none detected")
    )
    result = await chat_completion(
        SUMMARY_INSTRUCTION.format(kind="repository") + "\n\n" + context,
        max_tokens=600,
    )

    anchor_nodes = await db.execute(
        select(CodeNode).where(CodeNode.repo_id == repo.id).order_by(CodeNode.created_at).limit(1)
    )
    anchor = anchor_nodes.scalars().first()

    if cached:
        cached.content = result.text
        cached.model_used = result.model
        await db.flush()
        return result.text

    if anchor is not None:
        db.add(
            NodeSummary(
                node_id=anchor.id,
                summary_type="repo",
                content=result.text,
                model_used=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                source_hash=source_hash(repo.full_name, str(by_type)),
            )
        )
    await db.flush()
    return result.text


async def generate_architecture_overview(db: AsyncSession, repo: Repository) -> str:
    nodes = await db.execute(
        select(CodeNode)
        .where(CodeNode.repo_id == repo.id, CodeNode.type.in_(
            ["directory", "module", "package", "service", "page", "entry", "config"]
        ))
        .limit(40)
    )
    edges = await db.execute(
        select(CodeEdge).where(CodeEdge.repo_id == repo.id).limit(200)
    )

    node_list = [f"- [{n.type}] {n.name} @ {n.path}" for n in nodes.scalars().all()]
    edge_list = [f"- {e.type}: {e.source_id} -> {e.target_id}" for e in edges.scalars().all()]

    context = (
        f"repository: {repo.full_name}\n"
        f"modules:\n" + ("\n".join(node_list) or "- none") +
        "\nrelations:\n" + ("\n".join(edge_list) or "- none")
    )
    result = await chat_completion(
        "Produce a concise architecture overview (mermaid diagram plus 5 bullet "
        "explanations) for a developer onboarding to this repository.\n\n" + context,
        max_tokens=900,
    )
    return result.text
