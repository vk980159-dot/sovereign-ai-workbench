# 05. Security Audit & Ledger Inspector UI
**Status:** [VERIFIED]

- **Function:** `verifyAuditChain()` in `frontend/index.html`.
- **Workflow:** Calls `GET /api/audit/verify` -> computes real-time chain verification -> displays green "100% TAMPER-PROOF" badge and ledger statistics (total entries checked).
