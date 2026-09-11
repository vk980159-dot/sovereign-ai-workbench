# 02. Tool: `read_document`
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/doc_tools.py`
- **Function:** `read_document(file_path: str)`
- **Purpose:** Reads text from local files (.txt, .md, .pdf).
- **Security:** Restricted via `validate_sandbox_path()` to `multimodal_uploads/` and `demo_data/`. Traversal attempts raise `PermissionError`.
