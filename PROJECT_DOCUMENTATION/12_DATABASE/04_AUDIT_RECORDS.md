# 04. Audit Trail Records (`audit_trail.jsonl`)
**Status:** [VERIFIED]

## Schema
- `entry_id INTEGER`: Incremental entry index.
- `timestamp TEXT`: UTC ISO-8601 string.
- `event_type TEXT`: Action classification.
- `user_id TEXT`: Operator username.
- `payload TEXT`: JSON serialized event data.
- `previous_hash TEXT`: 64-character SHA-256 predecessor hash.
- `current_hash TEXT`: 64-character SHA-256 block hash.
- **Current Verified Count:** 1,228 cryptographically chained entries from genesis hash.
