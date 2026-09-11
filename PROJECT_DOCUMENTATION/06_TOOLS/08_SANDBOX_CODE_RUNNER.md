# 08. Tool: Sandbox Code Execution
**Status:** [VERIFIED RESTRICTED]

- **File:** `backend/app/agents/tools/calc_tools.py`
- **Architectural Policy:** In high-consequence industrial software, running unconstrained arbitrary Python code or shell scripts from an LLM is an unacceptable vulnerability.
- **Implementation:** Code execution is strictly restricted to deterministic AST mathematical evaluation and unit conversions. Arbitrary shell execution is blocked.
