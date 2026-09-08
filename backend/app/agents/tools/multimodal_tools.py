"""
Multimodal Document & Structured Table Processing Tools (SIH26117).
Provides safe tool handlers for multimodal document reading (scanned PDF, digital PDF, OCR)
and structured tabular analysis with deterministic metrics.
"""

import os
from typing import Dict, Any, List, Optional
from app.config import settings, BASE_DIR
from app.agents.multimodal.pdf_processor import analyze_and_extract_pdf
from app.agents.multimodal.table_extractor import TableExtractor
from app.agents.multimodal.ocr_provider import local_ocr_provider
from app.agents.multimodal.evidence import DocumentEvidence


def _find_multimodal_file(filename: str) -> Optional[str]:
    """Resolves filename across authorized local directories."""
    clean_name = os.path.basename(filename)
    candidates = [
        os.path.join(settings.MULTIMODAL_UPLOAD_DIR, clean_name),
        os.path.join(settings.UPLOAD_DIR, clean_name),
        os.path.join(settings.DEMO_DATA_DIR, clean_name),
        os.path.join(settings.OUTPUT_DIR, clean_name),
        os.path.join(BASE_DIR, clean_name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def multimodal_document_reader(
    filename: str,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reads multimodal documents including native PDFs, scanned PDFs (with local OCR),
    images, and structured documents. Returns verified evidence items.
    """
    file_path = _find_multimodal_file(filename)
    if not file_path:
        return {
            "found": False,
            "filename": filename,
            "error": f"File '{filename}' was not found in authorized local storage."
        }

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        analysis = analyze_and_extract_pdf(file_path=file_path, task_id=task_id)
        evidence_dicts = [e.to_dict() for e in analysis.evidence_list]
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "extension": ext,
            "doc_type": analysis.doc_type,
            "page_count": analysis.page_count,
            "has_images": analysis.has_images,
            "ocr_applied": analysis.ocr_applied,
            "ocr_status": analysis.ocr_status,
            "evidence_count": len(evidence_dicts),
            "evidence": evidence_dicts,
            "extracted_text_preview": analysis.combined_text[:1500],
            "total_characters": len(analysis.combined_text)
        }

    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        # Run local OCR
        ocr_res = local_ocr_provider.perform_ocr(file_path)
        extracted_text = ocr_res.get("text", "")
        evidence = DocumentEvidence(
            document_id=os.path.basename(file_path),
            filename=os.path.basename(file_path),
            page_number=1,
            chunk_id=f"{os.path.basename(file_path)}_img_ocr",
            extraction_method="OCR" if ocr_res.get("ocr_applied") else "DIRECT",
            source_type="IMAGE",
            text_excerpt=extracted_text,
            confidence=ocr_res.get("confidence", 0.0),
            sha256=ocr_res.get("sha256", "")
        )
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "extension": ext,
            "doc_type": "IMAGE",
            "ocr_applied": ocr_res.get("ocr_applied", False),
            "ocr_status": ocr_res.get("ocr_status", "UNKNOWN"),
            "evidence": [evidence.to_dict()],
            "extracted_text_preview": extracted_text[:1500],
            "total_characters": len(extracted_text)
        }

    else:
        # Standard text file
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        evidence = DocumentEvidence(
            document_id=os.path.basename(file_path),
            filename=os.path.basename(file_path),
            page_number=1,
            chunk_id=f"{os.path.basename(file_path)}_text",
            extraction_method="DIRECT",
            source_type="TEXT",
            text_excerpt=text
        )
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "extension": ext,
            "doc_type": "TEXT",
            "evidence": [evidence.to_dict()],
            "extracted_text_preview": text[:1500],
            "total_characters": len(text)
        }


def table_analyzer_tool(
    filename: str,
    max_rows: int = 100
) -> Dict[str, Any]:
    """
    Parses and summarizes structured tables (CSV, JSON) and extracts statistical metrics.
    """
    file_path = _find_multimodal_file(filename)
    if not file_path:
        return {
            "found": False,
            "filename": filename,
            "error": f"File '{filename}' was not found in authorized local storage."
        }

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return TableExtractor.extract_from_csv(file_path, max_rows=max_rows)
    elif ext == ".json":
        return TableExtractor.extract_from_json(file_path)
    else:
        return {
            "found": False,
            "error": f"Table extraction not supported for extension '{ext}'."
        }
