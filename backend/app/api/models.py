"""
Pydantic Data Models for API Requests, Responses, and Streaming Events.
Strict typing guarantees enterprise robustness and schema validation.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    username: str = Field(..., min_length=3, max_length=32, description="Unique username for local account")
    email: str = Field(..., min_length=5, max_length=150, description="Valid email address")
    password: str = Field(..., min_length=8, description="Secure account password")
    confirm_password: str = Field(..., min_length=8, description="Matching password confirmation")


class RegisterResponse(BaseModel):
    status: str = "SUCCESS"
    message: str
    username: str


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username or email address")
    password: str = Field(..., min_length=1, description="Account password")
    link_token: Optional[str] = Field(None, description="Optional account link token for confirming social identity linking")


class OAuthProvidersResponse(BaseModel):
    google: bool = Field(False, description="Whether Google OAuth is configured and enabled")
    github: bool = Field(False, description="Whether GitHub OAuth is configured and enabled")
    environment: str = Field("production-airgapped", description="Current operating environment")
    github_redirect_uri: Optional[str] = Field(None, description="Configured GitHub OAuth callback URI (sanitized)")
    google_redirect_uri: Optional[str] = Field(None, description="Configured Google OAuth callback URI (sanitized)")
    public_share: bool = Field(False, description="Whether Public Share Mode is active")
    temporary_tunnel: bool = Field(False, description="Whether active public URL is a temporary Quick Tunnel")
    stable_tunnel: bool = Field(False, description="Whether active public URL is a stable Cloudflare Named Tunnel")
    notice: Optional[str] = Field(None, description="Informational notice regarding OAuth availability")


class UserResponse(BaseModel):
    username: str
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    user_id: Optional[int] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_hours: int


class LogoutResponse(BaseModel):
    status: str
    message: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or research prompt")
    session_id: Optional[str] = Field(None, description="Optional persistent session identifier")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="Number of context chunks to retrieve")


class QueryResponse(BaseModel):
    session_id: str
    status: str
    final_report: str
    confidence: float
    verdict: str
    iteration_count: int
    citations: List[str]
    action_items: List[str]
    audit_hash: str


class DocumentIngestResponse(BaseModel):
    filename: str
    document_id: str
    sha256: str
    characters: int
    chunks_created: int
    message: str


class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_records: int
    message: str
    latest_hash: str


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    environment: str = "production-airgapped"
    air_gapped: bool
    public_share: Union[bool, Dict[str, Any]] = Field(False, description="Whether secure public share tunnel is active or public share metadata")
    runtime_mode: str = Field("LOCAL_AIR_GAPPED", description="Runtime mode: LOCAL_AIR_GAPPED, PUBLIC_SHARE, or CLOUD_DEMO")
    runtime_label: str = Field("AIR-GAPPED / ON-PREMISE VERIFIED", description="User-facing runtime label")
    runtime_notice: Optional[str] = Field(None, description="Notice explaining runtime characteristics")
    ollama_endpoint: str
    ollama_connected: Optional[bool] = None
    embeddings_status: str = Field("OPERATIONAL", description="Status of local embedding engine")
    default_model: str
    chroma_collection: str
    total_vectors: int
    audit_integrity: bool
    ocr_available: bool = Field(True, description="Whether local OCR is available")
    vision_available: bool = Field(True, description="Whether local vision is available")
    chroma_available: bool = Field(True, description="Whether local vector database is available")
    external_ai_calls: int = Field(0, description="Cryptographically verified external AI API calls (strictly 0 on-premise)")
    zero_external_ai: bool = Field(True, description="Cryptographically verified zero external AI services")


class PublicShareResponse(BaseModel):
    enabled: bool
    runtime_mode: str
    public_url: Optional[str] = None
    stable_url: Optional[str] = None
    local_url: str = "http://127.0.0.1:8000"
    ai_runtime: str = "LOCAL"
    ollama_connected: bool = True
    external_ai_calls: int = 0
    tunnel_provider: Optional[str] = "cloudflare"
    tunnel_type: Optional[str] = "quick"
    notice: Optional[str] = None


class DocumentItem(BaseModel):
    document_id: str
    filename: str
    chunks_count: int
    sha256: str
    extension: str


class AdminUserItem(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class CreateTaskRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Task instruction or research question")
    session_id: Optional[str] = Field(None, description="Optional session identifier for WebSocket correlation")
    deliverable_format: Optional[str] = Field("AUTO", description="Target deliverable format: AUTO, DOCX, XLSX, PPTX, PDF, MARKDOWN")


class TaskResponse(BaseModel):
    task_id: str
    session_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    query: str
    category: Optional[str] = None
    status: str
    task_plan: List[Dict[str, Any]] = []
    current_step: int = 0
    total_steps: int = 0
    completed_steps: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []
    final_report: Optional[str] = None
    confidence: float = 0.0
    verdict: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class TaskEventItem(BaseModel):
    id: int
    task_id: str
    timestamp: str
    event_type: str
    message: str
    step: Optional[int] = None
    tool_name: Optional[str] = None
    details: Dict[str, Any] = {}
    status: Optional[str] = "OK"


class ArtifactItem(BaseModel):
    filename: str
    filepath: Optional[str] = None
    file_path: Optional[str] = None
    size_bytes: int = 0
    sha256: str = ""
    created_at: Optional[str] = ""
    artifact_type: Optional[str] = "document"
    format: Optional[str] = None
    title: Optional[str] = None
    confidence: Optional[float] = 1.0
    verification_status: Optional[str] = "VERIFIED"


class AICapabilitiesResponse(BaseModel):
    reasoning_model: str
    embedding_model: str
    ocr_provider: str
    ocr_available: bool
    ocr_status: str
    ocr_message: str
    vision_provider: str
    vision_available: bool
    vision_status: str
    vision_model: Optional[str] = None
    vision_message: str
    deliverable_generators: List[str]


class MultimodalUploadResponse(BaseModel):
    file_id: str
    filename: str
    original_filename: str
    sha256: str
    size_bytes: int
    mime_type: str
    detected_type: str
    page_count: int
    ocr_applied: bool
    ocr_status: str
    evidence_count: int
    preview_text: str
    message: str


class UploadedFileResponse(BaseModel):
    file_id: str
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    filename: str
    original_filename: str
    sha256: str
    mime_type: str
    size_bytes: int
    page_count: int
    detected_type: str
    ocr_status: str
    vision_status: str
    processing_status: str
    created_at: str
