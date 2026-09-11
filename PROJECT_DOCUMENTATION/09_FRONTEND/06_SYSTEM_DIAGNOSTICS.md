# 06. System Diagnostics Panel
**Status:** [VERIFIED]

- **Function:** `fetchHealth()` in `frontend/index.html`.
- **Workflow:** Polls `GET /api/health` -> renders real-time status cards for Ollama port 11434, Tesseract version 5.4.0, and ChromaDB collection status.
