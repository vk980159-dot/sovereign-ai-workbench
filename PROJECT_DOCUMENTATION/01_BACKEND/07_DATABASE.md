# 07. Database Layer (`backend/app/database/task_store.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/database/task_store.py`

## 2. File Purpose
SQLite data access object managing tasks, execution events, uploaded files, and generated deliverables.

## 3. Database Schema (`tasks.db`)
- `tasks`: `id TEXT PRIMARY KEY`, `title TEXT`, `prompt TEXT`, `status TEXT`, `user_id TEXT`, `mode TEXT`, `created_at TEXT`, `completed_at TEXT`, `error TEXT`.
- `task_events`: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `task_id TEXT`, `event_type TEXT`, `payload TEXT`, `timestamp TEXT`.
- `uploaded_files`: `id TEXT PRIMARY KEY`, `original_name TEXT`, `stored_path TEXT`, `file_type TEXT`, `size_bytes INTEGER`, `sha256 TEXT`, `uploaded_at TEXT`.
- `artifacts`: `id TEXT PRIMARY KEY`, `task_id TEXT`, `file_path TEXT`, `artifact_type TEXT`, `size_bytes INTEGER`, `sha256 TEXT`, `created_at TEXT`.

## 4. Security Implementation
Uses parameterized SQL queries (`cursor.execute(sql, (param1, param2))`) exclusively; 100% immune to SQL injection.
