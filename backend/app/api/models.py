"""
Pydantic Data Models for API Requests, Responses, and Streaming Events.
Strict typing guarantees enterprise robustness and schema validation.
"""

from typing import List, Dict, Any, Optional
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
    ollama_endpoint: str
    ollama_connected: Optional[bool] = None
    default_model: str
    chroma_collection: str
    total_vectors: int
    audit_integrity: bool


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
    filepath: str
    size_bytes: int
    sha256: str
    created_at: str
