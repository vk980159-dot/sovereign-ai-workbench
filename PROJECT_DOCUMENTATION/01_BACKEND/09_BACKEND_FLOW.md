# 09. Complete Backend Execution Flow
**Status:** [VERIFIED]

## Step-by-Step Server Request Lifecycle

```
1. Client sends HTTP request (e.g. POST /api/tasks)
   ├── RateLimiter middleware checks client IP sliding window (allowed if < 60 req/min)
   └── CORS middleware verifies Host header

2. Route Handler Dependency Resolution:
   ├── Extracts Bearer JWT token from Authorization header
   ├── get_current_user() validates signature and checks revoked_tokens table in auth.db
   └── require_role() confirms user has 'lead_engineer' or 'admin' role

3. Task Initialization:
   ├── task_store.create_task() inserts record with status 'QUEUED' into tasks.db
   └── Returns immediate HTTP 202 Accepted with task_id to client

4. Asynchronous Background Execution:
   ├── FastAPI BackgroundTasks spawns run_agent_task(task_id, prompt)
   ├── LangGraph StateGraph executes: security_gate -> planner -> executor -> verifier -> synthesizer
   └── During execution, ws_manager.broadcast_event() pushes live telemetry over WebSockets

5. Task Completion:
   ├── Artifact generators write files to generated_artifacts/
   ├── DeliverableValidator confirms structural OpenXML / magic byte integrity
   ├── AuditLogger appends event to audit_trail.jsonl with forward SHA-256 hash
   └── task_store.update_task_status() marks task 'COMPLETED' in tasks.db
```
