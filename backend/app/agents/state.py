"""
Agent State Definition for LangGraph State Machine.
Defines strongly typed mutable state passed across all multi-step agentic nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    Unified state schema for Sovereign Multi-Step Agentic Engine (SIH26117).
    Maintains full lifecycle state: planning, tool executions, observations,
    knowledge retrieval, verification, retry tracking, evidence, and audit logs.
    """
    # Core Task & Identity Context
    task_id: str
    session_id: str
    user_id: Optional[str]
    username: Optional[str]
    original_query: str
    user_query: str
    sanitized_query: str
    task_category: str

    # Planning & Dynamic Routing
    task_plan: List[Dict[str, Any]]
    current_step: int
    total_steps: int
    completed_steps: List[Dict[str, Any]]
    failed_steps: List[Dict[str, Any]]
    step_retries: Dict[str, int]

    # Knowledge & Tool Execution
    retrieved_documents: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    retrieval_summary: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    observations: List[Dict[str, Any]]

    # Reasoning & Analysis
    reasoning_summary: str
    analysis_draft: str

    # Verification & Quality Assurance
    verification_results: Dict[str, Any]
    confidence: float
    audit_confidence: float
    audit_verdict: str
    audit_feedback: str
    audit_discrepancies: List[str]

    # Final Synthesis & Generated Artifacts
    deliverable_format: Optional[str]
    final_answer: str
    final_report: str
    evidence: List[Dict[str, Any]]
    citations: List[str]
    action_items: List[str]
    generated_artifacts: List[Dict[str, Any]]

    # Execution Telemetry & Lifecycle
    status: str
    current_agent: str
    agent_logs: List[Dict[str, Any]]
    error: Optional[str]
    iteration_count: int
    max_iterations: int
    started_at: str
    completed_at: Optional[str]
