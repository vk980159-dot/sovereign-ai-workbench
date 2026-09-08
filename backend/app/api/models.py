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
