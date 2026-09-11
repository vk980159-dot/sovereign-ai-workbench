# 12. WebSocket Real-Time Console UI
**Status:** [VERIFIED]

- **Function:** `connectWebSocket(taskId)` in `frontend/index.html`.
- **Event Handling:** Listens on `ws://127.0.0.1:8000/ws/tasks/{taskId}`. Dynamically parses JSON frames and appends color-coded logs:
  - `[SECURITY]` (Green / Red)
  - `[PLAN]` (Blue)
  - `[TOOL]` (Yellow)
  - `[VERIFY]` (Cyan)
  - `[ARTIFACT]` (Magenta)
