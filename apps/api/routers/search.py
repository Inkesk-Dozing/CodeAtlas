import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import CodeNode, Repository, User
from schemas import (
    CodeNodeResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
)
from services.auth import get_current_user

router = APIRouter(prefix="/repos/{repo_id}/search", tags=["search"])


async def _get_repo(repo_id: str, db: AsyncSession) -> Repository:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


async def _embed_query(query: str) -> list[float] | None:
    try:
        import httpx

        from config import settings

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": query},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
    except Exception:
        pass
    return None


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    repo_id: str,
    payload: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_repo(repo_id, db)
    start = time.time()

    query_vector = await _embed_query(payload.query)

    results: list[SearchResultResponse] = []

    if query_vector:
        vector_sql = text("""
            SELECT *, 1 - (embedding <=> CAST(:qv AS vector)) AS score
            FROM code_nodes
            WHERE repo_id = :repo_id
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> CAST(:qv AS vector)) > :threshold
            ORDER BY embedding <=> CAST(:qv AS vector)
            LIMIT :limit
        """)
        params = {"qv": str(query_vector), "repo_id": repo_id, "threshold": payload.threshold, "limit": payload.limit}
        if payload.types:
            vector_sql = text(str(vector_sql) + "")
        result = await db.execute(vector_sql, params)
        for row in result.mappings():
            node = await db.get(CodeNode, str(row["id"]))
            if node:
                results.append(
                    SearchResultResponse(
                        node=CodeNodeResponse.model_validate(node),
                        score=float(row["score"]),
                        match_type="semantic",
                        snippet=node.summary or node.meta.get("docstring"),
                    )
                )

    if not results:
        keyword_sql = text("""
            SELECT *, ts_rank_cd(search_vector, plainto_tsquery('english', :q)) AS score
            FROM code_nodes
            WHERE repo_id = :repo_id
              AND search_vector @@ plainto_tsquery('english', :q)
            ORDER BY score DESC
            LIMIT :limit
        """)
        result = await db.execute(keyword_sql, {"q": payload.query, "repo_id": repo_id, "limit": payload.limit})
        for row in result.mappings():
            node = await db.get(CodeNode, str(row["id"]))
            if node:
                results.append(
                    SearchResultResponse(
                        node=CodeNodeResponse.model_validate(node),
                        score=float(row["score"]),
                        match_type="keyword",
                        snippet=node.summary or node.meta.get("docstring"),
                    )
                )

    took_ms = int((time.time() - start) * 1000)
    return SearchResponse(results=results, took_ms=took_ms)


@router.post("/structural", response_model=SearchResponse)
async def structural_search(
    repo_id: str,
    payload: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_repo(repo_id, db)
    start = time.time()

    query = select(CodeNode).where(CodeNode.repo_id == repo_id)

    if payload.types:
        query = query.where(CodeNode.type.in_(payload.types))

    query = query.where(
        (CodeNode.name.ilike(f"%{payload.query}%"))
        | (CodeNode.path.ilike(f"%{payload.query}%"))
    )
    query = query.limit(payload.limit)

    result = await db.execute(query)
    nodes = result.scalars().all()

    results = [
        SearchResultResponse(
            node=CodeNodeResponse.model_validate(n),
            score=1.0 - i * 0.05,
            match_type="structural",
            snippet=n.summary,
        )
        for i, n in enumerate(nodes)
    ]

    took_ms = int((time.time() - start) * 1000)
    return SearchResponse(results=results, took_ms=took_ms)


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    repo_id: str,
    payload: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_repo(repo_id, db)
    start = time.time()

    semantic_resp = await semantic_search(repo_id, payload, user, db)
    structural_resp = await structural_search(repo_id, payload, user, db)

    seen: dict[str, SearchResultResponse] = {}
    for r in semantic_resp.results:
        seen[r.node.id] = r
    for r in structural_resp.results:
        if r.node.id in seen:
            seen[r.node.id].score = min(1.0, seen[r.node.id].score * 0.6 + r.score * 0.4)
        else:
            seen[r.node.id] = r

    sorted_results = sorted(seen.values(), key=lambda x: x.score, reverse=True)[: payload.limit]
    took_ms = int((time.time() - start) * 1000)
    return SearchResponse(results=sorted_results, took_ms=took_ms)
