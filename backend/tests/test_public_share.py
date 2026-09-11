"""
Comprehensive Test Suite for Public Share Mode & Secure Cloudflare Tunnel (SIH26117).
Validates:
1. Runtime Mode Detection (PUBLIC_SHARE vs LOCAL_AIR_GAPPED vs CLOUD_DEMO)
2. Health Diagnostics and Zero External AI Verification
3. Public URL Detection from Environment and File
4. Strict Ollama Loopback Isolation (Never Public)
5. Upload Size Limits (HTTP 413)
6. File Extension Whitelist & Executable Blacklist (HTTP 400)
7. User Isolation on Deliverables/Artifacts (HTTP 403)
8. Authentication & RBAC Enforcement on Public Endpoints
9. WebSocket Telemetry Streaming
10. In-Memory Rate Limiting (HTTP 429)
11. Cloud Demo Mode Truthful Labeling
12. Local Air-Gap Mode Truthful Labeling
13. Absolute Prohibition of False Air-Gap Claims in Public Share
14. Legitimate Artifact Retrieval & Download
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import (
    settings,
    get_runtime_mode_info,
    verify_zero_external_ai,
    get_public_url,
    is_public_share_active,
    validate_air_gap_compliance,
    AirGapViolationError,
)
from app.security.auth import create_session_token
from app.security.rate_limiter import SovereignRateLimiter
from app.database.task_store import register_artifact


class TestPublicShareMode(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Create test tokens
        self.admin_token = create_session_token({"id": "1", "username": "admin", "role": "admin", "email": "admin@sovereign.local"})
        self.user_a_token = create_session_token({"id": "user_101", "username": "alice", "role": "user", "email": "alice@sovereign.local"})
        self.user_b_token = create_session_token({"id": "user_102", "username": "bob", "role": "user", "email": "bob@sovereign.local"})

    # -------------------------------------------------------------
    # 1. Runtime Mode Detection
    # -------------------------------------------------------------
    def test_01_public_share_runtime_mode(self):
        """Verify that when public share is active, runtime mode is PUBLIC_SHARE and zero external AI is verified."""
        with patch("app.config.is_public_share_active", return_value=True):
            info = get_runtime_mode_info(ollama_connected=True)
            self.assertEqual(info["runtime_mode"], "PUBLIC_SHARE")
            self.assertEqual(info["runtime_label"], "PUBLIC SHARE / LOCAL AI")
            self.assertIn("HTTPS tunnel", info["runtime_notice"])

            zero_audit = verify_zero_external_ai()
            self.assertTrue(zero_audit["zero_external_ai"])
            self.assertEqual(zero_audit["external_ai_calls"], 0)
            self.assertEqual(zero_audit["local_reasoning_model"], settings.DEFAULT_MODEL)

    # -------------------------------------------------------------
    # 2. Public Share Health Endpoint
    # -------------------------------------------------------------
    def test_02_public_share_health(self):
        """Verify GET /api/v1/health exposes public_share block, zero_external_ai, and capabilities."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.1:latest"}, {"name": "llava:latest"}]}

        with patch("app.config.is_public_share_active", return_value=True), \
             patch("app.config.get_public_url", return_value="https://test-demo.trycloudflare.com"), \
             patch("httpx.AsyncClient.get", return_value=mock_resp):

            resp = self.client.get("/api/v1/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertEqual(data["runtime_mode"], "PUBLIC_SHARE")
            self.assertEqual(data["runtime_label"], "PUBLIC SHARE / LOCAL AI")
            self.assertTrue(data["zero_external_ai"])
            self.assertEqual(data["external_ai_calls"], 0)
            self.assertIn("public_share", data)
            self.assertTrue(data["public_share"]["active"])
            self.assertEqual(data["public_share"]["public_url"], "https://test-demo.trycloudflare.com")
            self.assertEqual(data["public_share"]["ai_runtime"], "LOCAL")

            # Capabilities check
            self.assertIn("ocr_available", data)
            self.assertIn("vision_available", data)
            self.assertIn("chroma_available", data)

    # -------------------------------------------------------------
    # 3. Public URL Detection
    # -------------------------------------------------------------
    def test_03_public_url_detection(self):
        """Test get_public_url reads from environment and tracking file correctly."""
        # 1. From environment
        with patch.object(settings, "PUBLIC_BASE_URL", "https://env-tunnel.trycloudflare.com"):
            self.assertEqual(get_public_url(), "https://env-tunnel.trycloudflare.com")

        # 2. From file
        with tempfile.TemporaryDirectory() as tmpdir:
            url_file = Path(tmpdir) / ".public_share_url"
            url_file.write_text("https://file-tunnel.trycloudflare.com", encoding="utf-8")

            with patch.object(settings, "PUBLIC_BASE_URL", ""), \
                 patch("app.config.PUBLIC_SHARE_FILE", url_file):
                self.assertEqual(get_public_url(), "https://file-tunnel.trycloudflare.com")

        # 3. None when absent
        with patch.object(settings, "PUBLIC_BASE_URL", ""), \
             patch("app.config.PUBLIC_SHARE_FILE", Path("non_existent_file_path_12345")):
            self.assertIsNone(get_public_url())

    # -------------------------------------------------------------
    # 4. Ollama Loopback Strict Isolation (Never Public)
    # -------------------------------------------------------------
    def test_04_ollama_never_public(self):
        """Verify Ollama URL must strictly be loopback or private, rejecting public IPs even in public mode."""
        # Loopback must pass
        with patch.object(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"):
            validate_air_gap_compliance()

        # Public internet address must fail with AirGapViolationError
        with patch.object(settings, "OLLAMA_BASE_URL", "http://93.184.216.34:11434"), \
             patch.object(settings, "PUBLIC_SHARE_ENABLED", True):
            with self.assertRaises(AirGapViolationError):
                validate_air_gap_compliance()

    # -------------------------------------------------------------
    # 5. Upload Size Limits (HTTP 413)
    # -------------------------------------------------------------
    def test_05_public_upload_limits(self):
        """Verify uploads exceeding max MB are rejected with HTTP 413 Payload Too Large."""
        # Set limit to 1MB and test 2MB payload
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_MAX_UPLOAD_MB", 1):

            large_content = b"X" * (2 * 1024 * 1024)
            files = {"file": ("big_doc.pdf", large_content, "application/pdf")}
            headers = {"Authorization": f"Bearer {self.user_a_token}"}

            resp = self.client.post("/api/v1/upload", files=files, headers=headers)
            self.assertEqual(resp.status_code, 413)
            self.assertIn("exceeds maximum permissible upload limit", resp.json()["detail"])

    # -------------------------------------------------------------
    # 6. File Extension Whitelist & Executable Blacklist (HTTP 400)
    # -------------------------------------------------------------
    def test_06_public_file_validation(self):
        """Verify executable binaries and unauthorized file extensions are rejected with HTTP 400."""
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        dangerous_files = ["malware.exe", "trojan.bat", "exploit.ps1", "script.sh", "library.dll"]

        for bad_filename in dangerous_files:
            files = {"file": (bad_filename, b"echo unsafe", "application/octet-stream")}
            resp = self.client.post("/api/v1/upload", files=files, headers=headers)
            self.assertEqual(resp.status_code, 400, f"Failed to reject dangerous file: {bad_filename}")
            self.assertIn("strictly forbidden", resp.json()["detail"])

    # -------------------------------------------------------------
    # 7. User Isolation on Deliverables/Artifacts
    # -------------------------------------------------------------
    def test_07_public_user_isolation(self):
        """Verify user B cannot download artifacts generated by user A, while user A and admin can."""
        test_filename = "test_user_isolation_doc.docx"
        test_path = os.path.join(settings.OUTPUT_DIR, test_filename)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        with open(test_path, "wb") as f:
            f.write(b"Confidential User A Deliverable")

        try:
            # Register artifact owned by user_101 (Alice)
            register_artifact(
                task_id="task_iso_101",
                filename=test_filename,
                artifact_type="DOCX",
                user_id="user_101"
            )

            # User B (Bob) attempts access -> 403 Forbidden
            headers_b = {"Authorization": f"Bearer {self.user_b_token}"}
            resp_b = self.client.get(f"/api/v1/artifacts/{test_filename}", headers=headers_b)
            self.assertEqual(resp_b.status_code, 403)

            # User A (Alice) accesses -> 200 OK
            headers_a = {"Authorization": f"Bearer {self.user_a_token}"}
            resp_a = self.client.get(f"/api/v1/artifacts/{test_filename}", headers=headers_a)
            self.assertEqual(resp_a.status_code, 200)

            # Admin accesses -> 200 OK
            headers_admin = {"Authorization": f"Bearer {self.admin_token}"}
            resp_admin = self.client.get(f"/api/v1/artifacts/{test_filename}", headers=headers_admin)
            self.assertEqual(resp_admin.status_code, 200)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    # -------------------------------------------------------------
    # 8. Authentication & Protected Endpoints
    # -------------------------------------------------------------
    def test_08_public_authentication(self):
        """Verify protected endpoints require valid JWT authentication."""
        # Unauthenticated upload attempt -> 401
        files = {"file": ("notes.txt", b"sample notes", "text/plain")}
        resp_no_auth = self.client.post("/api/v1/upload", files=files)
        self.assertEqual(resp_no_auth.status_code, 401)

        # Invalid token -> 401
        resp_bad_auth = self.client.post("/api/v1/upload", files=files, headers={"Authorization": "Bearer badtoken123"})
        self.assertEqual(resp_bad_auth.status_code, 401)

        # Public share metadata endpoint is publicly accessible for status polling
        resp_runtime = self.client.get("/api/v1/runtime/public-share")
        self.assertEqual(resp_runtime.status_code, 200)
        self.assertIn("ai_runtime", resp_runtime.json())

    # -------------------------------------------------------------
    # 9. WebSocket Telemetry Streaming
    # -------------------------------------------------------------
    def test_09_public_websocket(self):
        """Verify /ws/telemetry connects and handles client telemetry connections."""
        with self.client.websocket_connect("/ws/telemetry") as ws:
            ws.send_json({"type": "PING"})
            # Verify socket stays open without exception

    # -------------------------------------------------------------
    # 10. In-Memory Rate Limiter
    # -------------------------------------------------------------
    def test_10_public_rate_limit(self):
        """Verify rate limiter triggers after reaching requests-per-minute threshold."""
        limiter = SovereignRateLimiter()
        client_ip = "192.168.1.50"

        # Allow 5 requests
        for _ in range(5):
            self.assertTrue(limiter.check_rate_limit(client_ip, max_requests=5, window_seconds=60, raise_exception=False))

        # 6th request must be rejected
        self.assertFalse(limiter.check_rate_limit(client_ip, max_requests=5, window_seconds=60, raise_exception=False))

    # -------------------------------------------------------------
    # 11. Cloud Demo Mode Truthful Labeling
    # -------------------------------------------------------------
    def test_11_cloud_demo_mode(self):
        """Verify runtime reports CLOUD DEMO when public share is active but Ollama is offline."""
        with patch("app.config.is_public_share_active", return_value=True):
            info = get_runtime_mode_info(ollama_connected=False)
            self.assertEqual(info["runtime_mode"], "CLOUD_DEMO")
            self.assertEqual(info["runtime_label"], "CLOUD DEMO / LOCAL AI REQUIRED")
            self.assertIn("Local Ollama daemon is currently offline", info["runtime_notice"])

    # -------------------------------------------------------------
    # 12. Local Air-Gap Mode Truthful Labeling
    # -------------------------------------------------------------
    def test_12_local_airgap_mode(self):
        """Verify runtime reports LOCAL_AIR_GAPPED when public share is off and Ollama is online."""
        with patch("app.config.is_public_share_active", return_value=False):
            info = get_runtime_mode_info(ollama_connected=True)
            self.assertEqual(info["runtime_mode"], "LOCAL_AIR_GAPPED")
            self.assertEqual(info["runtime_label"], "AIR-GAPPED / ON-PREMISE VERIFIED")
            self.assertIsNone(info["runtime_notice"])

    # -------------------------------------------------------------
    # 13. Prohibition of False Air-Gap Claims in Public Share Mode
    # -------------------------------------------------------------
    def test_13_public_share_no_false_airgap_claim(self):
        """Verify system never claims 'AIR-GAPPED' when public share is active."""
        with patch("app.config.is_public_share_active", return_value=True):
            info = get_runtime_mode_info(ollama_connected=True)
            self.assertNotEqual(info["runtime_mode"], "LOCAL_AIR_GAPPED")
            self.assertNotIn("AIR-GAPPED", info["runtime_label"])
            self.assertIn("PUBLIC SHARE", info["runtime_label"])
            self.assertIn("not an air-gapped environment", info["runtime_notice"])

    # -------------------------------------------------------------
    # 14. Artifact Retrieval & Download
    # -------------------------------------------------------------
    def test_14_public_share_artifact_download(self):
        """Verify legitimate user can download their generated deliverable."""
        test_filename = "verified_deliverable_sample.pdf"
        test_path = os.path.join(settings.OUTPUT_DIR, test_filename)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        payload_bytes = b"%PDF-1.4 Mock Deliverable Payload for Testing"
        with open(test_path, "wb") as f:
            f.write(payload_bytes)

        try:
            register_artifact(
                task_id="task_dl_99",
                filename=test_filename,
                artifact_type="PDF",
                user_id="user_101"
            )

            headers = {"Authorization": f"Bearer {self.user_a_token}"}

            # Download via /artifacts/download/{filename}
            resp = self.client.get(f"/api/v1/artifacts/download/{test_filename}", headers=headers)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.content, payload_bytes)

            # Download via /agent/artifacts/download/{filename}
            resp_alias = self.client.get(f"/api/v1/agent/artifacts/download/{test_filename}", headers=headers)
            self.assertEqual(resp_alias.status_code, 200)
            self.assertEqual(resp_alias.content, payload_bytes)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


if __name__ == "__main__":
    unittest.main()
