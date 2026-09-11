# 08. Agent Iteration & Self-Correction Loop
**Status:** [VERIFIED]

## Loop Mechanics
When the Verifier node detects a parameter out of tolerance or an ungrounded claim:
1. Generates corrective guidance (e.g. "Vibration exceeds ISO-10816 Limit. Mandate emergency shutdown in recommendations.").
2. Increments `iteration_count`.
3. Re-routes execution to the Executor to run corrective tools.
4. Bounded by `MAX_ITERATIONS = 10` to guarantee termination.
