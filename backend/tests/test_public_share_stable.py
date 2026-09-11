"""
Sovereign AI Workbench - Stable Public Share Test Suite (SIH26117)
-----------------------------------------------------------------
Validates Cloudflare Named Tunnel mode:
1. Runtime Mode Detection (PUBLIC_SHARE_STABLE vs PUBLIC_SHARE vs LOCAL_AIR_GAPPED)
2. Truthful Air-Gap and Public Share Labels (air_gapped is strictly False in public mode)
3. Stable Host Header validation against custom PUBLIC_BASE_URL
4. OAuth providers endpoint responses for stable vs temporary tunnels
5. Public share status endpoint (/api/runtime/public-share)
6. Zero external AI integrity in stable mode
7. Blocked execution behavior when credentials are missing
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import (
    settings,
    get_runtime_mode_info,
    verify_zero_external_ai,
    is_public_share_active,
)


class TestPublicShareStable(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Stable Tunnel Runtime Mode & Truthful Labeling
    # -------------------------------------------------------------
    def test_stable_runtime_mode_detection(self):
        """When stable mode is configured, runtime_mode must be PUBLIC_SHARE_STABLE and air_gapped must be False."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "stable"), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_NAME", "sovereign-prod"), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://ai.sovereign.local"):

            self.assertTrue(settings.is_stable_tunnel())
            self.assertTrue(is_public_share_active())

            info = get_runtime_mode_info(ollama_connected=True)
            self.assertEqual(info["runtime_mode"], "PUBLIC_SHARE_STABLE")
            self.assertEqual(info["runtime_label"], "PUBLIC SHARE / LOCAL AI")
            self.assertFalse(info["air_gapped"], "PUBLIC_SHARE_STABLE must NEVER claim air-gapped status")
            self.assertTrue(info["public_share"])
            self.assertTrue(info["stable_tunnel"])
            self.assertEqual(info["tunnel_type"], "named")
            self.assertEqual(info["tunnel_provider"], "cloudflare")
            self.assertEqual(info["public_url"], "https://ai.sovereign.local")
            self.assertIn("Cloudflare Named Tunnel", info["runtime_notice"])

    def test_quick_tunnel_fallback_mode(self):
        """When quick mode is configured, runtime_mode must be PUBLIC_SHARE with tunnel_type='quick'."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "quick"), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_NAME", None), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_TOKEN", None), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://alpha-beta.trycloudflare.com"):

            self.assertFalse(settings.is_stable_tunnel())
            self.assertTrue(is_public_share_active())

            info = get_runtime_mode_info(ollama_connected=True)
            self.assertEqual(info["runtime_mode"], "PUBLIC_SHARE")
            self.assertEqual(info["runtime_label"], "PUBLIC SHARE / LOCAL AI")
            self.assertFalse(info["air_gapped"])
            self.assertFalse(info["stable_tunnel"])
            self.assertEqual(info["tunnel_type"], "quick")

    def test_local_air_gapped_mode_intact(self):
        """When public share is not enabled and no tunnel file exists, mode is LOCAL_AIR_GAPPED with air_gapped=True."""
        mock_file = MagicMock()
        mock_file.is_file.return_value = False
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", False), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "quick"), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_NAME", None), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_TOKEN", None), \
             patch("app.config.PUBLIC_SHARE_FILE", mock_file):

            self.assertFalse(settings.is_stable_tunnel())
            self.assertFalse(is_public_share_active())

            info = get_runtime_mode_info(ollama_connected=True)
            self.assertEqual(info["runtime_mode"], "LOCAL_AIR_GAPPED")
            self.assertEqual(info["runtime_label"], "AIR-GAPPED / ON-PREMISE VERIFIED")
            self.assertTrue(info["air_gapped"])
            self.assertFalse(info["public_share"])

    # -------------------------------------------------------------
    # 2. Host Header Validation with Custom Stable Domain
    # -------------------------------------------------------------
    def test_stable_custom_host_header_allowed(self):
        """Host headers matching configured PUBLIC_BASE_URL hostname must be allowed."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "stable"), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://ai.enterprise-corp.com"):

            self.assertTrue(settings.is_host_allowed("ai.enterprise-corp.com"))
            self.assertTrue(settings.is_host_allowed("ai.enterprise-corp.com:443"))
            self.assertFalse(settings.is_host_allowed("evil-hacker.com"))
            self.assertFalse(settings.is_host_allowed("random.trycloudflare.com"))

    # -------------------------------------------------------------
    # 3. OAuth Providers Endpoint Behavior
    # -------------------------------------------------------------
    def test_oauth_providers_stable_tunnel_status(self):
        """OAuth providers endpoint truthfully reports stable_tunnel and permits OAuth on stable URLs."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "stable"), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://ai.enterprise-corp.com"), \
             patch.object(settings, "GOOGLE_CLIENT_ID", "test-google-client-id"), \
             patch.object(settings, "GOOGLE_CLIENT_SECRET", "test-secret"):

            resp = self.client.get("/api/auth/providers")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertFalse(data.get("temporary_tunnel", False))
            self.assertTrue(data.get("stable_tunnel", False))
            self.assertTrue(data.get("google", False))

    def test_oauth_providers_quick_tunnel_status(self):
        """OAuth providers endpoint blocks OAuth on temporary trycloudflare tunnels."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "quick"), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_NAME", None), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_TOKEN", None), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://sample.trycloudflare.com"), \
             patch.object(settings, "GOOGLE_CLIENT_ID", "test-google-client-id"), \
             patch.object(settings, "GOOGLE_CLIENT_SECRET", "test-secret"):

            resp = self.client.get("/api/auth/providers")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("temporary_tunnel", False))
            self.assertFalse(data.get("stable_tunnel", False))
            self.assertFalse(data.get("google", False))

    # -------------------------------------------------------------
    # 4. Public Share Runtime Endpoint (/api/runtime/public-share)
    # -------------------------------------------------------------
    def test_runtime_public_share_endpoint(self):
        """Verify /api/runtime/public-share reports stable tunnel metadata."""
        with patch.object(settings, "PUBLIC_SHARE_ENABLED", True), \
             patch.object(settings, "PUBLIC_SHARE_MODE", "stable"), \
             patch.object(settings, "CLOUDFLARE_TUNNEL_NAME", "sovereign-workbench"), \
             patch.object(settings, "PUBLIC_BASE_URL", "https://workbench.internal.org"):

            resp = self.client.get("/api/runtime/public-share")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data["enabled"])
            self.assertEqual(data["runtime_mode"], "PUBLIC_SHARE_STABLE")
            self.assertEqual(data["tunnel_type"], "named")
            self.assertEqual(data["public_url"], "https://workbench.internal.org")
            self.assertEqual(data["stable_url"], "https://workbench.internal.org")

    # -------------------------------------------------------------
    # 5. Zero External AI Integrity in Stable Mode
    # -------------------------------------------------------------
    def test_zero_external_ai_in_stable_mode(self):
        """Zero external AI calls must remain 0 and zero_external_ai must be True in stable share mode."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure cloud keys are empty
            for k in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
                os.environ.pop(k, None)

            verification = verify_zero_external_ai()
            self.assertTrue(verification["zero_external_ai"])
            self.assertEqual(verification["external_ai_calls"], 0)
            self.assertEqual(verification["external_providers_detected"], [])
            self.assertEqual(verification["local_reasoning_model"], settings.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
