# 02. Scanned PDF Processing Engine
**Status:** [VERIFIED]

- **File Path:** `backend/app/agents/multimodal/pdf_processor.py`: `PDFProcessor`
- **The "Invisible Text" Challenge:** Scanned physical documents contain embedded bitmap images with 0 selectable text characters.
- **Algorithm:** Checks selectable text density per page. If text < 50 characters, renders page to 300 DPI PNG pixmap (`fitz.Matrix(2.0, 2.0)`) and dispatches to local Tesseract OCR engine.
