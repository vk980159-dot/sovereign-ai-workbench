"""
LangGraph StateGraph Assembly & Workflow Execution.
Configures explicit node transitions, fact-checking conditional re-routing,
and in-memory checkpointed state persistence.
"""

import uuid
from typing import AsyncGenerator, Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agents.state import AgentState
from app.agents.nodes import (
    retriever_node,
    analyst_node,
    auditor_node,
    reporter_node
)


def audit_router(state: AgentState) -> str:
    """
    Conditional edge router following Auditor fact-checking.
    If confidence < 0.80 and iteration ceiling has not been reached, re-routes to Analyst.
    Otherwise advances to Reporter.
    """
    confidence = state.get("audit_confidence", 0.0)
    verdict = state.get("audit_verdict", "APPROVED")
    current_iter = state.get("iteration_count", 1)
    max_iters = state.get("max_iterations", settings.MAX_AUDIT_ITERATIONS)

    # Re-route condition: Low confidence and under iteration limit
    if (confidence < settings.MIN_AUDIT_CONFIDENCE or verdict == "REJECTED") and current_iter < max_iters:
        return "analyst"

    return "reporter"


def build_sovereign_agent_graph():
    """
    Constructs and compiles the 4-agent state machine.
    Workflow: Retriever -> Analyst -> Auditor -> (Analyst <loop> OR Reporter) -> END
    """
    workflow = StateGraph(AgentState)

    # 1. Register Agents as Nodes
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("reporter", reporter_node)

    # 2. Define Execution Graph Edges
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "analyst")
    workflow.add_edge("analyst", "auditor")

    # 3. Dynamic Self-Correction Feedback Loop
    workflow.add_conditional_edges(
        "auditor",
        audit_router,
        {
            "analyst": "analyst",
            "reporter": "reporter"
        }
    )

    # 4. Final Termination Edge
    workflow.add_edge("reporter", END)

    # 5. Persistent Checkpointing for Air-Gapped State Recovery
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


# Pre-compiled workflow graph singleton
sovereign_graph = build_sovereign_agent_graph()


async def run_agent_workflow(
    query: str,
    session_id: Optional[str] = None,
    on_thought_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
) -> Dict[str, Any]:
    """
    Executes the multi-agent workflow for a given query.
    Optionally emits real-time agent thoughts to a WebSocket callback.

    Returns:
        Final combined AgentState dictionary.
    """
    sid = session_id or str(uuid.uuid4())

    initial_state: AgentState = {
        "session_id": sid,
        "user_query": query,
        "sanitized_query": "",
        "retrieved_docs": [],
        "retrieval_summary": "",
        "analysis_draft": "",
        "iteration_count": 0,
        "max_iterations": settings.MAX_AUDIT_ITERATIONS,
        "audit_confidence": 0.0,
        "audit_verdict": "PENDING",
        "audit_feedback": "",
        "audit_discrepancies": [],
        "final_report": "",
        "citations": [],
        "action_items": [],
        "current_agent": "Retriever",
        "status": "INITIALIZED",
        "agent_logs": [],
        "error": None
    }

    config = {"configurable": {"thread_id": sid}}
    last_state = initial_state
    emitted_log_count = 0

    # Stream state updates node by node
    async for output in sovereign_graph.astream(initial_state, config=config):
        for node_name, node_output in output.items():
            last_state = {**last_state, **node_output}

            # Emit new logs to callback if attached
            if on_thought_callback and "agent_logs" in node_output:
                current_logs = node_output["agent_logs"]
                # Stream newly added logs
                while emitted_log_count < len(current_logs):
                    await on_thought_callback(current_logs[emitted_log_count])
                    emitted_log_count += 1

    return last_state
