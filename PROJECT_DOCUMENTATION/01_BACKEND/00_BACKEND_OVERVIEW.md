# 00. Backend Architecture Overview
**Status:** [VERIFIED]

## Architecture Summary
The backend of the Sovereign AI Workbench is an asynchronous, high-performance web service built with **FastAPI**, **Pydantic v2**, and **Uvicorn**. It binds to localhost `127.0.0.1:8000` and coordinates identity management, document ingestion, vector retrieval, agent execution, deliverable generation, and WebSocket telemetry broadcasting.

## Core Modules
- `backend/app/main.py`: Application factory, lifespan lifecycle manager, CORS, rate limiting.
- `backend/app/config.py`: Centralized environment settings (`BaseSettings`) and runtime mode detection.
- `backend/app/api/router.py`: REST endpoint router (auth, tasks, docs, audit, judge demo).
- `backend/app/api/models.py`: Pydantic request and response schemas.
- `backend/app/api/ws_manager.py`: WebSocket connection manager for live telemetry streaming.
- `backend/app/security/auth.py`: Cryptographic bcrypt hashing, JWT tokens, jti revocation, RBAC.
- `backend/app/database/task_store.py`: SQLite ORM/DAO managing `tasks.db`.
