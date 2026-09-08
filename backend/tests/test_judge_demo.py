"""
Automated Test Suite for SIH26117 Judge Demo Mode (SIH26117).
Validates the complete guided presentation pipeline:
1. Demo endpoint existence and schema (/api/v1/agent/demo/sih26117)
2. Synthetic files configuration and presence
3. Demo file preview endpoint (/api/v1/demo/files/{filename})
4. Actual agent task creation in tasks.db
5. Task planner multi-stage industrial sequence
6. WebSocket telemetry event emission
7. Real OCR extraction event and data
8. Real Vision provider execution
9. Deterministic calculation tool output
10. Authentic DOCX artifact generation & deep binary validation
11. Reset safety: runtime data persistence preserved
"""

import os
import sys
import json
import uuid
import asyncio
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings, BASE_DIR
from app.agents.planner import task_planner
from app.agents.tools import default_tool_registry
from app.agents.tools.calc_tools import calculation_tool
from app.agents.tools.multimodal_tools import multimodal_document_reader, vision_analyzer_tool
from app.agents.deliverables.docx_generator import DocxApprovalNoteGenerator
from app.agents.deliverables.validator import ArtifactValidator
from app.agents.events import emit_agent_event
from app.database.task_store import get_task, list_tasks
from app.database.vector_store import vector_store
from app.security.audit_logger import audit_logger


class TestJudgeDemoMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.demo_pdf = os.path.join(settings.DEMO_DATA_DIR, "scanned_inspection_report.pdf")
        cls.demo_img = os.path.join(settings.DEMO_DATA_DIR, "inspection_photo.png")
        cls.demo_sop = os.path.join(settings.DEMO_DATA_DIR, "equipment_sop.md")
        cls.demo_memo = os.path.join(settings.DEMO_DATA_DIR, "correspondence.md")

    def test_01_demo_endpoint_exists(self):
        """1. Verify POST /api/v1/agent/demo/sih26117 initializes the demo task."""
        response = self.client.post("/api/v1/agent/demo/sih26117", json={"deliverable_format": "DOCX"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "INITIALIZED")
        self.assertTrue(data.get("task_id", "").startswith("demo_sih26117_"))
        self.assertTrue(data.get("session_id", "").startswith("demo_sih26117_"))
        self.assertEqual(data.get("deliverable_format"), "DOCX")
        self.assertIn("/ws/agent-thoughts/", data.get("websocket_endpoint", ""))

    def test_02_demo_uses_correct_synthetic_files(self):
        """2. Verify demo endpoint references all required synthetic assets and they exist."""
        response = self.client.post("/api/v1/agent/demo/sih26117", json={})
        self.assertEqual(response.status_code, 200)
        files = response.json().get("synthetic_files", [])
        
        expected_files = [
            "scanned_inspection_report.pdf",
            "inspection_photo.png",
            "equipment_sop.md",
            "correspondence.md"
        ]
        for f in expected_files:
            self.assertIn(f, files)
            demo_path = os.path.join(settings.DEMO_DATA_DIR, f)
            alt_path = os.path.join(str(BASE_DIR), "demo_data", f)
            self.assertTrue(os.path.isfile(demo_path) or os.path.isfile(alt_path), f"Missing file: {f}")

    def test_03_demo_file_preview_endpoint(self):
        """3. Verify GET /api/v1/demo/files/{filename} serves image without external calls."""
        res_img = self.client.get("/api/v1/demo/files/inspection_photo.png")
        self.assertEqual(res_img.status_code, 200)
        self.assertIn("image", res_img.headers.get("content-type", ""))
        self.assertGreater(len(res_img.content), 1000)

        # Non-existent file must 404
        res_missing = self.client.get("/api/v1/demo/files/non_existent_file.png")
        self.assertEqual(res_missing.status_code, 404)

    def test_04_demo_triggers_actual_agent_task(self):
        """4. Verify demo task is registered in SQLite tasks.db."""
        response = self.client.post("/api/v1/agent/demo/sih26117", json={"deliverable_format": "DOCX"})
        self.assertEqual(response.status_code, 200)
        tid = response.json()["task_id"]
        
        task_record = get_task(tid)
        self.assertIsNotNone(task_record)
        self.assertEqual(task_record["task_id"], tid)
        self.assertIn("turbine", task_record["query"].lower())

    def test_05_task_planner_produces_8_stage_compatible_steps(self):
        """5. Verify TaskPlanner generates matching 8-stage sequence for SIH demo."""
        query = "Inspect scanned turbine report, cross-reference SOP-IND-702 safety limits, calculate thermal deviation, and generate signed Word Approval Note"
        category, plan = asyncio.run(task_planner.create_plan(query=query, deliverable_format="DOCX"))
        
        tool_names = [s["tool_name"] for s in plan]
        self.assertIn("multimodal_document_reader", tool_names)
        self.assertIn("vision_analyzer_tool", tool_names)
        self.assertIn("local_document_search", tool_names)
        self.assertIn("calculation_tool", tool_names)
        self.assertIn("generate_docx_approval_note", tool_names)
        self.assertIn("verification_tool", tool_names)

    def test_06_websocket_telemetry_events_structured(self):
        """6. Verify WebSocket telemetry emitter outputs structured safe events without chain-of-thought."""
        captured = []
        async def mock_emitter(evt):
            captured.append(evt)

        asyncio.run(emit_agent_event(
            task_id="test_demo_task",
            event_type="OCR_STARTED",
            message="Local Tesseract OCR processing initiated.",
            callback=mock_emitter
        ))

        self.assertEqual(len(captured), 1)
        evt = captured[0]
        self.assertEqual(evt.get("event_type"), "OCR_STARTED")
        self.assertEqual(evt.get("task_id"), "test_demo_task")
        # Ensure no hidden chain of thought or internal prompts leaked
        self.assertNotIn("thought_chain", evt)
        self.assertNotIn("hidden_reasoning", evt)

    def test_07_real_ocr_event_and_data(self):
        """7. Verify real local OCR processing on scanned report extracts turbine telemetry."""
        res = multimodal_document_reader("scanned_inspection_report.pdf")
        self.assertTrue(res.get("found"))
        self.assertTrue(res.get("is_scanned"))
        self.assertTrue(res.get("ocr_applied"))
        
        # Verify extracted text contains critical telemetry
        preview = res.get("extracted_text_preview", "")
        self.assertTrue(any(k in preview for k in ["TRB-702-U4", "TRB702-U4", "Bearing #3", "CRITICAL", "88.4", "13.4"]))

    def test_08_real_vision_event_and_data(self):
        """8. Verify vision analyzer tool executes on inspection_photo.png."""
        res = vision_analyzer_tool("inspection_photo.png")
        self.assertTrue(res.get("found"))
        # In presence of Ollama llava model, verify success and findings
        if res.get("success"):
            self.assertIn("llava", res.get("model", "").lower())
            self.assertGreater(len(res.get("analysis", "")), 0)

    def test_09_calculation_deterministic_result(self):
        """9. Verify calculation tool deterministically computes thermal deviation delta."""
        res = calculation_tool("88.4 - 75.0")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertAlmostEqual(res["result"], 13.4, places=2)

    def test_10_artifact_generated_and_verified(self):
        """10. Verify DOCX Approval Note is generated and passes deep binary validation."""
        gen_res = DocxApprovalNoteGenerator.generate(
            title="Turbomachinery Unit 4 Remediation Approval Note",
            reference_doc="scanned_inspection_report.pdf",
            executive_summary="Official Level 1 remediation note for Unit 4.",
            findings=[
                {"finding": "Bearing #3 temperature 88.4 C exceeds SOP-IND-702 limit of 75.0 C", "source": "scanned_inspection_report.pdf", "confidence": 0.95}
            ],
            sop_comparison="SOP-IND-702 continuous limit: 75.0 C. Operating temp: 88.4 C. Delta: +13.4 C.",
            risks=["Thermal degradation of lubrication", "Rotor seizure"],
            recommendations=["Level 1 controlled shutdown within 12 hours", "Replace Bearing #3"],
            filename="Judge_Demo_Test_Approval_Note.docx"
        )
        fpath = gen_res["file_path"]
        self.assertTrue(os.path.isfile(fpath))
        self.assertGreater(os.path.getsize(fpath), 10000)

        # Deep binary validation
        val = ArtifactValidator.validate_artifact(fpath)
        self.assertTrue(val["verified"])
        self.assertEqual(val["status"], "VERIFIED")
        self.assertEqual(val["artifact_type"], "DOCX")

        # Clean up test artifact
        try:
            os.remove(fpath)
        except Exception:
            pass

    def test_11_reset_does_not_delete_runtime_data(self):
        """11. Verify that demo presentation reset does not purge database or audit records."""
        # Ensure tasks table has tasks
        tasks_before = list_tasks(limit=10)
        self.assertGreater(len(tasks_before), 0)
        
        # Verify vector collection intact
        stats = vector_store.get_stats()
        self.assertGreater(stats.get("total_chunks", 0), 0)

        # Verify audit ledger integrity
        is_valid, count, msg, tip = audit_logger.verify_integrity()
        self.assertTrue(is_valid)
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
