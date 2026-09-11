# 08. Code Execution Security (AST Sandboxing)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/tools/calc_tools.py`: `_eval_ast(node)`

## 2. The LLM Math & Code Execution Hazard
Allowing LLMs to execute raw Python code via `eval()` or `exec()` is an existential vulnerability allowing Remote Code Execution (RCE). Conversely, relying on LLMs for raw arithmetic leads to calculation hallucinations.

## 3. Sovereign Solution: Sandboxed AST Recursive Evaluator
The workbench parses calculation expressions into an Abstract Syntax Tree:
- **Allowed Nodes:** `ast.Expression`, `ast.BinOp` (`Add`, `Sub`, `Mult`, `Div`, `Pow`), `ast.UnaryOp` (`USub`, `UAdd`), `ast.Constant`, `ast.Num`.
- **Whitelisted Functions:** Only `abs`, `round`, `min`, `max`, `sqrt`.
- **Strictly Blocked:** All imports, variable assignments, attribute lookups (`node.attr`), built-in execution functions.
Raises `ValueError("Unsupported or unsafe expression")` on any non-mathematical node.
