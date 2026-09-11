# 08. Judge Demo End-to-End Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_judge_demo.py` (4 tests)
- **Tests Covered:**
  - `test_judge_demo_endpoint_trigger`: Validates `POST /api/judge-demo`.
  - `test_judge_demo_websocket_telemetry`: Confirms event streaming.
  - `test_judge_demo_deliverable_generation`: Asserts DOCX/XLSX generation.
