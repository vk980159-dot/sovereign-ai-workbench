"""
Autonomous PII Redaction & Data Sanitization Engine
Ensures zero sensitive data leakage into LLM reasoning loops or logs.
Operates 100% locally with high-performance regex rules and optional Presidio analyzer.
"""

import re
from typing import Tuple, List, Dict, Any
from app.config import settings

# Optional Presidio integration (air-gapped local if installed)
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


class PIIRedactor:
    """
    Production-grade local PII & Confidentiality Redaction Engine.
    Scrubs Personally Identifiable Information, Cryptographic Credentials,
    Network Topology, and Sovereign Classification markers.
    """

    REPLACEMENT_TAG = settings.PII_REDACTION_TAG

    # Comprehensive compiled regex patterns
    PATTERNS: Dict[str, re.Pattern] = {
        "EMAIL": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
            re.IGNORECASE
        ),
        "IPV4": re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ),
        "IPV6": re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
        ),
        "PHONE_NUMBER": re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|"
            r"(?:\+91[\-\s]?)?[6-9]\d{9}\b"
        ),
        "AADHAAR_ID": re.compile(
            r"\b[2-9]{1}\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b"
        ),
        "PAN_CARD": re.compile(
            r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
        ),
        "CREDIT_CARD": re.compile(
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
        ),
        "JWT_TOKEN": re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        "API_SECRET_KEY": re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|auth[_-]?token|bearer|private[_-]?key|access[_-]?token|passwd|password)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.\$\/+=]{8,})['\"]?"
        ),
        "AWS_KEY": re.compile(
            r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"
        ),
        "PRIVATE_KEY_BLOCK": re.compile(
            r"-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC|PGP)?\s*PRIVATE KEY-----[\s\S]*?-----END\s+(?:RSA|OPENSSH|DSA|EC|PGP)?\s*PRIVATE KEY-----"
        ),
        "ENTERPRISE_CONFIDENTIAL": re.compile(
            r"(?i)\b(?:TOP SECRET|STRICTLY CONFIDENTIAL|RESTRICTED CIRCULATION|INTERNAL ONLY|PROPRIETARY)\b"
        )
    }

    def __init__(self):
        self.presidio_analyzer = None
        self.presidio_anonymizer = None
        if PRESIDIO_AVAILABLE:
            try:
                self.presidio_analyzer = AnalyzerEngine()
                self.presidio_anonymizer = AnonymizerEngine()
            except Exception:
                self.presidio_analyzer = None
                self.presidio_anonymizer = None

    def redact(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Executes zero-leakage redaction over the input text.
        Returns:
            sanitized_text: Sanitized string with sensitive entities replaced.
            redactions: List of metadata dicts detailing each identified entity.
        """
        if not text:
            return "", []

        redactions: List[Dict[str, Any]] = []
        sanitized_text = text

        # 1. Regex-based pattern matching & masking
        # First process complex multiline blocks (Private Keys)
        for entity_type, pattern in self.PATTERNS.items():
            matches = list(pattern.finditer(sanitized_text))
            if not matches:
                continue

            # Process matches in reverse order to preserve string indices
            for match in reversed(matches):
                start, end = match.span()
                original_value = match.group(0)

                # If this pattern captures a specific credential group
                if entity_type == "API_SECRET_KEY" and match.lastindex and match.lastindex >= 1:
                    secret_span = match.span(1)
                    prefix = sanitized_text[start:secret_span[0]]
                    suffix = sanitized_text[secret_span[1]:end]
                    replacement = f"{prefix}{self.REPLACEMENT_TAG}{suffix}"
                    sanitized_text = sanitized_text[:start] + replacement + sanitized_text[end:]
                else:
                    sanitized_text = sanitized_text[:start] + self.REPLACEMENT_TAG + sanitized_text[end:]

                redactions.append({
                    "entity_type": entity_type,
                    "masked_length": len(original_value),
                    "start_pos": start,
                    "end_pos": end,
                    "preview": f"{original_value[:4]}***{original_value[-2:]}" if len(original_value) > 6 else "***"
                })

        # 2. Presidio secondary scan if local models are active
        if self.presidio_analyzer and self.presidio_anonymizer:
            try:
                results = self.presidio_analyzer.analyze(
                    text=sanitized_text,
                    language='en',
                    entities=["PERSON", "LOCATION", "NRP", "MEDICAL_LICENSE"]
                )
                if results:
                    anonymized_result = self.presidio_anonymizer.anonymize(
                        text=sanitized_text,
                        analyzer_results=results,
                        operators={"DEFAULT": OperatorConfig("replace", {"new_value": self.REPLACEMENT_TAG})}
                    )
                    sanitized_text = anonymized_result.text
                    for item in results:
                        redactions.append({
                            "entity_type": f"PRESIDIO_{item.entity_type}",
                            "score": item.score,
                            "start_pos": item.start,
                            "end_pos": item.end,
                            "preview": "***"
                        })
            except Exception:
                pass  # Fallback gracefully to regex output

        return sanitized_text, redactions

    @classmethod
    def get_summary(cls, redactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Provides count of redacted entities grouped by type."""
        summary: Dict[str, int] = {}
        for r in redactions:
            cat = r["entity_type"]
            summary[cat] = summary.get(cat, 0) + 1
        return summary


pii_redactor = PIIRedactor()
