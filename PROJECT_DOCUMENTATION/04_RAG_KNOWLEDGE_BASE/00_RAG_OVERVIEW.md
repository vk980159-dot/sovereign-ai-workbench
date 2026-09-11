# 00. RAG & Local Knowledge Base Overview
**Status:** [VERIFIED]

## Architecture Summary
Retrieval-Augmented Generation (RAG) ensures that the agent answers engineering questions and audits machinery based strictly on verified on-premise documentation rather than LLM training memory.

## Core Components
- **Vector Store:** ChromaDB (`chromadb.PersistentClient`) in `chroma_db/`.
- **Collection:** `sovereign_knowledge_base` (30 active verified chunks).
- **Embedding Model:** `nomic-embed-text:latest` (768 dimensions).
- **Document Ingestion:** PyMuPDF (`fitz`) + Tesseract OCR v5.4.0 + PII Redactor.
- **Retrieval Engine:** Cosine similarity search returning ranked chunks with metadata.
