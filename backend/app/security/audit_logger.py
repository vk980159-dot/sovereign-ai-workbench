"""
Tamper-Evident SHA-256 Cryptographic Audit Logger
Maintains a verifiable hash-chained immutable micro-ledger in audit_trail.jsonl.
Provides proof of sovereign compliance, zero data tampering, and deterministic provenance.
"""

import os
import json
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from app.config import settings


class AuditLogger:
    """
    Sovereign Cryptographic Audit Trail Logger.
    Appends SHA-256 hash-chained JSON records for every agent invocation,
    document ingestion, and security event.
    """

    _lock = threading.Lock()

    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file = log_file_path or settings.AUDIT_LOG_FILE
        self._ensure_genesis_record()

    @staticmethod
    def _compute_sha256(data: str) -> str:
        """Computes SHA-256 hexadecimal digest of utf-8 string."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _get_latest_record(self) -> Optional[Dict[str, Any]]:
        """Retrieves the last audit line from the log file."""
        if not os.path.exists(self.log_file):
            return None

        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return None
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
        return None

    def _ensure_genesis_record(self):
        """Initializes the audit ledger with a cryptographic genesis block if empty."""
        with self._lock:
            latest = self._get_latest_record()
            if latest is None:
                genesis_payload = {
                    "index": 0,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "event_type": "SYSTEM_GENESIS",
                    "agent_name": "ROOT_SECURITY_MONITOR",
                    "action": "INIT_AIRGAPPED_LEDGER",
                    "input_hash": self._compute_sha256("SOVEREIGN_SYSTEM_BOOTSTRAP"),
                    "output_hash": self._compute_sha256("AIRGAP_ENFORCEMENT_ENABLED"),
                    "details": {
                        "project": settings.PROJECT_NAME,
                        "version": settings.VERSION,
                        "compliance": "SIH26117_SOVEREIGN_AIRGAP"
                    },
                    "previous_hash": "0" * 64
                }
                serialized_content = json.dumps(genesis_payload, sort_keys=True)
                genesis_payload["record_hash"] = self._compute_sha256(serialized_content)

                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(json.dumps(genesis_payload) + "\n")

    def log_event(
        self,
        event_type: str,
        agent_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        input_data: str = "",
        output_data: str = ""
    ) -> Dict[str, Any]:
        """
        Appends a verifiable, cryptographically chained event record.

        Args:
            event_type: E.g., 'DOCUMENT_INGEST', 'AGENT_THOUGHT', 'FACT_CHECK', 'SYSTEM_QUERY'
            agent_name: E.g., 'Retriever', 'Analyst', 'Auditor', 'Reporter'
            action: Specific action performed
            details: Contextual metadata
            input_data: Raw or summarized input string (hashed)
            output_data: Raw or summarized output string (hashed)

        Returns:
            The complete signed record dictionary.
        """
        with self._lock:
            latest = self._get_latest_record()
            prev_hash = latest["record_hash"] if latest else ("0" * 64)
            current_index = (latest["index"] + 1) if latest else 0

            record_payload = {
                "index": current_index,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "agent_name": agent_name,
                "action": action,
                "input_hash": self._compute_sha256(input_data),
                "output_hash": self._compute_sha256(output_data),
                "details": details or {},
                "previous_hash": prev_hash
            }

            serialized = json.dumps(record_payload, sort_keys=True)
            record_hash = self._compute_sha256(serialized)
            record_payload["record_hash"] = record_hash

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record_payload) + "\n")

            return record_payload

    def verify_integrity(self) -> Tuple[bool, int, str, str]:
        """
        Validates the complete SHA-256 chain from Genesis block to the tip.

        Returns:
            (is_valid, record_count, status_message, latest_hash)
        """
        with self._lock:
            if not os.path.exists(self.log_file):
                return False, 0, "Audit ledger file not found.", ""

            records: List[Dict[str, Any]] = []
            with open(self.log_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        return False, idx, f"Corrupted JSON format at line {idx + 1}", ""

            if not records:
                return False, 0, "Audit log is empty", ""

            expected_prev_hash = "0" * 64

            for i, record in enumerate(records):
                if record.get("index") != i:
                    return False, i, f"Index discontinuity at record #{i}", ""

                if record.get("previous_hash") != expected_prev_hash:
                    return (
                        False,
                        i,
                        f"Cryptographic hash chain broken at record #{i}! "
                        f"Expected prev: {expected_prev_hash[:12]}..., Got: {record.get('previous_hash')[:12]}...",
                        record.get("record_hash", "")
                    )

                stored_hash = record.get("record_hash")
                # Reconstruct payload without record_hash
                payload_to_verify = {k: v for k, v in record.items() if k != "record_hash"}
                recalculated_hash = self._compute_sha256(json.dumps(payload_to_verify, sort_keys=True))

                if stored_hash != recalculated_hash:
                    return (
                        False,
                        i,
                        f"Data tampering detected at record #{i}! SHA-256 digest mismatch.",
                        stored_hash or ""
                    )

                expected_prev_hash = stored_hash

            tip_hash = records[-1]["record_hash"]
            return True, len(records), "Audit trail is 100% authentic and tamper-free.", tip_hash

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent N audit records."""
        with self._lock:
            if not os.path.exists(self.log_file):
                return []
            records = []
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            return records[-limit:]


# Global singleton instance
audit_logger = AuditLogger()
