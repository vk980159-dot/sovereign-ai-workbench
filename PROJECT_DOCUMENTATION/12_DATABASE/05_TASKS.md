# 05. Tasks Table (`tasks.db:tasks`)
**Status:** [VERIFIED]

## Schema
- `id TEXT PRIMARY KEY`: Task UUID.
- `title TEXT`: Short task heading.
- `prompt TEXT`: Raw industrial user prompt.
- `status TEXT`: `QUEUED` | `RUNNING` | `COMPLETED` | `FAILED` | `CANCELLED`.
- `user_id TEXT`: Creator identifier.
- `mode TEXT`: Execution mode (`STANDARD` | `JUDGE_DEMO`).
- `created_at TEXT`, `completed_at TEXT`, `error TEXT`.
- **Current Verified Count:** 111 task records.
