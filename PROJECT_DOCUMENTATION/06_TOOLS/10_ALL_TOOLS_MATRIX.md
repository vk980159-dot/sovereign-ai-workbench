# 10. Master 16 Tools Specification Matrix
**Status:** [VERIFIED]

| # | Tool Name | Implementing File | Input Types | Output Type | Security Boundary |
|---|-----------|-------------------|-------------|-------------|-------------------|
| 1 | `rag_search` | `doc_tools.py` | `str, int` | `List[SearchResult]` | Local ChromaDB only |
| 2 | `read_document` | `doc_tools.py` | `str` | `str` | Sandboxed directories |
| 3 | `summarize_document` | `doc_tools.py` | `str, int` | `str` | Local LLaMA-3.1 |
| 4 | `calculate_expression`| `calc_tools.py`| `str` | `dict (float)`| AST parser (No eval) |
| 5 | `unit_conversion` | `calc_tools.py`| `float, str, str` | `dict` | Deterministic matrix |
| 6 | `statistical_summary`| `calc_tools.py`| `List[float]` | `dict` | Deterministic math |
| 7 | `ocr_image_or_pdf` | `multimodal_tools.py` | `str, str` | `OCRResult` | Local Tesseract CLI |
| 8 | `vision_inspect_image`| `multimodal_tools.py`| `str, str` | `VisionResult`| Local LLaVA v1.6 |
| 9 | `extract_document_tables`| `multimodal_tools.py`| `str` | `List[dict]` | PyMuPDF sandboxed |
| 10 | `verify_claim_against_evidence`| `verify_tools.py` | `str, str` | `VerificationResult`| LLaMA + Evidence anchor |
| 11 | `verify_tolerance_limits`| `verify_tools.py` | `str, float, float`| `dict` | Deterministic comparator |
| 12 | `generate_docx_approval_note`| `deliverable_tools.py` | `dict` | `str (filepath)` | python-docx |
| 13 | `generate_xlsx_calculation_sheet`| `deliverable_tools.py`| `dict` | `str (filepath)` | openpyxl (formulas) |
| 14 | `generate_pptx_briefing`| `deliverable_tools.py` | `dict` | `str (filepath)` | python-pptx (16:9) |
| 15 | `generate_pdf_compliance_report`| `deliverable_tools.py` | `dict` | `str (filepath)` | ReportLab flowables |
| 16 | `save_text_artifact` | `artifact_tools.py` | `str, str` | `str (filepath)` | Sandboxed artifacts dir |
