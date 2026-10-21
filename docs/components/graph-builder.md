# Graph Builder Component Specification

## Purpose
The Graph Builder compiles AST symbol nodes and relational references into a multi-layered dependency graph structure. It resolves cross-file import statements, component hierarchy relationships, and database schema mappings.

## System Dependencies
- **SQLAlchemy 2.0**: Relational persistence and batch operations.
- **PostgreSQL pgvector**: Hybrid relational-vector database storage.
- **React Flow (Frontend)**: Client-side visualization library rendering node and edge payloads.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Import Symbol Resolution | $O(E \cdot \log N)$ | $O(E)$ | Edge symbol lookup against indexed node dictionary |
| Neighborhood Extraction | $O(V_{sub} + E_{sub})$ | $O(V_{sub} + E_{sub})$ | BFS/DFS traversal up to depth $d$ |
| Graph Layout (Dagre) | $O(V \cdot E)$ | $O(V + E)$ | Hierarchical layout calculation for UI rendering |

---

# Issue Mapper Component Specification

## Purpose
The Issue Mapper translates unstructured GitHub issues (text, stack traces, user reports) into precise codebase node targets, providing engineers with confidence-scored mappings and visual graph highlights.

## System Dependencies
- **pgvector HNSW Index**: Vector similarity search over `code_nodes`.
- **FastAPI**: Backend REST API serving issue analysis requests.
- **TF-IDF & Pattern Regex**: Keyword and symbol pattern extraction from issue bodies.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Text Pattern Extraction | $O(T)$ | $O(K)$ | Parsing $T$ text characters for $K$ target keywords/file paths |
| HNSW Vector Query | $O(\log N_{nodes})$ | $O(k_{neighbors})$ | Approximate nearest neighbor vector search for top-$k$ matches |
| Subgraph Candidate Expansion | $O(k \cdot d_{avg})$ | $O(k \cdot d_{avg})$ | Expanding top-$k$ nodes to 1-hop adjacent graph neighbors |
