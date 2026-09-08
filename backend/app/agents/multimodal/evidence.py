"""
Structured Document Evidence Model (SIH26117).
Ensures every extracted industrial fact is cryptographically and contextually traceable.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentEvidence(BaseModel):
    """
    Traceable evidence item linking an extracted fact to its source document and location.
    """
    document_id: str = Field(..., description="Unique document ID (first 16 chars of sha256 or custom id)")
    filename: str = Field(..., description="Original or sanitized filename")
    page_number: Optional[int] = Field(None, description="1-indexed page number if document is paginated (PDF)")
    chunk_id: Optional[str] = Field(None, description="Vector store chunk identifier if indexed into ChromaDB")
    extraction_method: str = Field("native_text", description="'native_text', 'ocr', 'vision', or 'table'")
    source_type: str = Field("document", description="'pdf', 'scanned_pdf', 'image', 'table', 'csv', 'json'")
    text_excerpt: str = Field(..., description="Verbatim text excerpt or evidence snippet")
    confidence: float = Field(1.0, description="Extraction or OCR confidence score (0.0 - 1.0)")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Optional spatial bounding coordinates {x, y, w, h}")
    sha256: str = Field(..., description="SHA-256 digest of source file or page image")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_citation_format(self) -> str:
        loc = f"p. {self.page_number}" if self.page_number else "Section"
        method = f"[{self.extraction_method.upper()}]" if self.extraction_method != "native_text" else ""
        return f"[{self.filename} - {loc} {method} (Confidence: {int(self.confidence * 100)}%)]"

    def to_citation_string(self) -> str:
        return self.to_citation_format()

