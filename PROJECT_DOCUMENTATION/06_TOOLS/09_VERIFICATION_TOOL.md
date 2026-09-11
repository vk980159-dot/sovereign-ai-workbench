# 09. Tool: `verify_tolerance_limits`
**Status:** [VERIFIED]

- **File:** `backend/app/agents/tools/verify_tools.py`
- **Function:** `verify_tolerance_limits(parameter: str, actual_value: float, max_limit: float, min_limit: Optional[float] = None, unit: str = "")`
- **Purpose:** Evaluates physical measurements against ISO/industrial limits (e.g. vibration 8.42 vs 5.0 mm/s).
- **Output:** Status (`WITHIN_LIMITS`, `CRITICAL_EXCEEDANCE`), percentage variance, mandatory remediation recommendation.
