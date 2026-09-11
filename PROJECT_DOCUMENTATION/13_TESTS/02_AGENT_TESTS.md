# 02. Agent Engine & LangGraph Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_agent_engine.py` (11 tests)
- **Tests Covered:**
  - `test_state_graph_compilation`: Validates LangGraph nodes & edges.
  - `test_planner_node_json_schema`: Validates emitted plan structure.
  - `test_executor_tool_dispatch`: Validates tool observation capture.
  - `test_verifier_retry_loop`: Asserts retry transition on tolerance failure.
  - `test_ast_math_sandboxing`: Confirms arithmetic succeeds and `eval()` blocked.
