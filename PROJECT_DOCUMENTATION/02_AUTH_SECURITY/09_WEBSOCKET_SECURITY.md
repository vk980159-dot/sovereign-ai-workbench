# 09. WebSocket Security Architecture
**Status:** [VERIFIED]

## 1. File Path
`backend/app/api/ws_manager.py`: `ConnectionManager`

## 2. Handshake & Authentication
WebSocket connections on `/ws/tasks/{task_id}` authenticate via token query parameter or first-frame handshake payload.

## 3. Channel Isolation
Connections are isolated by `task_id`. Clients only receive telemetry frames belonging to the specific task channel they subscribed to.

## 4. Stale Connection Cleanup
Silent disconnection or client network loss is handled gracefully: stale socket references are dropped during broadcast loops without throwing unhandled exceptions.
