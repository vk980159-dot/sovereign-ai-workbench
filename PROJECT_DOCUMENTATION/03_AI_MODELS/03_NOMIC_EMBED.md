# 03. Nomic Embed Text v1.5 Model
**Status:** [VERIFIED ACTIVE]

- **Model Tag:** `nomic-embed-text:latest`
- **Output Dimensions:** 768-dimensional dense float vector
- **Where Loaded:** Local Ollama daemon (`http://127.0.0.1:11434/api/embeddings`)
- **Where Called:** `backend/app/rag/vector_store.py:ChromaVectorStore`
- **Why Used:** High MTEB retrieval benchmark score for dense semantic passage matching; supports 8,192 token input contexts.
- **Task Types:** Embedding document chunks during ingestion; embedding user queries during RAG search.
