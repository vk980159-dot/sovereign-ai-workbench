# 07. Public Share & Rate Limiting Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_public_share.py` (14 tests)
- **Tests Covered:**
  - `test_sliding_window_rate_limiter`: Asserts HTTP 429 after 60 req/min.
  - `test_cloudflare_runner_lifecycle`: Validates tunnel process start/stop.
  - `test_security_response_headers`: Validates X-Frame-Options, CSP.
