# 11. "Why Did We Add This?" - Component Justification Index
**Status:** [VERIFIED]

| Component / Feature | Why Did We Add It? | What Problem Does It Solve? | What Would Happen Without It? | Implementing File & Function | SIH Requirement |
|---------------------|--------------------|-----------------------------|-------------------------------|------------------------------|-----------------|
| **Local Ollama Daemon** | To execute open-weight models on host PC | Eliminates reliance on cloud AI APIs | Confidential data leaked to cloud; air-gap broken | `agents/model_provider.py` | #1, #2, #4 |
| **LangGraph StateGraph** | Structured agent finite state machine | Prevents uncontrolled LLM loops & rambling | Unpredictable agent behavior; no verification retry | `agents/graph.py:create_agent_graph()` | #7, #8, #13 |
| **Tesseract OCR v5.4.0** | To digitize paper inspection logs | Extracts text from scanned bitmap PDFs | System blind to scanned paper work orders | `agents/multimodal/ocr_provider.py` | #14, #15 |
| **Local LLaVA v1.6** | Photographic visual defect analysis | Diagnoses physical cracks and thermal wear | Cannot analyze machinery photos | `agents/multimodal/vision_provider.py` | #18, #19 |
| **ChromaDB Vector Store** | Persistent local document retrieval | Grounds answers in plant SOPs & manuals | LLM hallucinates tolerances and procedures | `rag/vector_store.py:ChromaVectorStore` | #12, #20, #21 |
| **AST Math Evaluator** | Deterministic numeric calculation | Eliminates LLM arithmetic hallucinations | Agent calculates 8.42 - 5.0 incorrectly | `agents/tools/calc_tools.py:calculate_expression()` | #10, #26 |
| **Deliverable Validator** | Validates generated Office/PDF binaries | Ensures files open cleanly without corruption | User downloads corrupted or empty files | `agents/deliverables/validator.py` | #23, #24, #28 |
| **Cryptographic Hash Chain**| Tamper-evident audit logging | Proves mathematically that logs were not altered | Malicious actors can doctor incident logs | `security/audit_logger.py:log_event()` | #30 |
| **PII Redaction Engine** | Masks sensitive identity numbers | Prevents indexing Aadhaar/PAN/SSN in RAG | Privacy law violations (DPDP Act, GDPR) | `security/pii_redactor.py:redact_text()` | #3, #20 |
| **JWT JTI Revocation** | Server-side token blocklisting | Prevents replay attacks after user logout | Revoked tokens remain valid until expiry | `security/auth.py:revoke_token()` | #1, #30 |
| **Security Gate Node** | Pre-execution prompt sanitization | Defends against prompt injection & shell commands| Malicious prompt executes local OS commands | `agents/security_gate.py:evaluate_prompt()` | #2, #28 |
| **Sliding Rate Limiter** | Restricts IP request velocity | Prevents DoS attacks and GPU queue exhaustion | Host workstation freezes under request flood | `security/rate_limiter.py` | #1, #30 |
| **WebSocket Hub** | Real-time agent thought streaming | Eliminates continuous HTTP polling | Operator cannot see what agent is doing | `api/ws_manager.py:broadcast_event()` | #29 |
| **1-Click Judge Demo** | Automated end-to-end demonstration | Lets judges evaluate full stack in 15 seconds | Complex manual setup required for demo | `api/router.py:trigger_judge_demo()` | All 30 |
