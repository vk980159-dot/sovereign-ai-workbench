"""
Autonomous Local Authentication & Session Security Engine (Argon2id + SQLite)
100% Air-Gapped, Zero Cloud Dependencies (No Auth0, Firebase, Supabase, or Clerk).
Provides user self-registration, Argon2 password hashing, dual username/email authentication,
cryptographic HMAC-SHA256 session tokens, and SHA-256 micro-ledger audit logging.
"""

import os
import re
import sqlite3
import secrets
import hashlib
import hmac
import base64
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from app.config import settings
from app.security.audit_logger import audit_logger

security_bearer = HTTPBearer(auto_error=False)

# Optional Argon2id hasher (recommended) with automatic fallback
try:
    import argon2
    _argon2_hasher = argon2.PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=1,
        hash_len=32,
        type=argon2.Type.ID
    )
except Exception:
    _argon2_hasher = None

# Validation regular expressions
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


def _get_db_connection() -> sqlite3.Connection:
    """Provides a thread-safe connection to the local SQLite auth database."""
    conn = sqlite3.connect(settings.AUTH_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """
    Hashes password using Argon2id (memory-hard, resistant to GPU/ASIC attacks).
    Falls back to PBKDF2-HMAC-SHA256 (100,000 iterations) if Argon2 is unavailable.
    Returns standard serialized hash string.
    """
    if _argon2_hasher is not None:
        return _argon2_hasher.hash(password)

    # Standard library PBKDF2 fallback
    salt_bytes = secrets.token_bytes(16)
    salt_hex = salt_bytes.hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        iterations=100_000
    ).hex()
    return f"pbkdf2${salt_hex}${pwd_hash}"


