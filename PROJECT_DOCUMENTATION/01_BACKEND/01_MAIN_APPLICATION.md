# 01. Main Application (`backend/app/main.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/main.py`

## 2. File Purpose
Serves as the master entrypoint for the FastAPI application. Wires up ASGI middleware, API routers, static frontend assets, and startup/shutdown lifecycle hooks.

## 3. Why This File Exists
Unifies authentication, LangGraph agent workflows, ChromaDB vector stores, deliverable storage, and WebSocket connections into a single runnable server instance.

## 4. SIH Requirement Supported
Requirement #1 (Self-hosted deployment), Requirement #2 (Air-gapped execution).

## 5. Main Functions
- `lifespan(app: FastAPI)`: Asynchronous context manager executing on server startup. Ensures directories (`multimodal_uploads`, `generated_artifacts`, `chroma_db`) exist, initializes SQLite tables, bootstraps default admin account if absent, and closes database connections on shutdown.
- `create_app() -> FastAPI`: Application factory function instantiating FastAPI with CORS middleware, RateLimiter middleware, and route registrations.

## 6. Security Implementation
- Enforces strict CORS headers: allows `http://127.0.0.1:8000` and `http://localhost:8000`.
- Injects `SlidingWindowRateLimiter` middleware (60 req/min).
- Serves static files strictly from designated `/frontend` directory.

## 7. Execution Flow
Invoked by Uvicorn: `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`. Runs startup lifecycle -> mounts `/api`, `/ws`, `/artifacts` -> begins listening for requests.
