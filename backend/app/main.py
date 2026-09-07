"""
Sovereign AI Workbench - FastAPI Entry Point (SIH26117)
Serves High-Security REST API, WebSocket Agent Streams, and Embedded Frontend Dashboard.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
import httpx

from app.config import settings, validate_air_gap_compliance
from app.api.router import api_router
from app.security.audit_logger import audit_logger
from app.security.auth import init_auth_db, get_current_user_optional
from app.database.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle hooks.
    Enforces strict air-gapped security validations.
    """
    print("=" * 70)
    print(" [SOVEREIGN AI WORKBENCH - BOOT SEQUENCE INITIATED]")
    print("=" * 70)

    # 0. Enforce Air-Gap Policy
    try:
        validate_air_gap_compliance()
        print(" [AIR-GAP VALIDATOR]: PASS. All endpoints bound to strictly local networks.")
    except Exception as e:
        print(f" [AIR-GAP VALIDATOR FATAL]: {e}")
        raise e

    # 1. Initialize Local SQLite Authentication Database and Admin Seed
    try:
        init_auth_db()
        print(f" [AUTH ENGINE]: Initialized. SQLite DB: '{settings.AUTH_DB_PATH}'. Initial admin bootstrapped.")
    except Exception as e:
        print(f" [AUTH ENGINE FATAL]: {e}")
        raise e

    # 2. Cryptographic Audit Chain Check
    is_valid, count, msg, tip_hash = audit_logger.verify_integrity()
    print(f" [AUDIT INTEGRITY]: Verified {count} records. Tip Hash: {tip_hash[:16]}... ({msg})")

    # 3. Vector Database Verification
    stats = vector_store.get_stats()
    total_chunks = stats.get("total_chunks", 0)
    print(f" [VECTOR ENGINE]: Active. Collection: '{stats.get('collection_name', 'sovereign_knowledge_base')}' ({total_chunks} chunks indexed).")

    # 4. Local Ollama Health Probe
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                print(f" [LOCAL INFERENCE]: Connected to Ollama. Models available: {models}")
            else:
                print(f" [LOCAL INFERENCE WARNING]: Ollama returned status {resp.status_code}")
    except Exception:
        print(f" [LOCAL INFERENCE NOTICE]: Ollama daemon at {settings.OLLAMA_BASE_URL} is currently unreachable.")
        print(f"                            Ensure 'ollama serve' is running with model '{settings.DEFAULT_MODEL}'.")

    print("=" * 70)
    print(f" WORKBENCH READY AT: http://{settings.HOST}:{settings.PORT}")
    print("=" * 70)

    yield

    print("\n[SOVEREIGN AI WORKBENCH]: Shutdown completed securely.")


# FastAPI Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Air-Gapped Sovereign Multi-Agent AI Workbench (SIH 2026 Problem ID: SIH26117)",
    lifespan=lifespan
)

# CORS Policy (Configured for local sovereign operation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST and WebSocket API Router (supports both /api and /api/v1)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")

# Static frontend paths
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
LOGIN_HTML = FRONTEND_DIR / "login.html"
REGISTER_HTML = FRONTEND_DIR / "register.html"


@app.get("/")
async def serve_root(request: Request):
    """
    Serves the dashboard if the user has an active authenticated session.
    Redirects unauthenticated visitors to /login.
    """
    user = get_current_user_optional(request)
    if user:
        if INDEX_HTML.exists():
            return FileResponse(str(INDEX_HTML))
        return JSONResponse(
            content={
                "project": settings.PROJECT_NAME,
                "status": "ONLINE",
                "message": "Frontend index.html not located at frontend/index.html",
                "api_docs": "/docs"
            }
        )
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login")
async def serve_login(request: Request):
    """
    Serves the sovereign authentication login portal.
    If already authenticated, redirects directly to dashboard (/).
    """
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    if LOGIN_HTML.exists():
        return FileResponse(str(LOGIN_HTML))
    return JSONResponse(
        content={
            "error": "login.html not located at frontend/login.html",
            "api_docs": "/docs"
        },
        status_code=404
    )


@app.get("/register")
async def serve_register(request: Request):
    """
    Serves the sovereign user registration portal.
    If already authenticated, redirects directly to dashboard (/).
    """
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    if REGISTER_HTML.exists():
        return FileResponse(str(REGISTER_HTML))
    return JSONResponse(
        content={
            "error": "register.html not located at frontend/register.html",
            "api_docs": "/docs"
        },
        status_code=404
    )


@app.get("/dashboard")
async def serve_dashboard(request: Request):
    """Protected dashboard alias."""
    user = get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if INDEX_HTML.exists():
        return FileResponse(str(INDEX_HTML))
    return RedirectResponse(url="/login", status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
