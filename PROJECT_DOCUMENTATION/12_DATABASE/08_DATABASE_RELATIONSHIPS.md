# 08. Entity Relationship Diagram
**Status:** [VERIFIED]

```
[auth.db: users]
       │
       ├──(1:N)──► [auth.db: linked_accounts] (OAuth providers)
       │
       └──(1:N)──► [tasks.db: tasks]
                         │
                         ├──(1:N)──► [tasks.db: task_events] (WebSocket logs)
                         │
                         └──(1:N)──► [tasks.db: artifacts] (Deliverables)

[auth.db: revoked_tokens] (Independent Blocklist)
[audit_trail.jsonl]       (Independent Cryptographic Forward Hash Chain)
[chroma_db/]              (Independent Vector Index with Document Metadata)
```
