"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("github_org_id", sa.BigInteger, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("settings", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("quota", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("github_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), index=True),
        sa.Column("avatar_url", sa.Text),
        sa.Column("name", sa.String(255)),
        sa.Column("github_token_encrypted", sa.LargeBinary),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("settings", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "org_members",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )

    op.create_table(
        "github_installations",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("installation_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id")),
        sa.Column("github_account_name", sa.String(255), nullable=False),
        sa.Column("github_account_type", sa.String(50), nullable=False),
        sa.Column("permissions", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("suspended", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("github_id", sa.BigInteger, nullable=False, unique=True, index=True),
        sa.Column("installation_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(500), nullable=False, unique=True, index=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("is_private", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("language", sa.String(50)),
        sa.Column("description", sa.Text),
        sa.Column("clone_url", sa.Text, nullable=False),
        sa.Column("settings", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("error_message", sa.Text),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True)),
        sa.Column("last_analyzed_sha", sa.String(40)),
        sa.Column("node_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ingestion_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("mode", sa.String(50), nullable=False, server_default="full"),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued", index=True),
        sa.Column("current_stage", sa.String(50)),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("branch", sa.String(255)),
        sa.Column("commit_sha", sa.String(40)),
        sa.Column("files_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("files_processed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("nodes_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("edges_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text),
        sa.Column("error_stage", sa.String(50)),
        sa.Column("stage_timings", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "code_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("language", sa.String(50)),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("summary", sa.Text),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("embedding", postgresql.VECTOR(384)),
        sa.Column("search_vector", postgresql.TSVECTOR()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("repo_id", "path", "name", "type", name="uq_node_identity"),
    )
    op.create_index("idx_nodes_repo_type", "code_nodes", ["repo_id", "type"])
    op.create_index("idx_nodes_repo_path", "code_nodes", ["repo_id", "path"])
    op.create_index("idx_nodes_embedding", "code_nodes", ["embedding"], postgresql_using="hnsw")
    op.create_index("idx_nodes_search", "code_nodes", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "code_edges",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("repo_id", "source_id", "target_id", "type", name="uq_edge_identity"),
    )
    op.create_index("idx_edges_source", "code_edges", ["source_id"])
    op.create_index("idx_edges_target", "code_edges", ["target_id"])
    op.create_index("idx_edges_type", "code_edges", ["repo_id", "type"])

    op.create_table(
        "issues",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_issue_id", sa.BigInteger, nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("state", sa.String(20), nullable=False, server_default="open"),
        sa.Column("labels", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("assignees", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("author", sa.String(255)),
        sa.Column("url", sa.Text),
        sa.Column("embedding", postgresql.VECTOR(384)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("repo_id", "number", name="uq_issue_repo_number"),
    )

    op.create_table(
        "issue_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("issue_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("mappings", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="v1.0.0"),
        sa.Column("generation_ms", sa.Integer),
        sa.Column("validated", sa.Boolean),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "mapping_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("mapping_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("issue_mappings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.String(30), nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "node_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("node_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("code_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("source_hash", sa.String(64)),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("node_id", "summary_type", name="uq_node_summary"),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("citations", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id")),
        sa.Column("org_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("organizations.id")),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=False)),
        sa.Column("details", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION nodes_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.path, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'C') ||
                setweight(to_tsvector('english', COALESCE(NEW.metadata->>'docstring', '')), 'D');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER nodes_search_update
        BEFORE INSERT OR UPDATE ON code_nodes
        FOR EACH ROW EXECUTE FUNCTION nodes_search_vector_update();
    """)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("node_summaries")
    op.drop_table("mapping_feedback")
    op.drop_table("issue_mappings")
    op.drop_table("issues")
    op.drop_table("code_edges")
    op.drop_table("code_nodes")
    op.drop_table("ingestion_tasks")
    op.drop_table("repositories")
    op.drop_table("github_installations")
    op.drop_table("org_members")
    op.drop_table("users")
    op.drop_table("organizations")
