"""
Tests for Local Authentication, Password Hashing, and Session Token Lifecycle.
Sovereign AI Workbench (SIH26117)
"""

import unittest
from app.security.auth import (
    hash_password,
    verify_password,
    create_session_token,
    verify_session_token,
    logout_user,
    create_oauth_state,
    verify_oauth_state
)


class TestAuthSecurity(unittest.TestCase):
    def test_password_hashing(self):
        raw = "SecurePassword2026!"
        pw_hash = hash_password(raw)
        self.assertNotEqual(pw_hash, raw)
        self.assertTrue(verify_password(raw, pw_hash))
        self.assertFalse(verify_password("WrongPassword!", pw_hash))

    def test_session_token_lifecycle(self):
        user = {
            "id": "u-test-123",
            "username": "testuser",
            "email": "test@sovereign.local",
            "role": "analyst"
        }
        token = create_session_token(user)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

        payload = verify_session_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "testuser")
        self.assertEqual(payload["uid"] if "uid" in payload else payload["user_id"], "u-test-123")
        self.assertEqual(payload["role"], "analyst")

        # Logout / Revoke token
        success = logout_user(token)
        self.assertTrue(success)
        self.assertIsNone(verify_session_token(token))

    def test_oauth_state_csrf(self):
        state = create_oauth_state("google")
        self.assertTrue(verify_oauth_state(state, expected_cookie=state, expected_provider="google"))
        self.assertFalse(verify_oauth_state(state, expected_cookie="different", expected_provider="google"))
        self.assertFalse(verify_oauth_state(state, expected_cookie=state, expected_provider="github"))


if __name__ == "__main__":
    unittest.main()
