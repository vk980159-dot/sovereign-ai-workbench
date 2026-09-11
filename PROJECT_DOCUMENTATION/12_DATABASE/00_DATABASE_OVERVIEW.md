# 00. Database Architecture Overview
**Status:** [VERIFIED]

## Multi-Database Persistence Model
The workbench separates authentication, operational telemetry, vector embeddings, and compliance logging across 4 dedicated persistence systems:
1. `auth.db` (SQLite): Users, bcrypt hashes, JWT revocations, OAuth accounts.
2. `tasks.db` (SQLite): Tasks, event logs, file uploads, artifact metadata.
3. `chroma_db/` (ChromaDB): Persistent dense vector store for RAG.
4. `audit_trail.jsonl` (JSONL): Immutable cryptographic SHA-256 hash-chained ledger.
