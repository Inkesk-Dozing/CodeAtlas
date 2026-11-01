"""add ingestion_errors table

Revision ID: 0002_ingestion_errors
Revises: 0001_initial
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_ingestion_errors"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_errors",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("ingestion_tasks.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("error_stage", sa.String(50)),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text()),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_errors")