def verify_password(plain_password: str, stored_hash: str, legacy_salt: Optional[str] = None) -> bool:
    """
    Verifies a plain password against the stored hash in constant time.
    Supports Argon2id, serialized PBKDF2, and legacy dual-column hashes.
    """
    if not stored_hash or not plain_password:
        return False

    # 1. Argon2 verification
    if stored_hash.startswith("$argon2"):
        if _argon2_hasher is None:
            return False
        try:
            return _argon2_hasher.verify(stored_hash, plain_password)
        except Exception:
            return False

    # 2. Serialized PBKDF2 verification (pbkdf2$salt$hash)
    if stored_hash.startswith("pbkdf2$"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                salt_bytes = bytes.fromhex(parts[1])
                computed_hash = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt_bytes,
                    iterations=100_000
                ).hex()
                return hmac.compare_digest(computed_hash, parts[2])
        except Exception:
            return False

    # 3. Legacy hash + salt dual-column PBKDF2 fallback
    if legacy_salt:
        try:
            salt_bytes = bytes.fromhex(legacy_salt)
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt_bytes,
                iterations=100_000
            ).hex()
            return hmac.compare_digest(computed_hash, stored_hash)
        except Exception:
            return False

    return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Enforces password strength policies for on-premise accounts:
    - Minimum length (default 8 characters)
    - At least one letter
    - At least one digit or special character
    """
    min_len = getattr(settings, "PASSWORD_MIN_LENGTH", 8)
    if len(password) < min_len:
        return False, f"Password must contain at least {min_len} characters."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one number or special character."
    return True, None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_session_token(user: Dict[str, Any], expires_hours: Optional[int] = None) -> str:
    """
    Generates a tamper-evident HMAC-SHA256 signed session token.
    Token structure: [base64_payload].[base64_signature]
    """
    hours = expires_hours or settings.SESSION_EXPIRE_HOURS
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=hours)

    payload = {
        "sub": user["username"],
        "email": user.get("email", ""),
        "full_name": user.get("full_name", user["username"]),
        "user_id": user.get("id"),
        "role": user.get("role", "user"),
        "jti": secrets.token_hex(16),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }

    serialized_payload = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    encoded_payload = _b64url_encode(serialized_payload)

    signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()
    encoded_signature = _b64url_encode(signature)

    return f"{encoded_payload}.{encoded_signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates token signature, expiration timestamp, and revocation status.
    Returns decoded token payload if authentic, None otherwise.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        encoded_payload, encoded_signature = parts
        expected_signature = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            encoded_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()

        actual_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        payload_bytes = _b64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("exp", 0) < now_ts:
            return None

        # Check revocation table in database
        jti = payload.get("jti")
        if jti:
            with _get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,))
                if cur.fetchone() is not None:
                    return None

        return payload
    except Exception:
        return None


def init_auth_db():
    """
    Bootstraps the local SQLite authentication database.
    Creates schema, applies automatic migrations, and seeds the initial admin if needed.
    """
    os.makedirs(os.path.dirname(os.path.abspath(settings.AUTH_DB_PATH)), exist_ok=True)
    with _get_db_connection() as conn:
        cur = conn.cursor()

        # 1. Create table if not exists with updated schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL DEFAULT '',
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                revoked_at TEXT NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS linked_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL COLLATE NOCASE,
                provider_user_id TEXT NOT NULL,
                provider_email TEXT NOT NULL DEFAULT '' COLLATE NOCASE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

        # Ensure index on linked_accounts
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_linked_provider_uid ON linked_accounts (provider COLLATE NOCASE, provider_user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_linked_user_id ON linked_accounts (user_id)")
        conn.commit()

        # 2. Check for schema migration on existing tables
        cur.execute("PRAGMA table_info(users)")
        columns = {row["name"] for row in cur.fetchall()}

        if "full_name" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")
        if "email" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")
            cur.execute("UPDATE users SET email = username || '@sovereign.local' WHERE email = ''")
        if "is_active" not in columns:
            cur.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        conn.commit()

        # Ensure index on email and username
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username COLLATE NOCASE)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email COLLATE NOCASE)")
        conn.commit()

        # 3. Check if initial bootstrap administrator is needed
        cur.execute("SELECT COUNT(*) as count FROM users")
        row = cur.fetchone()
        if row and row["count"] == 0:
            bootstrap_admin_user(
                username=settings.ADMIN_DEFAULT_USERNAME,
                password=settings.ADMIN_DEFAULT_PASSWORD,
                email=getattr(settings, "ADMIN_DEFAULT_EMAIL", "admin@sovereign.local"),
                full_name=getattr(settings, "ADMIN_DEFAULT_FULL_NAME", "Sovereign Administrator")
            )


def bootstrap_admin_user(
    username: str,
    password: str,
    email: str = "admin@sovereign.local",
    full_name: str = "Sovereign Administrator"
) -> bool:
    """
    Safely creates or resets the primary administrator account in local SQLite.
    Logs AUTH_BOOTSTRAP to the immutable SHA-256 micro-ledger without exposing passwords.
    """
    pwd_hash = hash_password(password)
    now_iso = datetime.now(timezone.utc).isoformat()

    with _get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE users 
                SET full_name = ?, email = ?, password_hash = ?, salt = '', role = 'admin', is_active = 1
                WHERE id = ?
            """, (full_name.strip(), email.strip().lower(), pwd_hash, existing["id"]))
        else:
            cur.execute("""
                INSERT INTO users (full_name, username, email, password_hash, salt, role, is_active, created_at)
                VALUES (?, ?, ?, ?, '', 'admin', 1, ?)
            """, (full_name.strip(), username.strip(), email.strip().lower(), pwd_hash, now_iso))
        conn.commit()

    # Log to cryptographic audit ledger
    audit_logger.log_event(
        event_type="AUTH_BOOTSTRAP",
        agent_name="AUTH_ENGINE",
        action="BOOTSTRAP_ADMIN_USER",
        details={
            "username": username.strip(),
            "email_domain": email.split("@")[-1] if "@" in email else "local",
            "role": "admin",
            "note": "Primary administrator account provisioned locally in air-gapped storage."
        },
        input_data=f"BOOTSTRAP_ADMIN_{username.strip()}",
        output_data="ADMIN_PROVISIONED_SUCCESS"
    )
    return True


