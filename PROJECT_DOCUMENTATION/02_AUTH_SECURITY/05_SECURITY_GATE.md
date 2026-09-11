# 05. Security Gate & Prompt Sanitization
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/security_gate.py`: `SecurityGate.evaluate_prompt()`

## 2. Architectural Role
Mandatory first node in the LangGraph state machine. Evaluates raw user prompts before any planning or model reasoning occurs.

## 3. Attack Signatures Detected
- **Prompt Injection:** "ignore previous instructions", "system override", "DAN mode", "disregard safety guidelines".
- **OS Shell Commands:** `rm -rf`, `powershell`, `cmd.exe`, `format c:`, `/bin/sh`, `curl`, `wget`, `nc -e`.
- **Path Traversal:** `../`, `..\`, `/etc/passwd`, `C:\Windows`.

## 4. Evaluation Logic & Fallback
Calculates a heuristic risk score. If `risk_score > 0.3` or any blocked keyword matches:
- Sets `passed = False`.
- Logs `SECURITY_VIOLATION` to `audit_trail.jsonl`.
- Terminates graph execution immediately; returns HTTP 400 Bad Request to user.
