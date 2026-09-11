# 05. Authentication Subsystem (`backend/app/security/auth.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/security/auth.py`

## 2. File Purpose
Provides user credential verification, password hashing, JWT creation, token validation, and token revocation.

## 3. Cryptographic Implementation
- **Hashing:** `bcrypt` via `passlib.context.CryptContext` with salt cost 12. Constant-time comparison prevents timing attacks.
- **JWT Signing:** `HS256` symmetric signing with `settings.SECRET_KEY`.
- **JWT Claims:** `sub` (username), `role` (user role), `exp` (expiration), `jti` (unique UUID4).
- **Revocation:** `revoke_token(token)` writes `jti` to `auth.db:revoked_tokens`.
- **Validation:** `get_current_user()` decodes token, verifies signature, confirms `jti` is not in revocation table, and checks user active status in `auth.db`.
