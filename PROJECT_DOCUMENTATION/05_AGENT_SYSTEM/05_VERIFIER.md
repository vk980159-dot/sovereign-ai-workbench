# 05. Verifier Node (`backend/app/agents/verifier.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/verifier.py`: `OutputVerifier.verify_state()`

## 2. Verification Rules
- Audits numerical values against retrieved engineering thresholds (e.g. 8.42 mm/s vs 5.0 mm/s limit).
- Cross-references factual claims against source document excerpts.
- If violation detected: generates actionable remediation guidance and triggers retry loop.
