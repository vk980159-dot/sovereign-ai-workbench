# 07. Tool: `save_text_artifact`
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/artifact_tools.py`
- **Function:** `save_text_artifact(filename: str, content: str)`
- **Purpose:** Persists raw Markdown, TXT, or JSON reports to `generated_artifacts/`.
- **Security:** Filename sanitized; path traversal blocked.
