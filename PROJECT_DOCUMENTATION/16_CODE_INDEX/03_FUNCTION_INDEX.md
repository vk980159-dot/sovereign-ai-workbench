# 03. Master Function Index
**Status:** [VERIFIED]

| Function Name | Source File | Purpose | Caller | Input | Output |
|---------------|-------------|---------|--------|-------|--------|
| `verify_password` | `auth.py` | Verifies bcrypt salted hash | `login_for_access_token` | `str, str` | `bool` |
| `create_access_token` | `auth.py` | Signs HS256 JWT with `jti` | `login_for_access_token` | `dict, timedelta` | `str` |
| `revoke_token` | `auth.py` | Adds `jti` to blocklist table | `logout` route | `str` | `bool` |
| `evaluate_prompt` | `security_gate.py` | Detects prompt injection/shell | `security_gate_node` | `str` | `SecurityEvaluation` |
| `generate_plan` | `planner.py` | Decomposes prompt to JSON steps | `planner_node` | `str, str, list` | `List[PlanStep]` |
| `execute_plan_step` | `executor.py` | Executes tool step from registry | `executor_node` | `PlanStep, AgentState` | `StepObservation` |
| `verify_state` | `verifier.py` | Audits measurements vs standards | `verifier_node` | `AgentState` | `VerificationResult` |
| `calculate_expression`| `calc_tools.py`| Evaluates math safely via AST | `TOOL_REGISTRY` | `str` | `dict (float)` |
| `extract_text` | `ocr_provider.py` | Runs Tesseract v5.4.0 CLI | `multimodal_tools.py` | `str, str` | `OCRResult` |
| `inspect_image` | `vision_provider.py`| Calls Ollama LLaVA with base64 | `multimodal_tools.py` | `str, str` | `VisionResult` |
| `process_pdf` | `pdf_processor.py`| PyMuPDF vector/raster check | `router.py`, Tools | `str` | `ProcessedDocument`|
| `generate_approval_note`| `docx_generator.py`| Builds styled corporate DOCX | `deliverable_tools.py`| `dict` | `str (filepath)` |
| `generate_calculation_sheet`| `xlsx_generator.py`| Builds XLSX with live formulas| `deliverable_tools.py`| `dict` | `str (filepath)` |
| `validate_artifact` | `validator.py` | Validates magic bytes & OpenXML | Synthesizer, Tools | `str` | `ValidationResult` |
| `similarity_search` | `vector_store.py` | Cosine similarity search | `rag_search` tool | `str, int` | `List[SearchResult]`|
| `log_event` | `audit_logger.py` | Appends SHA-256 chained entry | Nodes, Tools | `str, str, dict` | `str (hash)` |
| `verify_integrity` | `audit_logger.py` | Re-hashes all ledger entries | `verify_audit_trail` route| None | `dict` |
| `trigger_judge_demo` | `router.py` | One-click full turbine scenario | Frontend UI | None | `dict` |
