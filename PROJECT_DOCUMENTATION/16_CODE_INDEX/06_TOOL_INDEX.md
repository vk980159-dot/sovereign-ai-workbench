# 06. Master Registered Tool Index
**Status:** [VERIFIED]

| # | Tool Identifier | Category | Underlying Module | Security Sandbox |
|---|-----------------|----------|-------------------|------------------|
| 1 | `rag_search` | Knowledge | `tools/doc_tools.py` | Local ChromaDB vector query |
| 2 | `read_document` | Filesystem | `tools/doc_tools.py` | Sandboxed uploads & demo dirs |
| 3 | `summarize_document` | Summarization | `tools/doc_tools.py` | Local LLaMA-3.1 inference |
| 4 | `calculate_expression` | Math | `tools/calc_tools.py` | Sandboxed AST parser (No eval) |
| 5 | `unit_conversion` | Engineering | `tools/calc_tools.py` | Deterministic conversion matrix |
| 6 | `statistical_summary` | Statistics | `tools/calc_tools.py` | Deterministic array metrics |
| 7 | `ocr_image_or_pdf` | Multimodal | `tools/multimodal_tools.py`| Local Tesseract v5.4.0 CLI |
| 8 | `vision_inspect_image` | Multimodal | `tools/multimodal_tools.py`| Local Ollama LLaVA v1.6 |
| 9 | `extract_document_tables`| Multimodal | `tools/multimodal_tools.py`| PyMuPDF gridline extractor |
| 10 | `verify_claim_against_evidence`| Verification | `tools/verify_tools.py` | LLaMA + Evidence citation anchor |
| 11 | `verify_tolerance_limits`| Verification | `tools/verify_tools.py` | Deterministic tolerance comparator |
| 12 | `generate_docx_approval_note`| Deliverables | `tools/deliverable_tools.py`| python-docx builder |
| 13 | `generate_xlsx_calculation_sheet`| Deliverables | `tools/deliverable_tools.py`| openpyxl builder with formulas |
| 14 | `generate_pptx_briefing`| Deliverables | `tools/deliverable_tools.py`| python-pptx widescreen builder |
| 15 | `generate_pdf_compliance_report`| Deliverables | `tools/deliverable_tools.py`| ReportLab flowable builder |
| 16 | `save_text_artifact` | Deliverables | `tools/artifact_tools.py` | Sandboxed generated_artifacts/ |
