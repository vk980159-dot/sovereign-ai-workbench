# 10. Agent Security Perimeter
**Status:** [VERIFIED]

## Multi-Layered Agent Defenses
1. `security_gate` evaluates prompt before LangGraph planning.
2. Tools whitelisted strictly in `TOOL_REGISTRY` (arbitrary method calls impossible).
3. Sandboxed AST parser for math expressions (no `eval()` or OS shell).
4. Path sandbox restricting file reads/writes to `multimodal_uploads/`, `demo_data/`, `generated_artifacts/`.
