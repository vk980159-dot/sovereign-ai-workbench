# 00. Multimodal Ingestion & Vision Architecture Overview
**Status:** [VERIFIED]

## Multimodal Engine Components
The multimodal subsystem enables the Sovereign AI Workbench to ingest and understand non-textual engineering assets without sending files to external cloud vision APIs:
1. **Tesseract OCR v5.4.0 Engine:** Digitize multi-page scanned PDF documents and equipment tags.
2. **PyMuPDF (`fitz`) Hybrid Pipeline:** Distinguishes digital vector PDFs from scanned bitmap PDFs.
3. **Local LLaVA v1.6 7B Vision Model:** Visual question answering for machinery defect photos.
4. **Table Extractor:** Discovers and formats structured tabular data from PDF pages.
