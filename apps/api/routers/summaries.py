from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import CodeNode, Repository, User
from schemas import ArchitectureResponse, SummaryResponse
from services.ai.summaries import (
    generate_architecture_overview,
    generate_node_summary,
    generate_repo_summary,
)
from services.auth import get_current_user

router = APIRouter(prefix="/repos/{repo_id}", tags=["summaries"])


async def _verify_repo(repo_id: str, db: AsyncSession) -> Repository:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/summary", response_model=SummaryResponse)
async def get_repo_summary(
    repo_id: str,
    regenerate: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await _verify_repo(repo_id, db)
    content = await generate_repo_summary(db, repo)

    top = await db.execute(
        select(CodeNode)
        .where(CodeNode.repo_id == repo_id)
        .order_by(CodeNode.updated_at.desc())
        .limit(10)
    )
    key_files = [
        {"name": n.name, "path": n.path, "type": n.type, "summary": n.summary}
        for n in top.scalars().all()
    ]

    return SummaryResponse(
        path=repo.full_name,
        summary=content,
        key_files=key_files,
        generated_at=None if regenerate else repo.last_analyzed_at,
    )


@router.get("/architecture", response_model=ArchitectureResponse)
async def get_architecture(
    repo_id: str,
    format: str = Query("markdown", pattern="^(markdown|mermaid)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = await _verify_repo(repo_id, db)
    content = await generate_architecture_overview(db, repo)
    return ArchitectureResponse(format=format, content=content)


@router.get("/nodes/{node_id}/summary")
async def get_node_summary(
    repo_id: str,
    node_id: str,
    regenerate: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)
    node = await db.get(CodeNode, node_id)
    if node is None or node.repo_id != repo_id:
        raise HTTPException(status_code=404, detail="Node not found")

    summary = await generate_node_summary(db, node, force=regenerate)
    return {
        "node_id": node_id,
        "summary": summary.content,
        "model": summary.model_used,
        "generated_at": summary.generated_at,
    }
