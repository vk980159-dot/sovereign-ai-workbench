"""
Persistent SQLite Task & Event Store (SIH26117).
Provides user-isolated task history, event logging, cancellation tracking,
and artifact association.
"""

import sqlite3
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.config import settings

_db_lock = threading.Lock()


def _get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.TASK_DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_task_db():
    """Initializes tasks and task_events tables if they do not exist."""
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    user_id TEXT,
                    username TEXT,
                    query TEXT NOT NULL,
                    category TEXT,
                    status TEXT NOT NULL,
                    task_plan TEXT,
                    current_step INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    completed_steps TEXT,
                    evidence TEXT,
                    artifacts TEXT,
                    final_report TEXT,
                    confidence REAL DEFAULT 0.0,
                    verdict TEXT DEFAULT 'PENDING',
                    error TEXT,
                    is_cancelled INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS task_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    step INTEGER,
                    tool_name TEXT,
                    details TEXT,
                    status TEXT,
                    FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                )
            """)
            conn.commit()


# Initialize on import
init_task_db()


def create_task(
    task_id: str,
    query: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    session_id: Optional[str] = None,
    category: str = "multi_step_agentic_task"
) -> Dict[str, Any]:
    """Creates a new task in PENDING status."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tasks (
                    task_id, session_id, user_id, username, query, category,
                    status, task_plan, completed_steps, evidence, artifacts,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', '[]', '[]', '[]', '[]', ?)
            """, (task_id, session_id or task_id, user_id, username or "sovereign_operator", query, category, now_iso))
            conn.commit()

    return {
        "task_id": task_id,
        "session_id": session_id or task_id,
        "query": query,
        "status": "PENDING",
        "created_at": now_iso
    }


def update_task(task_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Updates fields of an existing task."""
    allowed_fields = {
        "status", "category", "task_plan", "current_step", "total_steps",
        "completed_steps", "evidence", "artifacts", "final_report",
        "confidence", "verdict", "error", "is_cancelled", "completed_at"
    }
    updates = []
    values = []
    for k, v in kwargs.items():
        if k in allowed_fields:
            updates.append(f"{k} = ?")
            if isinstance(v, (list, dict)):
                values.append(json.dumps(v))
            else:
                values.append(v)

    if not updates:
        return get_task(task_id)

    values.append(task_id)
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?"
            cur.execute(query, tuple(values))
            conn.commit()

    return get_task(task_id)


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves task by ID."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _format_task_row(row)


def list_tasks(
    user_id: Optional[str] = None,
    role: str = "user",
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Lists tasks with strict user isolation unless role is admin."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        if role == "admin" or user_id is None:
            cur.execute("""
                SELECT * FROM tasks
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        else:
            cur.execute("""
                SELECT * FROM tasks
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        return [_format_task_row(r) for r in cur.fetchall()]


def cancel_task(task_id: str) -> bool:
    """Signals task cancellation."""
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE tasks SET is_cancelled = 1, status = 'CANCELLED' WHERE task_id = ?", (task_id,))
            conn.commit()
            return cur.rowcount > 0


def is_cancelled(task_id: str) -> bool:
    """Checks if cancellation was requested for task_id."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_cancelled FROM tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        return bool(row and row["is_cancelled"] == 1)


def log_task_event(
    task_id: str,
    event_type: str,
    message: str,
    step: Optional[int] = None,
    tool_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: Optional[str] = "OK"
) -> Dict[str, Any]:
    """Appends structured task execution event."""
    now_iso = datetime.now(timezone.utc).isoformat()
    det_str = json.dumps(details or {})
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO task_events (
                    task_id, timestamp, event_type, message, step,
                    tool_name, details, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, now_iso, event_type, message, step, tool_name, det_str, status))
            conn.commit()

    return {
        "task_id": task_id,
        "timestamp": now_iso,
        "event_type": event_type,
        "message": message,
        "step": step,
        "tool_name": tool_name,
        "details": details or {},
        "status": status
    }


def get_task_events(task_id: str) -> List[Dict[str, Any]]:
    """Retrieves all event records for a given task."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM task_events WHERE task_id = ? ORDER BY id ASC", (task_id,))
        rows = cur.fetchall()
        events = []
        for r in rows:
            events.append({
                "id": r["id"],
                "task_id": r["task_id"],
                "timestamp": r["timestamp"],
                "event_type": r["event_type"],
                "message": r["message"],
                "step": r["step"],
                "tool_name": r["tool_name"],
                "details": json.loads(r["details"]) if r["details"] else {},
                "status": r["status"]
            })
        return events


def get_task_artifacts(task_id: str) -> List[Dict[str, Any]]:
    """Retrieves artifacts associated with task."""
    task = get_task(task_id)
    if not task:
        return []
    return task.get("artifacts", [])


def _format_task_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "task_id": row["task_id"],
        "session_id": row["session_id"],
        "user_id": row["user_id"],
        "username": row["username"],
        "query": row["query"],
        "category": row["category"],
        "status": row["status"],
        "task_plan": json.loads(row["task_plan"]) if row["task_plan"] else [],
        "current_step": row["current_step"],
        "total_steps": row["total_steps"],
        "completed_steps": json.loads(row["completed_steps"]) if row["completed_steps"] else [],
        "evidence": json.loads(row["evidence"]) if row["evidence"] else [],
        "artifacts": json.loads(row["artifacts"]) if row["artifacts"] else [],
        "final_report": row["final_report"],
        "confidence": row["confidence"],
        "verdict": row["verdict"],
        "error": row["error"],
        "is_cancelled": bool(row["is_cancelled"]),
        "created_at": row["created_at"],
        "completed_at": row["completed_at"]
    }
