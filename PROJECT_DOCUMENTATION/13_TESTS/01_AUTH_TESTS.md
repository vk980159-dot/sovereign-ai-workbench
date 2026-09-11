# 01. Authentication & Session Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_auth.py` (8 tests)
- **Tests Covered:**
  - `test_password_hash_verification`: Validates salted bcrypt hashes.
  - `test_jwt_creation_and_validation`: Validates HS256 claims.
  - `test_expired_token_rejected`: Rejects expired JWTs.
  - `test_jti_revocation`: Validates token blocklisting on logout.
  - `test_rbac_role_enforcement`: Asserts HTTP 403 on unauthorized roles.
