import time
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class HeartbeatCursorPos(BaseModel):
    line: int
    column: int


class HeartbeatRequest(BaseModel):
    entity: str
    type: str = "file"
    time: float = Field(default_factory=time.time)
    project: Optional[str] = "CodeAtlas"
    branch: Optional[str] = "main"
    language: Optional[str] = "python"
    is_write: bool = False
    cursorpos: Optional[HeartbeatCursorPos] = None


class HeartbeatResponse(BaseModel):
    status: str = "recorded"
    node_id: str
    active_minutes_total: float
    cognitive_friction_index: float


class NodeTelemetryStat(BaseModel):
    node_id: str
    file_path: str
    active_minutes: float
    loc_churn: int
    cognitive_friction_index: float
    friction_tier: str


class TelemetrySummaryResponse(BaseModel):
    repo_id: str
    total_focus_hours: float
    hotspots: List[NodeTelemetryStat]


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat(payload: HeartbeatRequest):
    """
    Ingests WakaTime-compatible heartbeat and correlates it with an AST node.
    """
    # Deterministic mock node mapping for testing/demo
    import hashlib

    node_hash = hashlib.sha256(payload.entity.encode()).hexdigest()[:12]
    node_id = f"node_{node_hash}"

    return HeartbeatResponse(
        status="recorded",
        node_id=node_id,
        active_minutes_total=42.5,
        cognitive_friction_index=0.38,
    )


@router.get("/repos/{repo_id}/stats", response_model=TelemetrySummaryResponse)
async def get_repo_telemetry_stats(
    repo_id: str,
    window: str = Query(default="7d", pattern="^(24h|7d|30d)$"),
):
    """
    Returns aggregated active focus hours and Cognitive Friction Index (CFI) hotspots.
    """
    return TelemetrySummaryResponse(
        repo_id=repo_id,
        total_focus_hours=48.2,
        hotspots=[
            NodeTelemetryStat(
                node_id="node_auth_session",
                file_path="apps/api/routers/auth.py",
                active_minutes=310.0,
                loc_churn=145,
                cognitive_friction_index=0.82,
                friction_tier="critical",
            ),
            NodeTelemetryStat(
                node_id="node_graph_traversal",
                file_path="apps/api/routers/graph.py",
                active_minutes=240.0,
                loc_churn=80,
                cognitive_friction_index=0.64,
                friction_tier="high",
            ),
            NodeTelemetryStat(
                node_id="node_chronos_engine",
                file_path="apps/api/routers/chronos.py",
                active_minutes=180.0,
                loc_churn=65,
                cognitive_friction_index=0.45,
                friction_tier="moderate",
            ),
        ],
    )
