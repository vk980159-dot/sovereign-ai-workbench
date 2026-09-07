"""
Unit tests for Production Cloud Deployment Settings and Health Endpoint.
Sovereign AI Workbench (SIH26117)
"""

import os
import unittest
from fastapi.testclient import TestClient
from app.config import WorkbenchSettings
from app.main import app


class TestDeploymentConfig(unittest.TestCase):
    def test_environment_variable_overrides(self):
        os.environ["PORT"] = "10000"
        os.environ["HOST"] = "0.0.0.0"
        os.environ["ENVIRONMENT"] = "production-cloud"
        os.environ["AIR_GAP_STRICT_MODE"] = "false"
        os.environ["DATA_DIR"] = "/test/data"
        os.environ["CORS_ORIGINS"] = "https://workbench.onrender.com,https://sih.gov.in"

        settings = WorkbenchSettings()
        self.assertEqual(settings.PORT, 10000)
        self.assertEqual(settings.HOST, "0.0.0.0")
        self.assertEqual(settings.ENVIRONMENT, "production-cloud")
        self.assertFalse(settings.AIR_GAP_STRICT_MODE)
        self.assertTrue(settings.AUTH_DB_PATH.startswith(os.path.abspath("/test/data")))
        self.assertIn("https://workbench.onrender.com", settings.get_cors_origins())
        self.assertIn("https://sih.gov.in", settings.get_cors_origins())

        # Cleanup env vars
        del os.environ["PORT"]
        del os.environ["HOST"]
        del os.environ["ENVIRONMENT"]
        del os.environ["AIR_GAP_STRICT_MODE"]
        del os.environ["DATA_DIR"]
        del os.environ["CORS_ORIGINS"]

    def test_health_endpoint_contract(self):
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn("environment", data)
        self.assertIn("air_gapped", data)
        self.assertIn("ollama_endpoint", data)
        self.assertIn("default_model", data)
        self.assertIn("chroma_collection", data)
        self.assertIn("total_vectors", data)
        self.assertIn("audit_integrity", data)


if __name__ == "__main__":
    unittest.main()
