"""
Tests for Confidential PII Redaction Engine.
Sovereign AI Workbench (SIH26117)
"""

import unittest
from app.security.pii_redactor import PIIRedactor


class TestPIIRedaction(unittest.TestCase):
    def test_pii_redaction_patterns(self):
        redactor = PIIRedactor()
        raw_text = (
            "Contact agent John Doe at john.doe@example.gov.in or call +91 9876543210. "
            "Aadhaar: 2345 6789 0123. PAN: ABCDE1234F."
        )
        redacted_text, records = redactor.redact(raw_text)

        # Raw sensitive tokens must not be in redacted text
        self.assertNotIn("john.doe@example.gov.in", redacted_text)
        self.assertNotIn("2345 6789 0123", redacted_text)
        self.assertNotIn("ABCDE1234F", redacted_text)
        self.assertGreater(len(records), 0)


if __name__ == "__main__":
    unittest.main()
