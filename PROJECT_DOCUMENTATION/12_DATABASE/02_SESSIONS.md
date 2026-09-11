# 02. Session Management & Tokens
**Status:** [VERIFIED]

- **Session Type:** Stateless signed JWT (HS256).
- **Session Duration:** 480 minutes (8 hours).
- **Revocation Enforcement:** Queried against `revoked_tokens` table on every request.
