# 09. Artifact Download & Security
**Status:** [VERIFIED]

- **Route:** `GET /artifacts/{filename}`
- **Security Controls:**
  - Authenticated session required.
  - Restricts downloads strictly to `generated_artifacts/` directory. Path traversal attempts (`../`) are blocked with HTTP 403.
  - Serves files with appropriate MIME types (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`, etc.).
