# 02. PDF Processing & Rasterization
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/multimodal/pdf_processor.py`: `PDFProcessor`

## 2. Hybrid Processing Algorithm
- Uses PyMuPDF (`fitz`).
- Iterates page-by-page. Checks text density:
  - If page text length >= 50 characters: extracts digital vector text directly.
  - If page text length < 50 characters: page is a scanned bitmap. Rasterizes at 300 DPI (`matrix = fitz.Matrix(2.0, 2.0)`) -> passes pixmap to Tesseract OCR v5.4.0.
- Aggregates digital and OCR text into a unified `ProcessedDocument` object.
