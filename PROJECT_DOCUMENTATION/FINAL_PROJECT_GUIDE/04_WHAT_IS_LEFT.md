# 04. What is Left: Gaps, Remaining Work & Pre-SIH Roadmap
**Project:** Sovereign AI Workbench  
**Status:** OBJECTIVE GAP AUDIT & REMAINING TASKS

---

## 1. What is Complete vs Partial vs Not Implemented

### WHAT IS COMPLETE (Production Quality in Current Codebase):
- 100% Local air-gapped web gateway on `127.0.0.1:8000`
- Zero cloud AI runtime (Ollama local inference on `127.0.0.1:11434`)
- LLaMA-3.1 8B text reasoning and planning
- LLaVA v1.6 7B photographic visual defect inspection
- Nomic Embed Text 768-dimensional dense vector embeddings
- Tesseract OCR v5.4.0 integration for multi-page scanned PDFs
- ChromaDB persistent local RAG knowledge base (30 active chunks)
- Sandboxed AST mathematical calculation engine (zero eval, zero arithmetic hallucination)
- 16 registered safe deterministic tools with path traversal sandboxing
- Programmatic Word (.docx), Excel (.xlsx with formulas), PowerPoint (.pptx), and PDF (.pdf) generators
- Deep Deliverable Validator inspecting OpenXML ZIP structures and magic bytes
- Cryptographic SHA-256 forward hash-chained audit ledger (1,228 entries verified)
- Real-time WebSocket event telemetry streaming to browser console
- In-memory sliding-window rate limiter (60 req/min, burst 10)
- 80/80 automated test suite passing across 9 test files
- 1-Click Judge Demo Mode executing the complete turbine remediation scenario

---

### WHAT IS PARTIAL (Functional but Has Identified Architectural Boundaries):
1. **Dynamic Task-Based Model Routing (`PARTIALLY IMPLEMENTED`)**:
   - *Current State:* Static routing by tool type (vision -> LLaVA, reasoning -> LLaMA, embeddings -> Nomic). Qwen-2.5 3B is loaded in local Ollama but not dynamically invoked.
   - *Missing:* A dynamic complexity classifier that routes simple single-step queries to Qwen-3B and reserves LLaMA-8B for complex multi-variable tasks.
2. **Cursive Handwritten OCR (`PARTIALLY IMPLEMENTED`)**:
   - *Current State:* Tesseract v5.4.0 reads printed text (>99%) and block handwriting (~85%).
   - *Missing:* Degraded, stylized cursive historical maintenance logs exhibit ~35% character error rates. Requires fine-tuning or packaging an on-premise TrOCR model.
3. **Native Engineering CAD Drawing Ingestion (`PARTIALLY IMPLEMENTED`)**:
   - *Current State:* Ingests schematics in PDF, PNG, and JPEG formats.
   - *Missing:* Cannot parse raw vector CAD binaries (.dwg, .dxf, STEP) directly without prior rasterization.
4. **Hierarchical Semantic Document Chunking (`PARTIALLY IMPLEMENTED`)**:
   - *Current State:* Uses 500-character sliding window with 50-character overlap.
   - *Missing:* Header-aware AST chunking that respects document chapter hierarchy (Section 4.1, 4.2).
5. **OS-Level Tool Containerization (`PARTIALLY IMPLEMENTED`)**:
   - *Current State:* Python in-process AST sandboxing and path boundary validation.
   - *Missing:* Ephemeral Docker container isolation per individual tool execution.

---

### WHAT IS NOT IMPLEMENTED (Architectural Exclusions):
1. **Multi-Node Distributed Clustering (`NOT IMPLEMENTED`)**:
   - The workbench is intentionally designed as a standalone, self-contained single-workstation appliance for plant engineers. Multi-node cluster orchestration (Ray, Kubernetes) is out of scope.
