from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/flight-simulator", tags=["flight-simulator"])


class Mission(BaseModel):
    id: str
    title: str
    track: str
    difficulty: str
    reward_badge_tier: str
    description: str


class SessionCreateResponse(BaseModel):
    session_id: str
    mission_id: str
    current_branch: str
    status: str


class GitCommandRequest(BaseModel):
    command: str


class GitCommandResponse(BaseModel):
    stdout: str
    stderr: Optional[str] = None
    current_branch: str
    dag_state: Dict[str, Any]


class PRReviewBotComment(BaseModel):
    file: str
    line: int
    message: str


class PRReviewResponse(BaseModel):
    pr_number: int
    status: str
    ci_checks: Dict[str, str]
    bot_comments: List[PRReviewBotComment]


MISSIONS_CATALOG = [
    Mission(
        id="mission_git_01",
        title="Branching & First Pull Request",
        track="beginner",
        difficulty="introductory",
        reward_badge_tier="Git Flight Certified",
        description="Master creating feature branches, staging files, committing with conventional messages, and opening your first pull request.",
    ),
    Mission(
        id="mission_git_02",
        title="Upstream Merge Conflict Resolution",
        track="intermediate",
        difficulty="moderate",
        reward_badge_tier="Conflict Master",
        description="Learn how to inspect merge conflict markers, resolve upstream differences safely, and finalize clean merge commits.",
    ),
    Mission(
        id="mission_git_03",
        title="Interactive Rebase & Commit Squashing",
        track="advanced",
        difficulty="challenging",
        reward_badge_tier="Architectural Contributor",
        description="Reorder, reword, and squash messy commit histories before upstream merging into main.",
    ),
]


@router.get("/missions", response_model=List[Mission])
async def list_missions():
    """
    Returns available Flight Simulator learning missions.
    """
    return MISSIONS_CATALOG


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(mission_id: str):
    """
    Spawns a new in-memory virtual Git flight simulation session.
    """
    session_id = f"flight_{uuid4().hex[:10]}"
    return SessionCreateResponse(
        session_id=session_id,
        mission_id=mission_id,
        current_branch="main",
        status="in_progress",
    )


@router.post("/sessions/{session_id}/command", response_model=GitCommandResponse)
async def execute_virtual_command(session_id: str, payload: GitCommandRequest):
    """
    Executes a virtual Git CLI command in browser memory.
    """
    cmd = payload.command.strip()

    if cmd.startswith("git checkout -b "):
        branch_name = cmd.split(" ")[-1]
        return GitCommandResponse(
            stdout=f"Switched to a new branch '{branch_name}'",
            current_branch=branch_name,
            dag_state={
                "head": "commit_virtual_01",
                "branches": ["main", branch_name],
            },
        )
    elif cmd == "git status":
        return GitCommandResponse(
            stdout="On branch main\nYour branch is up to date with 'origin/main'.\n\nChanges to be committed:\n  (use 'git restore --staged <file>...' to unstage)\n\tmodified:   README.md",
            current_branch="main",
            dag_state={"head": "commit_virtual_01", "branches": ["main"]},
        )
    elif cmd.startswith("git commit"):
        return GitCommandResponse(
            stdout="[feat/add-badge 8f91a0c] feat: integrate verified contributor badge\n 1 file changed, 5 insertions(+)",
            current_branch="feat/add-badge",
            dag_state={
                "head": "commit_virtual_02",
                "branches": ["main", "feat/add-badge"],
            },
        )
    else:
        return GitCommandResponse(
            stdout=f"Executed: {cmd}",
            current_branch="main",
            dag_state={"head": "commit_virtual_01", "branches": ["main"]},
        )


@router.post("/sessions/{session_id}/pr-review", response_model=PRReviewResponse)
async def submit_simulated_pr(session_id: str):
    """
    Simulates automated CI checks and multi-persona AI review bot feedback.
    """
    return PRReviewResponse(
        pr_number=42,
        status="passed",
        ci_checks={
            "linter": "passed",
            "typecheck": "passed",
            "unit_tests": "passed",
        },
        bot_comments=[
            PRReviewBotComment(
                file="README.md",
                line=14,
                message="Excellent addition of the verifiable badge embed! Conventional commit format looks crisp.",
            )
        ],
    )

