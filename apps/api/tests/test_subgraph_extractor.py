"""Unit and integration tests for Subgraph Exploration & Neighborhood Extraction (Issue #48)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from models import CodeEdge, CodeNode
from services.graph_builder.subgraph_extractor import SubgraphExtractor


@pytest.fixture
def mock_subgraph_data() -> tuple[dict[str, CodeNode], list[CodeEdge]]:
    # Create node graph:
    # A (controller) -> B (service) -> C (database model)
    # D (external caller) -> A (controller)
    node_a = CodeNode(id="node_a", repo_id="repo_1", name="AuthController", type="controller", path="auth/controller.py")
    node_b = CodeNode(id="node_b", repo_id="repo_1", name="AuthService", type="service", path="auth/service.py")
    node_c = CodeNode(id="node_c", repo_id="repo_1", name="UserModel", type="model", path="auth/user.py")
    node_d = CodeNode(id="node_d", repo_id="repo_1", name="ExternalRouter", type="route", path="api/router.py")

    nodes = {"node_a": node_a, "node_b": node_b, "node_c": node_c, "node_d": node_d}

    edge_1 = CodeEdge(id="e1", repo_id="repo_1", source_id="node_d", target_id="node_a", type="calls")
    edge_2 = CodeEdge(id="e2", repo_id="repo_1", source_id="node_a", target_id="node_b", type="calls")
    edge_3 = CodeEdge(id="e3", repo_id="repo_1", source_id="node_b", target_id="node_c", type="uses")

    edges = [edge_1, edge_2, edge_3]
    return nodes, edges


@pytest.mark.asyncio
async def test_subgraph_downstream_traversal(mock_subgraph_data: tuple[dict[str, CodeNode], list[CodeEdge]]) -> None:
    nodes_dict, all_edges = mock_subgraph_data
    mock_db = AsyncMock()

    # Step 1: Mock seed node query
    mock_seed_result = MagicMock()
    mock_seed_result.scalars.return_value.all.return_value = [nodes_dict["node_a"]]

    # Step 2: Mock edge query for downstream (source in frontier)
    # From node_a -> node_b (e2)
    mock_edge_result = MagicMock()
    mock_edge_result.scalars.return_value.all.return_value = [all_edges[1]]

    # Step 3: Mock node query
    mock_nodes_result = MagicMock()
    mock_nodes_result.scalars.return_value.all.return_value = [nodes_dict["node_a"], nodes_dict["node_b"]]

    mock_db.execute.side_effect = [mock_seed_result, mock_edge_result, mock_nodes_result]

    extractor = SubgraphExtractor(db=mock_db, repo_id="repo_1")
    nodes, edges = await extractor.extract_subgraph(
        node_ids=["node_a"],
        depth=1,
        direction="downstream",
    )

    # Acceptance criteria: Downstream traversal only finds dependencies/callees
    node_ids = {n.id for n in nodes}
    assert "node_a" in node_ids
    assert "node_b" in node_ids
    assert "node_d" not in node_ids  # Upstream caller excluded
    assert len(edges) == 1
    assert edges[0].id == "e2"


@pytest.mark.asyncio
async def test_subgraph_upstream_traversal(mock_subgraph_data: tuple[dict[str, CodeNode], list[CodeEdge]]) -> None:
    nodes_dict, all_edges = mock_subgraph_data
    mock_db = AsyncMock()

    # Seed node: node_a
    mock_seed_result = MagicMock()
    mock_seed_result.scalars.return_value.all.return_value = [nodes_dict["node_a"]]

    # Upstream: target in frontier -> finds e1 (node_d -> node_a)
    mock_edge_result = MagicMock()
    mock_edge_result.scalars.return_value.all.return_value = [all_edges[0]]

    mock_nodes_result = MagicMock()
    mock_nodes_result.scalars.return_value.all.return_value = [nodes_dict["node_a"], nodes_dict["node_d"]]

    mock_db.execute.side_effect = [mock_seed_result, mock_edge_result, mock_nodes_result]

    extractor = SubgraphExtractor(db=mock_db, repo_id="repo_1")
    nodes, edges = await extractor.extract_subgraph(
        node_ids=["node_a"],
        depth=1,
        direction="upstream",
    )

    # Acceptance criteria: Upstream traversal only finds callers/consumers
    node_ids = {n.id for n in nodes}
    assert "node_a" in node_ids
    assert "node_d" in node_ids
    assert "node_b" not in node_ids  # Downstream dependency excluded
    assert len(edges) == 1
    assert edges[0].id == "e1"


@pytest.mark.asyncio
async def test_subgraph_empty_seed_nodes() -> None:
    mock_db = AsyncMock()
    extractor = SubgraphExtractor(db=mock_db, repo_id="repo_1")
    nodes, edges = await extractor.extract_subgraph(node_ids=[])
    assert nodes == []
    assert edges == []
