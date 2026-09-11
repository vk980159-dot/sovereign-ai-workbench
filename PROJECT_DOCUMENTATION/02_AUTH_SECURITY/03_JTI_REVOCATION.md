# 03. JTI Token Revocation Architecture
**Status:** [VERIFIED]

## 1. File Path & Functions
`backend/app/security/auth.py`: `revoke_token(token: str)`, `is_token_revoked(jti: str)`

## 2. The Replay Attack Problem
Stateless JWTs normally remain valid until expiration even if an operator logs out or an account is suspended. An attacker intercepting an unexpired token could impersonate the engineer.

## 3. Sovereign Solution: Cryptographic JTI Blocklisting
1. Every issued JWT contains a unique UUID4 in the `jti` (JWT ID) claim.
2. Upon logout (`POST /api/auth/logout`), the server extracts the `jti` and writes it to `auth.db:revoked_tokens` table.
3. Every authenticated request checks `auth.db:revoked_tokens`. If the `jti` is found, the request is rejected with HTTP 401.

## 4. Database Table Schema
`revoked_tokens`: `jti TEXT PRIMARY KEY`, `revoked_at TEXT`, `expires_at TEXT`.
Expired entries are periodically purged to maintain minimal table size.
