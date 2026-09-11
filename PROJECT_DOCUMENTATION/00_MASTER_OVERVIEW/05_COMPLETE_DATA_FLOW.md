# 05. Complete Data Flow
**Status:** [VERIFIED]

## End-to-End Industrial Processing Lifecycle

```
[Operator Uploads Scanned PDF / Photo]
             │
             ▼
[FastAPI Ingestion Endpoint: /api/docs/upload]
  1. Validates magic bytes and file extension
  2. Generates SHA-256 checksum -> stages file in multimodal_uploads/
  3. PDFProcessor checks digital text density:
     ├── If vector PDF -> extracts digital text directly via PyMuPDF
     └── If scanned bitmap -> rasterizes pages at 300 DPI -> invokes Tesseract OCR v5.4.0
  4. PIIRedactor scans text -> masks Aadhaar, PAN, SSN with [REDACTED_...]
  5. Document chunks (500 chars) embedded via Nomic Embed Text -> indexed in ChromaDB
             │
             ▼
[User Submits Task Request: /api/tasks]
  1. SecurityGate scans prompt for prompt injection and OS commands
  2. Planner node queries local LLaMA-3.1 -> emits dependency-ordered JSON plan
  3. Executor node iterates steps -> calls registered safe tools:
     ├── rag_search: queries ChromaDB -> retrieves SOP-IND-702 threshold (5.0 mm/s)
     ├── ocr_image_or_pdf: extracts measured reading (8.42 mm/s)
     ├── vision_inspect_image: LLaVA analyzes bearing photo -> identifies fatigue crack
     └── calculate_expression: AST math calculates variance: ((8.42-5.0)/5.0)*100 = 68.4%
  4. Verifier node compares measurements against SOP limits:
     └── Flags CRITICAL_TOLERANCE_EXCEEDANCE (+68.4%) -> enforces emergency shutdown clause
  5. Synthesizer node invokes deliverable generators:
     ├── docx_generator.py -> writes Turbine_Approval_Note.docx
     ├── xlsx_generator.py -> writes Turbine_Calculations.xlsx with live formulas
     ├── pptx_generator.py -> writes Turbine_Briefing.pptx
     └── pdf_generator.py  -> writes Turbine_Audit_Report.pdf
  6. DeliverableValidator performs deep inspection (magic bytes, OpenXML ZIP structure)
  7. Cryptographic AuditLogger appends entry to audit_trail.jsonl with forward SHA-256 hash
  8. WebSocket streams live completion event to frontend dashboard
```
