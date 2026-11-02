"""Tests for CodeNode & CodeEdge composite and trigram indexes optimization."""

import importlib

from models.entities import CodeEdge, CodeNode


def test_code_edge_composite_indexes_configured():
    index_names = {idx.name for idx in CodeEdge.__table__.indexes}
    assert "idx_edges_source_target" in index_names
    assert "idx_edges_target_source" in index_names

    # Check columns indexed
    source_target = next(idx for idx in CodeEdge.__table__.indexes if idx.name == "idx_edges_source_target")
    target_source = next(idx for idx in CodeEdge.__table__.indexes if idx.name == "idx_edges_target_source")

    assert [col.name for col in source_target.columns] == ["source_id", "target_id"]
    assert [col.name for col in target_source.columns] == ["target_id", "source_id"]


def test_code_node_trigram_and_filter_indexes_configured():
    index_names = {idx.name for idx in CodeNode.__table__.indexes}
    assert "idx_nodes_trgm_name_path" in index_names
    assert "idx_nodes_repo_type" in index_names

    trgm_idx = next(idx for idx in CodeNode.__table__.indexes if idx.name == "idx_nodes_trgm_name_path")
    assert [col.name for col in trgm_idx.columns] == ["name", "path"]
    assert trgm_idx.dialect_options.get("postgresql", {}).get("using") == "gin"


def test_migration_0003_definition():
    migration_mod = importlib.import_module("migrations.versions.0003_subgraph_traversal_indexes")
    assert migration_mod.revision == "0003_subgraph_traversal_indexes"
    assert migration_mod.down_revision == "0002_ingestion_errors"
    assert callable(migration_mod.upgrade)
    assert callable(migration_mod.downgrade)
