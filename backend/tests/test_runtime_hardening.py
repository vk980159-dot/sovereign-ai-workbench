"""
Comprehensive Test Suite for OAuth Hardening, Runtime Mode Detection, Ingestion Error Safety,
and Cloud Demo Honesty (SIH26117).
"""

import os
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from urllib.parse import urlparse, parse_qs

from app.main import app
from app.config import settings, WorkbenchSettings, _clean_credential
from app.security.auth import create_oauth_state, verify_oauth_state, create_session_token
from app.api.router import _is_ollama_connection_error


class TestOAuthAndRuntimeHardening(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. GitHub local redirect URI generation
    # -------------------------------------------------------------
    def test_01_github_local_redirect_uri_generation(self):
        """Verify GitHub login initiates flow with exact http://127.0.0.1:8000/api/auth/github/callback."""
        with patch.object(settings, "GITHUB_CLIENT_ID", "test_gh_client_id"),              patch.object(settings, "GITHUB_CLIENT_SECRET", "test_gh_secret"),              patch.object(settings, "GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/github/callback"):
            response = self.client.get("/api/auth/github/login", follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            redirect_url = response.headers["location"]
            self.assertTrue(redirect_url.startswith("https://github.com/login/oauth/authorize"))
            parsed = urlparse(redirect_url)
            qs = parse_qs(parsed.query)
            self.assertEqual(qs["redirect_uri"][0], "http://127.0.0.1:8000/api/auth/github/callback")
            self.assertEqual(qs["client_id"][0], "test_gh_client_id")

    # -------------------------------------------------------------
    # 2. GitHub callback uses 127.0.0.1 without conversion to localhost
    # -------------------------------------------------------------
    def test_02_github_callback_uses_127_0_0_1(self):
        """Verify redirect URI is strictly 127.0.0.1 and not converted to localhost."""
        with patch.object(settings, "GITHUB_CLIENT_ID", "gh_id"),              patch.object(settings, "GITHUB_CLIENT_SECRET", "gh_sec"),              patch.object(settings, "GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/github/callback"):
            response = self.client.get("/api/auth/github/login", follow_redirects=False)
            parsed = urlparse(response.headers["location"])
            qs = parse_qs(parsed.query)
            self.assertIn("127.0.0.1:8000", qs["redirect_uri"][0])
            self.assertNotIn("localhost:8000", qs["redirect_uri"][0])

    # -------------------------------------------------------------
    # 3. Authorization and token exchange use the same redirect URI
    # -------------------------------------------------------------
    def test_03_auth_and_token_exchange_use_same_redirect_uri(self):
        """Verify authorization URL and token exchange post identical redirect URI to GitHub."""
        local_uri = "http://127.0.0.1:8000/api/auth/github/callback"
        state = create_oauth_state("github")

        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "mock_gh_access_token"}

        mock_user_resp = MagicMock()
        mock_user_resp.status_code = 200
        mock_user_resp.json.return_value = {"id": 12345, "login": "testdev", "name": "Test Dev", "email": "testdev@sovereign.local"}

        mock_emails_resp = MagicMock()
        mock_emails_resp.status_code = 200
        mock_emails_resp.json.return_value = [{"email": "testdev@sovereign.local", "primary": True, "verified": True}]

        with patch.object(settings, "GITHUB_CLIENT_ID", "gh_client"),              patch.object(settings, "GITHUB_CLIENT_SECRET", "gh_secret"),              patch.object(settings, "GITHUB_REDIRECT_URI", local_uri),              patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,              patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:

            mock_post.return_value = mock_token_resp
            mock_get.side_effect = [mock_user_resp, mock_emails_resp]

            # 1. Login auth URL uses local_uri
            login_resp = self.client.get("/api/auth/github/login", follow_redirects=False)
            qs = parse_qs(urlparse(login_resp.headers["location"]).query)
            self.assertEqual(qs["redirect_uri"][0], local_uri)

            # 2. Callback token exchange uses local_uri
            client = TestClient(app, cookies={"oauth_state_github": state})
            cb_resp = client.get(f"/api/auth/github/callback?code=mock_code&state={state}", follow_redirects=False)

            # Verify token exchange payload
            mock_post.assert_called_once()
            called_data = mock_post.call_args[1].get("data") or mock_post.call_args.kwargs.get("data")
            self.assertEqual(called_data["redirect_uri"], local_uri)
            self.assertEqual(called_data["client_id"], "gh_client")
            self.assertEqual(called_data["code"], "mock_code")

    # -------------------------------------------------------------
    # 4. Production redirect URI handling
    # -------------------------------------------------------------
    def test_04_production_redirect_uri_handling(self):
        """Verify production-cloud environment uses Render production callback URI."""
        prod_uri = "https://sovereign-ai-workbench-wb96.onrender.com/api/auth/github/callback"
        with patch.object(settings, "ENVIRONMENT", "production-cloud"),              patch.object(settings, "GITHUB_CLIENT_ID", "gh_id"),              patch.object(settings, "GITHUB_CLIENT_SECRET", "gh_sec"),              patch.object(settings, "GITHUB_REDIRECT_URI", prod_uri):
            response = self.client.get("/api/auth/github/login", follow_redirects=False)
            qs = parse_qs(urlparse(response.headers["location"]).query)
            self.assertEqual(qs["redirect_uri"][0], prod_uri)

    # -------------------------------------------------------------
    # 5. OAuth configuration sanitization
    # -------------------------------------------------------------
    def test_05_oauth_configuration_sanitization(self):
        """Verify quotes, angle brackets, and whitespace are thoroughly stripped."""
        self.assertEqual(_clean_credential('  "my_secret_token"  '), "my_secret_token")
        self.assertEqual(_clean_credential(" 'my_secret_token' "), "my_secret_token")
        self.assertEqual(_clean_credential(' <http://127.0.0.1:8000/callback> '), "http://127.0.0.1:8000/callback")
        self.assertEqual(_clean_credential('""'), "")
        self.assertEqual(_clean_credential(None), "")

    # -------------------------------------------------------------
    # 6. GitHub OAuth state validation
    # -------------------------------------------------------------
    def test_06_github_oauth_state_validation(self):
        """Verify CSRF rejection when state token does not match cookie or has wrong provider."""
        state = create_oauth_state("github")
        # Missing state
        resp = self.client.get("/api/auth/github/callback?code=abc", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("error=missing_credentials", resp.headers["location"])

        # Mismatched state
        client = TestClient(app, cookies={"oauth_state_github": state})
        resp = client.get("/api/auth/github/callback?code=abc&state=tampered_state", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("error=csrf_validation_failed", resp.headers["location"])

    # -------------------------------------------------------------
    # 7. Cloud mode Ollama unavailable
    # -------------------------------------------------------------
    def test_07_cloud_mode_ollama_unavailable(self):
        """Verify health endpoint dynamically reports CLOUD DEMO and DEGRADED when Ollama is unreachable in cloud."""
        with patch.object(settings, "ENVIRONMENT", "production-cloud"),              patch.object(settings, "AIR_GAP_STRICT_MODE", False),              patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
            resp = self.client.get("/api/v1/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["runtime_mode"], "CLOUD_DEMO")
            self.assertEqual(data["runtime_label"], "CLOUD DEMO / LOCAL AI REQUIRED")
            self.assertIn("requires the local/on-premise runtime", data["runtime_notice"])
            self.assertFalse(data["ollama_connected"])
            self.assertEqual(data["embeddings_status"], "DEGRADED / DEPENDENT ON OLLAMA")

    # -------------------------------------------------------------
    # 8. Local mode Ollama available
    # -------------------------------------------------------------
    def test_08_local_mode_ollama_available(self):
        """Verify health endpoint reports AIR-GAPPED / ON-PREMISE VERIFIED when Ollama is reachable."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.1:latest"}]}

        with patch.object(settings, "ENVIRONMENT", "production-airgapped"),              patch.object(settings, "AIR_GAP_STRICT_MODE", True),              patch("httpx.AsyncClient.get", return_value=mock_resp):
            resp = self.client.get("/api/v1/health")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["runtime_mode"], "LOCAL_AIR_GAPPED")
            self.assertEqual(data["runtime_label"], "AIR-GAPPED / ON-PREMISE VERIFIED")
            self.assertTrue(data["ollama_connected"])
            self.assertEqual(data["embeddings_status"], "OPERATIONAL")

    # -------------------------------------------------------------
    # 9. Correct environment labeling
    # -------------------------------------------------------------
    def test_09_correct_environment_labeling_in_providers(self):
        """Verify /auth/providers safely exposes environment and redirect URI without secret leaks."""
        with patch.object(settings, "ENVIRONMENT", "production-airgapped"),              patch.object(settings, "GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/github/callback"),              patch.object(settings, "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback"):
            resp = self.client.get("/api/v1/auth/providers")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["environment"], "production-airgapped")
            self.assertEqual(data["github_redirect_uri"], "http://127.0.0.1:8000/api/auth/github/callback")
            self.assertNotIn("client_secret", data)
            self.assertNotIn("secret", str(data).lower())

    # -------------------------------------------------------------
    # 10. Knowledge Base graceful Ollama failure
    # -------------------------------------------------------------
    def test_10_knowledge_base_graceful_ollama_failure_local(self):
        """Verify upload returns clean HTTP 503 when local Ollama is offline."""
        admin_token = create_session_token({"username": "admin", "role": "admin", "id": 1, "email": "admin@sovereign.local"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        with patch.object(settings, "ENVIRONMENT", "production-airgapped"),              patch("app.database.vector_store.vector_store.ingest_file", side_effect=Exception("HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded (Caused by NewConnectionError: Connection refused)")):
            files = {"file": ("test.txt", b"Sample industrial equipment operational limits content.", "text/plain")}
            resp = self.client.post("/api/v1/upload", files=files, headers=headers)
            self.assertEqual(resp.status_code, 503)
            self.assertIn("Local AI engine is unavailable", resp.json()["detail"])

    # -------------------------------------------------------------
    # 11. No raw traceback returned to frontend
    # -------------------------------------------------------------
    def test_11_no_raw_traceback_in_cloud_failure(self):
        """Verify cloud mode ingestion failure does not leak technical stack trace or ports."""
        admin_token = create_session_token({"username": "admin", "role": "admin", "id": 1, "email": "admin@sovereign.local"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        with patch.object(settings, "ENVIRONMENT", "production-cloud"),              patch("app.database.vector_store.vector_store.ingest_file", side_effect=Exception("HTTPConnectionPool(host='localhost', port=11434): Max retries exceeded (Caused by NewConnectionError: Connection refused)")):
            files = {"file": ("test.txt", b"Sample content.", "text/plain")}
            resp = self.client.post("/api/v1/upload", files=files, headers=headers)
            self.assertEqual(resp.status_code, 503)
            detail = resp.json()["detail"]
            self.assertNotIn("HTTPConnectionPool", detail)
            self.assertNotIn("NewConnectionError", detail)
            self.assertNotIn("Traceback", detail)
            self.assertIn("Local AI inference is unavailable in this cloud demonstration runtime", detail)

    # -------------------------------------------------------------
    # 12. Judge Demo refuses to fake cloud AI results
    # -------------------------------------------------------------
    def test_12_judge_demo_refuses_to_fake_when_ollama_unavailable(self):
        """Verify Judge Demo halts with clean HTTP 503 rather than fabricating AI stages when Ollama is down."""
        admin_token = create_session_token({"username": "admin", "role": "admin", "id": 1, "email": "admin@sovereign.local"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
            resp = self.client.post("/api/v1/agent/demo/sih26117", json={"deliverable_format": "DOCX"}, headers=headers)
            self.assertEqual(resp.status_code, 503)
            self.assertIn("Judge Demo requires the local sovereign runtime with Ollama, Tesseract and ChromaDB.", resp.json()["detail"])

    # -------------------------------------------------------------
    # 13. Existing Google OAuth remains working
    # -------------------------------------------------------------
    def test_13_existing_google_oauth_remains_working(self):
        """Verify Google OAuth flow and state generation remain intact."""
        with patch.object(settings, "GOOGLE_CLIENT_ID", "google_id"),              patch.object(settings, "GOOGLE_CLIENT_SECRET", "google_sec"),              patch.object(settings, "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/google/callback"):
            resp = self.client.get("/api/auth/google/login", follow_redirects=False)
            self.assertEqual(resp.status_code, 302)
            location = resp.headers["location"]
            self.assertTrue(location.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
            qs = parse_qs(urlparse(location).query)
            self.assertEqual(qs["redirect_uri"][0], "http://127.0.0.1:8000/api/auth/google/callback")
            self.assertEqual(qs["client_id"][0], "google_id")
            self.assertIn("oauth_state_google", resp.cookies)


if __name__ == "__main__":
    unittest.main()
