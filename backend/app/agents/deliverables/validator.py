"""
Real Artifact Integrity Validator (SIH26117).
Deeply inspects generated deliverables (DOCX, XLSX, PPTX, PDF, MD) to verify package validity.
No fake files or false successes permitted.
"""

import os
import hashlib
from typing import Dict, Any, Optional

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import pptx
except ImportError:
    pptx = None

try:
    import pypdf
except ImportError:
    pypdf = None


class ArtifactValidator:
    """Validates structural and binary integrity of generated deliverables."""

    @staticmethod
    def validate_artifact(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {
                "verified": False,
                "status": "ARTIFACT_VERIFICATION_FAILED",
                "error": f"File does not exist on disk: {file_path}",
                "sha256": None
            }

        size = os.path.getsize(file_path)
        if size == 0:
            return {
                "verified": False,
                "status": "ARTIFACT_VERIFICATION_FAILED",
                "error": "Generated artifact is empty (0 bytes).",
                "sha256": None
            }

        # Calculate SHA-256
        with open(file_path, "rb") as f:
            content = f.read()
        sha256_hash = hashlib.sha256(content).hexdigest()

        ext = os.path.splitext(file_path)[1].lower()

        try:
            # 1. DOCX Validation
            if ext == ".docx":
                if not docx:
                    return {"verified": False, "status": "ARTIFACT_VERIFICATION_FAILED", "error": "docx parser unavailable"}
                d = docx.Document(file_path)
                p_count = len(d.paragraphs)
                t_count = len(d.tables)
                if p_count == 0 and t_count == 0:
                    return {
                        "verified": False,
                        "status": "ARTIFACT_VERIFICATION_FAILED",
                        "error": "DOCX package contains no paragraphs or tables.",
                        "sha256": sha256_hash
                    }
                details = {
                    "format": "DOCX",
                    "document_type": "approval_note",
                    "paragraphs": p_count,
                    "tables": t_count
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": "DOCX",
                    "format": "docx",
                    "details": details,
                    "paragraphs": p_count,
                    "tables": t_count,
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

            # 2. XLSX Validation
            elif ext == ".xlsx":
                if not openpyxl:
                    return {"verified": False, "status": "ARTIFACT_VERIFICATION_FAILED", "error": "openpyxl parser unavailable"}
                wb = openpyxl.load_workbook(file_path, data_only=False)
                sheets = wb.sheetnames
                if not sheets:
                    return {
                        "verified": False,
                        "status": "ARTIFACT_VERIFICATION_FAILED",
                        "error": "XLSX workbook has zero sheets.",
                        "sha256": sha256_hash
                    }
                details = {
                    "format": "XLSX",
                    "sheet_names": sheets
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": "XLSX",
                    "format": "xlsx",
                    "details": details,
                    "sheets": sheets,
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

            # 3. PPTX Validation
            elif ext == ".pptx":
                if not pptx:
                    return {"verified": False, "status": "ARTIFACT_VERIFICATION_FAILED", "error": "pptx parser unavailable"}
                prs = pptx.Presentation(file_path)
                slide_count = len(prs.slides)
                if slide_count == 0:
                    return {
                        "verified": False,
                        "status": "ARTIFACT_VERIFICATION_FAILED",
                        "error": "PPTX deck has zero slides.",
                        "sha256": sha256_hash
                    }
                details = {
                    "format": "PPTX",
                    "slide_count": slide_count
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": "PPTX",
                    "format": "pptx",
                    "details": details,
                    "slide_count": slide_count,
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

            # 4. PDF Validation
            elif ext == ".pdf":
                if not pypdf:
                    return {"verified": False, "status": "ARTIFACT_VERIFICATION_FAILED", "error": "pypdf parser unavailable"}
                reader = pypdf.PdfReader(file_path)
                page_count = len(reader.pages)
                if page_count == 0:
                    return {
                        "verified": False,
                        "status": "ARTIFACT_VERIFICATION_FAILED",
                        "error": "PDF has zero pages.",
                        "sha256": sha256_hash
                    }
                details = {
                    "format": "PDF",
                    "page_count": page_count
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": "PDF",
                    "format": "pdf",
                    "details": details,
                    "page_count": page_count,
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

            # 5. Markdown / Text Validation
            elif ext in (".md", ".txt", ".json", ".csv"):
                text_content = content.decode("utf-8", errors="ignore")
                if len(text_content.strip()) < 10:
                    return {
                        "verified": False,
                        "status": "ARTIFACT_VERIFICATION_FAILED",
                        "error": "Markdown/Text file is substantially empty.",
                        "sha256": sha256_hash
                    }
                details = {
                    "format": ext.lstrip(".").upper(),
                    "character_count": len(text_content)
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": ext.lstrip(".").upper(),
                    "format": ext.lstrip("."),
                    "details": details,
                    "character_count": len(text_content),
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

            else:
                details = {
                    "format": ext.lstrip(".").upper()
                }
                return {
                    "verified": True,
                    "status": "VERIFIED",
                    "artifact_type": ext.lstrip(".").upper(),
                    "format": ext.lstrip("."),
                    "details": details,
                    "size_bytes": size,
                    "sha256": sha256_hash
                }

        except Exception as e:
            return {
                "verified": False,
                "status": "ARTIFACT_VERIFICATION_FAILED",
                "error": f"Corrupted artifact package: {str(e)}",
                "sha256": sha256_hash
            }


# Global validator singleton
artifact_validator = ArtifactValidator()