def register_user(
    full_name: str,
    username: str,
    email: str,
    password: str,
    confirm_password: str,
    client_ip: str = "127.0.0.1"
) -> Dict[str, Any]:
    """
    Registers a new sovereign user with complete input validation and Argon2 hashing.
    Rejects duplicate username/email and records registration into SHA-256 audit trail.
    """
    full_name = full_name.strip()
    username = username.strip()
    email = email.strip().lower()

    # 1. Full name validation
    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name must be at least 2 characters in length."
        )

    # 2. Username format validation
    if not USERNAME_REGEX.match(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-32 characters long and contain only letters, numbers, underscores, or hyphens."
        )

    # 3. Email format validation
    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # 4. Password confirmation match
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password do not match."
        )

    # 5. Password complexity requirement
    is_strong, reason = validate_password_strength(password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Password does not meet minimum complexity standards."
        )

    # 6. Uniqueness checks in local SQLite
    with _get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, email FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
            (username, email)
        )
        existing = cur.fetchone()
        if existing:
            # Safe generic error message preventing unauthorized enumeration
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email is already registered."
            )

        # 7. Hash password with Argon2 and persist
        pwd_hash = hash_password(password)
        now_iso = datetime.now(timezone.utc).isoformat()

        cur.execute("""
            INSERT INTO users (full_name, username, email, password_hash, salt, role, is_active, created_at)
            VALUES (?, ?, ?, ?, '', 'user', 1, ?)
        """, (full_name, username, email, pwd_hash, now_iso))
        conn.commit()

    # 8. Log registration success to SHA-256 micro-ledger (never log passwords!)
    audit_logger.log_event(
        event_type="AUTH_REGISTER_SUCCESS",
        agent_name="AUTH_ENGINE",
        action="USER_REGISTRATION",
        details={
            "username": username,
            "email_domain": email.split("@")[-1] if "@" in email else "local",
            "client_ip": client_ip,
            "role": "user"
        },
        input_data=f"REGISTER_USER_{username}",
        output_data="ACCOUNT_CREATED_SUCCESS"
    )

    return {
        "status": "SUCCESS",
        "message": "Account created successfully. Please sign in.",
        "username": username
    }


def authenticate_user(
    username_or_email: str,
    password: str,
    client_ip: str = "127.0.0.1",
    link_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Verifies credentials allowing login via username OR email address.
    If an account link_token is present and valid, links the social identity to this account.
    Logs success/failure to the SHA-256 micro-ledger without logging passwords.
    """
    identifier = username_or_email.strip()

    with _get_db_connection() as conn:
        cur = conn.cursor()
        # Query matching either username or email (case-insensitive)
        cur.execute("""
            SELECT * FROM users 
            WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?))
              AND is_active = 1
        """, (identifier, identifier.lower()))
        user_row = cur.fetchone()
        if not user_row:
            audit_logger.log_event(
                event_type="AUTH_FAILURE",
                agent_name="AUTH_ENGINE",
                action="LOGIN_REJECTED",
                details={
                    "attempted_identifier": identifier[:50],
                    "client_ip": client_ip,
                    "reason": "Invalid credentials or non-existent account"
                },
                input_data=f"LOGIN_ATTEMPT_{identifier[:50]}",
                output_data="ACCESS_DENIED_401"
            )
            return None

        salt_val = user_row["salt"] if "salt" in user_row.keys() else None
        if not verify_password(password, user_row["password_hash"], salt_val):
            audit_logger.log_event(
                event_type="AUTH_FAILURE",
                agent_name="AUTH_ENGINE",
                action="LOGIN_REJECTED",
                details={
                    "attempted_identifier": identifier[:50],
                    "client_ip": client_ip,
                    "reason": "Invalid credentials or non-existent account"
                },
                input_data=f"LOGIN_ATTEMPT_{identifier[:50]}",
                output_data="ACCESS_DENIED_401"
            )
            return None

        # Update last login timestamp
        now_iso = datetime.now(timezone.utc).isoformat()
        cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso, user_row["id"]))
        conn.commit()

        # Audit log successful authentication
        audit_logger.log_event(
            event_type="AUTH_SUCCESS",
            agent_name="AUTH_ENGINE",
            action="LOGIN_APPROVED",
            details={
                "username": user_row["username"],
                "role": user_row["role"],
                "client_ip": client_ip
            },
            input_data=f"LOGIN_SUCCESS_{user_row['username']}",
            output_data="SESSION_TOKEN_ISSUED"
        )

        # Process explicit account linking if a valid link_token was provided
        if link_token:
            link_payload = verify_account_link_token(link_token)
            if link_payload:
                link_social_account(
                    user_id=user_row["id"],
                    provider=link_payload["provider"],
                    provider_user_id=link_payload["provider_user_id"],
                    provider_email=link_payload.get("email", user_row["email"]),
                    client_ip=client_ip
                )

        return {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "role": user_row["role"]
        }


# ==========================================
# OAUTH 2.0 / SOCIAL AUTHENTICATION HELPERS
# ==========================================

def create_oauth_state(provider: str) -> str:
    """
    Generates a cryptographically signed, tamper-resistant OAuth state token.
    Prevents Cross-Site Request Forgery (CSRF) in the OAuth callback flow.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "provider": provider.lower(),
        "nonce": secrets.token_hex(16),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp())
    }
    serialized = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    encoded_payload = _b64url_encode(serialized)
    sig = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_b64url_encode(sig)}"


