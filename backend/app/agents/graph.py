"""
LangGraph Multi-Step Agentic StateGraph (SIH26117).
Orchestrates: Security Gate -> Task Planner -> Execution Loop -> Verification -> Synthesizer.
Provides full lifecycle persistence and backward compatibility.
"""

import uuid
from typing import Dict, Any, Callable, Optional, Awaitable
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agents.state import AgentState
from app.agents.nodes import (
    security_gate_node,
    planner_node,
    execution_node,
    verifier_node,
    synthesizer_node
)
from app.agents.events import (
    emit_agent_event,
    register_event_callback,
    unregister_event_callback,
    TASK_CREATED,
    TASK_COMPLETED,
    TASK_FAILED
)
from app.database.task_store import (
    create_task,
    update_task,
    get_task
)
from app.security.audit_logger import audit_logger


def verification_router(state: AgentState) -> str:
    """Routes to synthesizer upon verification."""
    # In this multi-step architecture, executor handles inner bounded tool retries.
    # The verifier assigns confidence and verdict, and routes to synthesizer.
    return "synthesizer"


def build_agentic_workflow():
    """Compiles the sovereign agentic state machine."""
    workflow = StateGraph(AgentState)

    workflow.add_node("security_gate", security_gate_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", execution_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("security_gate")
    workflow.add_edge("security_gate", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "verifier")
    workflow.add_conditional_edges("verifier", verification_router, {"synthesizer": "synthesizer"})
    workflow.add_edge("synthesizer", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


sovereign_agent_graph = build_agentic_workflow()
build_sovereign_agent_graph = build_agentic_workflow


async def run_agentic_task(
    query: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    ws_emitter: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Main entry point to execute an authentic multi-step agentic task.
    Integrates with SQLite task persistence, SHA-256 audit ledger, and WebSocket events.
    """
    tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
    sid = session_id or tid
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Initialize in task store
    create_task(
        task_id=tid,
        query=query,
        user_id=user_id,
        username=username,
        session_id=sid
    )

    # 2. Emit TASK_CREATED
    await emit_agent_event(
        task_id=tid,
        event_type=TASK_CREATED,
        message=f"Agentic task '{tid}' initialized for query: '{query[:80]}'",
        status="PENDING",
        callback=ws_emitter
    )

    # 3. Log genesis in audit ledger
    audit_logger.log_event(
        event_type="TASK_CREATED",
        agent_name="Orchestrator",
        action="INIT_TASK",
        details={"task_id": tid, "session_id": sid, "user": username or "anonymous"},
        input_data=query[:150],
        output_data="PENDING"
    )

    # 4. Construct initial state
    initial_state: AgentState = {
        "task_id": tid,
        "session_id": sid,
        "user_id": user_id,
        "username": username,
        "original_query": query,
        "user_query": query,
        "sanitized_query": query,
        "task_category": "multi_step_agentic_task",
        "task_plan": [],
        "current_step": 0,
        "total_steps": 0,
        "completed_steps": [],
        "failed_steps": [],
        "step_retries": {},
        "retrieved_documents": [],
        "retrieved_docs": [],
        "retrieval_summary": "",
        "tool_calls": [],
        "tool_results": [],
        "observations": [],
        "reasoning_summary": "",
        "analysis_draft": "",
        "verification_results": {},
        "confidence": 0.0,
        "audit_confidence": 0.0,
        "audit_verdict": "PENDING",
        "audit_feedback": "",
        "audit_discrepancies": [],
        "final_answer": "",
        "final_report": "",
        "evidence": [],
        "citations": [],
        "action_items": [],
        "generated_artifacts": [],
        "status": "INITIALIZED",
        "current_agent": "SecurityGate",
        "agent_logs": [],
        "error": None,
        "iteration_count": 0,
        "max_iterations": settings.MAX_AUDIT_ITERATIONS,
        "started_at": now_iso,
        "completed_at": None
    }

    config = {"configurable": {"thread_id": tid}}
    final_state = initial_state

    # 5. Stream LangGraph execution
    if ws_emitter:
        register_event_callback(tid, ws_emitter)
        register_event_callback(sid, ws_emitter)

    try:
        async for output in sovereign_agent_graph.astream(initial_state, config=config):
            for node_name, node_output in output.items():
                final_state = {**final_state, **node_output}
    finally:
        if ws_emitter:
            unregister_event_callback(tid)
            unregister_event_callback(sid)

    # 6. Update task store with completed state
    update_task(
        task_id=tid,
        status=final_state.get("status", "COMPLETED"),
        task_plan=final_state.get("task_plan", []),
        completed_steps=final_state.get("completed_steps", []),
        evidence=final_state.get("retrieved_documents", []),
        artifacts=final_state.get("generated_artifacts", []),
        final_report=final_state.get("final_answer", ""),
        confidence=final_state.get("confidence", 0.0),
        verdict=final_state.get("audit_verdict", "APPROVED"),
        error=final_state.get("error"),
        completed_at=datetime.now(timezone.utc).isoformat()
    )

    # 7. Emit terminal event
    evt_type = TASK_COMPLETED if final_state.get("status") == "COMPLETED" else TASK_FAILED
    await emit_agent_event(
        task_id=tid,
        event_type=evt_type,
        message=f"Agentic task '{tid}' reached state: {final_state.get('status')}",
        status=final_state.get("status"),
        details={"confidence": final_state.get("confidence"), "verdict": final_state.get("audit_verdict")},
        callback=ws_emitter
    )

    return final_state


async def run_agent_workflow(
    query: str,
    session_id: Optional[str] = None,
    on_thought_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for existing endpoints and tests.
    """
    async def adapter_callback(event_dict: Dict[str, Any]):
        if on_thought_callback:
            # Convert to legacy thought format
            legacy_thought = {
                "timestamp": event_dict.get("timestamp"),
                "agent": event_dict.get("event_type", "Agent"),
                "thought": event_dict.get("message", ""),
                "step": event_dict.get("event_type", "EXECUTION")
            }
            res = on_thought_callback(legacy_thought)
            import inspect
            if inspect.isawaitable(res):
                await res

    return await run_agentic_task(
        query=query,
        session_id=session_id,
        ws_emitter=adapter_callback
    )
