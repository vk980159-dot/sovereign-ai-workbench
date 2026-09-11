# 01. Master Source File Index
**Status:** [VERIFIED]

| Source File | Purpose | Main Classes | Main Functions | Used By | SIH Requirement |
|-------------|---------|--------------|----------------|---------|-----------------|
| `backend/app/main.py` | FastAPI entrypoint & lifecycles | - | `create_app`, `lifespan` | Uvicorn / start.bat | #1, #2 |
| `backend/app/config.py` | Settings & runtime detection | `Settings` | `get_runtime_mode` | All backend modules | #1, #2 |
| `backend/app/api/router.py` | RESTful API endpoints | - | Route handlers | Frontend / Clients | #1, #29 |
| `backend/app/api/models.py` | Pydantic request/response schemas| Pydantic models | - | `router.py`, `graph.py` | #1 |
| `backend/app/api/ws_manager.py` | WebSocket telemetry manager | `ConnectionManager` | `connect`, `broadcast` | Graph nodes, UI | #29 |
| `backend/app/security/auth.py` | Password hashing, JWT, RBAC | `UserAuthManager` | `verify_password`, `create_token` | `router.py` | #1 |
| `backend/app/security/audit_logger.py` | Cryptographic SHA-256 ledger | `AuditLogger` | `log_event`, `verify_integrity` | Security gate, tools | #30 |
| `backend/app/security/pii_redactor.py` | PII regex scrubber | `PIIRedactor` | `redact_text` | Ingestion, RAG | #3, #20 |
| `backend/app/security/rate_limiter.py` | Sliding-window IP rate limiter | `SlidingWindowRateLimiter` | `is_allowed`, `dispatch` | `main.py` middleware | #1, #30 |
| `backend/app/agents/graph.py` | LangGraph state machine | - | `create_agent_graph`, `run_agent_task`| `router.py` | #7, #8 |
| `backend/app/agents/nodes.py` | LangGraph node callbacks | - | `planner_node`, `executor_node`, etc. | `graph.py` | #7, #8, #13 |
| `backend/app/agents/planner.py` | Task decomposition & JSON plan | `TaskPlanner` | `generate_plan` | `nodes.py` | #7 |
| `backend/app/agents/executor.py` | Tool dispatcher & observation | `StepExecutor` | `execute_plan_step` | `nodes.py` | #8 |
| `backend/app/agents/verifier.py` | Tolerance & evidence auditor | `OutputVerifier` | `verify_state` | `nodes.py` | #13, #26 |
| `backend/app/agents/security_gate.py`| Pre-execution prompt sanitizer | `SecurityGate` | `evaluate_prompt` | `nodes.py` | #2, #28 |
| `backend/app/agents/model_provider.py`| Local Ollama HTTP client | `OllamaModelProvider` | `generate`, `chat`, `embed` | Planner, RAG | #4, #5 |
| `backend/app/agents/tools/__init__.py`| Tool registry & whitelist | `BaseTool` | `register_tool`, `get_tool` | `executor.py` | #9, #10 |
| `backend/app/agents/tools/calc_tools.py`| AST math & unit converter | - | `calculate_expression`, `unit_conv` | `TOOL_REGISTRY` | #10, #26 |
| `backend/app/agents/tools/doc_tools.py`| Document reader & RAG search | - | `rag_search`, `read_document` | `TOOL_REGISTRY` | #9, #12 |
| `backend/app/agents/multimodal/ocr_provider.py`| Tesseract OCR v5.4.0 wrapper | `TesseractOCRProvider` | `extract_text` | Tools, PDFProcessor | #14, #15 |
| `backend/app/agents/multimodal/vision_provider.py`| Ollama LLaVA v1.6 wrapper | `LocalVisionProvider` | `inspect_image` | Tools | #18, #19 |
| `backend/app/agents/multimodal/pdf_processor.py`| PyMuPDF hybrid rasterizer | `PDFProcessor` | `process_pdf` | Uploads, Tools | #14, #15 |
| `backend/app/agents/deliverables/docx_generator.py`| Word approval memo builder | `DOCXGenerator` | `generate_approval_note` | Tools | #22, #23 |
| `backend/app/agents/deliverables/xlsx_generator.py`| Excel formula sheet builder | `XLSXGenerator` | `generate_calculation_sheet`| Tools | #11, #24 |
| `backend/app/agents/deliverables/pptx_generator.py`| PowerPoint briefing builder | `PPTXGenerator` | `generate_briefing` | Tools | #25 |
| `backend/app/agents/deliverables/pdf_generator.py`| ReportLab PDF audit builder | `PDFGenerator` | `generate_compliance_report`| Tools | #23 |
| `backend/app/agents/deliverables/validator.py`| Deep OpenXML ZIP validator | `DeliverableValidator` | `validate_artifact` | Synthesizer, Tools | #28 |
| `backend/app/database/task_store.py`| SQLite tasks.db DAO | `TaskStore` | `create_task`, `add_event` | `router.py`, `graph.py` | #1 |
| `backend/app/rag/vector_store.py`| ChromaDB persistent client | `ChromaVectorStore` | `similarity_search`, `add_docs` | Tools, Uploads | #12, #20 |
| `frontend/index.html` | Vanilla single-page UI | - | `submitTask`, `triggerJudgeDemo` | Browser | #1, #29 |
| `scripts/public_share_runner.py` | Cloudflare tunnel supervisor | `PublicShareManager` | `start_tunnel`, `stop_tunnel` | Operators | Remote Share |
