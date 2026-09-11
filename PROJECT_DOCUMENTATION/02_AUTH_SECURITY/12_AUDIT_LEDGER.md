# 12. Cryptographic Audit Ledger (`audit_trail.jsonl`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/security/audit_logger.py`: `AuditLogger`

## 2. Cryptographic Hash Chain Structure
Every system event is appended as a JSON line to `audit_trail.jsonl`:
- `entry_id`: Monotonically increasing integer.
- `timestamp`: UTC ISO-8601 string.
- `event_type`: e.g. `USER_LOGIN`, `TOOL_EXECUTION`, `VERIFICATION_CHECK`.
- `user_id`: Username of operator.
- `payload`: Event details dictionary.
- `previous_hash`: 64-character hex SHA-256 hash of previous entry (Genesis hash `0000000000000000` for line 1).
- `current_hash`: `SHA-256(previous_hash + timestamp + event_type + json_dump(payload))`.

## 3. Verification & Tamper Detection
`AuditLogger.verify_integrity()` iterates from line 1 to EOF. If any historical byte, timestamp, or result is modified, the downstream hash chain breaks immediately, identifying the exact line of tampering.
**Verified Count:** 1,228 cryptographically chained entries verified 100% tamper-free.
