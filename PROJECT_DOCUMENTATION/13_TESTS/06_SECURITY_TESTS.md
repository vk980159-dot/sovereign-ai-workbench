# 06. Security & Hardening Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_runtime_hardening.py` (13 tests)
- **Tests Covered:**
  - `test_security_gate_prompt_injection`: Blocks jailbreak phrases.
  - `test_security_gate_shell_injection`: Blocks `rm -rf`, `powershell`, `cmd.exe`.
  - `test_path_traversal_blocking`: Blocks `../../Windows` file operations.
  - `test_audit_ledger_tamper_detection`: Re-hashes ledger and detects spoofed lines.
