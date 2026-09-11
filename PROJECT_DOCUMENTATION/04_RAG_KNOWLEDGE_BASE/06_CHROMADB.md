# 06. ChromaDB Vector Database
**Status:** [VERIFIED]

## 1. File Path & Configuration
`backend/app/rag/vector_store.py`: `ChromaVectorStore`

## 2. Storage & Collection
- **Client:** `chromadb.PersistentClient(path="./chroma_db")`.
- **Storage Backend:** Local SQLite metadata database + Parquet vector index.
- **Collection Name:** `sovereign_knowledge_base`.
- **Current Indexed Contents:** 30 chunks indexed from `demo_data/equipment_sop.md`, `demo_data/correspondence.md`, and safety specifications.
