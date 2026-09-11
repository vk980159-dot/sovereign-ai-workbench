# 04. API Request & Response Models (`backend/app/api/models.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/api/models.py`

## 2. File Purpose
Defines strictly typed Pydantic v2 data models for API payloads, ensuring request validation and predictable response structures.

## 3. Key Pydantic Models
- `UserLoginRequest`: Fields `username: str`, `password: str`.
- `TokenResponse`: Fields `access_token: str`, `token_type: str`, `role: str`, `expires_in: int`.
- `TaskCreateRequest`: Fields `title: str`, `prompt: str`, `mode: Optional[str]`, `attached_files: List[str]`.
- `TaskStatusResponse`: Fields `task_id: str`, `status: str`, `progress: float`, `artifacts: List[ArtifactMeta]`, `error: Optional[str]`.
- `AuditVerificationResponse`: Fields `verified: bool`, `entries_checked: int`, `tamper_detected: bool`, `first_violation_line: Optional[int]`.
- `HealthStatusResponse`: Fields `status: str`, `runtime_mode: str`, `ollama_connected: bool`, `tesseract_installed: bool`, `chromadb_ready: bool`.
