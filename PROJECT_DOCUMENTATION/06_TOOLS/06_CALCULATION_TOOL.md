# 06. Tool: `calculate_expression`
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/calc_tools.py`
- **Function:** `calculate_expression(expression: str)`
- **Purpose:** Evaluates mathematical expressions deterministically without using `eval()`.
- **Security:** Sandboxed AST evaluator allowing only binary operators and whitelisted math functions (`sqrt`, `abs`, `round`).
- **Real-World Value:** Guarantees zero arithmetic hallucination when calculating engineering deviations.
