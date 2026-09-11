# 09. Agent Memory & Context Window Management
**Status:** [VERIFIED]

## Memory Architecture
- **In-Task Short Term Memory:** Maintained in `AgentState["observations"]` throughout graph traversal.
- **Long Term Persistent Memory:** Stored in SQLite `tasks.db` (task events) and ChromaDB (indexed knowledge).
- **Context Management:** High-resolution images are resized (max 1024x1024); document texts are segmented to prevent context overflow.