2. **Interactive In-UI User Role Management Table (`NOT IMPLEMENTED`)**:
   - User creation and role assignment are handled via registration endpoints and CLI scripts (`bootstrap_admin.py`). A visual admin user table editor is not yet built into the frontend dashboard.

---

## 2. Pre-SIH Remaining Work & Priority Table

| Feature / Task | Current Status | Identified Gap | Remaining Engineering Work | Priority |
|---|---|---|---|---|
| **Dynamic Model Router** | `PARTIAL` | Qwen-3B is idle; LLaMA-8B handles all reasoning | Implement prompt token/complexity classifier to dispatch to Qwen-3B | **HIGH** |
| **In-UI Admin User Table** | `PARTIAL` | Admin role exists; UI lacks user management grid | Build simple administrative user table modal in `frontend/index.html` | **MEDIUM** |
| **Semantic Markdown Chunking**| `PARTIAL` | Fixed 500-char window cuts paragraphs arbitrarily | Split markdown chunks on `##` header boundaries before embedding | **HIGH** |
| **TrOCR Transformer for Cursive**| `NOT IMPLEMENTED` | Tesseract struggles on cursive field handwriting | Package quantized on-premise TrOCR checkpoint for cursive text | **LOW** (Post-SIH) |
| **Multi-Worker Redis Pub/Sub**| `NOT IMPLEMENTED` | WebSockets bounded to single Uvicorn process | Add Redis Pub/Sub broker for horizontal cluster scaling | **LOW** (Enterprise) |
| **Offline Font Bundling** | `PARTIAL` | UI references Google Fonts with local fallbacks | Download Roboto & JetBrains Mono `.woff2` files locally into `/frontend` | **MEDIUM** |
| **Pre-Flight System Check Script**| `PARTIAL` | Manual verification of Ollama/Tesseract | Create `verify_stack.bat` to test Ollama, Tesseract, ChromaDB in 5s | **CRITICAL** |

---

## 3. Top 10 Things to Fix / Polish Before SIH Judging

1. **Create One-Click Pre-Flight Check Script (`verify_stack.bat`)**: A 5-second sanity check script that queries Ollama, checks Tesseract version, verifies ChromaDB, and runs test suite before walking up to judges.
2. **Bundle Local Offline Fonts**: Ensure `frontend/index.html` loads bundled local `.woff2` font files rather than relying on Google Fonts CDN fallbacks when Ethernet is completely unplugged.
3. **Wire Dynamic Routing to Qwen-3B**: Add a simple heuristic classifier in `model_provider.py` so that when a prompt is under 50 words and involves simple translation or classification, it calls `qwen2.5:3b-instruct` to demonstrate multi-model agility.
4. **Implement Section-Aware RAG Chunking**: Enhance `rag/vector_store.py` to chunk on markdown header boundaries (`#`, `##`), improving retrieval precision for multi-clause SOPs.
5. **Add Visual Admin User Grid**: Add an "Admin Panel" tab in `frontend/index.html` allowing an admin to view active users and toggle roles (`lead_engineer`, `auditor`).
6. **Pre-Cache Model Weights in VRAM**: Ensure `start.bat` executes an initial warm-up query to `llama3.1:latest` and `llava:latest` on boot so that the first judge interaction has zero cold-start delay.
7. **Refine Cursive Handwriting Disclaimer**: Clearly explain to judges that Tesseract v5.4.0 is optimized for machine print and block handwriting, while specialized deep cursive HTR is on the post-competition roadmap.
8. **Add Instant Download Zip**: Provide a single button on the dashboard to download all generated deliverables (DOCX, XLSX, PPTX, PDF) in a single compressed ZIP archive.
9. **Add Visual Token Counter in Live Console**: Display real-time token throughput (tokens/second) and GPU/CPU inference latency in the WebSocket telemetry feed.
10. **Practice Live Air-Gap Disconnect**: Rehearse physically disconnecting Wi-Fi/Ethernet in front of judges while the turbine demo runs live to prove zero cloud dependencies.
