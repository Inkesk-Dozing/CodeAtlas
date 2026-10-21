# RAG Chat Engine Component Specification

## Purpose
The RAG (Retrieval-Augmented Generation) Chat Engine enables interactive natural language Q&A across the repository context, retrieving top matching code nodes and assembling prompt contexts for streaming LLM responses.

## System Dependencies
- **Ollama / CodeLlama 7B**: Local LLM execution engine.
- **pgvector**: Semantic retrieval store.
- **Server-Sent Events (SSE)**: Real-time token streaming to frontend interface.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Query Vector Embedding | $O(L_{query} \cdot D)$ | $O(V_{dim})$ | Embedding generation for user prompt |
| Vector Nearest Neighbor Search | $O(\log N)$ | $O(K \cdot V_{dim})$ | Retrieving top-$K$ context nodes |
| Prompt Construction | $O(K \cdot C_{node})$ | $O(K \cdot C_{node})$ | Formatting $K$ code snippets into prompt window |
| Streaming Inference | $O(N_{tokens} \cdot M_{model})$ | $O(M_{context})$ | LLM autoregressive token generation |
