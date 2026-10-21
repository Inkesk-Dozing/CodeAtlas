from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─── Auth ────────────────────────────────────────────────────────────────────

class AuthCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(ORMModel):
    id: str
    github_id: int
    username: str
    email: str | None
    avatar_url: str | None
    name: str | None
    created_at: datetime


# ─── Repository ──────────────────────────────────────────────────────────────

class RepositorySettings(BaseModel):
    ignored_paths: list[str] = Field(default_factory=lambda: [
        "node_modules/**", "dist/**", ".git/**", "*.lock",
    ])
    analysis_depth: str = "full"
    generate_docs: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"


class RepositoryCreate(BaseModel):
    github_id: int = Field(..., gt=0)
    installation_id: int = Field(..., gt=0)
    name: str
    full_name: str
    owner: str
    clone_url: str
    default_branch: str = "main"
    is_private: bool = True
    language: str | None = None
    description: str | None = None
    settings: RepositorySettings = Field(default_factory=RepositorySettings)


class RepositoryResponse(ORMModel):
    id: str
    github_id: int
    installation_id: int
    name: str
    full_name: str
    owner: str
    default_branch: str
    is_private: bool
    language: str | None
    description: str | None
    status: str
    error_message: str | None
    last_analyzed_at: datetime | None
    last_analyzed_sha: str | None
    node_count: int
    edge_count: int
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class RepositoryUpdate(BaseModel):
    settings: RepositorySettings | None = None
    status: str | None = None


class RepositoryStats(BaseModel):
    node_count: int
    edge_count: int
    by_type: dict[str, int]
    by_language: dict[str, int]
    last_ingestion: dict[str, Any] | None = None


# ─── Graph ───────────────────────────────────────────────────────────────────

class CodeNodeResponse(ORMModel):
    id: str
    repo_id: str
    type: str
    name: str
    path: str
    language: str | None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="meta")
    summary: str | None
    created_at: datetime
    updated_at: datetime


class CodeEdgeResponse(ORMModel):
    id: str
    repo_id: str
    source_id: str
    target_id: str
    type: str
    weight: float
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="meta")
    created_at: datetime


class GraphResponse(BaseModel):
    nodes: list[CodeNodeResponse]
    edges: list[CodeEdgeResponse]
    next_cursor: str | None = None
    has_more: bool = False
    total: int = 0


class GraphQuery(BaseModel):
    limit: int = Field(default=500, ge=1, le=2000)
    cursor: str | None = None
    types: list[str] | None = None
    languages: list[str] | None = None
    min_complexity: float | None = None
    max_complexity: float | None = None


class SubgraphQuery(BaseModel):
    center_node_id: str
    radius: int = Field(default=2, ge=1, le=5)
    edge_types: list[str] | None = None
    max_nodes: int = Field(default=200, ge=10, le=500)


class NodeDetailResponse(CodeNodeResponse):
    neighbors: dict[str, list[CodeEdgeResponse]] | None = None
    code_preview: str | None = None


# ─── Search ──────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    types: list[str] | None = None
    threshold: float = Field(default=0.3, ge=0.0, le=1.0)


class SearchResultResponse(BaseModel):
    node: CodeNodeResponse
    score: float
    match_type: str
    snippet: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResultResponse]
    took_ms: int


# ─── Ingestion ───────────────────────────────────────────────────────────────

class IngestionTrigger(BaseModel):
    mode: str = Field(default="full", pattern="^(full|incremental)$")
    branch: str | None = None
    force: bool = False


class IngestionStatusResponse(BaseModel):
    id: str
    repo_id: str
    mode: str
    status: str
    current_stage: str | None
    progress: int
    branch: str | None
    commit_sha: str | None
    files_total: int
    files_processed: int
    nodes_created: int
    edges_created: int
    error: str | None
    stage_timings: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


# ─── Issue Mapping ───────────────────────────────────────────────────────────

class IssueResponse(BaseModel):
    id: str
    repo_id: str
    number: int
    title: str
    body: str | None
    state: str
    labels: list[str]
    assignees: list[str]
    author: str | None
    url: str | None
    closed_at: datetime | None


class MappingEvidence(BaseModel):
    semantic_match: bool = False
    structural_match: bool = False
    historical_match: bool = False
    propagation_match: bool = False
    matched_keywords: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)


class CodeMapping(BaseModel):
    node: CodeNodeResponse
    confidence: float
    confidence_tier: str
    evidence: MappingEvidence
    suggested_actions: list[str] = Field(default_factory=list)


class IssueMappingResponse(BaseModel):
    issue_number: int
    status: str
    mappings: list[CodeMapping]
    model_version: str
    generated_at: datetime | None


class IssueAnalyzeRequest(BaseModel):
    include_comments: bool = True
    max_comments: int = Field(default=10, ge=0, le=50)
    force_refresh: bool = False


class MappingFeedbackRequest(BaseModel):
    node_id: str
    rating: str = Field(..., pattern="^(relevant|partially_relevant|irrelevant)$")
    comment: str | None = Field(None, max_length=1000)


# ─── Summaries ───────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    path: str
    summary: str
    key_files: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime | None = None


class ArchitectureResponse(BaseModel):
    format: str
    content: str


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


class ChatCitation(BaseModel):
    node_id: str
    path: str
    snippet: str
    relevance: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]
    session_id: str
    tokens_used: int | None = None


# ─── Webhook ─────────────────────────────────────────────────────────────────

class WebhookResponse(BaseModel):
    received: bool
    event: str
    delivery_id: str


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    checks: dict[str, str]
    timestamp: datetime
