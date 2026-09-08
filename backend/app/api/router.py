"""
API Endpoints for Document Ingestion, Agent Querying, Cryptographic Auditing,
and WebSocket Real-Time Thought Streaming.
"""

import os
import uuid
import shutil
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import httpx
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Request,
    Response,
    status
)
from fastapi.responses import RedirectResponse

from app.config import settings
from app.api.models import (
    QueryRequest,
    QueryResponse,
    DocumentIngestResponse,
    AuditVerifyResponse,
    SystemHealthResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    UserResponse,
    OAuthProvidersResponse,
    DocumentItem,
    AdminUserItem,
    CreateTaskRequest,
    TaskResponse,
    TaskEventItem,
    ArtifactItem
)
from fastapi.responses import FileResponse
from app.database.vector_store import vector_store
from app.database.task_store import (
    get_task,
    list_tasks,
    get_task_events,
    get_task_artifacts,
    cancel_task
)
from app.security.audit_logger import audit_logger
from app.security.auth import (
    authenticate_user,
    register_user,
    logout_user,
    create_session_token,
    verify_session_token,
    get_current_user,
    get_token_from_request,
    create_oauth_state,
    verify_oauth_state,
    resolve_social_user,
    log_oauth_event,
    get_all_users
)
from app.agents.graph import run_agent_workflow, run_agentic_task

api_router = APIRouter()


def is_request_secure(req: Request) -> bool:
    """Determines whether a cookie should have the secure flag set."""
    if req.url.scheme == "https":
        return True
    if req.headers.get("x-forwarded-proto") == "https":
        return True
    if "cloud" in settings.ENVIRONMENT.lower():
        return True
    return False


# Active WebSocket Connection Manager
from app.api.ws_manager import ws_manager, ConnectionManager


# ==========================================
# 0. AUTHENTICATION & SESSION MANAGEMENT
# ==========================================
@api_router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(register_req: RegisterRequest, request: Request):
    """
    Registers a new sovereign user account locally in SQLite with Argon2 hashing.
    Enforces format validation, password complexity, and uniqueness.
    Logs successful registration to SHA-256 micro-ledger without leaking passwords.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    result = register_user(
        full_name=register_req.full_name,
        username=register_req.username,
        email=register_req.email,
        password=register_req.password,
        confirm_password=register_req.confirm_password,
        client_ip=client_ip
    )
    return RegisterResponse(
        status="SUCCESS",
        message=result["message"],
        username=result["username"]
    )


@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_req: LoginRequest, request: Request, response: Response):
    """
    Authenticates username or email and password against local SQLite database.
    Issues HMAC-SHA256 signed session token.
    Sets HTTP-only secure cookie and returns bearer token for client storage.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_dict = authenticate_user(
        username_or_email=login_req.username,
        password=login_req.password,
        client_ip=client_ip,
        link_token=login_req.link_token
    )
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sovereign credentials. Access denied."
        )

    token = create_session_token(user_dict)

    # Set HTTP-only cookie for seamless browser navigation
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=is_request_secure(request)
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            username=user_dict["username"],
            role=user_dict.get("role", "user"),
            email=user_dict.get("email"),
            full_name=user_dict.get("full_name"),
            user_id=user_dict.get("id")
        ),
        expires_hours=settings.SESSION_EXPIRE_HOURS
    )


@api_router.post("/auth/logout", response_model=LogoutResponse)
async def logout(request: Request, response: Response):
    """
    Terminates session, revokes HMAC token in database, and clears cookie.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    token = get_token_from_request(request)
    if token:
        logout_user(token, client_ip=client_ip)

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    return LogoutResponse(status="SUCCESS", message="Session securely terminated.")


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns currently authenticated user profile."""
    return UserResponse(
        username=current_user["username"],
        role=current_user.get("role", "user"),
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        user_id=current_user.get("user_id")
    )


# ==========================================
# 0.1 SOCIAL OAUTH 2.0 AUTHENTICATION
# ==========================================

