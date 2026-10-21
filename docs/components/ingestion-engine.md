# Ingestion Engine Component Specification

## Purpose
The Ingestion Engine is responsible for securely cloning target repositories, parsing source files using Tree-Sitter AST grammar queries, extracting structural entity nodes (classes, methods, routes, entities), and computing vector embeddings for downstream retrieval.

## System Dependencies
- **Tree-Sitter**: Multi-language AST parser for TypeScript, JavaScript, and Python.
- **Sentence-Transformers / Ollama**: Vector embedding generation model (`nomic-embed-text`).
- **MinIO / Local Disk**: Object storage container for temporary cloned source files.
- **Celery & Redis**: Background job queue management.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Repository Clone | $O(S)$ | $O(S)$ | Linear with total source repository file size $S$ |
| AST File Parsing | $O(F \cdot L)$ | $O(L_{max})$ | $F$ files, $L$ lines per file; $L_{max}$ max lines in single file |
| Symbol Extraction | $O(N_{ast})$ | $O(N_{nodes})$ | Traversing AST nodes $N_{ast}$ to produce code symbol nodes $N_{nodes}$ |
| Embedding Batch Generation | $O(B \cdot D)$ | $O(B \cdot V)$ | Batch size $B$, text token length $D$, vector dimension $V$ |
| Vector Index Insertion | $O(N_{nodes} \log N_{nodes})$ | $O(N_{nodes} \cdot V)$ | HNSW graph construction complexity in pgvector |

## Failure Modes & Resilience
1. **Parser Exception**: Malformed syntax in source files triggers an immediate non-fatal error log; parsing continues for remaining project files.
2. **Ollama Worker Timeout**: Embedding request retries up to 3 times with exponential backoff before marking node embeddings as deferred.
