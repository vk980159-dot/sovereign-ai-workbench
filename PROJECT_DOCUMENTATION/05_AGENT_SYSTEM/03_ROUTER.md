# 03. Agent Router & Conditional Edges
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/nodes.py`: `should_continue(state: AgentState) -> str`

## 2. Conditional Routing Logic
- If `state["verification_results"][-1].passed == True`: routes to `"synthesizer"`.
- If verification failed AND `state["iteration_count"] < 10`: routes back to `"executor"` with corrective feedback.
- If `state["iteration_count"] >= 10`: terminates loop and routes to `"synthesizer"` with unverified warning flag.
