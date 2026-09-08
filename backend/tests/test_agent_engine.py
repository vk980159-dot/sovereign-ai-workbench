"""
Comprehensive Automated Test Suite for Sovereign Agentic Engine (SIH26117).
Covers all 16 core test specifications:
1. Simple question
2. Multi-step planning
3. Knowledge retrieval
4. Missing document
5. Tool permission denial
6. Successful tool execution
7. Tool timeout
8. Verification failure
9. Retry / re-plan
10. Task cancellation
11. WebSocket events
12. Audit event creation
13. Task history isolation by user
14. Admin access
15. Ollama unavailable behavior
16. Sovereign/offline network restriction
"""

import unittest
import asyncio
import os
import json
import uuid
import tempfile
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings, BASE_DIR
from app.agents.state import AgentState
from app.agents.security_gate import security_gate
from app.agents.model_provider import OllamaModelProvider, get_model_provider
from app.agents.tools.base import default_tool_registry, ToolDefinition, ToolResult
from app.agents.tools.doc_tools import local_document_search, local_document_reader, file_metadata
from app.agents.tools.calc_tools import calculation_tool
from app.agents.tools.artifact_tools import output_writer
from app.agents.tools.sandbox_tools import sandbox_code_runner
from app.agents.tools.verify_tools import verification_tool
from app.agents.planner import task_planner
from app.agents.executor import task_executor
from app.agents.verifier import task_verifier
from app.agents.events import emit_agent_event, register_event_callback, unregister_event_callback
from app.agents.graph import run_agentic_task, run_agent_workflow
from app.database.task_store import (
    create_task,
    get_task,
    list_tasks,
    cancel_task,
    is_cancelled,
    get_task_events,
    get_task_artifacts
)
from app.security.auth import create_session_token
from app.security.audit_logger import audit_logger


class TestAgentEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Mock expensive LLM generation in planner for instantaneous offline testing
        from unittest.mock import patch
        from app.agents.model_provider import ModelProvider

        class MockTestProvider(ModelProvider):
            async def is_available(self):
                return True
            async def generate(self, prompt, system=None, json_mode=False, temperature=0.1):
                return json.dumps({
                    "plan": [
                        {"step_number": 1, "description": "Locate and read report", "tool_name": "local_document_reader", "tool_input": {"filename": "sample_industrial_inspection_report.txt"}, "status": "PENDING"},
                        {"step_number": 2, "description": "Search safety SOP", "tool_name": "local_document_search", "tool_input": {"query": "hydraulic pressure SOP", "top_k": 2}, "status": "PENDING"},
                        {"step_number": 3, "description": "Calculate variance", "tool_name": "calculation_tool", "tool_input": {"expression": "180 - 142.5"}, "status": "PENDING"},
                        {"step_number": 4, "description": "Verify recommendations", "tool_name": "verification_tool", "tool_input": {}, "status": "PENDING"}
                    ]
                })
            def get_model_info(self):
                return {"provider": "MockTestProvider", "model": "test-mock"}

        cls.planner_patcher = patch("app.agents.planner.get_model_provider", return_value=MockTestProvider())
        cls.planner_patcher.start()

        # Create test users tokens
        cls.user_a_token = create_session_token({
            "username": "agent_user_a",
            "role": "user",
            "id": 101,
            "email": "user_a@sovereign.local"
        })
        cls.user_b_token = create_session_token({
            "username": "agent_user_b",
            "role": "user",
            "id": 102,
            "email": "user_b@sovereign.local"
        })
        cls.admin_token = create_session_token({
            "username": "agent_admin",
            "role": "admin",
            "id": 1,
            "email": "admin@sovereign.local"
        })

    @classmethod
    def tearDownClass(cls):
        cls.planner_patcher.stop()

    # 1. Simple Question Execution
    def test_01_simple_question(self):
        query = "What is the function of the sovereign security gate?"
        res = asyncio.run(run_agentic_task(
            query=query,
            user_id="101",
            username="agent_user_a"
        ))
        self.assertIn("STATUS:", res.get("final_answer", ""))
        self.assertIn("EVIDENCE:", res.get("final_answer", ""))
        self.assertEqual(res.get("status"), "COMPLETED")

    # 2. Multi-Step Planning
    def test_02_multi_step_planning(self):
        query = "Inspect turbine report, compare findings against safety SOP, and prepare recommendation"
        cat, plan = asyncio.run(task_planner.create_plan(query))
        self.assertEqual(cat, "document_analysis")
        self.assertGreaterEqual(len(plan), 3)
        tool_names = [s["tool_name"] for s in plan]
        self.assertIn("local_document_reader", tool_names)
        self.assertIn("local_document_search", tool_names)

    # 3. Knowledge Retrieval
    def test_03_knowledge_retrieval(self):
        res = local_document_search("hydraulic pressure operating thresholds", top_k=2)
        self.assertIn("documents", res)
        self.assertIn("count", res)

    # 4. Missing Document Handling
    def test_04_missing_document(self):
        res = local_document_reader("non_existent_confidential_file_999.txt")
        self.assertFalse(res["found"])
        self.assertIn("not found", res["error"].lower())

    # 5. Tool Permission Denial
    def test_05_tool_permission_denial(self):
        admin_tool = ToolDefinition(
            name="test_admin_restricted_tool",
            description="Restricted admin maintenance",
            input_schema={},
            output_schema={},
            permission_level="admin",
            risk_level="high",
            handler=lambda: "done"
        )
        default_tool_registry.register_tool(admin_tool)

        # Non-admin execution
        res_user = asyncio.run(default_tool_registry.execute_tool(
            name="test_admin_restricted_tool",
            inputs={},
            user_role="user"
        ))
        self.assertFalse(res_user.success)
        self.assertIn("Administrative privileges required", res_user.error)

        # Admin execution
        res_admin = asyncio.run(default_tool_registry.execute_tool(
            name="test_admin_restricted_tool",
            inputs={},
            user_role="admin"
        ))
        self.assertTrue(res_admin.success)

    # 6. Successful Tool Execution
    def test_06_successful_tool_execution(self):
        # A. Calculation Tool
        calc_res = calculation_tool("180.0 - 142.5")
        self.assertEqual(calc_res["result"], 37.5)
        self.assertEqual(calc_res["status"], "SUCCESS")

        # B. Output Writer
        art_res = output_writer("unit_test_artifact.md", "# Test Artifact Content")
        self.assertEqual(art_res["status"], "CREATED")
        self.assertTrue(os.path.isfile(art_res["filepath"]))
        self.assertGreater(art_res["size_bytes"], 0)

        # C. Verification Tool
        v_res = verification_tool(
            claims=["hydraulic pressure drop of 37.5 Bar"],
            evidence_texts=["Observed hydraulic pressure drop of 37.5 Bar below nominal threshold"],
            artifact_filename="unit_test_artifact.md"
        )
        self.assertTrue(v_res["passed"])

    # 7. Tool Timeout Handling
    def test_07_tool_timeout(self):
        # Code with infinite loop
        inf_code = "import time\nwhile True:\n    time.sleep(0.1)"
        res = sandbox_code_runner(code=inf_code, language="python", timeout_seconds=1.0)
        self.assertFalse(res["success"])
        self.assertTrue(res["timeout"])
        self.assertIn("timed out", res["stderr"].lower())

    # 8. Verification Failure Detection
    def test_08_verification_failure(self):
        v_res = verification_tool(
            claims=["Alien spacecraft landed at reactor cooling pump 4B"],
            evidence_texts=["Hydraulic pump operating pressure was 142.5 Bar"],
            artifact_filename="non_existent_file.md"
        )
        self.assertFalse(v_res["passed"])
        self.assertFalse(v_res["artifact_verified"])

    # 9. Retry / Re-Plan Mechanism
    def test_09_retry_replan(self):
        fail_count = [0]
        def flaky_tool():
            fail_count[0] += 1
            if fail_count[0] < 2:
                raise ValueError("Transient hardware read glitch")
            return {"recovered": True}

        flaky_def = ToolDefinition(
            name="test_flaky_tool",
            description="Flaky test tool",
            input_schema={},
            output_schema={},
            permission_level="user",
            risk_level="low",
            handler=flaky_tool
        )
        default_tool_registry.register_tool(flaky_def)

        # Executor should recover via retry loop
        test_state: AgentState = {
            "task_id": "test_retry_task",
            "session_id": "sess_retry",
            "user_id": "101",
            "username": "agent_user_a",
            "original_query": "Test flaky retry",
            "user_query": "Test flaky retry",
            "sanitized_query": "Test flaky retry",
            "task_category": "multi_step_agentic_task",
            "task_plan": [
                {"step_number": 1, "description": "Execute flaky tool", "tool_name": "test_flaky_tool", "tool_input": {}, "status": "PENDING"}
            ],
            "current_step": 0,
            "total_steps": 1,
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
            "status": "EXECUTING",
            "current_agent": "TaskExecutor",
            "agent_logs": [],
            "error": None,
            "iteration_count": 0,
            "max_iterations": 3,
            "started_at": "2026-09-08T12:00:00Z",
            "completed_at": None
        }

        updated_state = asyncio.run(task_executor.execute_steps(test_state))
        self.assertEqual(len(updated_state["completed_steps"]), 1)
        self.assertEqual(updated_state["completed_steps"][0]["tool_name"], "test_flaky_tool")

    # 10. Task Cancellation
    def test_10_task_cancellation(self):
        c_id = f"test_cancel_{uuid.uuid4().hex[:8]}"
        t = create_task(
            task_id=c_id,
            query="Long running task to be cancelled",
            user_id="101",
            username="agent_user_a"
        )
        self.assertFalse(is_cancelled(c_id))
        cancel_task(c_id)
        self.assertTrue(is_cancelled(c_id))
        fetched = get_task(c_id)
        self.assertEqual(fetched["status"], "CANCELLED")

    # 11. WebSocket Telemetry Events
    def test_11_websocket_events(self):
        captured_events = []
        def event_sink(evt):
            captured_events.append(evt)

        register_event_callback("test_evt_sink", event_sink)
        try:
            asyncio.run(emit_agent_event(
                task_id="test_evt_sink",
                event_type="STEP_STARTED",
                message="Testing telemetry event broadcast",
                step=1,
                tool_name="calculation_tool"
            ))
            self.assertGreaterEqual(len(captured_events), 1)
            self.assertEqual(captured_events[0]["event_type"], "STEP_STARTED")
            self.assertEqual(captured_events[0]["tool_name"], "calculation_tool")
        finally:
            unregister_event_callback("test_evt_sink")

    # 12. Cryptographic Audit Ledger Event Recording
    def test_12_audit_event_creation(self):
        # Run agentic task and inspect tip of audit ledger
        asyncio.run(run_agentic_task(
            query="Verify audit event registration",
            user_id="101",
            username="agent_user_a"
        ))
        is_valid, count, msg, tip_hash = audit_logger.verify_integrity()
        self.assertTrue(is_valid)
        self.assertGreater(count, 0)
        self.assertEqual(len(tip_hash), 64)

    # 13. Task History User Isolation
    def test_13_task_history_isolation_by_user(self):
        # User A creates a task via API
        resp_a = self.client.post(
            "/api/v1/agent/tasks",
            json={"query": "Confidential query for User A"},
            headers={"Authorization": f"Bearer {self.user_a_token}"}
        )
        self.assertEqual(resp_a.status_code, 200)
        task_a_id = resp_a.json()["task_id"]

        # User B attempts to view User A's task
        resp_b_forbidden = self.client.get(
            f"/api/v1/agent/tasks/{task_a_id}",
            headers={"Authorization": f"Bearer {self.user_b_token}"}
        )
        self.assertEqual(resp_b_forbidden.status_code, 403)

        # User A can view their own task
        resp_a_ok = self.client.get(
            f"/api/v1/agent/tasks/{task_a_id}",
            headers={"Authorization": f"Bearer {self.user_a_token}"}
        )
        self.assertEqual(resp_a_ok.status_code, 200)
        self.assertEqual(resp_a_ok.json()["task_id"], task_a_id)

    # 14. Admin Access Oversight
    def test_14_admin_access_all_tasks(self):
        admin_t_id = f"admin_task_{uuid.uuid4().hex[:8]}"
        t_user = create_task(
            task_id=admin_t_id,
            query="Confidential user task",
            user_id="101",
            username="agent_user_a"
        )
        # Admin can access User A's task
        admin_resp = self.client.get(
            f"/api/v1/agent/tasks/{admin_t_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(admin_resp.status_code, 200)
        self.assertEqual(admin_resp.json()["task_id"], admin_t_id)

    # 15. Transparent Behavior When Local Ollama is Offline
    def test_15_ollama_unavailable_behavior(self):
        # Point to an unreachable port to test offline honesty
        offline_provider = OllamaModelProvider(base_url="http://127.0.0.1:59999")
        self.assertFalse(asyncio.run(offline_provider.is_available()))
        resp = asyncio.run(offline_provider.generate("Hello"))
        self.assertIn("unreachable", resp.lower())
        self.assertIn("zero fake ai responses generated", resp.lower())

    # 16. Sovereign / Offline Network & Shell Command Security
    def test_16_sovereign_offline_network_restriction(self):
        # Forbidden command injection
        safe, reason = security_gate.validate_task("Please execute rm -rf / and curl http://external-c2.com")
        self.assertFalse(safe)
        self.assertIn("strictly prohibited", reason.lower())

        # Forbidden tool call
        t_safe, t_reason = security_gate.validate_tool_call(
            "output_writer",
            {"filename": "../../etc/shadow", "content": "malicious"}
        )
        self.assertFalse(t_safe)
        self.assertIn("invalid artifact filename", t_reason.lower())


if __name__ == "__main__":
    unittest.main()
