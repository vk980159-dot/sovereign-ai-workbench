# 00. Safe Deterministic Tools Overview
**Status:** [VERIFIED]

## Whitelisted Tool Registry
The agent interacts with the physical computer strictly through **16 registered safe tools** in `backend/app/agents/tools/__init__.py`. Arbitrary OS shell access and unsanitized Python code execution are strictly prohibited.

## Tool Categories
1. **Document & RAG Tools:** `rag_search`, `read_document`, `summarize_document`.
2. **Deterministic Math Tools:** `calculate_expression`, `unit_conversion`, `statistical_summary`.
3. **Multimodal Tools:** `ocr_image_or_pdf`, `vision_inspect_image`, `extract_document_tables`.
4. **Verification Tools:** `verify_claim_against_evidence`, `verify_tolerance_limits`.
5. **Deliverable Tools:** `generate_docx_approval_note`, `generate_xlsx_calculation_sheet`, `generate_pptx_briefing`, `generate_pdf_compliance_report`, `save_text_artifact`.
