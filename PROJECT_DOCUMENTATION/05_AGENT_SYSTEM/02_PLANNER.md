# 02. Task Planner Node (`backend/app/agents/planner.py`)
**Status:** [VERIFIED]

## 1. File Path & Architecture
`backend/app/agents/planner.py`: `TaskPlanner.generate_plan()`

## 2. Planning Logic
- Prompts local LLaMA-3.1 with system instructions defining the 16 registered safe tools and expected JSON schema.
- Emits a list of structured `PlanStep` objects (tool name, arguments, description, verification criteria).
- **Fallback Planner:** If LLM output fails JSON schema validation, triggers `_fallback_heuristic_plan()` to guarantee task continuity without crashing.
