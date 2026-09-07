"""
Agent State Definition for LangGraph State Machine.
Defines typed immutable/mutable state passed across all multi-agent nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    Unified state schema for Sovereign Multi-Agent Workflow.
    Preserves audit trails, intermediate thoughts, iterative corrections, and source citations.
    """
    # Core Request Context
    session_id: str
    user_query: str
    sanitized_query: str

    # Node 1: Retriever Outputs
    retrieved_docs: List[Dict[str, Any]]
    retrieval_summary: str

    # Node 2: Analyst Outputs
    analysis_draft: str
    iteration_count: int
    max_iterations: int

    # Node 3: Auditor Outputs
    audit_confidence: float
    audit_verdict: str
    audit_feedback: str
    audit_discrepancies: List[str]

    # Node 4: Reporter Outputs
    final_report: str
    citations: List[str]
    action_items: List[str]

    # System Status & Live Streamed Telemetry
    current_agent: str
    status: str
    agent_logs: List[Dict[str, Any]]
    error: Optional[str]
