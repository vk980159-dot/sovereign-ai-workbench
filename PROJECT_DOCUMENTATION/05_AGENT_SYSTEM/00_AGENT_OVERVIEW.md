# 00. Agent Architecture Overview
**Status:** [VERIFIED]

## LangGraph State Machine Topology
The agent core is implemented via a compiled **LangGraph** finite-state machine (`StateGraph`).

```
[START] ──► [security_gate] ──► [planner] ──► [executor] ──► [verifier] ──► [synthesizer] ──► [END]
                                                 ▲              │ (Retry Loop)
                                                 └──────────────┘
```
Enforces deterministic state transitions, step-by-step tool execution, and an iterative self-correction loop bounded by a strict guardrail (`MAX_ITERATIONS = 10`).
