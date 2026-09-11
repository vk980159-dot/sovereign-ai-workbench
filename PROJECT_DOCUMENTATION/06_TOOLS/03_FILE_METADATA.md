# 03. Tool: File Metadata & Inspection
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/doc_tools.py`
- **Function:** `get_file_info(file_path: str)`
- **Purpose:** Returns file size, MIME type, last modified timestamp, and SHA-256 hash.
- **Security:** Sandboxed directory access.
