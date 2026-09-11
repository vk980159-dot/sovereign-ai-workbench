# 13. Frontend-to-Backend REST & WS Mapping
**Status:** [VERIFIED]

| UI Component | JavaScript Function | Backend Endpoint | Protocol |
|--------------|---------------------|------------------|----------|
| Login Form | `handleLogin()` | `/api/auth/token` | HTTP POST |
| User Badge | `loadUserProfile()`| `/api/auth/me` | HTTP GET |
| Task Input | `submitTask()` | `/api/tasks` | HTTP POST |
| Telemetry Console | `connectWebSocket()`| `/ws/tasks/{id}` | WebSocket |
| Upload Dropzone | `uploadFile()` | `/api/docs/upload` | HTTP POST |
| Artifact Cards | `loadArtifacts()` | `/api/tasks/{id}/artifacts` | HTTP GET |
| Audit Badge | `verifyAuditChain()`| `/api/audit/verify` | HTTP GET |
| Judge Demo Card | `triggerJudgeDemo()`| `/api/judge-demo` | HTTP POST |
