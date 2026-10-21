import uuid
from datetime import datetime

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import BYTEA, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    github_org_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    quota: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "max_repos": 5,
            "max_ingestions_per_month": 100,
            "max_api_calls_per_day": 1000,
        },
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))

    members: Mapped[list["OrgMember"]] = relationship(back_populates="org", lazy="selectin")
    repositories: Mapped[list["Repository"]] = relationship(back_populates="org", lazy="selectin")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    github_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(String(255))
    github_token_encrypted: Mapped[bytes | None] = mapped_column(BYTEA)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    memberships: Mapped[list["OrgMember"]] = relationship(back_populates="user", lazy="selectin")


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_member"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    org_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    invited_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    org: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class GitHubInstallation(Base, TimestampMixin):
    __tablename__ = "github_installations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    org_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    github_account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    github_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    org_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    language: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    clone_url: Mapped[str] = mapped_column(Text, nullable=False)
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "ignored_paths": ["node_modules/**", "dist/**", ".git/**", "*.lock"],
            "analysis_depth": "full",
            "generate_docs": True,
            "embedding_model": "all-MiniLM-L6-v2",
        },
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_analyzed_sha: Mapped[str | None] = mapped_column(String(40))
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    org: Mapped["Organization | None"] = relationship(back_populates="repositories")
    nodes: Mapped[list["CodeNode"]] = relationship(back_populates="repo", lazy="noload")
    edges: Mapped[list["CodeEdge"]] = relationship(back_populates="repo", lazy="noload")


class IngestionTask(Base, TimestampMixin):
    __tablename__ = "ingestion_tasks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    triggered_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="full")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    current_stage: Mapped[str | None] = mapped_column(String(50))
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    branch: Mapped[str | None] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(40))
    files_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nodes_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edges_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    error_stage: Mapped[str | None] = mapped_column(String(50))
    stage_timings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CodeNode(Base, TimestampMixin):
    __tablename__ = "code_nodes"
    __table_args__ = (
        UniqueConstraint("repo_id", "path", "name", "type", name="uq_node_identity"),
        Index("idx_nodes_repo_type", "repo_id", "type"),
        Index("idx_nodes_repo_path", "repo_id", "path"),
        Index("idx_nodes_repo_language", "repo_id", "language"),
        Index("idx_nodes_embedding", "embedding", postgresql_using="hnsw"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50))
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    embedding = mapped_column(VECTOR(384), nullable=True)
    search_vector = mapped_column(TSVECTOR, nullable=True)

    repo: Mapped["Repository"] = relationship(back_populates="nodes")

    outgoing_edges: Mapped[list["CodeEdge"]] = relationship(
        back_populates="source_node",
        foreign_keys="CodeEdge.source_id",
        lazy="noload",
    )
    incoming_edges: Mapped[list["CodeEdge"]] = relationship(
        back_populates="target_node",
        foreign_keys="CodeEdge.target_id",
        lazy="noload",
    )


class CodeEdge(Base, TimestampMixin):
    __tablename__ = "code_edges"
    __table_args__ = (
        UniqueConstraint("repo_id", "source_id", "target_id", "type", name="uq_edge_identity"),
        Index("idx_edges_source", "source_id"),
        Index("idx_edges_target", "target_id"),
        Index("idx_edges_type", "repo_id", "type"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    meta: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    repo: Mapped["Repository"] = relationship(back_populates="edges")
    source_node: Mapped["CodeNode"] = relationship(foreign_keys=[source_id], back_populates="outgoing_edges")
    target_node: Mapped["CodeNode"] = relationship(foreign_keys=[target_id], back_populates="incoming_edges")


class Issue(Base, TimestampMixin):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("repo_id", "number", name="uq_issue_repo_number"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    github_issue_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    labels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    assignees: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    author: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(Text)
    embedding = mapped_column(VECTOR(384), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IssueMapping(Base, TimestampMixin):
    __tablename__ = "issue_mappings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False
    )
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    mappings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0.0")
    generation_ms: Mapped[int | None] = mapped_column(Integer)
    validated: Mapped[bool | None] = mapped_column(Boolean)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MappingFeedback(Base):
    __tablename__ = "mapping_feedback"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    mapping_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("issue_mappings.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    rating: Mapped[str] = mapped_column(String(30), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class NodeSummary(Base):
    __tablename__ = "node_summaries"
    __table_args__ = (UniqueConstraint("node_id", "summary_type", name="uq_node_summary"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    node_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False
    )
    summary_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    source_hash: Mapped[str | None] = mapped_column(String(64))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(500))

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", lazy="selectin", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"))
    org_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
