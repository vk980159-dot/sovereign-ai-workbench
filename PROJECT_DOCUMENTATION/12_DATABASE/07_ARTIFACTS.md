# 07. Artifacts Table (`tasks.db:artifacts`)
**Status:** [VERIFIED]

## Schema
- `id TEXT PRIMARY KEY`: Artifact UUID.
- `task_id TEXT`: Foreign key linking to `tasks.id`.
- `file_path TEXT`: Absolute path in `generated_artifacts/`.
- `artifact_type TEXT`: `DOCX` | `XLSX` | `PPTX` | `PDF` | `MARKDOWN`.
- `size_bytes INTEGER`: Byte count.
- `sha256 TEXT`: Verified deliverable SHA-256 checksum.
- `created_at TEXT`: Timestamp.
- **Current Verified Count:** 43 generated deliverable records.
