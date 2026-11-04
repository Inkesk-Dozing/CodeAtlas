"""add composite and trigram indexes for subgraph traversal

Revision ID: 0003_subgraph_traversal_indexes
Revises: 0002_ingestion_errors
Create Date: 2026-11-03
"""
from alembic import op

revision = "0003_subgraph_traversal_indexes"
down_revision = "0002_ingestion_errors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pg_trgm extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2. Composite B-tree indexes on code_edges for bidirectional traversal
    op.create_index(
        "idx_edges_source_target",
        "code_edges",
        ["source_id", "target_id"],
    )
    op.create_index(
        "idx_edges_target_source",
        "code_edges",
        ["target_id", "source_id"],
    )

    # 3. Trigram GIN index on code_nodes(name, path) for substring search
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_nodes_trgm_name_path ON code_nodes "
        "USING gin (name gin_trgm_ops, path gin_trgm_ops);"
    )


def downgrade() -> None:
    op.drop_index("idx_nodes_trgm_name_path", table_name="code_nodes")
    op.drop_index("idx_edges_target_source", table_name="code_edges")
    op.drop_index("idx_edges_source_target", table_name="code_edges")
