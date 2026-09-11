# 06. Uploaded Files Table (`tasks.db:uploaded_files`)
**Status:** [VERIFIED]

## Schema
- `id TEXT PRIMARY KEY`: Upload UUID.
- `original_name TEXT`: Original filename.
- `stored_path TEXT`: Absolute path in `multimodal_uploads/`.
- `file_type TEXT`: MIME type (`application/pdf`, etc.).
- `size_bytes INTEGER`: Exact byte count.
- `sha256 TEXT`: Pre-computed cryptographic checksum.
- `uploaded_at TEXT`: Timestamp.
- **Current Verified Count:** 49 uploaded file records.
