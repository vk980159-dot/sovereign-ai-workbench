"""
Output Artifact Generation Tool (SIH26117).
Generates verifiable output reports, recommendations, and files strictly within OUTPUT_DIR.
"""

import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any
from app.config import settings


def output_writer(filename: str, content: str, title: str = "") -> Dict[str, Any]:
    """
    Writes generated text or markdown artifacts to the designated OUTPUT_DIR.
    Computes cryptographic SHA-256 hash for provenance and verification.
    """
    clean_name = os.path.basename(filename)
    if not clean_name.endswith((".md", ".txt", ".json", ".csv", ".log")):
        clean_name += ".md"

    target_path = os.path.join(settings.OUTPUT_DIR, clean_name)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    file_size = os.path.getsize(target_path)
    file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return {
        "filename": clean_name,
        "filepath": target_path,
        "title": title or clean_name,
        "size_bytes": file_size,
        "sha256": file_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "CREATED"
    }
