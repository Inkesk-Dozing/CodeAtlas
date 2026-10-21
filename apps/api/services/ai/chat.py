"""RAG chat: retrieve repo context, answer with citations, persist sessions."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChatMessage, ChatSession, CodeNode, Issue
from schemas import ChatCitation, ChatResponse
from services.ai.llm import chat_completion, embed

logger = logging.getLogger(__name__)

RETRIEVAL_LIMIT = 8
CONTEXT_TOKEN_BUDGET = 6000


async def _retrieve(db: AsyncSession, repo_id: str, question: str) -> list[tuple[CodeNode, float]]:
    candidates: dict[str, tuple[CodeNode, float]] = {}

    vector = await embed(question)
    if vector:
        rows = await db.execute(
            text(
                """
                SELECT id, 1 - (embedding <=> CAST(:qv AS vector)) AS score
                FROM code_nodes
                WHERE repo_id = :repo_id AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:qv AS vector)
                LIMIT :lim
                """
            ),
            {"qv": str(vector), "repo_id": repo_id, "lim": RETRIEVAL_LIMIT * 2},
        )
        for row in rows.mappings():
            score = float(row["score"] or 0.0)
            if score < 0.25:
                continue
            node = await db.get(CodeNode, str(row["id"]))
            if node:
                candidates[node.id] = (node, score)

    keyword_rows = await db.execute(
        text(
            """
            SELECT id, ts_rank_cd(search_vector, plainto_tsquery('english', :q)) AS score
            FROM code_nodes
            WHERE repo_id = :repo_id AND search_vector @@ plainto_tsquery('english', :q)
            ORDER BY score DESC
            LIMIT :lim
            """
        ),
        {"q": question, "repo_id": repo_id, "lim": RETRIEVAL_LIMIT},
    )
    for row in keyword_rows.mappings():
        score = min(1.0, float(row["score"] or 0.0)) * 0.9
        node = await db.get(CodeNode, str(row["id"]))
        if node is None:
            continue
        if node.id in candidates:
            prev = candidates[node.id]
            candidates[node.id] = (node, min(1.0, max(prev[1], score)))
        else:
            candidates[node.id] = (node, score)

    ranked = sorted(candidates.values(), key=lambda x: x[1], reverse=True)
    return ranked[:RETRIEVAL_LIMIT]


async def _retrieve_issue_context(db: AsyncSession, repo_id: str, question: str) -> list[str]:
    rows = await db.execute(
        select(Issue)
        .where(Issue.repo_id == repo_id)
        .order_by(Issue.updated_at.desc())
        .limit(5)
    )
    snippets: list[str] = []
    q_lower = question.lower()
    for issue in rows.scalars().all():
        content = f"{issue.title} {issue.body or ''}".lower()
        if any(word in content for word in q_lower.split() if len(word) > 3):
            snippets.append(
                f"[#{issue.number}] {issue.title} (state: {issue.state})\n{issue.body or ''}"
            )
    return snippets[:3]


async def ask(
    db: AsyncSession,
    repo_id: str,
    user_id: str,
    question: str,
    *,
    session_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> ChatResponse:
    retrieved = await _retrieve(db, repo_id, question)
    issue_snippets = await _retrieve_issue_context(db, repo_id, question)

    context_blocks: list[str] = []
    citations: list[ChatCitation] = []
    used = 0
    for node, score in retrieved:
        block = (
            f"### {node.path} :: {node.name}\n"
            f"type={node.type} language={node.language or 'n/a'}\n"
            f"{(node.summary or node.meta.get('docstring') or '')[:800]}"
        )
        if used + len(block) > CONTEXT_TOKEN_BUDGET:
            break
        used += len(block)
        context_blocks.append(block)
        citations.append(
            ChatCitation(
                node_id=node.id,
                path=node.path,
                snippet=(node.summary or "")[:400],
                relevance=round(score, 4),
            )
        )

    for snippet in issue_snippets:
        context_blocks.append(f"### related issue\n{snippet[:600]}")

    system = (
        "You are CodeAtlas, an expert software onboarding assistant. Answer strictly "
        "from the repository context below. Cite files as [path]. If the context does "
        "not cover the question, say what is missing instead of inventing details."
    )
    prompt = (
        "Repository context:\n\n" + "\n\n".join(context_blocks)
        + f"\n\nQuestion: {question}"
    )

    result = await chat_completion(prompt, history=history, system=system)

    chat_session: ChatSession | None = None
    if session_id:
        chat_session = await db.get(ChatSession, session_id)
    if chat_session is None:
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            repo_id=repo_id,
            user_id=user_id,
            title=question[:120],
        )
        db.add(chat_session)

    db.add(
        ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=question,
            citations=[],
        )
    )
    db.add(
        ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=result.text,
            citations=[c.model_dump(mode="json") for c in citations],
            tokens_used=(result.input_tokens or 0) or None,
        )
    )
    await db.flush()

    return ChatResponse(
        answer=result.text,
        citations=citations,
        session_id=chat_session.id,
        tokens_used=result.input_tokens,
    )


async def list_sessions(db: AsyncSession, repo_id: str, user_id: str) -> list[ChatSession]:
    rows = await db.execute(
        select(ChatSession)
        .where(ChatSession.repo_id == repo_id, ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
    )
    return list(rows.scalars().all())


async def get_session_messages(db: AsyncSession, session_id: str) -> list[ChatMessage]:
    rows = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return list(rows.scalars().all())
