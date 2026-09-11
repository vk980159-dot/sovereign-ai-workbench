# 07. File Upload Validation & Security
**Status:** [VERIFIED]

## 1. File Path
`backend/app/api/router.py`: `upload_document()`

## 2. Security Controls
1. **Extension Whitelisting:** Allowed: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.txt`, `.md`.
2. **Magic Byte Verification:** Inspects binary headers (`%PDF-` for PDFs, `PNG` for PNGs, `ÿØÿ` for JPEGs).
3. **Filename Sanitization:** Strips path separators, spaces, and non-alphanumeric characters. Prefixes unique UUID (`file_124b93e5_...`).
4. **Payload Size Capping:** Hard maximum limit of 10 MB per upload to prevent memory exhaustion DoS.
5. **Cryptographic Checksum:** Computes SHA-256 hash immediately upon upload; logged to `tasks.db:uploaded_files`.
