# 08. Complete Multimodal Ingestion Trace
**Status:** [VERIFIED]

```
[Incoming Document: Scanned PDF / Image]
                  │
                  ▼
         [PyMuPDF Inspector]
           ├── Digital Vector PDF? ──► Extract Text Directly
           └── Scanned Bitmap PDF? ──► Rasterize at 300 DPI
                                              │
                                              ▼
                                     [Tesseract OCR v5.4.0]
                                              │
                                              ▼
                                    Extracted Text Stream
                                              │
                                              ▼
                                     [PIIRedactor Engine]
                                              │
                                              ▼
                                  [ChromaDB Local RAG]
```
