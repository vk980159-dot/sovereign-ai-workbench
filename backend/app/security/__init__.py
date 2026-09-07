"""
Security Module for Sovereign AI Workbench
Provides zero-leakage PII Redaction and SHA-256 Cryptographic Audit Trails.
"""

from .pii_redactor import PIIRedactor
from .audit_logger import AuditLogger
from .auth import (
    init_auth_db,
    authenticate_user,
    register_user,
    bootstrap_admin_user,
    logout_user,
    create_session_token,
    verify_session_token,
    get_current_user,
    get_current_user_optional,
    get_token_from_request,
    create_oauth_state,
    verify_oauth_state,
    create_account_link_token,
    verify_account_link_token,
    link_social_account,
    resolve_social_user,
    log_oauth_event
)

__all__ = [
    "PIIRedactor",
    "AuditLogger",
    "init_auth_db",
    "authenticate_user",
    "register_user",
    "bootstrap_admin_user",
    "logout_user",
    "create_session_token",
    "verify_session_token",
    "get_current_user",
    "get_current_user_optional",
    "get_token_from_request",
    "create_oauth_state",
    "verify_oauth_state",
    "create_account_link_token",
    "verify_account_link_token",
    "link_social_account",
    "resolve_social_user",
    "log_oauth_event"
]
