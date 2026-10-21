from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import CodeEdge, CodeNode, Repository, User
from schemas import (
    CodeEdgeResponse,
    CodeNodeResponse,
    GraphResponse,
    NodeDetailResponse,
)
from services.auth import get_current_user

router = APIRouter(prefix="/repos/{repo_id}", tags=["graph"])


async def _verify_repo(repo_id: str, db: AsyncSession) -> Repository:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    repo_id: str,
    limit: int = Query(default=500, ge=1, le=2000),
    cursor: str | None = None,
    types: str | None = None,
    languages: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    node_query = select(CodeNode).where(CodeNode.repo_id == repo_id)

    if types:
        type_list = [t.strip() for t in types.split(",")]
        node_query = node_query.where(CodeNode.type.in_(type_list))
    if languages:
        lang_list = [lang.strip() for lang in languages.split(",")]
        node_query = node_query.where(CodeNode.language.in_(lang_list))
    if cursor:
        node_query = node_query.where(CodeNode.id > cursor)

    total_result = await db.execute(
        select(func.count(CodeNode.id)).where(CodeNode.repo_id == repo_id)
    )
    total = total_result.scalar() or 0

    node_query = node_query.order_by(CodeNode.id).limit(limit + 1)
    result = await db.execute(node_query)
    nodes = result.scalars().all()

    has_more = len(nodes) > limit
    nodes = nodes[:limit]
    node_ids = [n.id for n in nodes]

    edges_result = await db.execute(
        select(CodeEdge).where(
            CodeEdge.repo_id == repo_id,
            CodeEdge.source_id.in_(node_ids),
            CodeEdge.target_id.in_(node_ids),
        )
    )
    edges = edges_result.scalars().all()

    next_cursor = nodes[-1].id if has_more and nodes else None

    return GraphResponse(
        nodes=[CodeNodeResponse.model_validate(n) for n in nodes],
        edges=[CodeEdgeResponse.model_validate(e) for e in edges],
        next_cursor=next_cursor,
        has_more=has_more,
        total=total,
    )


@router.get("/graph/subgraph", response_model=GraphResponse)
async def get_subgraph(
    repo_id: str,
    center_node_id: str = Query(...),
    radius: int = Query(default=2, ge=1, le=5),
    max_nodes: int = Query(default=200, ge=10, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    center = await db.get(CodeNode, center_node_id)
    if center is None:
        raise HTTPException(status_code=404, detail="Center node not found")

    visited = {center.id}
    frontier = {center.id}
    all_edges: list[CodeEdge] = []

    for _ in range(radius):
        if not frontier:
            break
        result = await db.execute(
            select(CodeEdge).where(
                CodeEdge.repo_id == repo_id,
                (CodeEdge.source_id.in_(frontier)) | (CodeEdge.target_id.in_(frontier)),
            )
        )
        round_edges = result.scalars().all()
        next_frontier: set[str] = set()
        for edge in round_edges:
            all_edges.append(edge)
            for nid in (edge.source_id, edge.target_id):
                if nid not in visited and len(visited) < max_nodes:
                    visited.add(nid)
                    next_frontier.add(nid)
        frontier = next_frontier

    nodes_result = await db.execute(select(CodeNode).where(CodeNode.id.in_(visited)))
    nodes = nodes_result.scalars().all()

    seen_edge_ids = set()
    unique_edges = []
    for e in all_edges:
        if e.id not in seen_edge_ids:
            seen_edge_ids.add(e.id)
            unique_edges.append(e)

    return GraphResponse(
        nodes=[CodeNodeResponse.model_validate(n) for n in nodes],
        edges=[CodeEdgeResponse.model_validate(e) for e in unique_edges],
        total=len(nodes),
    )


@router.get("/nodes/{node_id}", response_model=NodeDetailResponse)
async def get_node_detail(
    repo_id: str,
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    node = await db.get(CodeNode, node_id)
    if node is None or node.repo_id != repo_id:
        raise HTTPException(status_code=404, detail="Node not found")

    incoming_result = await db.execute(
        select(CodeEdge).where(CodeEdge.target_id == node_id, CodeEdge.repo_id == repo_id)
    )
    outgoing_result = await db.execute(
        select(CodeEdge).where(CodeEdge.source_id == node_id, CodeEdge.repo_id == repo_id)
    )

    return NodeDetailResponse(
        **CodeNodeResponse.model_validate(node).model_dump(),
        neighbors={
            "incoming": [CodeEdgeResponse.model_validate(e) for e in incoming_result.scalars()],
            "outgoing": [CodeEdgeResponse.model_validate(e) for e in outgoing_result.scalars()],
        },
        code_preview=node.meta.get("code_preview"),
    )


@router.get("/nodes/{node_id}/neighbors", response_model=GraphResponse)
async def get_node_neighbors(
    repo_id: str,
    node_id: str,
    direction: str = Query(default="both", pattern="^(incoming|outgoing|both)$"),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    edge_query = select(CodeEdge).where(CodeEdge.repo_id == repo_id)

    if direction == "incoming":
        edge_query = edge_query.where(CodeEdge.target_id == node_id)
    elif direction == "outgoing":
        edge_query = edge_query.where(CodeEdge.source_id == node_id)
    else:
        edge_query = edge_query.where(
            (CodeEdge.source_id == node_id) | (CodeEdge.target_id == node_id)
        )

    edge_query = edge_query.limit(limit)
    edges_result = await db.execute(edge_query)
    edges = edges_result.scalars().all()

    neighbor_ids = set()
    for e in edges:
        neighbor_ids.add(e.source_id)
        neighbor_ids.add(e.target_id)
    neighbor_ids.discard(node_id)

    nodes_result = await db.execute(select(CodeNode).where(CodeNode.id.in_(neighbor_ids)))
    nodes = nodes_result.scalars().all()

    return GraphResponse(
        nodes=[CodeNodeResponse.model_validate(n) for n in nodes],
        edges=[CodeEdgeResponse.model_validate(e) for e in edges],
        total=len(nodes),
    )