@api_router.get("/auth/providers", response_model=OAuthProvidersResponse)
async def get_oauth_providers():
    """
    Returns availability status of configured social OAuth identity providers.
    Allows frontend to dynamically show active vs air-gapped/disabled states.
    """
    return OAuthProvidersResponse(
        google=settings.google_oauth_configured(),
        github=settings.github_oauth_configured()
    )


@api_router.get("/auth/google/login")
async def google_login(request: Request):
    """
    Initiates Google OAuth 2.0 authorization-code flow.
    Generates cryptographic CSRF state token and redirects to Google.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not settings.google_oauth_configured():
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="OAUTH_DISABLED_OR_UNCONFIGURED",
            details={"reason": "Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET", "client_ip": client_ip}
        )
        return RedirectResponse(url="/login?error=oauth_not_configured&provider=google", status_code=302)

    log_oauth_event(
        event_type="GOOGLE_LOGIN_STARTED",
        provider="google",
        action="INITIATE_OAUTH_REDIRECT",
        details={"client_ip": client_ip}
    )

    state = create_oauth_state("google")
    client_id = settings.GOOGLE_CLIENT_ID.strip().lstrip('"\'<').rstrip('"\'>')
    redirect_uri = settings.GOOGLE_REDIRECT_URI.strip().lstrip('"\'<').rstrip('"\'>')
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    resp = RedirectResponse(url=auth_url, status_code=302)
    resp.set_cookie(
        key="oauth_state_google",
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return resp


@api_router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Processes Google OAuth 2.0 authorization-code callback.
    Validates CSRF state, exchanges code for access token, fetches profile,
    and resolves local user application session.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    cookie_state = request.cookies.get("oauth_state_google")

    if error:
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="OAUTH_CALLBACK_ERROR",
            details={"error": error, "client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=oauth_cancelled&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    if not code or not state:
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="MISSING_CODE_OR_STATE",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=missing_credentials&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    if not verify_oauth_state(state, expected_cookie=cookie_state, expected_provider="google"):
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="CSRF_STATE_VALIDATION_FAILED",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=csrf_validation_failed&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI
                }
            )
            if token_resp.status_code != 200:
                log_oauth_event(
                    event_type="GOOGLE_LOGIN_FAILED",
                    provider="google",
                    action="TOKEN_EXCHANGE_HTTP_ERROR",
                    details={"status_code": token_resp.status_code, "client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=token_exchange_failed&provider=google", status_code=302)
                resp.delete_cookie(key="oauth_state_google")
                return resp

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                log_oauth_event(
                    event_type="GOOGLE_LOGIN_FAILED",
                    provider="google",
                    action="MISSING_ACCESS_TOKEN",
                    details={"client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=invalid_token_response&provider=google", status_code=302)
                resp.delete_cookie(key="oauth_state_google")
                return resp

            userinfo_resp = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if userinfo_resp.status_code != 200:
                log_oauth_event(
                    event_type="GOOGLE_LOGIN_FAILED",
                    provider="google",
                    action="USERINFO_FETCH_FAILED",
                    details={"status_code": userinfo_resp.status_code, "client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=userinfo_failed&provider=google", status_code=302)
                resp.delete_cookie(key="oauth_state_google")
                return resp

            user_profile = userinfo_resp.json()
            provider_uid = str(user_profile.get("sub", "")).strip()
            email = str(user_profile.get("email", "")).strip().lower()
            full_name = str(user_profile.get("name", "")).strip()

    except Exception as exc:
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="OAUTH_NETWORK_EXCEPTION",
            details={"error": str(exc), "client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=oauth_network_error&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    if not provider_uid:
        log_oauth_event(
            event_type="GOOGLE_LOGIN_FAILED",
            provider="google",
            action="MISSING_PROVIDER_USER_ID",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=missing_user_id&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    resolution = resolve_social_user(
        provider="google",
        provider_user_id=provider_uid,
        email=email,
        full_name=full_name,
        client_ip=client_ip
    )

    if resolution["status"] == "AUTHENTICATED":
        session_token = create_session_token(resolution["user"])
        resp = RedirectResponse(url=f"/?token={session_token}", status_code=302)
        resp.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            httponly=True,
            samesite="lax",
            secure=is_request_secure(request)
        )
        resp.delete_cookie(key="oauth_state_google")
        return resp

    elif resolution["status"] == "LINK_REQUIRED":
        link_token = resolution["link_token"]
        query_str = urlencode({
            "link_required": "true",
            "provider": "google",
            "email": email,
            "link_token": link_token
        })
        resp = RedirectResponse(url=f"/login?{query_str}", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp

    else:
        resp = RedirectResponse(url="/login?error=authentication_failed&provider=google", status_code=302)
        resp.delete_cookie(key="oauth_state_google")
        return resp


@api_router.get("/auth/github/login")
async def github_login(request: Request):
    """
    Initiates GitHub OAuth 2.0 authorization-code flow.
    Generates cryptographic CSRF state token and redirects to GitHub.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not settings.github_oauth_configured():
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="OAUTH_DISABLED_OR_UNCONFIGURED",
            details={"reason": "Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET", "client_ip": client_ip}
        )
        return RedirectResponse(url="/login?error=oauth_not_configured&provider=github", status_code=302)

    log_oauth_event(
        event_type="GITHUB_LOGIN_STARTED",
        provider="github",
        action="INITIATE_OAUTH_REDIRECT",
        details={"client_ip": client_ip}
    )

    state = create_oauth_state("github")
    client_id = settings.GITHUB_CLIENT_ID.strip().lstrip('"\'<').rstrip('"\'>')
    redirect_uri = settings.GITHUB_REDIRECT_URI.strip().lstrip('"\'<').rstrip('"\'>')
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    resp = RedirectResponse(url=auth_url, status_code=302)
    resp.set_cookie(
        key="oauth_state_github",
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return resp


@api_router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Processes GitHub OAuth 2.0 authorization-code callback.
    Validates CSRF state, exchanges code for access token, fetches profile and emails,
    and resolves local user application session.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    cookie_state = request.cookies.get("oauth_state_github")

    if error:
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="OAUTH_CALLBACK_ERROR",
            details={"error": error, "client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=oauth_cancelled&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    if not code or not state:
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="MISSING_CODE_OR_STATE",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=missing_credentials&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    if not verify_oauth_state(state, expected_cookie=cookie_state, expected_provider="github"):
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="CSRF_STATE_VALIDATION_FAILED",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=csrf_validation_failed&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI
                },
                headers={"Accept": "application/json"}
            )
            if token_resp.status_code != 200:
                log_oauth_event(
                    event_type="GITHUB_LOGIN_FAILED",
                    provider="github",
                    action="TOKEN_EXCHANGE_HTTP_ERROR",
                    details={"status_code": token_resp.status_code, "client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=token_exchange_failed&provider=github", status_code=302)
                resp.delete_cookie(key="oauth_state_github")
                return resp

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                log_oauth_event(
                    event_type="GITHUB_LOGIN_FAILED",
                    provider="github",
                    action="MISSING_ACCESS_TOKEN",
                    details={"client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=invalid_token_response&provider=github", status_code=302)
                resp.delete_cookie(key="oauth_state_github")
                return resp

            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "Sovereign-AI-Workbench",
                "Accept": "application/vnd.github.v3+json"
            }
            user_resp = await client.get("https://api.github.com/user", headers=headers)
            if user_resp.status_code != 200:
                log_oauth_event(
                    event_type="GITHUB_LOGIN_FAILED",
                    provider="github",
                    action="USERINFO_FETCH_FAILED",
                    details={"status_code": user_resp.status_code, "client_ip": client_ip}
                )
                resp = RedirectResponse(url="/login?error=userinfo_failed&provider=github", status_code=302)
                resp.delete_cookie(key="oauth_state_github")
                return resp

            user_profile = user_resp.json()
            provider_uid = str(user_profile.get("id", "")).strip()
            login = str(user_profile.get("login", "")).strip()
            full_name = str(user_profile.get("name") or login).strip()
            email = str(user_profile.get("email") or "").strip().lower()

            # If user has private email on GitHub profile, fetch from emails endpoint
            if not email:
                try:
                    emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
                    if emails_resp.status_code == 200:
                        emails_list = emails_resp.json()
                        for entry in emails_list:
                            if entry.get("primary") and entry.get("verified"):
                                email = str(entry.get("email", "")).strip().lower()
                                break
                        if not email:
                            for entry in emails_list:
                                if entry.get("verified"):
                                    email = str(entry.get("email", "")).strip().lower()
                                    break
                except Exception:
                    pass

            if not email and login:
                email = f"{login}@users.noreply.github.com"

    except Exception as exc:
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="OAUTH_NETWORK_EXCEPTION",
            details={"error": str(exc), "client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=oauth_network_error&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    if not provider_uid:
        log_oauth_event(
            event_type="GITHUB_LOGIN_FAILED",
            provider="github",
            action="MISSING_PROVIDER_USER_ID",
            details={"client_ip": client_ip}
        )
        resp = RedirectResponse(url="/login?error=missing_user_id&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    resolution = resolve_social_user(
        provider="github",
        provider_user_id=provider_uid,
        email=email,
        full_name=full_name,
        client_ip=client_ip
    )

    if resolution["status"] == "AUTHENTICATED":
        session_token = create_session_token(resolution["user"])
        resp = RedirectResponse(url=f"/?token={session_token}", status_code=302)
        resp.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_token,
            max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            httponly=True,
            samesite="lax",
            secure=is_request_secure(request)
        )
        resp.delete_cookie(key="oauth_state_github")
        return resp

    elif resolution["status"] == "LINK_REQUIRED":
        link_token = resolution["link_token"]
        query_str = urlencode({
            "link_required": "true",
            "provider": "github",
            "email": email,
            "link_token": link_token
        })
        resp = RedirectResponse(url=f"/login?{query_str}", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp

    else:
        resp = RedirectResponse(url="/login?error=authentication_failed&provider=github", status_code=302)
        resp.delete_cookie(key="oauth_state_github")
        return resp


# ==========================================
# 1. DOCUMENT INGESTION ROUTE
# ==========================================
@api_router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Ingests PDF or Text documents locally.
    1. Validates file extension
    2. Scrubs PII entities via local regex/Presidio
    3. Generates local embeddings via Sentence-Transformers
    4. Indexes chunks into persistent ChromaDB
    5. Appends verifiable entry to SHA-256 audit ledger
    """
    allowed_extensions = {".pdf", ".txt", ".md", ".csv", ".json", ".log"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Save uploaded file locally in sandbox
    save_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}_{file.filename}")
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ingest into ChromaDB
        ingest_result = vector_store.ingest_file(
            file_path=save_path,
            original_filename=file.filename
        )

        return DocumentIngestResponse(
            filename=ingest_result["filename"],
            document_id=ingest_result["document_id"],
            sha256=ingest_result["sha256"],
            characters=ingest_result["characters"],
            chunks_created=ingest_result["chunks_created"],
            message=f"Document '{file.filename}' securely indexed into local knowledge base."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failure: {str(e)}")
    finally:
        # Clean up temporary local file
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception:
                pass


@api_router.get("/documents", response_model=List[DocumentItem])
async def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns all indexed documents currently stored in the local vector database."""
    return vector_store.get_indexed_documents()


@api_router.get("/admin/users", response_model=List[AdminUserItem])
async def list_admin_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Administrative user management endpoint. Protected by role-based access control."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access user ledger."
        )
    return get_all_users()


# ==========================================
# 2. MULTI-AGENT REASONING QUERY ROUTE
# ==========================================
@api_router.post("/query", response_model=QueryResponse)
async def query_workbench(
    request: QueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Synchronously triggers the LangGraph 4-agent state machine.
    Broadcasts real-time events to connected WebSocket clients during execution.
    """
    sid = request.session_id or str(uuid.uuid4())

    async def thought_emitter(log_dict: Dict[str, Any]):
        await ws_manager.broadcast_to_session(sid, {
            "type": "agent_thought",
            "data": log_dict
        })

    try:
        result_state = await run_agent_workflow(
            query=request.query,
            session_id=sid,
            on_thought_callback=thought_emitter
        )

        # Retrieve tip hash of audit trail
        _, _, _, tip_hash = audit_logger.verify_integrity()

        return QueryResponse(
            session_id=result_state["session_id"],
            status=result_state.get("status", "COMPLETED"),
            final_report=result_state.get("final_report", "No report generated."),
            confidence=result_state.get("audit_confidence", 0.0),
            verdict=result_state.get("audit_verdict", "APPROVED"),
            iteration_count=result_state.get("iteration_count", 1),
            citations=result_state.get("citations", []),
            action_items=result_state.get("action_items", []),
            audit_hash=tip_hash
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")


# ==========================================
# 2B. MULTI-STEP AGENTIC TASK ENGINE ROUTES
# ==========================================
@api_router.post("/agent/tasks", response_model=TaskResponse)
async def create_agent_task(
    task_req: CreateTaskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submits a multi-step sovereign agentic task for execution.
    Executes security gate, planning, tool operations, verification,
    and streams events over WebSocket.
    """
    sid = task_req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    username = current_user.get("username", "anonymous")
    user_id = str(current_user.get("id") or current_user.get("user_id") or username)

    async def thought_emitter(evt: Dict[str, Any]):
        await ws_manager.broadcast_to_session(sid, {
            "type": "agent_event",
            "data": evt
        })

    final_state = await run_agentic_task(
        query=task_req.query,
        user_id=user_id,
        username=username,
        session_id=sid,
        ws_emitter=thought_emitter
    )

    t_data = get_task(final_state["task_id"])
    if not t_data:
        raise HTTPException(status_code=500, detail="Task record initialization failed.")

    return TaskResponse(**t_data)


@api_router.get("/agent/tasks", response_model=List[TaskResponse])
async def list_agent_tasks(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lists tasks. Enforces user isolation: standard users see only their tasks;
    administrators have global oversight.
    """
    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    tasks = list_tasks(user_id=user_id, role=role, limit=limit, offset=offset)
    return [TaskResponse(**t) for t in tasks]


@api_router.get("/agent/tasks/{task_id}", response_model=TaskResponse)
async def get_agent_task_details(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves state and outputs of a specific agentic task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    if role != "admin" and task.get("user_id") and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Access to this sovereign task is restricted.")

    return TaskResponse(**task)


@api_router.post("/agent/tasks/{task_id}/cancel")
async def cancel_agent_task_route(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Signals cancellation to an active task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    if role != "admin" and task.get("user_id") and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Access restricted.")

    success = cancel_task(task_id)
    return {"task_id": task_id, "cancelled": success, "status": "CANCELLED"}


@api_router.post("/agent/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_agent_task_route(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Re-executes a failed or cancelled agentic task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    if role != "admin" and task.get("user_id") and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Access restricted.")

    sid = task.get("session_id") or f"session_{uuid.uuid4().hex[:8]}"
    username = current_user.get("username", "anonymous")

    final_state = await run_agentic_task(
        query=task["query"],
        user_id=user_id,
        username=username,
        session_id=sid
    )
    t_data = get_task(final_state["task_id"])
    return TaskResponse(**t_data)


@api_router.get("/agent/tasks/{task_id}/events", response_model=List[TaskEventItem])
async def get_task_event_stream(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves all telemetry and execution events recorded for a task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    if role != "admin" and task.get("user_id") and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Access restricted.")

    events = get_task_events(task_id)
    return [TaskEventItem(**e) for e in events]


@api_router.get("/agent/tasks/{task_id}/artifacts", response_model=List[ArtifactItem])
async def get_task_artifacts_list(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves artifacts generated by a task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    role = current_user.get("role", "user")
    user_id = str(current_user.get("id") or current_user.get("user_id") or current_user.get("username"))
    if role != "admin" and task.get("user_id") and task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Access restricted.")

    artifacts = get_task_artifacts(task_id)
    return [ArtifactItem(**a) for a in artifacts]


@api_router.get("/agent/artifacts/{filename}")
async def get_artifact_file(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Safely retrieves or downloads an artifact file from the designated OUTPUT_DIR."""
    clean_name = os.path.basename(filename)
    filepath = os.path.join(settings.OUTPUT_DIR, clean_name)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"Artifact '{clean_name}' not found.")

    return FileResponse(filepath, filename=clean_name)


# ==========================================
# 3. CRYPTOGRAPHIC AUDIT VERIFICATION
# ==========================================
@api_router.get("/audit/verify", response_model=AuditVerifyResponse)
async def verify_audit_ledger(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Re-calculates the complete SHA-256 blockchain from genesis to verify
    zero data tampering or unauthorized modifications.
    """
    is_valid, count, message, tip_hash = audit_logger.verify_integrity()
    return AuditVerifyResponse(
        is_valid=is_valid,
        total_records=count,
        message=message,
        latest_hash=tip_hash
    )


@api_router.get("/audit/logs")
async def get_audit_logs(limit: int = 50, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the most recent N records from the immutable audit trail."""
    return audit_logger.get_recent_logs(limit=limit)


# ==========================================
# 4. SYSTEM HEALTH & AIR-GAP STATUS
# ==========================================
@api_router.get("/health", response_model=SystemHealthResponse)
async def system_health():
    """Returns operational status, model configuration, and air-gap verification."""
    is_valid, _, _, _ = audit_logger.verify_integrity()
    stats = vector_store.get_stats()

    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=0.8) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            ollama_ok = (resp.status_code == 200)
    except Exception:
        ollama_ok = False

    return SystemHealthResponse(
        status="ONLINE_SECURE",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        air_gapped=settings.AIR_GAP_STRICT_MODE,
        ollama_endpoint=settings.OLLAMA_BASE_URL,
        ollama_connected=ollama_ok,
        default_model=settings.DEFAULT_MODEL,
        chroma_collection=stats.get("collection_name", settings.CHROMA_COLLECTION_NAME),
        total_vectors=stats.get("total_chunks", 0),
        audit_integrity=is_valid
    )


# ==========================================
# 5. WEBSOCKET REAL-TIME STREAMING TERMINAL
# ==========================================
@api_router.websocket("/ws/agent-thoughts/{session_id}")
async def websocket_agent_thoughts(websocket: WebSocket, session_id: str):
    """
    Bidirectional streaming WebSocket.
    Clients receive real-time node transitions, thoughts, confidence scores,
    and can trigger queries directly over socket.
    Requires valid session token via query parameter (?token=...) or cookie.
    """
    token = websocket.query_params.get("token")
    if not token:
        token = websocket.cookies.get(settings.SESSION_COOKIE_NAME)

    payload = verify_session_token(token) if token else None
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized sovereign access")
        return

    await ws_manager.connect(websocket, session_id)
    try:
        # Initial greeting and session acknowledgement
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "user": payload.get("sub", "authenticated_user"),
            "status": "Ready for sovereign agent commands."
        })

        while True:
            # Receive client queries over websocket
            client_msg = await websocket.receive_json()
            user_query = client_msg.get("query", "").strip()

            if not user_query:
                continue

            # Stream thoughts as agents execute
            async def ws_emitter(log_dict: Dict[str, Any]):
                await ws_manager.broadcast_to_session(session_id, {
                    "type": "agent_thought",
                    "data": log_dict
                })

            result = await run_agent_workflow(
                query=user_query,
                session_id=session_id,
                on_thought_callback=ws_emitter
            )

            # Send final report payload
            _, _, _, tip_hash = audit_logger.verify_integrity()
            await websocket.send_json({
                "type": "workflow_completed",
                "session_id": session_id,
                "data": {
                    "final_report": result.get("final_report", ""),
                    "confidence": result.get("audit_confidence", 0.0),
                    "verdict": result.get("audit_verdict", "APPROVED"),
                    "iterations": result.get("iteration_count", 1),
                    "citations": result.get("citations", []),
                    "action_items": result.get("action_items", []),
                    "audit_hash": tip_hash
                }
            })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)
    except Exception as e:
        ws_manager.disconnect(websocket, session_id)
