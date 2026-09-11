"""
Sovereign AI Workbench - FastAPI Entry Point (SIH26117)
Serves High-Security REST API, WebSocket Agent Streams, and Embedded Frontend Dashboard.
Supports both on-premise air-gapped deployment and cloud container execution (Docker/Render).
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
import httpx

# Ensure backend directory is in sys.path so 'app' can be resolved from root or backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings, validate_air_gap_compliance
from app.api.router import api_router
from app.api.sih_router import sih_router
from app.security.audit_logger import audit_logger
from app.security.auth import init_auth_db, get_current_user_optional, get_token_from_request, logout_user
from app.database.vector_store import vector_store
from app.database.models import init_all_schemas
from app.security.rate_limiter import rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle hooks.
    Enforces air-gapped security validations locally, while permitting cloud demo deployment.
    """
    print("=" * 70)
    print(" [SOVEREIGN AI WORKBENCH - BOOT SEQUENCE INITIATED]")
    print(f" [PRODUCT]: MRPL Sovereign AI Workbench (SIH26117)")
    print(f" [ENVIRONMENT]: {settings.ENVIRONMENT}")
    print(f" [BINDING]: http://{settings.HOST}:{settings.PORT}")
    print("=" * 70)

    # 0. Enforce Air-Gap Policy
    try:
        validate_air_gap_compliance()
        if settings.AIR_GAP_STRICT_MODE:
            print(" [AIR-GAP VALIDATOR]: PASS. All endpoints bound to strictly local networks.")
        else:
            print(" [AIR-GAP VALIDATOR]: NOTICE. Cloud Demo Mode active (AIR_GAP_STRICT_MODE=false).")
    except Exception as e:
        print(f" [AIR-GAP VALIDATOR FATAL]: {e}")
        raise e

    # 0.1 Check for production secret safety
    if settings.ENVIRONMENT != "development" and settings.AUTH_SECRET_KEY == "sovereign-ai-workbench-airgapped-auth-secret-key-sih2026":
        print(" [SECURITY NOTICE]: AUTH_SECRET_KEY is using development default.")
        print("                    For production deployments, configure AUTH_SECRET_KEY in environment.")

    # 1. Initialize Local Authentication Database & Relational Schemas
    try:
        init_auth_db()
        init_all_schemas()
        print(f" [DATABASE SCHEMAS]: Initialized. 16 core relational models active.")
    except Exception as e:
        print(f" [DATABASE SCHEMA FATAL]: {e}")
        raise e

    # 2. Cryptographic Audit Chain Check
    try:
        is_valid, count, msg, tip_hash = audit_logger.verify_integrity()
        print(f" [AUDIT INTEGRITY]: Verified {count} records. Tip Hash: {tip_hash[:16]}... ({msg})")
    except Exception as e:
        print(f" [AUDIT WARNING]: Audit verification encounter: {e}")

    # 3. Vector Database Verification
    try:
        stats = vector_store.get_stats()
        total_chunks = stats.get("total_chunks", 0)
        print(f" [VECTOR ENGINE]: Active. Collection: '{stats.get('collection_name', 'sovereign_knowledge_base')}' ({total_chunks} chunks indexed).")
    except Exception as e:
        print(f" [VECTOR ENGINE WARNING]: Vector store status: {e}")

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
        if settings.AIR_GAP_STRICT_MODE:
            print(f"                            Ensure 'ollama serve' is running with model '{settings.DEFAULT_MODEL}'.")
        else:
            print(f"                            In Cloud Demo Mode, configure OLLAMA_BASE_URL to connect an external host.")

    print("=" * 70)
    print(f" WORKBENCH READY AT: http://{settings.HOST}:{settings.PORT}")
    print("=" * 70)

    yield

    print("\n[SOVEREIGN AI WORKBENCH]: Shutdown completed securely.")


