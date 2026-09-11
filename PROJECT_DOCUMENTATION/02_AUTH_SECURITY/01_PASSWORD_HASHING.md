# 01. Password Hashing Architecture
**Status:** [VERIFIED]

## 1. File Path & Functions
`backend/app/security/auth.py`: `get_password_hash(password)`, `verify_password(plain, hashed)`

## 2. Algorithm & Parameters
- **Algorithm:** `bcrypt` (Blowfish-based key derivation function).
- **Cost Factor / Salt Rounds:** Cost 12 (4,096 iterations).
- **Salt Generation:** 128-bit cryptographically secure random salt automatically generated per password by `passlib`.

## 3. Threat Mitigation
- **Mitigates:** Offline dictionary attacks, rainbow table precomputation, brute force.
- **Timing Attacks:** Mitigated via `bcrypt.checkpw` constant-time memory comparison.

## 4. Database Storage
Stored in `auth.db:users.hashed_password` as a standard 60-character bcrypt hash string (e.g. `$2b$12$...`).
