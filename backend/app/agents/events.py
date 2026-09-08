"""
Structured Agent Event Definitions & WebSocket Streaming (SIH26117).
Broadcasts real-time step events to WebSocket clients without exposing private chain-of-thought.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Awaitable

# Standard Event Types
TASK_CREATED = "TASK_CREATED"
SECURITY_CHECK = "SECURITY_CHECK"
PLAN_CREATED = "PLAN_CREATED"
STEP_STARTED = "STEP_STARTED"
TOOL_SELECTED = "TOOL_SELECTED"
TOOL_STARTED = "TOOL_STARTED"
TOOL_COMPLETED = "TOOL_COMPLETED"
KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
DOCUMENT_RETRIEVED = "DOCUMENT_RETRIEVED"
REASONING_COMPLETED = "REASONING_COMPLETED"
VERIFICATION_STARTED = "VERIFICATION_STARTED"
VERIFICATION_PASSED = "VERIFICATION_PASSED"
VERIFICATION_FAILED = "VERIFICATION_FAILED"
REPLAN_STARTED = "REPLAN_STARTED"
STEP_FAILED = "STEP_FAILED"
TASK_COMPLETED = "TASK_COMPLETED"
TASK_FAILED = "TASK_FAILED"

# Multimodal Ingestion Events
FILE_RECEIVED = "FILE_RECEIVED"
FILE_SECURITY_CHECK = "FILE_SECURITY_CHECK"
FILE_HASHED = "FILE_HASHED"
DOCUMENT_TYPE_DETECTED = "DOCUMENT_TYPE_DETECTED"
PDF_ANALYSIS_STARTED = "PDF_ANALYSIS_STARTED"
OCR_STARTED = "OCR_STARTED"
OCR_COMPLETED = "OCR_COMPLETED"
OCR_FAILED = "OCR_FAILED"
VISION_STARTED = "VISION_STARTED"
VISION_COMPLETED = "VISION_COMPLETED"
VISION_UNAVAILABLE = "VISION_UNAVAILABLE"
TABLE_EXTRACTION_STARTED = "TABLE_EXTRACTION_STARTED"
TABLE_EXTRACTION_COMPLETED = "TABLE_EXTRACTION_COMPLETED"
EVIDENCE_CREATED = "EVIDENCE_CREATED"

# Deliverable Generation & Verification Events
ARTIFACT_GENERATION_STARTED = "ARTIFACT_GENERATION_STARTED"
ARTIFACT_GENERATED = "ARTIFACT_GENERATED"
ARTIFACT_VERIFICATION_STARTED = "ARTIFACT_VERIFICATION_STARTED"
ARTIFACT_VERIFICATION_PASSED = "ARTIFACT_VERIFICATION_PASSED"
ARTIFACT_VERIFICATION_FAILED = "ARTIFACT_VERIFICATION_FAILED"

_active_task_callbacks: Dict[str, Callable] = {}


def register_event_callback(identifier: str, callback: Callable):
    """Registers an event callback for a task_id or session_id."""
    _active_task_callbacks[identifier] = callback


def unregister_event_callback(identifier: str):
    """Removes an event callback when a task completes."""
    _active_task_callbacks.pop(identifier, None)


async def emit_agent_event(
    task_id: str,
    event_type: str,
    message: str,
    step: Optional[int] = None,
    tool_name: Optional[str] = None,
    documents: Optional[list] = None,
    status: str = "OK",
    details: Optional[Dict[str, Any]] = None,
    callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs and broadcasts a structured agent telemetry event.
    Logs event into SQLite task store and broadcasts to WebSocket clients.
    """
    from app.database.task_store import log_task_event
    from app.api.ws_manager import ws_manager

    now_iso = datetime.now(timezone.utc).isoformat()
    event_payload = {
        "task_id": task_id,
        "session_id": session_id or task_id,
        "timestamp": now_iso,
        "event_type": event_type,
        "message": message,
        "step": step,
        "tool_name": tool_name,
        "documents": documents or [],
        "status": status,
        "details": details or {}
    }

    # Record event persistently in task store
    try:
        log_task_event(
            task_id=task_id,
            event_type=event_type,
            message=message,
            step=step,
            tool_name=tool_name,
            details=details,
            status=status
        )
    except Exception:
        pass

    # Call direct or registered callback
    active_cb = callback or _active_task_callbacks.get(task_id) or _active_task_callbacks.get(session_id or "")
    if active_cb:
        try:
            res = active_cb(event_payload)
            import inspect
            if inspect.isawaitable(res):
                await res
        except Exception:
            pass

    # Broadcast over WebSocket to connected clients
    target_sid = session_id or task_id
    try:
        # Send structured agent_event
        await ws_manager.broadcast_to_session(target_sid, {
            "type": "agent_event",
            "data": event_payload
        })
        # Send backward-compatible agent_thought
        await ws_manager.broadcast_to_session(target_sid, {
            "type": "agent_thought",
            "data": {
                "timestamp": now_iso,
                "agent": tool_name or event_type,
                "thought": message,
                "step": f"Step {step}" if step else event_type
            }
        })
    except Exception:
        pass

    return event_payload
