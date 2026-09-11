"""
Sovereign AI Workbench - Public Share & Runtime Hardening Test Suite (SIH26117).
Validates:
- Strict Host Header Injection defenses (Phase 7)
- Offline Swagger UI without CDN dependencies (Phase 13 & 35)
- Rate Limiting under Public Share Mode (Phase 22)
- Sensitive path and secret file leakage prevention (Phase 37)
- Forbidden file upload rejection (Phase 14)
- Path traversal rejection on artifact retrieval (Phase 20)
- Runtime mode detection across Air-Gapped, Public Share, and Cloud (Phase 2)
"""

import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.config import settings, get_runtime_mode_info
from app.security.rate_limiter import rate_limiter
from app.security.auth import get_current_user


class TestPublicShareHardening(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        rate_limiter.reset()
        app.dependency_overrides.clear()

    def tearDown(self):
        rate_limiter.reset()
        app.dependency_overrides.clear()

    # ==========================================
    # 1. HOST HEADER INJECTION DEFENSES
    # ==========================================
    def test_host_header_validation_allowed(self):
        """Valid local and test hosts must be permitted."""
        for valid_host in ["localhost", "127.0.0.1", "testserver", "localhost:8000", "127.0.0.1:8000"]:
            response = self.client.get("/api/v1/health", headers={"Host": valid_host})
            self.assertEqual(response.status_code, 200, f"Host {valid_host} should be permitted")

    def test_host_header_validation_rejected(self):
        """Malicious external Host headers must be immediately rejected with HTTP 400."""
        for evil_host in ["evil.com", "attacker.io", "phishing-bank.com:8000", "192.168.99.99"]:
            response = self.client.get("/api/v1/health", headers={"Host": evil_host})
            self.assertEqual(response.status_code, 400, f"Malicious host {evil_host} must be rejected with 400")
            data = response.json()
            self.assertIn("Invalid or unauthorized Host header", data.get("detail", ""))

    def test_host_header_trycloudflare_allowed_in_public_mode(self):
        """Valid trycloudflare.com subdomains must be permitted when Public Share is active."""
        orig = settings.PUBLIC_SHARE_ENABLED
        try:
            settings.PUBLIC_SHARE_ENABLED = True
            response = self.client.get("/api/v1/health", headers={"Host": "sovereign-demo-node.trycloudflare.com"})
            self.assertEqual(response.status_code, 200)
        finally:
            settings.PUBLIC_SHARE_ENABLED = orig

    def test_tailscale_host_header_accepted_when_configured(self):
        """Tailscale Funnel host is accepted ONLY when configured via PUBLIC_BASE_URL."""
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://laptop-5shove4t.tail907df1.ts.net"}):
            # Test exact host
            resp = self.client.get("/api/v1/health", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"})
            self.assertEqual(resp.status_code, 200, "Configured Tailscale host must be permitted")

            # Test host with port
            resp = self.client.get("/api/v1/health", headers={"Host": "laptop-5shove4t.tail907df1.ts.net:443"})
            self.assertEqual(resp.status_code, 200, "Configured Tailscale host with port must be permitted")

            # Test docs endpoint under Tailscale host
            resp = self.client.get("/docs", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"})
            self.assertEqual(resp.status_code, 200)

            # Test openapi.json under Tailscale host
            resp = self.client.get("/openapi.json", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"})
            self.assertEqual(resp.status_code, 200)

            # Test root route (returns 302 to /login for unauthenticated requests)
            resp = self.client.get("/", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"}, follow_redirects=False)
            self.assertIn(resp.status_code, (200, 302))

            # Test localhost continues to work concurrently
            resp_local = self.client.get("/api/v1/health", headers={"Host": "localhost:8000"})
            self.assertEqual(resp_local.status_code, 200)

    def test_tailscale_host_header_rejected_when_not_configured(self):
        """Tailscale host header must be rejected with HTTP 400 when not configured."""
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": ""}), \
             patch.object(settings, "PUBLIC_BASE_URL", None):
            resp = self.client.get("/api/v1/health", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"})
            self.assertEqual(resp.status_code, 400)
            self.assertIn("Invalid or unauthorized Host header", resp.json().get("detail", ""))

    def test_arbitrary_tailscale_subdomains_rejected(self):
        """Arbitrary *.ts.net subdomains must NEVER be accepted; wildcards are strictly prohibited."""
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://laptop-5shove4t.tail907df1.ts.net"}):
            for unauthorized_ts in [
                "attacker.tail907df1.ts.net",
                "other-laptop.tail907df1.ts.net",
                "random-node.ts.net",
                "evil.ts.net",
                "laptop-5shove4t.other.ts.net"
            ]:
                resp = self.client.get("/api/v1/health", headers={"Host": unauthorized_ts})
                self.assertEqual(resp.status_code, 400, f"Host {unauthorized_ts} must be rejected with 400")
                self.assertIn("Invalid or unauthorized Host header", resp.json().get("detail", ""))

    def test_tailscale_websocket_telemetry(self):
        """WebSocket telemetry must connect successfully with the configured Tailscale host."""
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://laptop-5shove4t.tail907df1.ts.net"}):
            with self.client.websocket_connect("/ws/telemetry", headers={"Host": "laptop-5shove4t.tail907df1.ts.net"}) as ws:
                ws.send_text("PING")
                data = ws.receive_text()
                self.assertIn("PONG", data)

    # ==========================================
    # 2. OFFLINE SWAGGER UI ASSET INTEGRITY
    # ==========================================
    def test_swagger_offline_docs_endpoint(self):
        """Swagger /docs must serve local HTML without CDN dependency."""
        response = self.client.get("/docs", headers={"Host": "localhost"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        html = response.text
        # Verify local static asset references rather than CDN
        self.assertIn("/static/swagger/swagger-ui-bundle.js", html)
        self.assertIn("/static/swagger/swagger-ui.css", html)
        self.assertNotIn("cdn.jsdelivr.net", html)

    def test_swagger_static_assets_exist_locally(self):
        """The vendored swagger assets must exist on disk and be served directly."""
        static_bundle = Path(__file__).resolve().parent.parent / "app" / "static" / "swagger" / "swagger-ui-bundle.js"
        static_css = Path(__file__).resolve().parent.parent / "app" / "static" / "swagger" / "swagger-ui.css"
        self.assertTrue(static_bundle.is_file(), "swagger-ui-bundle.js must exist on disk")
        self.assertTrue(static_css.is_file(), "swagger-ui.css must exist on disk")
        self.assertGreater(static_bundle.stat().st_size, 100000)

        # Test serving via static mount
        resp_css = self.client.get("/static/swagger/swagger-ui.css", headers={"Host": "localhost"})
        self.assertEqual(resp_css.status_code, 200)

    # ==========================================
    # 3. RATE LIMITING IN PUBLIC SHARE MODE
    # ==========================================
    def test_rate_limiting_enforcement(self):
        """Rate limiter must return HTTP 429 when threshold is exceeded in public mode."""
        orig_share = settings.PUBLIC_SHARE_ENABLED
        orig_rpm = settings.PUBLIC_MAX_REQUESTS_PER_MINUTE
        try:
            settings.PUBLIC_SHARE_ENABLED = True
            settings.PUBLIC_MAX_REQUESTS_PER_MINUTE = 5
            # 5 requests should pass
            for i in range(5):
                resp = self.client.get("/api/v1/auth/providers", headers={"Host": "localhost", "cf-connecting-ip": "198.51.100.1"})
                self.assertEqual(resp.status_code, 200)

            # 6th request must trigger HTTP 429
            resp_blocked = self.client.get("/api/v1/auth/providers", headers={"Host": "localhost", "cf-connecting-ip": "198.51.100.1"})
            self.assertEqual(resp_blocked.status_code, 429)
            self.assertIn("Rate limit exceeded", resp_blocked.json().get("detail", ""))
        finally:
            settings.PUBLIC_SHARE_ENABLED = orig_share
            settings.PUBLIC_MAX_REQUESTS_PER_MINUTE = orig_rpm

    # ==========================================
    # 4. SENSITIVE PATH & SECRET LEAKAGE PREVENTION
    # ==========================================
    def test_secret_files_blocked(self):
        """Direct requests for .env, sqlite databases, or chroma directories must not be served."""
        forbidden_paths = [
            "/.env",
            "/backend/.env",
            "/database.db",
            "/tasks.db",
            "/auth.db",
            "/chroma_db",
            "/chroma_db/",
            "/backend/app/main.py",
            "/scripts/public_share_runner.py"
        ]
        for path in forbidden_paths:
            resp = self.client.get(path, headers={"Host": "localhost"})
            self.assertNotEqual(resp.status_code, 200, f"Sensitive path {path} must never return 200 OK")

    # ==========================================
    # 5. FORBIDDEN FILE UPLOAD EXTENSIONS
    # ==========================================
    def test_forbidden_file_uploads_rejected(self):
        """Executable, script, and archive file uploads must be rejected with HTTP 400."""
        app.dependency_overrides[get_current_user] = lambda: {"username": "test_user", "role": "user", "id": 1}
        forbidden_files = [
            ("payload.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("exploit.bat", b"@echo off\r\ncalc.exe", "text/plain"),
            ("script.py", b"import os; os.system('calc')", "text/x-python"),
            ("archive.zip", b"PK\x03\x04", "application/zip"),
            ("backdoor.ps1", b"Write-Host 'pwned'", "text/plain")
        ]
        for filename, content, mime in forbidden_files:
            files = {"file": (filename, content, mime)}
            resp = self.client.post("/api/v1/multimodal/upload", files=files, headers={"Host": "localhost"})
            self.assertEqual(resp.status_code, 400, f"File {filename} must be rejected with 400")
            self.assertIn("forbidden", resp.json().get("detail", "").lower())

    # ==========================================
    # 6. ARTIFACT PATH TRAVERSAL DEFENSES
    # ==========================================
    def test_artifact_download_path_traversal(self):
        """Relative navigation '..' in artifact downloads must be blocked."""
        app.dependency_overrides[get_current_user] = lambda: {"username": "test_user", "role": "user", "id": 1}
        resp = self.client.get("/api/v1/agent/artifacts/../../.env", headers={"Host": "localhost"})
        self.assertEqual(resp.status_code, 404)

    # ==========================================
    # 7. RUNTIME MODE CLASSIFICATION
    # ==========================================
    def test_runtime_mode_detection(self):
        """Runtime mode info must accurately reflect air-gapped vs public share."""
        orig_share = settings.PUBLIC_SHARE_ENABLED
        orig_airgap = settings.AIR_GAP_STRICT_MODE
        orig_env = settings.ENVIRONMENT
        orig_url = settings.PUBLIC_BASE_URL
        try:
            # 1. Local Air-Gapped Mode
            settings.PUBLIC_SHARE_ENABLED = False
            settings.AIR_GAP_STRICT_MODE = True
            settings.ENVIRONMENT = "production-airgapped"
            with patch("app.config.is_public_share_active", return_value=False):
                info = get_runtime_mode_info(ollama_connected=True)
                self.assertEqual(info["runtime_mode"], "LOCAL_AIR_GAPPED")
                self.assertTrue(info["air_gapped"])
                self.assertFalse(info["public_share"])

            # 2. Public Share Mode
            settings.PUBLIC_SHARE_ENABLED = True
            settings.PUBLIC_BASE_URL = "https://sovereign.trycloudflare.com"
            with patch("app.config.is_public_share_active", return_value=True):
                info = get_runtime_mode_info(ollama_connected=True)
                self.assertEqual(info["runtime_mode"], "PUBLIC_SHARE")
                self.assertFalse(info["air_gapped"])  # Truthfully not air-gapped
                self.assertTrue(info["public_share"])
                self.assertEqual(info["ai_runtime"], "LOCAL")
        finally:
            settings.PUBLIC_SHARE_ENABLED = orig_share
            settings.AIR_GAP_STRICT_MODE = orig_airgap
            settings.ENVIRONMENT = orig_env
            settings.PUBLIC_BASE_URL = orig_url

    # ==========================================
    # 8. OAUTH STATUS IN TEMPORARY TUNNEL
    # ==========================================
    def test_oauth_providers_in_temporary_tunnel(self):
        """In quick tunnel mode without PUBLIC_BASE_URL, OAuth providers must be marked disabled with a notice."""
        orig_share = settings.PUBLIC_SHARE_ENABLED
        orig_url = settings.PUBLIC_BASE_URL
        try:
            settings.PUBLIC_SHARE_ENABLED = True
            settings.PUBLIC_BASE_URL = None
            resp = self.client.get("/api/v1/auth/providers", headers={"Host": "localhost"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertFalse(data["google"])
            self.assertFalse(data["github"])
            self.assertTrue(data["temporary_tunnel"])
            self.assertIn("OAuth unavailable for temporary public tunnel", data.get("notice", ""))
        finally:
            settings.PUBLIC_SHARE_ENABLED = orig_share
            settings.PUBLIC_BASE_URL = orig_url


if __name__ == "__main__":
    unittest.main()