def verify_oauth_state(
    state: str,
    expected_cookie: Optional[str] = None,
    expected_provider: Optional[str] = None
) -> bool:
    """
    Validates OAuth state signature, expiration, and optional cookie/provider match.
    """
    if not state:
        return False
    try:
        parts = state.split(".")
        if len(parts) != 2:
            return False
        encoded_payload, encoded_sig = parts

        expected_sig = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            encoded_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(encoded_sig)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return False

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("exp", 0) < now_ts:
            return False

        if expected_provider and payload.get("provider") != expected_provider.lower():
            return False

        if expected_cookie and not hmac.compare_digest(state, expected_cookie):
            return False

        return True
    except Exception:
        return False


def create_account_link_token(
    provider: str,
    provider_user_id: str,
    email: str,
    display_name: str = ""
) -> str:
    """
    Generates a tamper-evident signed token for explicit account-linking verification.
    Valid for 15 minutes.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "type": "account_link",
        "provider": provider.lower(),
        "provider_user_id": str(provider_user_id),
        "email": email.strip().lower(),
        "display_name": display_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "jti": secrets.token_hex(16)
    }
    serialized = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    encoded_payload = _b64url_encode(serialized)
    sig = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_b64url_encode(sig)}"


def verify_account_link_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies HMAC signature and expiration on an account link confirmation token.
    """
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        encoded_payload, encoded_sig = parts

        expected_sig = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            encoded_payload.encode("utf-8"),
            hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(encoded_sig)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("exp", 0) < now_ts:
            return None
        if payload.get("type") != "account_link":
            return None

        return payload
    except Exception:
        return None


def log_oauth_event(
    event_type: str,
    provider: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    input_data: str = "",
    output_data: str = ""
):
    """Convenience wrapper for cryptographically recording OAuth lifecycle events."""
    payload_details = {"provider": provider.lower()}
    if details:
        payload_details.update(details)
    audit_logger.log_event(
        event_type=event_type,
        agent_name="AUTH_ENGINE",
        action=action,
        details=payload_details,
        input_data=input_data or f"{provider.upper()}_OAUTH_EVENT",
        output_data=output_data or f"{event_type}_RECORDED"
    )


