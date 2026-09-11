# 03. Text Extraction Subsystem
**Status:** [VERIFIED]

## Supported File Formats & Extractors
- `.pdf`: PyMuPDF (`fitz`) for vector text, Tesseract for raster pages.
- `.txt`, `.md`: Direct UTF-8 filesystem stream reader with encoding fallback.
- `.png`, `.jpg`, `.tiff`: Tesseract OCR v5.4.0 wrapper.
Extracted text is stripped of trailing null bytes and control characters before indexing.
