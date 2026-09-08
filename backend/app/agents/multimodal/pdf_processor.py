"""
Local PDF & Scanned Document Processor (SIH26117).
Performs deterministic text extraction, scanned page detection, and local OCR routing.
Never calls external cloud APIs.
"""

import os
import io
import hashlib
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    import pypdf
except ImportError:
    pypdf = None

from PIL import Image

from app.agents.multimodal.ocr_provider import get_ocr_provider, OCRProvider
from app.agents.multimodal.evidence import DocumentEvidence

logger = logging.getLogger("sovereign.pdf_processor")


class PageResult(BaseModel):
    page_number: int
    text: str
    extraction_method: str = "native_text"  # "native_text", "ocr", "none"
    is_scanned: bool = False
    confidence: float = 1.0
    char_count: int = 0
    image_count: int = 0


class PDFAnalysisResult(BaseModel):
    filename: str
    sha256: str
    document_type: str  # "PDF_TEXT", "PDF_SCANNED", "PDF_MIXED"
    page_count: int
    is_scanned: bool
    ocr_applied: bool
    ocr_status: str  # "NOT_REQUIRED", "SUCCESS", "OCR_UNAVAILABLE", "FAILED"
    full_text: str
    pages: List[PageResult]
    evidence_items: List[DocumentEvidence]


class PDFProcessor:
    """
    Analyzes PDF files, detects scanned pages, and orchestrates local OCR.
    """

    SCANNED_THRESHOLD_CHARS = 40

    def __init__(self, ocr_provider: Optional[OCRProvider] = None):
        self.ocr_provider = ocr_provider or get_ocr_provider()

    async def process_pdf(self, file_path: str, original_filename: Optional[str] = None) -> PDFAnalysisResult:
        if not pypdf:
            raise RuntimeError("pypdf dependency is not installed.")

        fname = original_filename or os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)

        pages: List[PageResult] = []
        evidence_items: List[DocumentEvidence] = []
        scanned_page_count = 0
        ocr_attempted = False
        ocr_status = "NOT_REQUIRED"

        for idx, page in enumerate(reader.pages, start=1):
            extracted = (page.extract_text() or "").strip()
            num_images = len(page.images) if hasattr(page, "images") else 0
            is_scanned = len(extracted) < self.SCANNED_THRESHOLD_CHARS and (num_images > 0 or len(extracted) == 0)

            if is_scanned:
                scanned_page_count += 1
                ocr_text = ""
                ocr_conf = 0.0

                # Attempt OCR on embedded page images if OCR is available
                if await self.ocr_provider.is_available():
                    ocr_attempted = True
                    for img_file in page.images:
                        try:
                            ocr_res = await self.ocr_provider.extract_text_from_image(img_file.data)
                            if ocr_res.get("success") and ocr_res.get("text"):
                                ocr_text += ("\n" + ocr_res["text"]).strip()
                                ocr_conf = max(ocr_conf, ocr_res.get("confidence", 0.8))
                        except Exception as e:
                            logger.warning(f"Error OCRing image on page {idx}: {e}")

                    if ocr_text:
                        ocr_status = "SUCCESS"
                        page_text = ocr_text
                        method = "ocr"
                        conf = ocr_conf or 0.85
                    else:
                        ocr_status = "FAILED"
                        page_text = extracted or "[SCANNED_PAGE_NO_TEXT_EXTRACTED]"
                        method = "scanned_empty"
                        conf = 0.2
                else:
                    ocr_status = "OCR_UNAVAILABLE"
                    page_text = extracted or "[SCANNED_PAGE_OCR_UNAVAILABLE]"
                    method = "scanned_no_ocr"
                    conf = 0.1
            else:
                page_text = extracted
                method = "native_text"
                conf = 1.0

            page_res = PageResult(
                page_number=idx,
                text=page_text,
                extraction_method=method,
                is_scanned=is_scanned,
                confidence=conf,
                char_count=len(page_text),
                image_count=num_images
            )
            pages.append(page_res)

            # Generate traceable evidence item for each page
            if page_text and not page_text.startswith("[SCANNED_PAGE"):
                evidence_items.append(DocumentEvidence(
                    document_id=file_sha256[:16],
                    filename=fname,
                    page_number=idx,
                    extraction_method=method,
                    source_type="scanned_pdf" if is_scanned else "pdf",
                    text_excerpt=page_text[:400],
                    confidence=conf,
                    sha256=file_sha256
                ))

        # Overall document classification
        is_overall_scanned = scanned_page_count > 0 and (scanned_page_count == total_pages or scanned_page_count >= total_pages / 2)
        if scanned_page_count == 0:
            doc_type = "PDF_TEXT"
        elif scanned_page_count == total_pages:
            doc_type = "PDF_SCANNED"
        else:
            doc_type = "PDF_MIXED"

        # Build full aggregated text
        full_text_parts = [f"--- [Page {p.page_number}] [{p.extraction_method.upper()}] ---\n{p.text}" for p in pages]
        full_text = "\n\n".join(full_text_parts)

        return PDFAnalysisResult(
            filename=fname,
            sha256=file_sha256,
            document_type=doc_type,
            page_count=total_pages,
            is_scanned=is_overall_scanned,
            ocr_applied=ocr_attempted and ocr_status == "SUCCESS",
            ocr_status=ocr_status,
            full_text=full_text,
            pages=pages,
            evidence_items=evidence_items
        )


# Global singleton
pdf_processor = PDFProcessor()


def analyze_and_extract_pdf(file_path: str, original_filename: Optional[str] = None, task_id: Optional[str] = None) -> PDFAnalysisResult:
    """
    Synchronous helper to run PDFProcessor.process_pdf in any execution context.
    """
    import asyncio
    import concurrent.futures

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, pdf_processor.process_pdf(file_path, original_filename)).result()
        else:
            return loop.run_until_complete(pdf_processor.process_pdf(file_path, original_filename))
    except RuntimeError:
        return asyncio.run(pdf_processor.process_pdf(file_path, original_filename))