def link_social_account(
    user_id: int,
    provider: str,
    provider_user_id: str,
    provider_email: str = "",
    client_ip: str = "127.0.0.1"
) -> bool:
    """
    Associates a verified external social identity to an existing local application user.
    Logs SOCIAL_ACCOUNT_LINKED to SHA-256 micro-ledger.
    """
    provider = provider.lower()
    provider_user_id = str(provider_user_id).strip()
    provider_email = provider_email.strip().lower()
    now_iso = datetime.now(timezone.utc).isoformat()

    with _get_db_connection() as conn:
        cur = conn.cursor()
        # Check if link already exists
        cur.execute(
            "SELECT id FROM linked_accounts WHERE provider = ? AND provider_user_id = ?",
            (provider, provider_user_id)
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                "UPDATE linked_accounts SET user_id = ?, provider_email = ? WHERE id = ?",
                (user_id, provider_email, existing["id"])
            )
        else:
            cur.execute("""
                INSERT INTO linked_accounts (user_id, provider, provider_user_id, provider_email, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, provider, provider_user_id, provider_email, now_iso))
        conn.commit()

    log_oauth_event(
        event_type="SOCIAL_ACCOUNT_LINKED",
        provider=provider,
        action="LINK_SOCIAL_IDENTITY",
        details={
            "user_id": user_id,
            "provider_user_id": provider_user_id,
            "provider_email_domain": provider_email.split("@")[-1] if "@" in provider_email else "unknown",
            "client_ip": client_ip
        },
        input_data=f"LINK_{provider.upper()}_TO_USER_{user_id}",
        output_data="SOCIAL_IDENTITY_LINKED_SUCCESS"
    )
    return True


def resolve_social_user(
    provider: str,
    provider_user_id: str,
    email: str,
    full_name: str = "",
    client_ip: str = "127.0.0.1"
) -> Dict[str, Any]:
    """
    Resolves an incoming OAuth authenticated identity according to Sovereign AI Workbench rules:
    1. If (provider, provider_user_id) exists in linked_accounts -> authenticate user directly.
    2. If not linked, but email matches an existing local user -> require explicit password confirmation.
    3. If neither -> create new local user account with disabled password and link identity.
    """
    provider = provider.lower()
    provider_user_id = str(provider_user_id).strip()
    email = email.strip().lower()
    full_name = full_name.strip() if full_name else ""

    with _get_db_connection() as conn:
        cur = conn.cursor()

        # Rule 1: Check linked_accounts
        cur.execute("""
            SELECT u.* FROM users u
            JOIN linked_accounts la ON u.id = la.user_id
            WHERE la.provider = ? AND la.provider_user_id = ?
        """, (provider, provider_user_id))
        linked_user = cur.fetchone()

        if linked_user:
            if not linked_user["is_active"]:
                return {
                    "status": "ERROR",
                    "error": "Account is inactive. Contact sovereign administrator."
                }
            now_iso = datetime.now(timezone.utc).isoformat()
            cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso, linked_user["id"]))
            conn.commit()

            log_oauth_event(
                event_type=f"{provider.upper()}_LOGIN_SUCCESS",
                provider=provider,
                action=f"{provider.upper()}_AUTH_APPROVED",
                details={
                    "username": linked_user["username"],
                    "role": linked_user["role"],
                    "client_ip": client_ip
                },
                input_data=f"{provider.upper()}_LOGIN_{linked_user['username']}",
                output_data="SESSION_TOKEN_ISSUED"
            )

            return {
                "status": "AUTHENTICATED",
                "user": {
                    "id": linked_user["id"],
                    "username": linked_user["username"],
                    "email": linked_user["email"],
                    "full_name": linked_user["full_name"],
                    "role": linked_user["role"]
                }
            }

        # Rule 2: Check if local account exists with same email
        if email:
            cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                # Local account exists with this email -> explicit linking required
                link_token = create_account_link_token(
                    provider=provider,
                    provider_user_id=provider_user_id,
                    email=email,
                    display_name=full_name or existing_user["full_name"]
                )
                log_oauth_event(
                    event_type=f"{provider.upper()}_LOGIN_LINK_REQUIRED",
                    provider=provider,
                    action="REQUIRE_PASSWORD_CONFIRMATION",
                    details={
                        "existing_username": existing_user["username"],
                        "email_domain": email.split("@")[-1] if "@" in email else "local",
                        "client_ip": client_ip
                    },
                    input_data=f"LINK_PROMPT_{provider.upper()}_{existing_user['username']}",
                    output_data="LINK_CONFIRMATION_REQUESTED"
                )
                return {
                    "status": "LINK_REQUIRED",
                    "link_token": link_token,
                    "email": email,
                    "provider": provider,
                    "existing_username": existing_user["username"]
                }

        # Rule 3: No account found -> create new local user and link
        base_username = ""
        if full_name:
            base_username = re.sub(r"[^a-zA-Z0-9_-]", "", full_name.lower().replace(" ", "_"))
        if not base_username and email:
            base_username = re.sub(r"[^a-zA-Z0-9_-]", "", email.split("@")[0].lower())
        if not base_username:
            base_username = f"{provider}_user"

        if len(base_username) < 3:
            base_username = f"{base_username}_{secrets.token_hex(2)}"
        if len(base_username) > 26:
            base_username = base_username[:26]

        candidate_username = base_username
        attempt = 0
        while True:
            cur.execute("SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)", (candidate_username,))
            if cur.fetchone() is None:
                break
            attempt += 1
            candidate_username = f"{base_username[:24]}_{secrets.token_hex(2)}"
            if attempt > 20:
                candidate_username = f"u_{secrets.token_hex(6)}"
                break

        now_iso = datetime.now(timezone.utc).isoformat()
        display_name = full_name or candidate_username
        dummy_pwd_hash = "oauth$social_identity_no_local_password"

        cur.execute("""
            INSERT INTO users (full_name, username, email, password_hash, salt, role, is_active, created_at, last_login)
            VALUES (?, ?, ?, ?, '', 'user', 1, ?, ?)
        """, (display_name, candidate_username, email, dummy_pwd_hash, now_iso, now_iso))
        new_user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO linked_accounts (user_id, provider, provider_user_id, provider_email, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (new_user_id, provider, provider_user_id, email, now_iso))
        conn.commit()

        log_oauth_event(
            event_type="SOCIAL_ACCOUNT_CREATED",
            provider=provider,
            action="CREATE_LOCAL_USER_FROM_OAUTH",
            details={
                "user_id": new_user_id,
                "username": candidate_username,
                "email_domain": email.split("@")[-1] if "@" in email else "local",
                "client_ip": client_ip
            },
            input_data=f"SOCIAL_CREATE_{provider.upper()}_{candidate_username}",
            output_data="LOCAL_USER_AND_IDENTITY_CREATED"
        )

        log_oauth_event(
            event_type=f"{provider.upper()}_LOGIN_SUCCESS",
            provider=provider,
            action=f"{provider.upper()}_AUTH_APPROVED",
            details={
                "username": candidate_username,
                "role": "user",
                "client_ip": client_ip
            },
            input_data=f"{provider.upper()}_LOGIN_{candidate_username}",
            output_data="SESSION_TOKEN_ISSUED"
        )

        return {
            "status": "AUTHENTICATED",
            "user": {
                "id": new_user_id,
                "username": candidate_username,
                "email": email,
                "full_name": display_name,
                "role": "user"
            }
        }


def logout_user(token: str, client_ip: str = "127.0.0.1") -> bool:
    """
    Revokes the current session token and logs the logout event.
    """
    payload = verify_session_token(token)
    if payload and payload.get("jti"):
        jti = payload["jti"]
        now_iso = datetime.now(timezone.utc).isoformat()
        with _get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO revoked_tokens (jti, revoked_at) VALUES (?, ?)", (jti, now_iso))
            conn.commit()

        audit_logger.log_event(
            event_type="AUTH_LOGOUT",
            agent_name="AUTH_ENGINE",
            action="SESSION_TERMINATED",
            details={
                "username": payload.get("sub", "unknown"),
                "client_ip": client_ip
            },
            input_data=f"LOGOUT_{payload.get('sub', 'unknown')}",
            output_data="SESSION_REVOKED"
        )
        return True
    return False


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts session token from:
    1. Authorization Bearer header
    2. HTTP-only session cookie
    3. Query parameter (?token=...)
    """
    # 1. Bearer Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 2. Cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token.strip()

    # 3. Query Parameter (essential for WebSocket handshakes)
    query_token = request.query_params.get("token")
    if query_token:
        return query_token.strip()

    return None


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces authentication on protected routes.
    Raises HTTP 401 if unauthenticated.
    """
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access Sovereign AI Workbench.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = verify_session_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "username": payload.get("sub"),
        "email": payload.get("email", ""),
        "full_name": payload.get("full_name", payload.get("sub")),
        "role": payload.get("role", "user"),
        "user_id": payload.get("user_id")
    }


def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    Non-blocking helper for page routing. Returns user payload if token is valid, None otherwise.
    """
    token = get_token_from_request(request)
    if not token:
        return None
    return verify_session_token(token)
