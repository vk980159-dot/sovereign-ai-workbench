# 01. Document Ingestion Pipeline
**Status:** [VERIFIED]

## 1. Ingestion Route
`POST /api/docs/upload` in `backend/app/api/router.py`.

## 2. Ingestion Steps
1. File uploaded -> SHA-256 computed -> saved in `multimodal_uploads/`.
2. `pdf_processor.py` extracts text (running OCR if pages are scanned bitmaps).
3. `pii_redactor.py` masks sensitive personal identifiers.
4. Text chunked into 500-character segments with 50-character overlap.
5. `vector_store.add_documents()` embeds chunks and commits to ChromaDB.
