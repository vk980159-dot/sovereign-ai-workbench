"""
Tests for Cryptographic Micro-Ledger and Tamper-Evidence.
Sovereign AI Workbench (SIH26117)
"""

import os
import tempfile
import json
import unittest
from app.security.audit_logger import AuditLogger


class TestAuditSecurity(unittest.TestCase):
    def test_microledger_hash_chain(self):
        fd, temp_log = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)

        try:
            logger = AuditLogger(log_file_path=temp_log)

            # Log 3 events
            rec1 = logger.log_event("TEST_EVENT_1", "AGENT_A", "ACTION_1", {"key": "val1"})
            rec2 = logger.log_event("TEST_EVENT_2", "AGENT_B", "ACTION_2", {"key": "val2"})
            rec3 = logger.log_event("TEST_EVENT_3", "AGENT_C", "ACTION_3", {"key": "val3"})

            self.assertEqual(rec2["previous_hash"], rec1["record_hash"])
            self.assertEqual(rec3["previous_hash"], rec2["record_hash"])

            # Verify chain integrity
            is_valid, count, msg, tip = logger.verify_integrity()
            self.assertTrue(is_valid)
            self.assertEqual(count, 4)  # Genesis + 3 events
            self.assertEqual(tip, rec3["record_hash"])

            # Simulate tampering with a record
            with open(temp_log, "r", encoding="utf-8") as f:
                lines = [json.loads(l) for l in f]

            lines[1]["action"] = "TAMPERED_ACTION"
            with open(temp_log, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(json.dumps(line) + "\n")

            # Verify tampering is immediately caught
            is_valid_after, count_after, msg_after, _ = logger.verify_integrity()
            self.assertFalse(is_valid_after)
            self.assertTrue("tamper" in msg_after.lower() or "mismatch" in msg_after.lower())

        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)


if __name__ == "__main__":
    unittest.main()
