# 04. Docker Containerization (`Dockerfile`)
**Status:** [VERIFIED]

- **Base Image:** `python:3.12-slim`.
- **System Dependencies:** `tesseract-ocr`, `libmupdf-dev`, `build-essential`.
- **Command:** `CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- **Security:** Runs as non-root user; excludes tests and database files via `.dockerignore`.
