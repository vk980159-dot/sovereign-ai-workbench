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


def _run_sync_coro(coro):
    """Executes an async coroutine safely whether an event loop is running or not."""
    import asyncio
    import concurrent.futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


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
        evidence_dicts = [e.to_dict() for e in analysis.evidence_items]
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "extension": ext,
            "doc_type": analysis.document_type,
            "page_count": analysis.page_count,
            "is_scanned": analysis.is_scanned,
            "ocr_applied": analysis.ocr_applied,
            "ocr_status": analysis.ocr_status,
            "evidence_count": len(evidence_dicts),
            "evidence": evidence_dicts,
            "extracted_text_preview": analysis.full_text[:1500],
            "total_characters": len(analysis.full_text)
        }

    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        # Run local OCR on image text
        import asyncio
        import hashlib
        with open(file_path, "rb") as f:
            content = f.read()
        f_sha256 = hashlib.sha256(content).hexdigest()

        ocr_res = _run_sync_coro(local_ocr_provider.extract_text_from_image(file_path))
        extracted_text = ocr_res.get("text", "")
        evidence = DocumentEvidence(
            document_id=f_sha256[:16],
            filename=os.path.basename(file_path),
            page_number=1,
            chunk_id=f"{os.path.basename(file_path)}_img_ocr",
            extraction_method="OCR",
            source_type="IMAGE",
            text_excerpt=extracted_text,
            confidence=ocr_res.get("confidence", 0.0),
            sha256=f_sha256
        )
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "extension": ext,
            "doc_type": "IMAGE",
            "ocr_applied": bool(extracted_text),
            "ocr_status": "SUCCESS" if ocr_res.get("success") else "FAILED",
            "evidence": [evidence.to_dict()],
            "extracted_text_preview": extracted_text[:1500],
            "total_characters": len(extracted_text)
        }

    else:
        # Standard text file
        import hashlib
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        f_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        evidence = DocumentEvidence(
            document_id=f_sha256[:16],
            filename=os.path.basename(file_path),
            page_number=1,
            chunk_id=f"{os.path.basename(file_path)}_text",
            extraction_method="DIRECT",
            source_type="TEXT",
            text_excerpt=text[:400],
            confidence=1.0,
            sha256=f_sha256
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


def vision_analyzer_tool(
    filename: str,
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes local technical diagrams, equipment photos, and visual inspection images
    using local Ollama vision model (llava). Returns observations and evidence metadata.
    """
    import asyncio
    import hashlib
    from app.agents.multimodal.vision_provider import ollama_vision_provider

    file_path = _find_multimodal_file(filename)
    if not file_path:
        return {
            "found": False,
            "filename": filename,
            "error": f"Image file '{filename}' was not found in authorized local storage."
        }

    with open(file_path, "rb") as f:
        content = f.read()
    f_sha256 = hashlib.sha256(content).hexdigest()

    p = prompt or "Identify the industrial equipment, physical conditions, telemetry labels, and any visible anomalies."
    vis_res = _run_sync_coro(ollama_vision_provider.analyze_image(file_path, p))

    if not vis_res.get("success"):
        return {
            "found": True,
            "filename": os.path.basename(file_path),
            "success": False,
            "error": vis_res.get("error", "Vision analysis failed or vision model unavailable."),
            "status": vis_res.get("status", "VISION_UNAVAILABLE"),
            "evidence": []
        }

    analysis_text = vis_res.get("analysis", "")
    evidence = DocumentEvidence(
        document_id=f_sha256[:16],
        filename=os.path.basename(file_path),
        page_number=1,
        chunk_id=f"{os.path.basename(file_path)}_vision",
        extraction_method="VISION",
        source_type="IMAGE",
        text_excerpt=analysis_text[:500],
        confidence=0.88,
        sha256=f_sha256
    )

    return {
        "found": True,
        "filename": os.path.basename(file_path),
        "success": True,
        "model": vis_res.get("model", "llava"),
        "analysis": analysis_text,
        "findings": vis_res.get("findings", []),
        "evidence": [evidence.to_dict()]
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
        return TableExtractor.extract_from_csv(file_path)
    else:
        return {
            "found": False,
            "error": f"Table extraction not supported for extension '{ext}'."
        }
