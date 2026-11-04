"""tune HNSW cosine index on code_nodes embedding

Revision ID: 0004_hnsw_cosine_index_tuning
Revises: 0003_subgraph_traversal_indexes
Create Date: 2026-11-03
"""
from alembic import op

revision = "0004_hnsw_cosine_index_tuning"
down_revision = "0003_subgraph_traversal_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop previous untuned index if exists
    op.execute("DROP INDEX IF EXISTS idx_nodes_embedding;")

    # Recreate tuned HNSW index with vector_cosine_ops, m=16, ef_construction=64
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_nodes_embedding ON code_nodes "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_nodes_embedding;")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_nodes_embedding ON code_nodes "
        "USING hnsw (embedding);"
    )
