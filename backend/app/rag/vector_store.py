"""
RAG Vector Store Interface (app/rag/vector_store.py)
Provides local ChromaDB storage and retrieval powered strictly by OllamaEmbeddings(model="nomic-embed-text").
All HuggingFace dependencies have been eliminated.
"""

from app.database.vector_store import (
    LocalVectorStore,
    vector_store,
    OllamaEmbeddings,
    HuggingFaceEmbeddings
)

__all__ = ["LocalVectorStore", "vector_store", "OllamaEmbeddings", "HuggingFaceEmbeddings"]