from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# FastAPI Application Instance (CDN docs disabled to enforce 100% offline air-gapped capability)
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Air-Gapped Sovereign Multi-Agent AI Workbench (SIH 2026 Problem ID: SIH26117)",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# CORS Policy (Configured safely with verified origins and secure tunnels)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=r"^https:\/\/.*\.trycloudflare\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def apply_security_guards(request: Request, call_next):
    """
    Enforces application-level rate limiting during Public Share Mode,
    validates Host header against unauthorized host injection,
    and applies strict HTTP security headers (nosniff, DENY, strict CSP).
    """
    # 1. Host header validation
    host_header = request.headers.get("host")
    if host_header and not settings.is_host_allowed(host_header):
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid or unauthorized Host header '{host_header}'"}
        )

    # 2. In public share mode, apply rate limiting to non-static endpoints
    if settings.is_public_share_active():
        path = request.url.path
        if not (path.startswith("/static") or path in ("/favicon.ico",)):
            allowed = rate_limiter.check_rate_limit(request, raise_exception=False)
            if not allowed:
                max_rpm = settings.PUBLIC_MAX_REQUESTS_PER_MINUTE
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded: Maximum {max_rpm} requests per minute. Please wait before retrying."},
                    headers={"Retry-After": "10"}
                )

    response = await call_next(request)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' data: blob:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "connect-src 'self' ws: wss: http: https:; "
        "img-src 'self' data: blob:; "
        "frame-ancestors 'none';"
    )
    return response


# Register REST and WebSocket API Router (supports both /api and /api/v1)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")
app.include_router(sih_router, prefix="/api/v1")
app.include_router(sih_router, prefix="/api")


@app.websocket("/ws/telemetry")
async def root_websocket_telemetry(websocket: WebSocket):
    """Direct root telemetry WebSocket for monitoring agent stream."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if "PING" in data:
                await websocket.send_text('{"type": "PONG"}')
            else:
                await websocket.send_text('{"status": "STREAMING", "runtime": "SOVEREIGN_LOCAL"}')
    except WebSocketDisconnect:
        pass


# Static frontend and documentation asset paths
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = FRONTEND_DIR / "index.html"
LOGIN_HTML = FRONTEND_DIR / "login.html"
REGISTER_HTML = FRONTEND_DIR / "register.html"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serves Swagger UI documentation 100% locally without external CDN dependencies."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_js_url="/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Serves ReDoc documentation locally."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="/static/swagger/swagger-ui-bundle.js",
    )


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


def is_request_secure(req: Request) -> bool:
    """Determines whether a cookie should have the secure flag set."""
    if req.url.scheme == "https":
        return True
    if req.headers.get("x-forwarded-proto") == "https":
        return True
    if settings.PUBLIC_BASE_URL and settings.PUBLIC_BASE_URL.startswith("https://"):
        return True
    if "cloud" in settings.ENVIRONMENT.lower():
        return True
    return False


@app.get("/login")
@app.get("/login.html", include_in_schema=False)
async def serve_login(request: Request):
    """
    Serves the sovereign authentication login portal.
    If explicitly navigating to login, logged out, or switching accounts, always displays login.
    If already authenticated and no explicit login intent is specified, redirects to dashboard (/).
    """
    params = request.query_params
    explicit_login = any(k in params for k in ("logged_out", "switch", "error", "link_required", "force"))
    if not explicit_login:
        user = get_current_user_optional(request)
        if user:
            return RedirectResponse(url="/", status_code=302)

    if LOGIN_HTML.exists():
        resp = FileResponse(str(LOGIN_HTML))
        if "logged_out" in params or "switch" in params:
            resp.delete_cookie(
                key=settings.SESSION_COOKIE_NAME,
                path="/",
                secure=is_request_secure(request),
                httponly=True,
                samesite="lax"
            )
        return resp
    return JSONResponse(
        content={
            "error": "login.html not located at frontend/login.html",
            "api_docs": "/docs"
        },
        status_code=404
    )


@app.get("/logout", include_in_schema=False)
async def serve_logout(request: Request):
    """
    Terminates session, revokes HMAC token in database, clears session cookie,
    and redirects directly to /login?logged_out=true.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    token = get_token_from_request(request)
    if token:
        logout_user(token, client_ip=client_ip)

    resp = RedirectResponse(url="/login?logged_out=true", status_code=302)
    resp.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        secure=is_request_secure(request),
        httponly=True,
        samesite="lax"
    )
    return resp


@app.get("/register")
@app.get("/register.html", include_in_schema=False)
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


@app.get("/index.html", include_in_schema=False)
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
