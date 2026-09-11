# 05. Complete System Architecture & Data/Network Flows
**Project:** Sovereign AI Workbench  
**Status:** VERIFIED IMPLEMENTED FROM CODEBASE

---

## 1. Complete Architecture Diagram

```
[ User & Client Tier ]
  Web Browser (Local / Remote) ──► Vanilla HTML5/CSS3/ES6 Dashboard & WebSocket Console
                                            │
                                            ▼
[ Ingress & Gateway Tier (Port 8000) ]
  FastAPI Application Gateway
  ├── Host & CORS Middleware
  ├── Sliding-Window Rate Limiter (60 req/min, burst 10)
  ├── REST Routers (/api/auth, /api/tasks, /api/docs, /api/audit, /api/judge-demo)
  └── WebSocket Connection Hub (/ws/tasks/{id})
                                            │
                                            ▼
[ Identity & Security Governance Tier ]
  ├── Salted Bcrypt Password Hashing & HS256 JWT
  ├── Server-Side JTI Revocation Blocklist (auth.db)
  ├── Role-Based Access Control (admin, lead_engineer, field_inspector, auditor)
  └── PII Redaction Engine (Aadhaar, PAN, SSN, emails, phone numbers)
                                            │
                                            ▼
[ LangGraph Sovereign Agent State Machine ]
  [START] ──► [security_gate] ──► [planner] ──► [executor] ──► [verifier] ──► [synthesizer] ──► [END]
                                                   ▲              │ (Cyclic Retry Loop)
                                                   └──────────────┘
                                            │
                                            ▼
[ Deterministic Safe Tools Sandbox (16 Tools) ]
  ├── RAG Search (ChromaDB + Nomic Embed)
  ├── Multimodal Ingestion (Tesseract OCR v5.4.0 + PyMuPDF)
  ├── Visual Defect Inspection (Local LLaVA v1.6 7B)
  ├── Sandboxed AST Math Calculator (No eval / No shell)
  ├── Tolerance & Evidence Verifier (ISO Operating Limits)
  └── Deliverable Builders (python-docx, openpyxl, python-pptx, ReportLab)
                                            │
                                            ▼
[ Local AI Model Tier (Ollama Port 11434) ]
  ├── LLaMA-3.1 8B (Text reasoning & planning)
  ├── LLaVA v1.6 7B (Visual crack & defect inspection)
  ├── Nomic Embed Text (768-dim dense RAG vectors)
  └── Qwen-2.5 3B (Auxiliary fast reasoning)
                                            │
                                            ▼
[ Persistence & Storage Tier ]
  ├── SQLite auth.db & tasks.db
  ├── ChromaDB Persistent Collection (chroma_db/sovereign_knowledge_base)
  ├── Deliverable Artifacts Storage (generated_artifacts/)
  └── Cryptographic SHA-256 Hash Chain Ledger (audit_trail.jsonl)
```

---

## 2. Complete End-to-End Data Flow

```
1. Ingestion:
   Operator uploads 'scanned_turbine_inspection_report.pdf' (650 KB)
   └── router.py checks format -> saves to multimodal_uploads/ -> logs SHA-256 in tasks.db.

2. Multimodal OCR & Pre-Processing:
   pdf_processor.py checks text density -> detects bitmap scan (<50 chars) -> rasterizes at 300 DPI.
   └── Invokes local Tesseract OCR v5.4.0 -> extracts text string (1,420 characters).
   └── pii_redactor.py scrubs personal identifiers -> replaces with [REDACTED_...].

3. RAG Knowledge Indexing & Retrieval:
   Text chunks (500 chars) embedded via local nomic-embed-text:latest -> persisted in ChromaDB.
   └── Agent issues rag_search("vibration tolerance SOP-IND-702").
   └── ChromaDB returns SOP-IND-702 Section 4.2 clause: "Maximum limit = 5.0 mm/s".

4. Deterministic Calculation:
   Agent extracts measured vibration reading: 8.42 mm/s.
   └── Invokes calculate_expression("(8.42 - 5.0) / 5.0 * 100").
   └── AST Math Sandbox evaluates expression -> returns 68.4% without arithmetic hallucination.

5. Tolerance Auditing & Verification:
   Verifier node compares 8.42 mm/s against 5.0 mm/s threshold.
   └── Flags CRITICAL_TOLERANCE_EXCEEDANCE (+68.4%) -> injects mandatory emergency shutdown clause.

6. Deliverable Compilation & Deep Validation:
   Synthesizer node invokes deliverable generators:
   ├── docx_generator.py -> writes Turbine_Remediation_Approval_Note.docx.
   ├── xlsx_generator.py -> writes calculation sheet with live formulas.
   ├── pptx_generator.py -> writes 16:9 executive briefing deck.
   └── pdf_generator.py  -> writes formal compliance audit report.
   └── validator.py inspects magic bytes (PK), OpenXML schemas -> returns valid.

7. Cryptographic Logging:
   audit_logger.py appends event to audit_trail.jsonl with forward SHA-256 hash.
   └── UI activates download buttons for DOCX, XLSX, PPTX, and PDF artifacts.
```

---

## 3. Network Flow & Sovereignty Boundary

### Local Air-Gapped Mode:
- Ingress: `http://127.0.0.1:8000` (FastAPI) and `ws://127.0.0.1:8000/ws/*` (WebSockets).
- Model Ingress: `http://127.0.0.1:11434` (Ollama HTTP daemon).
- Outbound Egress: **NONE (0.0%)**. All sockets bind strictly to loopback `127.0.0.1`.

### Public Share Mode (Remote Demonstration):
- Remote Client connects to Cloudflare Edge (`https://*.trycloudflare.com`).
- `cloudflared.exe` creates an encrypted reverse proxy pointing **strictly to port 8000**.
- Port 11434 (Ollama), SQLite databases, and Windows filesystem are completely unreachable externally.
- Rate limiter blocks requests exceeding 60 req/min per IP.
