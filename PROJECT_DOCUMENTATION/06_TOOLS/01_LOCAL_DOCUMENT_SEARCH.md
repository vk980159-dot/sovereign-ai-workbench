# 01. Tool: `rag_search`
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/doc_tools.py`
- **Function:** `rag_search(query: str, top_k: int = 4)`
- **Purpose:** Dense semantic vector retrieval across indexed plant SOPs and manuals in ChromaDB.
- **Input:** Search query string.
- **Output:** Ranked list of chunks with source metadata and similarity scores.
- **Security:** Local loopback only; zero external internet queries.
