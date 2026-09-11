# 01. Windows Local Deployment (`start.bat`)
**Status:** [VERIFIED ACTIVE]

- **Startup Script:** `start.bat`
- **Execution Steps:**
  1. Activates virtual environment: `call venv\Scripts\activate.bat`.
  2. Ensures directories exist: `multimodal_uploads`, `generated_artifacts`, `chroma_db`.
  3. Launches Uvicorn: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`.
- **Pre-requisites:** Python 3.12+, Ollama running on port 11434, Tesseract v5.4.0 in PATH.
