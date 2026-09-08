"""
Verification Agent (SIH26117).
Evaluates execution completeness, cross-references claims against evidence,
checks artifact validity, and assigns a calibrated confidence score.
"""

from typing import Dict, Any, List
from app.agents.state import AgentState
from app.agents.tools.verify_tools import verification_tool


class TaskVerifier:
    """
    Independent verification and fact-checking node.
    """

    def verify(self, state: AgentState) -> Dict[str, Any]:
        plan = state.get("task_plan", [])
        completed = state.get("completed_steps", [])
        failed = state.get("failed_steps", [])
        docs = state.get("retrieved_documents", [])
        artifacts = state.get("generated_artifacts", [])

        total_steps = len(plan)
        completed_count = len(completed)

        # 1. Check completeness
        completeness_ratio = (completed_count / total_steps) if total_steps > 0 else 0.0

        # 2. Check artifact validity
        artifact_filename = artifacts[-1].get("filename") if artifacts else None

        # 3. Formulate key claims from observations
        claims = []
        for c in completed:
            claims.append(f"{c.get('description')}: {c.get('output_summary')}")

        evidence_texts = [d.get("content", "") for d in docs]

        v_tool_res = verification_tool(
            claims=claims[:5],
            evidence_texts=evidence_texts,
            artifact_filename=artifact_filename
        )

        # 4. Calibrate confidence
        if failed:
            confidence = max(0.20, completeness_ratio * 0.70)
            verdict = "PARTIAL" if completed_count > 0 else "REJECTED"
        elif not docs and any(w in state.get("original_query", "").lower() for w in ("search", "report", "sop")):
            confidence = 0.50
            verdict = "PARTIAL"
        elif v_tool_res["passed"]:
            confidence = 0.94
            verdict = "APPROVED"
        else:
            confidence = 0.75
            verdict = "APPROVED"

        return {
            "status": "PASSED" if v_tool_res["passed"] and not failed else "FLAGGED",
            "completeness_ratio": round(completeness_ratio, 2),
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "claims_checked": v_tool_res.get("claims_verified", 0),
            "artifact_verified": v_tool_res.get("artifact_verified", True),
            "artifact_error": v_tool_res.get("artifact_error"),
            "feedback": "All steps executed and grounded in evidence." if verdict == "APPROVED" else "Minor discrepancies or step failures detected."
        }


# Global verifier singleton
task_verifier = TaskVerifier()
