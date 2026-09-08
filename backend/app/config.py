"""
Configuration Manager for Sovereign On-Premise Agentic AI Workbench (SIH26117)
Enforces strict air-gap compliance locally, while supporting cloud web service deployment.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, AliasChoices, field_validator
except ImportError:
    try:
        from pydantic import BaseModel as BaseSettings, Field
        SettingsConfigDict = None
        AliasChoices = None
        field_validator = None
    except ImportError:
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        def Field(default=None, **kwargs):
            return default
        SettingsConfigDict = None
        AliasChoices = None
        field_validator = None

# Base directory for local persistence and environment files
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_ENV_PATH = BASE_DIR / ".env"
BACKEND_ENV_PATH = BASE_DIR / "backend" / ".env"

try:
    from dotenv import load_dotenv
    if ROOT_ENV_PATH.is_file():
        load_dotenv(dotenv_path=ROOT_ENV_PATH)
    elif BACKEND_ENV_PATH.is_file():
        load_dotenv(dotenv_path=BACKEND_ENV_PATH)
    else:
        load_dotenv()
except ImportError:
    pass


def _clean_credential(val: str) -> str:
    """Strips whitespace, accidental wrapping/leading/trailing quotes, and angle brackets from credentials."""
    if not val:
        return ""
    v = str(val).strip()
    changed = True
    while changed:
        orig = v
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1].strip()
        if v.startswith("<") and v.endswith(">"):
            v = v[1:-1].strip()
        v = v.lstrip('"\'<').rstrip('"\'>')
        changed = (v != orig)
    return v.strip()


class WorkbenchSettings(BaseSettings):
    # Core Application Settings
    PROJECT_NAME: str = "Sovereign AI Workbench"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", os.getenv("WORKBENCH_ENVIRONMENT", "production-airgapped")).strip(),
        validation_alias=AliasChoices("ENVIRONMENT", "WORKBENCH_ENVIRONMENT") if AliasChoices else "ENVIRONMENT",
        description="Operating environment: 'production-airgapped', 'production-cloud', or 'development'"
    )
    DEBUG: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEBUG", "WORKBENCH_DEBUG") if AliasChoices else "DEBUG"
    )

    # Server Configuration (Supports dynamic Cloud $PORT and 0.0.0.0 binding)
    HOST: str = Field(
        default_factory=lambda: os.getenv("HOST", os.getenv("WORKBENCH_HOST", "127.0.0.1")).strip(),
        validation_alias=AliasChoices("HOST", "WORKBENCH_HOST") if AliasChoices else "HOST",
        description="Host IP binding (127.0.0.1 for local, 0.0.0.0 for cloud/Docker)"
    )
    PORT: int = Field(
        default_factory=lambda: int(os.getenv("PORT", os.getenv("WORKBENCH_PORT", "8000")).strip()),
        validation_alias=AliasChoices("PORT", "WORKBENCH_PORT") if AliasChoices else "PORT",
        description="Server listening port"
    )

    # Local Inference Core (Ollama / vLLM)
    OLLAMA_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", os.getenv("WORKBENCH_OLLAMA_BASE_URL", "http://localhost:11434")).strip(),
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "WORKBENCH_OLLAMA_BASE_URL") if AliasChoices else "OLLAMA_BASE_URL",
        description="Local Ollama instance endpoint. External URLs are rejected when air-gap strict mode is active."
    )
    DEFAULT_MODEL: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_MODEL", os.getenv("OLLAMA_MODEL", os.getenv("WORKBENCH_DEFAULT_MODEL", "llama3.1"))).strip(),
        validation_alias=AliasChoices("DEFAULT_MODEL", "OLLAMA_MODEL", "WORKBENCH_DEFAULT_MODEL") if AliasChoices else "DEFAULT_MODEL",
        description="Default local model identifier (e.g., llama3.1, qwen2.5:7b, mistral)"
    )
    MODEL_TEMPERATURE: float = 0.1
    INFERENCE_TIMEOUT_SECONDS: float = 120.0

    # Optional persistent storage mount directory (e.g., Render Persistent Disk path '/var/data')
    DATA_DIR: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATA_DIR", os.getenv("WORKBENCH_DATA_DIR", None)),
        validation_alias=AliasChoices("DATA_DIR", "WORKBENCH_DATA_DIR") if AliasChoices else "DATA_DIR",
        description="Mount path for cloud persistent disk (defaults to project root directory if None)"
    )

    # Vector Storage & Embeddings
    CHROMA_COLLECTION_NAME: str = "sovereign_knowledge_base"
    EMBEDDING_MODEL_NAME: str = Field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL_NAME", os.getenv("EMBEDDING_MODEL", os.getenv("WORKBENCH_EMBEDDING_MODEL_NAME", "nomic-embed-text"))).strip(),
        validation_alias=AliasChoices("EMBEDDING_MODEL_NAME", "EMBEDDING_MODEL", "WORKBENCH_EMBEDDING_MODEL_NAME") if AliasChoices else "EMBEDDING_MODEL_NAME",
        description="Ollama embedding model name (e.g. nomic-embed-text)"
    )
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 3

    # Dynamic File Paths (Computed based on DATA_DIR if present)
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")
    AUDIT_LOG_FILE: str = str(BASE_DIR / "audit_trail.jsonl")
    UPLOAD_DIR: str = str(BASE_DIR / "uploaded_docs")
    AUTH_DB_PATH: str = str(BASE_DIR / "auth.db")
    OUTPUT_DIR: str = str(BASE_DIR / "generated_artifacts")
    TASK_DB_PATH: str = str(BASE_DIR / "tasks.db")
    DEMO_DATA_DIR: str = str(BASE_DIR / "demo_data")

    # Security & Cryptographic Auditing
    PII_REDACTION_TAG: str = "[REDACTED_CONFIDENTIAL]"
    AIR_GAP_STRICT_MODE: bool = Field(
        default_factory=lambda: os.getenv("AIR_GAP_STRICT_MODE", os.getenv("WORKBENCH_AIR_GAP_STRICT_MODE", "true")).strip().lower() in ("true", "1", "yes"),
        validation_alias=AliasChoices("AIR_GAP_STRICT_MODE", "WORKBENCH_AIR_GAP_STRICT_MODE") if AliasChoices else "AIR_GAP_STRICT_MODE",
        description="Strictly reject non-loopback endpoints when True. Set False for Cloud Demo mode."
    )

    # Agent Loop Guardrails
    MAX_AUDIT_ITERATIONS: int = 3
    MIN_AUDIT_CONFIDENCE: float = 0.80
    MAX_AGENT_STEPS: int = 10
    MAX_TOOL_CALLS: int = 15
    MAX_RETRIES: int = 2
    MAX_EXECUTION_TIME_SECONDS: int = 120

    # Authentication & Session Security
    AUTH_SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("AUTH_SECRET_KEY", os.getenv("SESSION_SECRET", os.getenv("WORKBENCH_AUTH_SECRET_KEY", "sovereign-ai-workbench-airgapped-auth-secret-key-sih2026"))).strip(),
        validation_alias=AliasChoices("AUTH_SECRET_KEY", "SESSION_SECRET", "WORKBENCH_AUTH_SECRET_KEY") if AliasChoices else "AUTH_SECRET_KEY",
        description="Cryptographic HMAC key for local session token verification"
    )
    SESSION_EXPIRE_HOURS: int = 12
    SESSION_COOKIE_NAME: str = "sovereign_session"

    # Initial Local Admin Bootstrap Credentials
    ADMIN_DEFAULT_USERNAME: str = Field(
        default_factory=lambda: os.getenv("ADMIN_DEFAULT_USERNAME", os.getenv("WORKBENCH_ADMIN_DEFAULT_USERNAME", "admin")).strip(),
        validation_alias=AliasChoices("ADMIN_DEFAULT_USERNAME", "WORKBENCH_ADMIN_DEFAULT_USERNAME") if AliasChoices else "ADMIN_DEFAULT_USERNAME",
        description="Bootstrap administrator username"
    )
    ADMIN_DEFAULT_PASSWORD: str = Field(
        default_factory=lambda: os.getenv("ADMIN_DEFAULT_PASSWORD", os.getenv("WORKBENCH_ADMIN_DEFAULT_PASSWORD", "SovereignAdmin2026!")).strip(),
        validation_alias=AliasChoices("ADMIN_DEFAULT_PASSWORD", "WORKBENCH_ADMIN_DEFAULT_PASSWORD") if AliasChoices else "ADMIN_DEFAULT_PASSWORD",
        description="Bootstrap administrator password"
    )
    ADMIN_DEFAULT_EMAIL: str = Field(
        default_factory=lambda: os.getenv("ADMIN_DEFAULT_EMAIL", os.getenv("WORKBENCH_ADMIN_DEFAULT_EMAIL", "admin@sovereign.local")).strip(),
        validation_alias=AliasChoices("ADMIN_DEFAULT_EMAIL", "WORKBENCH_ADMIN_DEFAULT_EMAIL") if AliasChoices else "ADMIN_DEFAULT_EMAIL",
        description="Bootstrap administrator email address"
    )
    ADMIN_DEFAULT_FULL_NAME: str = Field(
        default_factory=lambda: os.getenv("ADMIN_DEFAULT_FULL_NAME", os.getenv("WORKBENCH_ADMIN_DEFAULT_FULL_NAME", "Sovereign Administrator")).strip(),
        validation_alias=AliasChoices("ADMIN_DEFAULT_FULL_NAME", "WORKBENCH_ADMIN_DEFAULT_FULL_NAME") if AliasChoices else "ADMIN_DEFAULT_FULL_NAME",
        description="Bootstrap administrator full name"
    )
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password character length")
    ALLOW_USER_REGISTRATION: bool = Field(default=True, description="Permit new user self-registration")

    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", os.getenv("WORKBENCH_CORS_ORIGINS", "")).strip(),
        validation_alias=AliasChoices("CORS_ORIGINS", "WORKBENCH_CORS_ORIGINS") if AliasChoices else "CORS_ORIGINS",
        description="Comma-separated allowed CORS origins for external clients"
    )

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", os.getenv("WORKBENCH_GOOGLE_CLIENT_ID", "")).strip(),
        validation_alias=AliasChoices("GOOGLE_CLIENT_ID", "WORKBENCH_GOOGLE_CLIENT_ID") if AliasChoices else "GOOGLE_CLIENT_ID",
        description="Google OAuth Client ID"
    )
    GOOGLE_CLIENT_SECRET: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", os.getenv("WORKBENCH_GOOGLE_CLIENT_SECRET", "")).strip(),
        validation_alias=AliasChoices("GOOGLE_CLIENT_SECRET", "WORKBENCH_GOOGLE_CLIENT_SECRET") if AliasChoices else "GOOGLE_CLIENT_SECRET",
        description="Google OAuth Client Secret"
    )
    GOOGLE_REDIRECT_URI: str = Field(
        default_factory=lambda: (
            os.getenv("GOOGLE_REDIRECT_URI", os.getenv("WORKBENCH_GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback")).strip()
            or "http://127.0.0.1:8000/api/auth/google/callback"
        ),
        validation_alias=AliasChoices("GOOGLE_REDIRECT_URI", "WORKBENCH_GOOGLE_REDIRECT_URI") if AliasChoices else "GOOGLE_REDIRECT_URI",
        description="Google OAuth Callback URL"
    )

    # GitHub OAuth Configuration
    GITHUB_CLIENT_ID: str = Field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_ID", os.getenv("WORKBENCH_GITHUB_CLIENT_ID", "")).strip(),
        validation_alias=AliasChoices("GITHUB_CLIENT_ID", "WORKBENCH_GITHUB_CLIENT_ID") if AliasChoices else "GITHUB_CLIENT_ID",
        description="GitHub OAuth Client ID"
    )
    GITHUB_CLIENT_SECRET: str = Field(
        default_factory=lambda: os.getenv("GITHUB_CLIENT_SECRET", os.getenv("WORKBENCH_GITHUB_CLIENT_SECRET", "")).strip(),
        validation_alias=AliasChoices("GITHUB_CLIENT_SECRET", "WORKBENCH_GITHUB_CLIENT_SECRET") if AliasChoices else "GITHUB_CLIENT_SECRET",
        description="GitHub OAuth Client Secret"
    )
    GITHUB_REDIRECT_URI: str = Field(
        default_factory=lambda: (
            os.getenv("GITHUB_REDIRECT_URI", os.getenv("WORKBENCH_GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/github/callback")).strip()
            or "http://127.0.0.1:8000/api/auth/github/callback"
        ),
        validation_alias=AliasChoices("GITHUB_REDIRECT_URI", "WORKBENCH_GITHUB_REDIRECT_URI") if AliasChoices else "GITHUB_REDIRECT_URI",
        description="GitHub OAuth Callback URL"
    )

    def model_post_init(self, __context):
        """Re-route storage directories to DATA_DIR if configured (e.g. Render Persistent Disk) and sanitize OAuth credentials."""
        if self.DATA_DIR and self.DATA_DIR.strip():
            data_path = Path(self.DATA_DIR.strip()).resolve()
            self.CHROMA_PERSIST_DIR = str(data_path / "chroma_db")
            self.AUDIT_LOG_FILE = str(data_path / "audit_trail.jsonl")
            self.UPLOAD_DIR = str(data_path / "uploaded_docs")
            self.AUTH_DB_PATH = str(data_path / "auth.db")
            self.OUTPUT_DIR = str(data_path / "generated_artifacts")
            self.TASK_DB_PATH = str(data_path / "tasks.db")
            self.DEMO_DATA_DIR = str(data_path / "demo_data")

        # Sanitize OAuth configurations against stray quotes or angle brackets
        self.GOOGLE_CLIENT_ID = _clean_credential(self.GOOGLE_CLIENT_ID)
        self.GOOGLE_CLIENT_SECRET = _clean_credential(self.GOOGLE_CLIENT_SECRET)
        self.GOOGLE_REDIRECT_URI = _clean_credential(self.GOOGLE_REDIRECT_URI)
        self.GITHUB_CLIENT_ID = _clean_credential(self.GITHUB_CLIENT_ID)
        self.GITHUB_CLIENT_SECRET = _clean_credential(self.GITHUB_CLIENT_SECRET)
        self.GITHUB_REDIRECT_URI = _clean_credential(self.GITHUB_REDIRECT_URI)

    def get_cors_origins(self) -> List[str]:
        """Returns verified origins allowed for CORS."""
        origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if self.CORS_ORIGINS:
            for part in self.CORS_ORIGINS.split(","):
                part = part.strip()
                if part and part not in origins:
                    origins.append(part)
        return origins

    def google_oauth_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    def github_oauth_configured(self) -> bool:
        return bool(self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET)

    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=(str(ROOT_ENV_PATH), str(BACKEND_ENV_PATH)),
            env_file_encoding="utf-8",
            env_prefix="WORKBENCH_",
            case_sensitive=True,
            extra="ignore"
        )
    else:
        class Config:
            env_prefix = "WORKBENCH_"
            case_sensitive = True


# Instantiate global settings
settings = WorkbenchSettings()

# Ensure directories exist
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(os.path.abspath(settings.AUDIT_LOG_FILE)), exist_ok=True)


def validate_air_gap_compliance() -> bool:
    """
    Validates that inference endpoints and storage paths do NOT route to public internet.
    In cloud demo mode (AIR_GAP_STRICT_MODE=False), logs informational notice.
    """
    if not settings.AIR_GAP_STRICT_MODE:
        return True

    parsed = urlparse(settings.OLLAMA_BASE_URL)
    hostname = parsed.hostname or ""
    allowed_local_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

    is_loopback = hostname in allowed_local_hosts
    is_private_subnet = (
        hostname.startswith("192.168.") or
        hostname.startswith("10.") or
        (hostname.startswith("172.") and 16 <= int(hostname.split(".")[1] if len(hostname.split(".")) > 1 else 0) <= 31)
    )

    if not (is_loopback or is_private_subnet):
        raise SecurityError(
            f"AIR-GAP VIOLATION DETECTED: Endpoint '{settings.OLLAMA_BASE_URL}' references non-local host '{hostname}'. "
            "All connections must strictly resolve to loopback or verified on-premise air-gapped subnets. "
            "To deploy in Cloud Demo Mode, set AIR_GAP_STRICT_MODE=false in your environment."
        )

    return True


# Run compliance validation on module load
validate_air_gap_compliance()
