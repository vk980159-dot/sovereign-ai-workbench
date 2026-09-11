# 09. Deployment & Airgap Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_deployment.py` (6 tests)
- **Tests Covered:**
  - `test_self_hosted_config`: Validates local directory initialization.
  - `test_airgap_compliance`: Asserts zero outbound external HTTP calls.
  - `test_file_permission_boundaries`: Asserts sandboxed directory isolation.
