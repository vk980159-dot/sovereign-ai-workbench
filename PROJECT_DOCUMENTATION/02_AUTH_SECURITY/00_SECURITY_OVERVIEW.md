# 00. Security Architecture & Threat Model Overview
**Status:** [VERIFIED]

## Security Philosophy: Zero Trust Air-Gapped Workbench
The Sovereign AI Workbench treats security as an engineering prerequisite rather than an afterthought. Because it handles confidential industrial metallurgy, plant downtime logs, and executive approval memos, the system enforces multi-layered defense in depth.

## Core Security Controls
1. **Cryptographic Identity:** Salted bcrypt password hashing + HS256 JWT tokens.
2. **Session Revocation:** Server-side `jti` blocklisting in SQLite `auth.db`.
3. **Role-Based Access Control:** Granular role enforcement (`admin`, `lead_engineer`, `field_inspector`, `auditor`).
4. **Prompt & Shell Sanitization:** LangGraph `security_gate` evaluates prompts prior to planning.
5. **Deterministic AST Math Sandbox:** Pure Python AST parsing; blocks `eval()` and `exec()`.
6. **Path Traversal Protection:** Canonical path resolution prevents escape from designated media folders.
7. **PII Masking:** Pre-indexing regex redaction of Aadhaar, PAN, SSN, emails, and phones.
8. **Sliding-Window Rate Limiting:** ASGI middleware preventing DoS resource starvation.
9. **Tamper-Evident Ledger:** Append-only SHA-256 forward hash-chained audit trail.
