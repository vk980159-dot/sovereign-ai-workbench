# 01. Local Air-Gapped Runtime Mode
**Status:** [VERIFIED ACTIVE]

- **Network Interfaces:** Binds exclusively to `127.0.0.1:8000` and `127.0.0.1:11434`.
- **Egress Policy:** Zero outbound internet packets.
- **External Auth:** OAuth endpoints fail closed; local bcrypt authentication enforced.
- **Verification:** Verified by test `test_deployment.py:test_airgap_compliance`.
