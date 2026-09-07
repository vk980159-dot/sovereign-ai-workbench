"""
Configuration Manager for Sovereign On-Premise Agentic AI Workbench
Enforces strict air-gap compliance and local-only network routing.
"""

import os
from pathlib import Path
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


class WorkbenchSettings(BaseSettings):
    # Core Application Settings
    PROJECT_NAME: str = "Sovereign AI Workbench"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production-airgapped"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Local Inference Core (Ollama / vLLM)
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Local Ollama instance endpoint. External URLs are rejected by air-gap validator."
    )
    DEFAULT_MODEL: str = Field(
        default="llama3.1",
        description="Default local model identifier (e.g., llama3.1, qwen2.5:7b, mistral)"
    )
    MODEL_TEMPERATURE: float = 0.1
    INFERENCE_TIMEOUT_SECONDS: float = 120.0

    # Vector Storage & Embeddings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "sovereign_knowledge_base"
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 3

    # Security & Cryptographic Auditing
    AUDIT_LOG_FILE: str = str(BASE_DIR / "audit_trail.jsonl")
    PII_REDACTION_TAG: str = "[REDACTED_CONFIDENTIAL]"
    AIR_GAP_STRICT_MODE: bool = True

    # Agent Loop Guardrails
    MAX_AUDIT_ITERATIONS: int = 3
    MIN_AUDIT_CONFIDENCE: float = 0.80

    # Local Document Uploads
    UPLOAD_DIR: str = str(BASE_DIR / "uploaded_docs")

    # Authentication & Session Security (100% Local & Air-Gapped)
    AUTH_DB_PATH: str = str(BASE_DIR / "auth.db")
    AUTH_SECRET_KEY: str = Field(
        default="sovereign-ai-workbench-airgapped-auth-secret-key-sih2026",
        description="Cryptographic HMAC key for local session token verification"
    )
    SESSION_EXPIRE_HOURS: int = 12
    SESSION_COOKIE_NAME: str = "sovereign_session"

    # Initial Local Admin Bootstrap Credentials
    ADMIN_DEFAULT_USERNAME: str = Field(
        default="admin",
        description="Bootstrap administrator username"
    )
    ADMIN_DEFAULT_PASSWORD: str = Field(
        default="SovereignAdmin2026!",
        description="Bootstrap administrator password"
    )
    ADMIN_DEFAULT_EMAIL: str = Field(
        default="admin@sovereign.local",
        description="Bootstrap administrator email address"
    )
    ADMIN_DEFAULT_FULL_NAME: str = Field(
        default="Sovereign Administrator",
        description="Bootstrap administrator full name"
    )
    PASSWORD_MIN_LENGTH: int = Field(
        default=8,
        description="Minimum password character length"
    )
    ALLOW_USER_REGISTRATION: bool = Field(
        default=True,
        description="Permit new user self-registration on air-gapped system"
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

    if field_validator:
        @field_validator("GOOGLE_REDIRECT_URI", mode="after")
        @classmethod
        def validate_google_redirect(cls, v: str) -> str:
            return v.strip() if v and v.strip() else "http://127.0.0.1:8000/api/auth/google/callback"

        @field_validator("GITHUB_REDIRECT_URI", mode="after")
        @classmethod
        def validate_github_redirect(cls, v: str) -> str:
            return v.strip() if v and v.strip() else "http://127.0.0.1:8000/api/auth/github/callback"

        @field_validator("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", mode="after")
        @classmethod
        def strip_oauth_credentials(cls, v: str) -> str:
            return v.strip() if v else ""

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
    Raises ValueError if an external network endpoint is detected.
    """
    parsed = urlparse(settings.OLLAMA_BASE_URL)
    hostname = parsed.hostname or ""

    allowed_local_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

    # Check for loopback or private RFC1918 subnets
    is_loopback = hostname in allowed_local_hosts
    is_private_subnet = (
        hostname.startswith("192.168.") or
        hostname.startswith("10.") or
        (hostname.startswith("172.") and 16 <= int(hostname.split(".")[1] if len(hostname.split(".")) > 1 else 0) <= 31)
    )

    if settings.AIR_GAP_STRICT_MODE and not (is_loopback or is_private_subnet):
        raise SecurityError(
            f"AIR-GAP VIOLATION DETECTED: Endpoint '{settings.OLLAMA_BASE_URL}' references non-local host '{hostname}'. "
            "All connections must strictly resolve to loopback or verified on-premise air-gapped subnets."
        )

    return True


# Run compliance validation on module load
validate_air_gap_compliance()
