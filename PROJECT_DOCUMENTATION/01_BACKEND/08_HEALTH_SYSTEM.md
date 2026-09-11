# 08. System Health & Diagnostics (`backend/app/api/router.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/api/router.py:get_health_status()`

## 2. File Purpose
Provides a comprehensive runtime health and readiness check for the entire workstation.

## 3. Subsystem Checks
1. **Ollama Daemon:** Sends HTTP GET to `http://127.0.0.1:11434/api/tags`. Confirms daemon is active and lists resident models.
2. **Tesseract OCR:** Executes `tesseract --version` via subprocess. Confirms binary is executable and returns version string (v5.4.0).
3. **ChromaDB:** Calls `vector_store.get_collection_stats()`. Confirms collection `sovereign_knowledge_base` is accessible.
4. **SQLite Databases:** Queries `auth.db` and `tasks.db` to confirm read/write availability.
5. **Runtime Mode:** Reports whether system is in `LOCAL_AIR_GAPPED`, `PUBLIC_SHARE`, or `CLOUD_DEMO` mode.
