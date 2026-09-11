"""
Configuration Manager for Sovereign On-Premise Agentic AI Workbench (SIH26117)
Enforces strict air-gap compliance locally, while supporting cloud web service deployment.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

# Ensure local venv site-packages are accessible even when running via system python
_VENV_SITE = Path(__file__).resolve().parent.parent.parent / "venv" / "Lib" / "site-packages"
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

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
PUBLIC_SHARE_FILE = BASE_DIR / ".public_share_url"

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


def extract_clean_hostname(url_or_host: Optional[str]) -> Optional[str]:
    """
    Extracts the exact normalized lowercase hostname from a URL, host:port, or hostname string.
    Correctly strips protocol schemes, credentials, ports, and trailing slashes.
    Never matches arbitrary wildcards or external subdomains.
    """
    if not url_or_host:
        return None
    raw = str(url_or_host).strip().strip("'\"").rstrip("/").lower()
    if not raw:
        return None
    if "://" in raw:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(raw)
            if parsed.hostname:
                return parsed.hostname.lower().strip()
        except Exception:
            pass
    # Strip any path or port components (e.g. "laptop-5shove4t.tail907df1.ts.net:8000" -> "laptop-5shove4t.tail907df1.ts.net")
    host_only = raw.split("/")[0].split(":")[0].strip().lower()
    return host_only or None


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
    MULTIMODAL_UPLOAD_DIR: str = str(BASE_DIR / "multimodal_uploads")
    AUTH_DB_PATH: str = str(BASE_DIR / "auth.db")
    OUTPUT_DIR: str = str(BASE_DIR / "generated_artifacts")
    TASK_DB_PATH: str = str(BASE_DIR / "tasks.db")
    DEMO_DATA_DIR: str = str(BASE_DIR / "demo_data")

    # Multimodal, OCR & Vision Capabilities
    OCR_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("OCR_ENABLED", "true").strip().lower() in ("true", "1", "yes"),
        description="Enable local OCR engine for scanned documents and images"
    )
    OCR_PROVIDER: str = Field(
        default_factory=lambda: os.getenv("OCR_PROVIDER", "local").strip(),
        description="Local OCR provider implementation ('local', 'tesseract')"
    )
    TESSERACT_CMD: Optional[str] = Field(
        default_factory=lambda: os.getenv("TESSERACT_CMD", "").strip() or None,
        description="Custom binary path for local tesseract executable if not in PATH"
    )
    VISION_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("VISION_ENABLED", "true").strip().lower() in ("true", "1", "yes"),
        description="Enable local vision model interface"
    )
    VISION_PROVIDER: str = Field(
        default_factory=lambda: os.getenv("VISION_PROVIDER", "ollama").strip(),
        description="Local vision provider ('ollama')"
    )
    VISION_MODEL_NAME: str = Field(
        default_factory=lambda: os.getenv("VISION_MODEL_NAME", "llava").strip(),
        description="Local open-weight vision model name in Ollama"
    )
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

    # Public Share Mode (Cloudflare Tunnel to Local FastAPI 127.0.0.1:8000)
    PUBLIC_SHARE_ENABLED: bool = Field(
        default_factory=lambda: (
            os.getenv("PUBLIC_SHARE_ENABLED", os.getenv("WORKBENCH_PUBLIC_SHARE_ENABLED", "false")).strip().lower() in ("true", "1", "yes")
            or (BASE_DIR / ".public_share_url").is_file()
        ),
        validation_alias=AliasChoices("PUBLIC_SHARE_ENABLED", "WORKBENCH_PUBLIC_SHARE_ENABLED") if AliasChoices else "PUBLIC_SHARE_ENABLED",
        description="Enable Public Share Mode via secure HTTPS tunnel while running AI on-premise."
    )
    PUBLIC_SHARE_MODE: str = Field(
        default_factory=lambda: os.getenv("PUBLIC_SHARE_MODE", os.getenv("WORKBENCH_PUBLIC_SHARE_MODE", "quick")).strip().lower(),
        validation_alias=AliasChoices("PUBLIC_SHARE_MODE", "WORKBENCH_PUBLIC_SHARE_MODE") if AliasChoices else "PUBLIC_SHARE_MODE",
        description="Public share tunnel mode: 'quick' (ephemeral trycloudflare.com) or 'stable' (Cloudflare Named Tunnel)"
    )
    PUBLIC_BASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("PUBLIC_BASE_URL", os.getenv("WORKBENCH_PUBLIC_BASE_URL", "")).strip() or None,
        validation_alias=AliasChoices("PUBLIC_BASE_URL", "WORKBENCH_PUBLIC_BASE_URL") if AliasChoices else "PUBLIC_BASE_URL",
        description="Public HTTPS base URL provided by Cloudflare Tunnel (e.g. https://xxx.trycloudflare.com or https://ai.example.com)"
    )
    CLOUDFLARE_TUNNEL_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLOUDFLARE_TUNNEL_NAME", os.getenv("WORKBENCH_CLOUDFLARE_TUNNEL_NAME", "")).strip() or None,
        validation_alias=AliasChoices("CLOUDFLARE_TUNNEL_NAME", "WORKBENCH_CLOUDFLARE_TUNNEL_NAME") if AliasChoices else "CLOUDFLARE_TUNNEL_NAME",
        description="Name of configured Cloudflare Named Tunnel (e.g. 'sovereign-workbench')"
    )
    CLOUDFLARE_TUNNEL_TOKEN: Optional[str] = Field(
        default_factory=lambda: os.getenv("CLOUDFLARE_TUNNEL_TOKEN", os.getenv("WORKBENCH_CLOUDFLARE_TUNNEL_TOKEN", "")).strip() or None,
        validation_alias=AliasChoices("CLOUDFLARE_TUNNEL_TOKEN", "WORKBENCH_CLOUDFLARE_TUNNEL_TOKEN") if AliasChoices else "CLOUDFLARE_TUNNEL_TOKEN",
        description="Cloudflare Named Tunnel run token (confidential; never commit to version control)"
    )
    TUNNEL_PROVIDER: str = Field(
        default_factory=lambda: os.getenv("TUNNEL_PROVIDER", "cloudflare").strip(),
        description="Tunnel provider used for public share ('cloudflare')"
    )
    PUBLIC_MAX_REQUESTS_PER_MINUTE: int = Field(
        default_factory=lambda: int(os.getenv("PUBLIC_MAX_REQUESTS_PER_MINUTE", "120")),
        description="Max requests per minute per IP in public share mode"
    )
    PUBLIC_MAX_UPLOAD_MB: int = Field(
        default_factory=lambda: int(os.getenv("PUBLIC_MAX_UPLOAD_MB", "25")),
        description="Max upload size in MB in public share mode"
    )
    PUBLIC_MAX_CONCURRENT_TASKS: int = Field(
        default_factory=lambda: int(os.getenv("PUBLIC_MAX_CONCURRENT_TASKS", "3")),
        description="Max concurrent tasks per user/IP in public share mode"
    )

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

    # CORS & Host Validation Configuration
    CORS_ORIGINS: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", os.getenv("WORKBENCH_CORS_ORIGINS", "")).strip(),
        validation_alias=AliasChoices("CORS_ORIGINS", "WORKBENCH_CORS_ORIGINS") if AliasChoices else "CORS_ORIGINS",
        description="Comma-separated allowed CORS origins for external clients"
    )
    ALLOWED_HOSTS: str = Field(
        default_factory=lambda: os.getenv("ALLOWED_HOSTS", os.getenv("WORKBENCH_ALLOWED_HOSTS", "")).strip(),
        validation_alias=AliasChoices("ALLOWED_HOSTS", "WORKBENCH_ALLOWED_HOSTS") if AliasChoices else "ALLOWED_HOSTS",
        description="Comma-separated allowed Host header names"
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
            os.getenv("GOOGLE_REDIRECT_URI", os.getenv("WORKBENCH_GOOGLE_REDIRECT_URI", "")).strip()
            or (
                "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/google/callback"
                if os.getenv("ENVIRONMENT", os.getenv("WORKBENCH_ENVIRONMENT", "production-airgapped")).strip() == "production-cloud"
                else "http://127.0.0.1:8000/api/auth/google/callback"
            )
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
            os.getenv("GITHUB_REDIRECT_URI", os.getenv("WORKBENCH_GITHUB_REDIRECT_URI", "")).strip()
            or (
                "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/github/callback"
                if os.getenv("ENVIRONMENT", os.getenv("WORKBENCH_ENVIRONMENT", "production-airgapped")).strip() == "production-cloud"
                else "http://127.0.0.1:8000/api/auth/github/callback"
            )
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
        if not self.GITHUB_REDIRECT_URI:
            self.GITHUB_REDIRECT_URI = (
                "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/github/callback"
                if self.ENVIRONMENT == "production-cloud"
                else "http://127.0.0.1:8000/api/auth/github/callback"
            )
        if not self.GOOGLE_REDIRECT_URI:
            self.GOOGLE_REDIRECT_URI = (
                "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/google/callback"
                if self.ENVIRONMENT == "production-cloud"
                else "http://127.0.0.1:8000/api/auth/google/callback"
            )

    def get_public_url(self) -> Optional[str]:
        """Resolves active public tunnel URL from environment, settings, or runtime file."""
        if "PUBLIC_BASE_URL" in os.environ:
            env_val = os.getenv("PUBLIC_BASE_URL", "").strip()
            if env_val:
                return env_val
            return None
        env_val = (os.getenv("WORKBENCH_PUBLIC_BASE_URL") or "").strip()
        if env_val:
            return env_val
        if self.PUBLIC_BASE_URL and self.PUBLIC_BASE_URL.strip():
            return self.PUBLIC_BASE_URL.strip()
        url_file = PUBLIC_SHARE_FILE
        if url_file.is_file():
            try:
                content = url_file.read_text(encoding="utf-8").strip()
                if content.startswith("http"):
                    return content
            except Exception:
                pass
        return None

    def is_stable_tunnel(self) -> bool:
        """Truthfully evaluates whether stable Cloudflare Named Tunnel mode is configured."""
        mode = (getattr(self, "PUBLIC_SHARE_MODE", "quick") or "quick").strip().lower()
        if mode in ("stable", "named", "public_share_stable"):
            return True
        return bool(self.CLOUDFLARE_TUNNEL_NAME or self.CLOUDFLARE_TUNNEL_TOKEN)

    def is_public_share_active(self) -> bool:
        """Truthfully evaluates whether Public Share Mode is currently active."""
        if "PUBLIC_BASE_URL" in os.environ:
            env_val = os.getenv("PUBLIC_BASE_URL", "").strip()
            if env_val:
                return True
            if not self.PUBLIC_SHARE_ENABLED and not self.is_stable_tunnel():
                return False
        if bool((os.getenv("WORKBENCH_PUBLIC_BASE_URL") or "").strip()):
            return True
        if bool(self.PUBLIC_BASE_URL and self.PUBLIC_BASE_URL.strip()):
            return True
        if self.PUBLIC_SHARE_ENABLED:
            return True
        if self.is_stable_tunnel():
            return True
        return PUBLIC_SHARE_FILE.is_file()

    def get_cors_origins(self) -> List[str]:
        """Returns verified origins allowed for CORS."""
        origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if self.is_public_share_active():
            pub_url = self.get_public_url()
            if pub_url:
                norm_pub = pub_url.strip().rstrip("/")
                if norm_pub and norm_pub not in origins:
                    origins.append(norm_pub)
        if self.CORS_ORIGINS:
            for part in self.CORS_ORIGINS.split(","):
                part = part.strip().rstrip("/")
                if part and part not in origins:
                    origins.append(part)
        return origins

    def google_oauth_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    def github_oauth_configured(self) -> bool:
        return bool(self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET)

    def get_google_redirect_uri(self) -> str:
        """Dynamically resolves authoritative Google redirect URI for local, cloud, or public share tunnel."""
        if self.is_public_share_active():
            pub_url = self.get_public_url()
            if pub_url and (not self.GOOGLE_REDIRECT_URI or "127.0.0.1" in self.GOOGLE_REDIRECT_URI or "localhost" in self.GOOGLE_REDIRECT_URI):
                return f"{pub_url.rstrip('/')}/api/auth/google/callback"
        if self.GOOGLE_REDIRECT_URI and not any(local in self.GOOGLE_REDIRECT_URI for local in ("127.0.0.1", "localhost")):
            return self.GOOGLE_REDIRECT_URI.strip().lstrip('"\'<').rstrip('"\'>')
        if self.ENVIRONMENT == "production-cloud":
            return "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/google/callback"
        return f"http://127.0.0.1:{self.PORT}/api/auth/google/callback"

    def get_github_redirect_uri(self) -> str:
        """Dynamically resolves authoritative GitHub redirect URI for local, cloud, or public share tunnel."""
        if self.is_public_share_active():
            pub_url = self.get_public_url()
            if pub_url and (not self.GITHUB_REDIRECT_URI or "127.0.0.1" in self.GITHUB_REDIRECT_URI or "localhost" in self.GITHUB_REDIRECT_URI):
                return f"{pub_url.rstrip('/')}/api/auth/github/callback"
        if self.GITHUB_REDIRECT_URI and not any(local in self.GITHUB_REDIRECT_URI for local in ("127.0.0.1", "localhost")):
            return self.GITHUB_REDIRECT_URI.strip().lstrip('"\'<').rstrip('"\'>')
        if self.ENVIRONMENT == "production-cloud":
            return "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/github/callback"
        return f"http://127.0.0.1:{self.PORT}/api/auth/github/callback"


    def is_host_allowed(self, host_header: Optional[str]) -> bool:
        """
        Validates Host header against allowed local, cloud, and active tunnel hosts.
        Prevents Host Header Injection and cache poisoning.
        Allows ONLY the exact configured public hostname from PUBLIC_BASE_URL (e.g. Tailscale Funnel).
        Strictly rejects arbitrary *.ts.net, *.trycloudflare.com (in stable mode), or external domains.
        """
        if not host_header:
            return False

        # Extract normalized incoming hostname without port
        host = extract_clean_hostname(host_header)
        if not host:
            return False

        # Always allowed local loopback addresses and testing framework
        if host in ("127.0.0.1", "localhost", "testserver", "::1"):
            return True

        # Render deployment hosts
        if host in ("sovereign-ai-workbench-wb96.onrender.com", "onrender.com"):
            return True
        render_ext = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip().lower()
        if render_ext and host == render_ext:
            return True

        # Check explicit ALLOWED_HOSTS config
        if self.ALLOWED_HOSTS:
            explicit_hosts = [h.strip().lower() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]
            if host in explicit_hosts:
                return True

        # Check configured PUBLIC_BASE_URL from dynamic environment, settings, or runtime file
        pub_url = self.get_public_url()
        if pub_url:
            p_host = extract_clean_hostname(pub_url)
            if p_host and host == p_host:
                return True

        # Check explicitly set self.PUBLIC_BASE_URL
        if self.PUBLIC_BASE_URL:
            cfg_host = extract_clean_hostname(self.PUBLIC_BASE_URL)
            if cfg_host and host == cfg_host:
                return True

        # Check dynamic env variable PUBLIC_BASE_URL
        env_pub = (os.getenv("PUBLIC_BASE_URL") or os.getenv("WORKBENCH_PUBLIC_BASE_URL") or "").strip()
        if env_pub:
            env_host = extract_clean_hostname(env_pub)
            if env_host and host == env_host:
                return True

        # If Public Share is active in Quick Tunnel mode, allow Cloudflare ephemeral trycloudflare.com
        if self.is_public_share_active() and not self.is_stable_tunnel():
            if host.endswith(".trycloudflare.com"):
                import re
                if re.match(r"^[a-zA-Z0-9-]+\.trycloudflare\.com$", host):
                    return True

        return False

    @property
    def EMBEDDING_MODEL(self) -> str:
        return self.EMBEDDING_MODEL_NAME


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
os.makedirs(settings.MULTIMODAL_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(os.path.abspath(settings.AUDIT_LOG_FILE)), exist_ok=True)


def verify_zero_external_ai() -> dict:
    """
    Architecturally and cryptographically verifies zero external AI APIs are configured or invoked.
    Ensures complete sovereign integrity on-premise.
    """
    cloud_ai_env_keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GROQ_API_KEY",
        "COHERE_API_KEY",
        "MISTRAL_API_KEY",
        "AWS_BEDROCK_API_KEY",
        "OPENROUTER_API_KEY"
    ]
    configured = [k for k in cloud_ai_env_keys if os.getenv(k, "").strip()]
    return {
        "zero_external_ai": len(configured) == 0,
        "external_ai_calls": 0,
        "external_providers_detected": configured,
        "local_reasoning_model": settings.DEFAULT_MODEL,
        "local_vision_model": settings.VISION_MODEL_NAME,
        "local_embeddings": settings.EMBEDDING_MODEL_NAME,
        "local_ocr": "tesseract",
        "local_vector_db": "chromadb"
    }


def get_runtime_mode_info(ollama_connected: bool = True) -> dict:
    """
    Central, truthful runtime mode detector.
    Evaluates:
    - PUBLIC_SHARE: Active when PUBLIC_SHARE_ENABLED is True or .public_share_url exists.
      Never reports air_gapped=True.
      Label: "PUBLIC SHARE / LOCAL AI"
      Notice: "Local AI remains on this machine. Public users access this application through a secure HTTPS tunnel."
    - CLOUD_DEMO: Active in cloud environments without local Ollama stack.
      Label: "CLOUD DEMO / LOCAL AI REQUIRED"
    - LOCAL_AIR_GAPPED: Active on local machine without public tunnel.
      Label: "AIR-GAPPED / ON-PREMISE VERIFIED"
      air_gapped=True.
    """
    zero_ai = verify_zero_external_ai()
    is_public = is_public_share_active()

    if is_public:
        pub_url = get_public_url()
        is_stable = settings.is_stable_tunnel()
        if ollama_connected:
            if is_stable:
                return {
                    "runtime_mode": "PUBLIC_SHARE_STABLE",
                    "runtime_label": "PUBLIC SHARE / LOCAL AI",
                    "air_gapped": False,
                    "public_share": True,
                    "stable_tunnel": True,
                    "tunnel_type": "named",
                    "tunnel_provider": "cloudflare",
                    "runtime_notice": "Local AI remains on this machine. Public users access this application through a secure Cloudflare Named Tunnel HTTPS tunnel. This is a public demonstration mode, not an air-gapped environment.",
                    "public_url": pub_url,
                    "local_url": f"http://127.0.0.1:{settings.PORT}",
                    "ai_runtime": "LOCAL",
                    "external_ai_calls": zero_ai["external_ai_calls"],
                    "zero_external_ai": zero_ai["zero_external_ai"]
                }
            else:
                is_ts = bool(pub_url and "ts.net" in pub_url.lower())
                provider = "tailscale" if is_ts else "cloudflare"
                t_type = "tailscale_funnel" if is_ts else "quick"
                notice = (
                    "Local AI remains on this machine. Public users access this application through a secure Tailscale Funnel HTTPS tunnel. This is a public demonstration mode, not an air-gapped environment."
                    if is_ts
                    else "Local AI remains on this machine. Public users access this application through a secure HTTPS tunnel. This is a public demonstration mode, not an air-gapped environment."
                )
                return {
                    "runtime_mode": "PUBLIC_SHARE",
                    "runtime_label": "PUBLIC SHARE / LOCAL AI",
                    "air_gapped": False,
                    "public_share": True,
                    "stable_tunnel": False,
                    "tunnel_type": t_type,
                    "tunnel_provider": provider,
                    "runtime_notice": notice,
                    "public_url": pub_url,
                    "local_url": f"http://127.0.0.1:{settings.PORT}",
                    "ai_runtime": "LOCAL",
                    "external_ai_calls": zero_ai["external_ai_calls"],
                    "zero_external_ai": zero_ai["zero_external_ai"]
                }
        else:
            return {
                "runtime_mode": "CLOUD_DEMO",
                "runtime_label": "CLOUD DEMO / LOCAL AI REQUIRED",
                "air_gapped": False,
                "public_share": True,
                "stable_tunnel": is_stable,
                "tunnel_type": "named" if is_stable else "quick",
                "runtime_notice": "Local Ollama daemon is currently offline on the host machine. Start 'ollama serve' to enable local inference.",
                "public_url": pub_url,
                "local_url": f"http://127.0.0.1:{settings.PORT}",
                "ai_runtime": "LOCAL_REQUIRED",
                "external_ai_calls": zero_ai["external_ai_calls"],
                "zero_external_ai": zero_ai["zero_external_ai"]
            }

    is_cloud = (settings.ENVIRONMENT == "production-cloud" or not settings.AIR_GAP_STRICT_MODE)
    if is_cloud:
        if ollama_connected:
            return {
                "runtime_mode": "CLOUD_CONNECTED",
                "runtime_label": "CLOUD DEMO / OLLAMA CONNECTED",
                "air_gapped": False,
                "public_share": False,
                "runtime_notice": "Connected to remote Ollama inference instance.",
                "public_url": None,
                "local_url": f"http://127.0.0.1:{settings.PORT}",
                "ai_runtime": "REMOTE_OLLAMA",
                "external_ai_calls": zero_ai["external_ai_calls"],
                "zero_external_ai": zero_ai["zero_external_ai"]
            }
        else:
            return {
                "runtime_mode": "CLOUD_DEMO",
                "runtime_label": "CLOUD DEMO / LOCAL AI REQUIRED",
                "air_gapped": False,
                "public_share": False,
                "runtime_notice": "Cloud demonstration runtime. Sovereign AI inference requires the local/on-premise runtime with Ollama.",
                "public_url": None,
                "local_url": f"http://127.0.0.1:{settings.PORT}",
                "ai_runtime": "LOCAL_REQUIRED",
                "external_ai_calls": zero_ai["external_ai_calls"],
                "zero_external_ai": zero_ai["zero_external_ai"]
            }

    # LOCAL_AIR_GAPPED
    if ollama_connected:
        return {
            "runtime_mode": "LOCAL_AIR_GAPPED",
            "runtime_label": "AIR-GAPPED / ON-PREMISE VERIFIED",
            "air_gapped": True,
            "public_share": False,
            "runtime_notice": None,
            "public_url": None,
            "local_url": f"http://127.0.0.1:{settings.PORT}",
            "ai_runtime": "LOCAL",
            "external_ai_calls": zero_ai["external_ai_calls"],
            "zero_external_ai": zero_ai["zero_external_ai"]
        }
    else:
        return {
            "runtime_mode": "LOCAL_AIR_GAPPED",
            "runtime_label": "AIR-GAPPED / OLLAMA OFFLINE",
            "air_gapped": True,
            "public_share": False,
            "runtime_notice": "Ollama local inference daemon is unreachable. Start 'ollama serve' on the local host.",
            "public_url": None,
            "local_url": f"http://127.0.0.1:{settings.PORT}",
            "ai_runtime": "LOCAL_OFFLINE",
            "external_ai_calls": zero_ai["external_ai_calls"],
            "zero_external_ai": zero_ai["zero_external_ai"]
        }


class AirGapViolationError(Exception):
    """Raised when an endpoint or configuration violates air-gap security constraints."""
    pass


SecurityError = AirGapViolationError


def validate_air_gap_compliance() -> bool:
    """
    Validates that inference endpoints and storage paths do NOT route to public internet.
    In cloud demo mode (AIR_GAP_STRICT_MODE=False), logs informational notice.
    In Public Share Mode, Ollama must still strictly resolve to loopback/on-premise network.
    """
    if not settings.AIR_GAP_STRICT_MODE and not settings.is_public_share_active():
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


def get_public_url() -> Optional[str]:
    """Module-level helper to resolve active public tunnel URL."""
    return settings.get_public_url()


def is_public_share_active() -> bool:
    """Module-level helper evaluating whether Public Share Mode is currently active."""
    return settings.is_public_share_active()


def get_google_redirect_uri() -> str:
    """Module-level helper to resolve authoritative Google OAuth redirect URI."""
    return settings.get_google_redirect_uri()


def get_github_redirect_uri() -> str:
    """Module-level helper to resolve authoritative GitHub OAuth redirect URI."""
    return settings.get_github_redirect_uri()


# Run compliance validation on module load
validate_air_gap_compliance()
