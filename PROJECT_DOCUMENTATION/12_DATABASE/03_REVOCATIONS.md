# 03. Revoked Tokens Table (`auth.db:revoked_tokens`)
**Status:** [VERIFIED]

## Schema
- `jti TEXT PRIMARY KEY`: Unique JWT ID string.
- `revoked_at TEXT`: Timestamp when user initiated logout.
- `expires_at TEXT`: Natural token expiration timestamp.
- **Current Verified Count:** 40 revoked tokens.
