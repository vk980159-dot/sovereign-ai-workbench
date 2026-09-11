# 07. Semantic Retrieval Engine
**Status:** [VERIFIED]

## 1. File Path & Query Flow
`backend/app/rag/vector_store.py`: `similarity_search(query: str, top_k: int = 4)`

## 2. Processing Steps
1. User query string converted to 768-dim vector via `nomic-embed-text:latest`.
2. ChromaDB queries collection using cosine distance metric.
3. Returns top-k matching document chunks with text, source file name, and similarity score.
4. Feeds retrieved chunks into agent context for factual grounding.
