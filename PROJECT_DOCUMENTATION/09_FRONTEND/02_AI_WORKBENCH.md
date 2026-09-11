# 02. AI Workbench Task Console
**Status:** [VERIFIED]

- **Function:** `submitTask()` in `frontend/index.html`.
- **Workflow:** User enters task prompt -> attaches staged files -> submits to `POST /api/tasks` -> receives `task_id` -> initiates WebSocket listener -> displays live execution logs.
