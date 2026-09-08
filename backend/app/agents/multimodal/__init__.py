"""
Multimodal Package Exports (SIH26117).
Provides local OCR, local Vision, PDF analysis, and Structured Table extraction.
"""

from app.agents.multimodal.evidence import DocumentEvidence
from app.agents.multimodal.ocr_provider import OCRProvider, LocalOCRProvider, get_ocr_provider, local_ocr_provider
from app.agents.multimodal.vision_provider import VisionProvider, OllamaVisionProvider, get_vision_provider, ollama_vision_provider
from app.agents.multimodal.pdf_processor import PDFProcessor, PDFAnalysisResult, pdf_processor, analyze_and_extract_pdf
from app.agents.multimodal.table_extractor import TableExtractor, StructuredTable, table_extractor

__all__ = [
    "DocumentEvidence",
    "OCRProvider",
    "LocalOCRProvider",
    "get_ocr_provider",
    "local_ocr_provider",
    "VisionProvider",
    "OllamaVisionProvider",
    "get_vision_provider",
    "ollama_vision_provider",
    "PDFProcessor",
    "PDFAnalysisResult",
    "pdf_processor",
    "analyze_and_extract_pdf",
    "TableExtractor",
    "StructuredTable",
    "table_extractor"
]
