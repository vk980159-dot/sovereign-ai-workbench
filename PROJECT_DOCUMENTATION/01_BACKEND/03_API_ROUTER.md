# 03. REST API Router (`backend/app/api/router.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/api/router.py`

## 2. File Purpose
Declares all RESTful endpoints consumed by the frontend dashboard and external clients.

## 3. Exposed Endpoints Summary
| Method | Endpoint | Purpose | Role Required |
|--------|----------|---------|---------------|
| `POST` | `/api/auth/token` | Authenticates username/password, issues JWT | Public |
| `POST` | `/api/auth/logout` | Revokes current JWT by adding `jti` to blocklist | Authenticated |
| `GET`  | `/api/auth/me` | Returns active user profile and RBAC role | Authenticated |
| `POST` | `/api/tasks` | Creates task and launches async LangGraph workflow | `lead_engineer`, `admin` |
| `GET`  | `/api/tasks/{id}`| Retrieves task progress, status, and artifact URLs | Authenticated |
| `POST` | `/api/docs/upload` | Validates, hashes, redacts, and stages files | `lead_engineer`, `admin` |
| `GET`  | `/api/audit/verify`| Re-hashes all entries in `audit_trail.jsonl` | `auditor`, `admin` |
| `POST` | `/api/judge-demo` | 1-Click trigger for end-to-end turbine scenario | Authenticated |
| `GET`  | `/api/health` | Comprehensive system diagnostic and model status | Public |

## 4. Security Implementation
Enforces role-based dependencies via `Depends(require_role([...]))`. Wraps task execution in background threads to avoid blocking HTTP workers.
