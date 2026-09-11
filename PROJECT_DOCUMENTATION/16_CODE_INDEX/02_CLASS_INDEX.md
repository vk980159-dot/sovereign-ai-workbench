# 02. Master Class Index
**Status:** [VERIFIED]

| Class | Source File | Purpose | Key Methods | Used By |
|-------|-------------|---------|-------------|---------|
| `Settings` | `config.py` | Pydantic configuration | `get_runtime_mode()` | Entire backend |
| `ConnectionManager` | `ws_manager.py` | WebSocket hub | `connect`, `disconnect`, `broadcast` | Router, Nodes |
| `AuditLogger` | `audit_logger.py` | SHA-256 hash-chain ledger | `log_event`, `verify_integrity` | Security gate, Tools |
| `PIIRedactor` | `pii_redactor.py` | Regex PII sanitizer | `redact_text` | Router, PDFProcessor |
| `SlidingWindowRateLimiter`| `rate_limiter.py`| DoS prevention middleware | `is_allowed` | FastAPI middleware |
| `SecurityGate` | `security_gate.py` | Prompt injection defense | `evaluate_prompt` | `security_gate_node` |
| `TaskPlanner` | `planner.py` | Sub-goal decomposition | `generate_plan` | `planner_node` |
| `StepExecutor` | `executor.py` | Tool execution & timing | `execute_plan_step` | `executor_node` |
| `OutputVerifier` | `verifier.py` | Tolerance compliance check | `verify_state` | `verifier_node` |
| `OllamaModelProvider` | `model_provider.py`| Local Ollama HTTP client | `generate`, `chat`, `embed` | Planner, RAG |
| `BaseTool` | `tools/base.py` | Abstract tool base class | `run` | All 16 tools |
| `TesseractOCRProvider` | `ocr_provider.py` | Tesseract v5.4.0 CLI wrapper| `extract_text` | Tools, PDFProcessor |
| `LocalVisionProvider` | `vision_provider.py`| Ollama LLaVA client | `inspect_image` | Tools |
| `PDFProcessor` | `pdf_processor.py` | PyMuPDF hybrid parser | `process_pdf` | Uploads, Tools |
| `DOCXGenerator` | `docx_generator.py` | Word approval note creator | `generate_approval_note` | Tools |
| `XLSXGenerator` | `xlsx_generator.py` | Excel formula workbook creator| `generate_calculation_sheet`| Tools |
| `PPTXGenerator` | `pptx_generator.py` | PowerPoint presentation creator| `generate_briefing` | Tools |
| `PDFGenerator` | `pdf_generator.py` | PDF compliance report creator| `generate_compliance_report`| Tools |
| `DeliverableValidator` | `validator.py` | OpenXML ZIP & magic byte check| `validate_artifact` | Tools, Synthesizer |
| `TaskStore` | `task_store.py` | SQLite DAO for tasks.db | `create_task`, `add_event` | Router, Graph |
| `ChromaVectorStore` | `vector_store.py` | ChromaDB persistent store | `similarity_search`, `add_docs`| Tools, Router |
