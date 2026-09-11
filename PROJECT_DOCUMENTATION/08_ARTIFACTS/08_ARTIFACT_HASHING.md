# 08. Cryptographic Artifact Checksums
**Status:** [VERIFIED]

- **Mechanism:** Immediately upon successful validation, `DeliverableValidator` computes the SHA-256 hash of the deliverable file.
- **Ledger Binding:** Hash is committed to `tasks.db:artifacts` table and appended to `audit_trail.jsonl`, establishing an immutable chain of custody.
