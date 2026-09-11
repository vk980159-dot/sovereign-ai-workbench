# 04. Role-Based Access Control (RBAC)
**Status:** [VERIFIED]

## 1. File Path & Implementation
`backend/app/security/auth.py`: `require_role(allowed_roles: List[str])`

## 2. Role Definitions
1. **`admin`**: Full administrative privileges; user management, system configuration, all task operations.
2. **`lead_engineer`**: Core operational role; task creation, RAG queries, deliverable downloads, document uploads.
3. **`field_inspector`**: Limited operational role; document uploads, inspection runs, judge demo execution.
4. **`auditor`**: Compliance role; read-only access to audit trail, cryptographic verification endpoint, task history.

## 3. Enforcement Pattern
```python
@router.post("/api/tasks")
async def create_task(
    payload: TaskCreateRequest,
    current_user: User = Depends(require_role(["lead_engineer", "admin"]))
):
    ...
```
Unauthorized requests receive HTTP 403 Forbidden with `{ "detail": "Insufficient permissions for this operation" }`.
