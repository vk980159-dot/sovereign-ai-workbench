# 02. Session Management System
**Status:** [VERIFIED]

## 1. File Path & Functions
`backend/app/security/auth.py`: `create_access_token()`, `get_current_user()`

## 2. Token Format & Signing
- **Format:** JSON Web Token (JWT), RFC 7519 compliant.
- **Signing Algorithm:** `HS256` (HMAC with SHA-256).
- **Key:** `settings.SECRET_KEY` (minimum 32 bytes).
- **Default Lifespan:** 480 minutes (8 hours) matching standard engineering plant shifts.

## 3. Payload Structure
```json
{
  "sub": "lead_engineer_1",
  "role": "lead_engineer",
  "jti": "8f3b2a14-49c0-4e12-87ad-bc39401f89aa",
  "iat": 1725900000,
  "exp": 1725928800
}
```

## 4. Transmission
Transmitted over HTTP via standard header: `Authorization: Bearer <jwt_token>`. Stored in browser `localStorage` in vanilla UI.
