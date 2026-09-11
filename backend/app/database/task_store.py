"""
Persistent SQLite Task & Event Store (SIH26117).
Provides user-isolated task history, event logging, cancellation tracking,
and artifact association.
"""

import sqlite3
import json
import uuid
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    file_id TEXT PRIMARY KEY,
                    task_id TEXT,
                    user_id TEXT,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    page_count INTEGER DEFAULT 0,
                    detected_type TEXT NOT NULL,
                    ocr_status TEXT DEFAULT 'NOT_ATTEMPTED',
                    vision_status TEXT DEFAULT 'NOT_ATTEMPTED',
                    processing_status TEXT DEFAULT 'READY',
                    extracted_text_preview TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    verification_status TEXT NOT NULL,
                    verification_details TEXT,
                    created_at TEXT NOT NULL
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


def record_uploaded_file(
    file_id: str,
    filename: str,
    original_filename: str,
    file_path: str,
    sha256: str,
    mime_type: str,
    size_bytes: int,
    detected_type: str,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None,
    page_count: int = 0,
    ocr_status: str = "NOT_ATTEMPTED",
    vision_status: str = "NOT_ATTEMPTED",
    processing_status: str = "READY",
    extracted_text_preview: str = ""
) -> Dict[str, Any]:
    """Stores metadata for an authenticated multimodal file upload."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO uploaded_files (
                    file_id, task_id, user_id, filename, original_filename,
                    file_path, sha256, mime_type, size_bytes, page_count,
                    detected_type, ocr_status, vision_status, processing_status,
                    extracted_text_preview, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, task_id, user_id, filename, original_filename,
                file_path, sha256, mime_type, size_bytes, page_count,
                detected_type, ocr_status, vision_status, processing_status,
                extracted_text_preview[:1000] if extracted_text_preview else "",
                now_iso
            ))
            conn.commit()

    return {
        "file_id": file_id,
        "task_id": task_id,
        "user_id": user_id,
        "filename": filename,
        "original_filename": original_filename,
        "file_path": file_path,
        "sha256": sha256,
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "page_count": page_count,
        "detected_type": detected_type,
        "ocr_status": ocr_status,
        "vision_status": vision_status,
        "processing_status": processing_status,
        "created_at": now_iso
    }


def get_uploaded_file(file_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieves uploaded file record with user isolation."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,))
        row = cur.fetchone()
        if not row:
            return None
        # Enforce user isolation
        if not is_admin and user_id and str(row["user_id"]) != str(user_id):
            return None
        return dict(row)


def list_uploaded_files(
    user_id: Optional[str] = None,
    is_admin: bool = False,
    limit: int = 50,
    offset: int = 0,
    role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists uploaded files with user isolation."""
    if role == "admin":
        is_admin = True

    with _get_db_conn() as conn:
        cur = conn.cursor()
        if is_admin or not user_id:
            cur.execute("SELECT * FROM uploaded_files ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
        else:
            cur.execute("SELECT * FROM uploaded_files WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", (str(user_id), limit, offset))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def record_artifact(
    artifact_id: Optional[str] = None,
    task_id: str = "",
    filename: str = "",
    file_path: str = "",
    artifact_type: str = "document",
    sha256: str = "",
    size_bytes: int = 0,
    verification_status: str = "VERIFIED",
    verification_details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Stores metadata for a generated deliverable artifact."""
    aid = artifact_id or f"art_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    det_str = json.dumps(verification_details or {})
    with _db_lock:
        with _get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO artifacts (
                    artifact_id, task_id, user_id, filename, file_path,
                    artifact_type, sha256, size_bytes, verification_status,
                    verification_details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aid, task_id, user_id, filename, file_path,
                artifact_type, sha256, size_bytes, verification_status,
                det_str, now_iso
            ))
            conn.commit()

    return {
        "artifact_id": aid,
        "task_id": task_id,
        "user_id": user_id,
        "filename": filename,
        "file_path": file_path,
        "artifact_type": artifact_type,
        "sha256": sha256,
        "size_bytes": size_bytes,
        "verification_status": verification_status,
        "verification_details": verification_details or {},
        "created_at": now_iso
    }


register_artifact = record_artifact


def get_artifact_record(filename: str, user_id: Optional[str] = None, is_admin: bool = False) -> Optional[Dict[str, Any]]:
    """Looks up artifact record by filename with user isolation."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM artifacts WHERE filename = ? ORDER BY created_at DESC LIMIT 1", (filename,))
        row = cur.fetchone()
        if not row:
            return None
        # Enforce user isolation
        if not is_admin and user_id and row["user_id"] and str(row["user_id"]) != str(user_id):
            return None
        res = dict(row)
        res["verification_details"] = json.loads(row["verification_details"]) if row["verification_details"] else {}
        return res


def list_task_artifacts(task_id: str) -> List[Dict[str, Any]]:
    """Retrieves all artifact records generated by a specific task."""
    with _get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM artifacts WHERE task_id = ? ORDER BY created_at ASC", (task_id,))
        rows = cur.fetchall()
        results = []
        for r in rows:
            item = dict(r)
            item["verification_details"] = json.loads(r["verification_details"]) if r["verification_details"] else {}
            results.append(item)
        return results

