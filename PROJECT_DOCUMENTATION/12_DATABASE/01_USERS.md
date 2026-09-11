# 01. Users Table (`auth.db:users`)
**Status:** [VERIFIED]

## Schema
- `id TEXT PRIMARY KEY`: Unique user UUID.
- `username TEXT UNIQUE`: Unique login handle.
- `hashed_password TEXT`: 60-character bcrypt salted hash.
- `role TEXT`: RBAC role (`admin`, `lead_engineer`, `field_inspector`, `auditor`).
- `is_active INTEGER`: Boolean active flag (1 = active, 0 = disabled).
- `created_at TEXT`: UTC ISO-8601 creation timestamp.
- **Current Verified Count:** 14 active accounts.
