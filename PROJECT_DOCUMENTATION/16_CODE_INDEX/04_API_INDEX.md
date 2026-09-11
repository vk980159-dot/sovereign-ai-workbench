# 04. Master REST & WebSocket API Index
**Status:** [VERIFIED]

| HTTP Method | Path | Function | Auth Required | RBAC Role | Purpose |
|-------------|------|----------|---------------|-----------|---------|
| `POST` | `/api/auth/token` | `login_for_access_token` | None | Public | Issues JWT bearer token |
| `POST` | `/api/auth/logout` | `logout_user` | Yes | Authenticated | Revokes current JWT `jti` |
| `GET` | `/api/auth/me` | `get_current_user_profile`| Yes | Authenticated | Returns user profile & role |
| `POST` | `/api/auth/register` | `register_user` | None | Public | Creates new local user account |
| `POST` | `/api/tasks` | `create_task` | Yes | `lead_engineer`, `admin` | Queues and starts agent task |
| `GET` | `/api/tasks/{task_id}` | `get_task_status` | Yes | Authenticated | Returns progress, status, artifacts |
| `POST` | `/api/docs/upload` | `upload_document` | Yes | `lead_engineer`, `admin` | Ingests, hashes, stages files |
| `GET` | `/api/docs` | `list_documents` | Yes | Authenticated | Lists indexed documents |
| `GET` | `/api/audit/verify` | `verify_audit_trail` | Yes | `auditor`, `admin` | Re-computes full hash chain |
| `POST` | `/api/judge-demo` | `trigger_judge_demo` | Yes | Authenticated | 1-Click end-to-end turbine demo |
| `GET` | `/api/health` | `get_health_status` | None | Public | Reports subsystem diagnostics |
| `GET` | `/artifacts/{filename}` | `download_artifact` | Yes | Authenticated | Serves generated deliverables |
| `WS` | `/ws/tasks/{task_id}` | `task_telemetry_ws` | Optional Token | Authenticated | Streams real-time JSON logs |
