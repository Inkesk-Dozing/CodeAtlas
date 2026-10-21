
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ChatSession, Repository, User
from schemas import ChatRequest, ChatResponse
from services.ai import chat as chat_service
from services.auth import get_current_user

router = APIRouter(prefix="/repos/{repo_id}/chat", tags=["chat"])


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list = Field(default_factory=list)
    created_at: str


async def _verify_repo(repo_id: str, db: AsyncSession) -> Repository:
    repo = await db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("", response_model=ChatResponse)
async def ask_question(
    repo_id: str,
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)

    if payload.session_id:
        session = await db.get(ChatSession, payload.session_id)
        if session is None or session.repo_id != repo_id or session.user_id != user.id:
            raise HTTPException(status_code=404, detail="Session not found")

    return await chat_service.ask(
        db,
        repo_id,
        user.id,
        payload.question,
        session_id=payload.session_id,
        history=payload.history,
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    repo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)
    sessions = await chat_service.list_sessions(db, repo_id, user.id)
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=list[MessageResponse])
async def get_session(
    repo_id: str,
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)
    session = await db.get(ChatSession, session_id)
    if session is None or session.repo_id != repo_id or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await chat_service.get_session_messages(db, session_id)
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    repo_id: str,
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_repo(repo_id, db)
    session = await db.get(ChatSession, session_id)
    if session is None or session.repo_id != repo_id or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.flush()
