# 11. Complete End-to-End Agent Flow
**Status:** [VERIFIED]

```
[User Task]
    │
    ▼
[security_gate_node] ──(Passed)──► [planner_node]
                                         │
                                         ▼
                                  [executor_node] ◄──────────────┐
                                         │                       │
                                         ▼                       │ (Retry)
                                  [verifier_node] ──(Failed)─────┘
                                         │ (Passed)
                                         ▼
                                 [synthesizer_node]
                                         │
                                         ▼
                                [Physical Deliverables]
```
