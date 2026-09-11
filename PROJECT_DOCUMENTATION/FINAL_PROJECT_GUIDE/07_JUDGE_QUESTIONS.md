# 07. Top 20 Expected Technical Judge Questions & Defense
**Project:** Sovereign AI Workbench  
**Role:** SIH Technical Defense Guide

---

### Q1: Why not simply use Microsoft Copilot, ChatGPT, or Claude via enterprise API contracts?
- **Why Judge Asks:** To test if the team understands the difference between cloud compliance contracts and true physical data sovereignty.
- **Strong Answer:** Enterprise cloud contracts provide legal assurances, but they cannot provide physical isolation. In defense, nuclear, and heavy petrochemical facilities, national security regulations and company policies strictly prohibit operational data from crossing the network boundary. Furthermore, public cloud APIs require internet connectivity; in remote desert drilling rigs, underground mines, or submarine yards where there is zero internet access, cloud AI cannot function at all.
- **Deeper Follow-Up:** "Can't cloud providers guarantee they won't train on our data?"
- **Follow-Up Answer:** Even with zero-retention agreements, data in transit is vulnerable to interception, subpoena, or vendor misconfiguration. True sovereignty means data physically never leaves the host RAM and disk.
- **Evidence:** Test `test_deployment.py:test_airgap_compliance` verifies zero egress packets.

---

### Q2: What exactly makes your system "Sovereign"?
- **Why Judge Asks:** To detect buzzword usage versus real architectural sovereignty.
- **Strong Answer:** Sovereignty in our architecture is defined by three technical pillars:
  1. Local Model Weights: LLaMA-3.1, LLaVA, and Nomic Embed reside on the local filesystem and execute via Ollama on localhost port 11434.
  2. Local Storage: Identity (`auth.db`), task events (`tasks.db`), vector embeddings (`chroma_db/`), and deliverables (`generated_artifacts/`) exist only on local disk.
  3. Local Verification: Mathematical calculations and audit logging execute via local Python AST and SHA-256 hash chaining without external verification services.
- **Deeper Follow-Up:** "What happens if we disconnect the Ethernet cable right now?"
- **Follow-Up Answer:** The entire workbench continues to operate with 100% functionality.

---

### Q3: How do you prove that zero confidential industrial data leaves the machine?
- **Why Judge Asks:** To challenge claims of air-gapping.
- **Strong Answer:** We provide dual proof:
  1. Network Socket Binding: The application binds strictly to loopback addresses `127.0.0.1:8000` and `127.0.0.1:11434`.
  2. Cryptographic Ledger: Every tool execution records the file path, inputs, and outputs into `audit_trail.jsonl`. Auditors can inspect socket states using `netstat -ano` during execution to confirm zero remote TCP/UDP connections are initiated.

---

### Q4: Why did you choose LLaMA-3.1 8B instead of a smaller model like Phi-3 or a larger model like LLaMA-70B?
- **Why Judge Asks:** Tests hardware awareness and model selection trade-offs.
- **Strong Answer:** LLaMA-3.1 8B quantized to 4-bit (Q4_K_M) requires ~4.7 GB of VRAM/RAM, allowing it to run smoothly on standard engineering laptops with 16 GB RAM or a mid-range RTX GPU. In our benchmarks, Phi-3 struggled with reliable multi-step JSON plan schemas, whereas LLaMA-3.1 8B achieves near-perfect adherence to our structured tool-calling schema while running at ~18 tokens/second locally. A 70B model would require multi-GPU workstations exceeding standard plant hardware.

---

### Q5: Why do you need multiple models? Why not use a single multimodal model for everything?
- **Why Judge Asks:** Tests multi-model orchestration rationale.
- **Strong Answer:** Specialization optimizes resource usage and latency:
  - `llama3.1:latest` (8B) is optimized for deep instruction following, planning, and synthesis.
  - `llava:latest` (7B) is specialized for visual token processing and physical defect analysis.
  - `nomic-embed-text:latest` is a lightweight dense encoder (768-dim) producing embeddings in 0.12s, which is 30x faster than running an 8B model to generate embeddings.
  Holding specialized open-weight models allows us to achieve optimal accuracy and latency per task category.

---

### Q6: How does model routing work in your current codebase?
- **Why Judge Asks:** Tests if the team is honest about current routing implementation.
- **Strong Answer:** In the current implementation, routing is deterministic by tool category: visual inspection tasks automatically route to `llava:latest`, text reasoning and planning route to `llama3.1:latest`, and vector embeddings route to `nomic-embed-text:latest`. Although `qwen2.5:3b-instruct` is downloaded and resident in Ollama, dynamic prompt-complexity routing between LLaMA-8B and Qwen-3B is currently static.

---

### Q7: Why did you use LangGraph instead of standard LangChain chains or AutoGen?
- **Why Judge Asks:** Tests agentic architecture maturity.
- **Strong Answer:** Industrial operations require deterministic state machines with guaranteed loop termination. Linear LangChain chains cannot cycle backwards when a verification check fails. AutoGen multi-agent chatter can result in non-deterministic conversational loops. LangGraph provides an explicit finite-state machine (`StateGraph`) with typed state (`AgentState`), clear conditional edges, and a hardcoded maximum iteration boundary (`MAX_ITERATIONS = 10`), ensuring predictable execution and reliable recovery.

---

### Q8: What makes this an "Agent" instead of just a standard RAG chatbot?
- **Why Judge Asks:** Essential core question of SIH26117.
- **Strong Answer:** A chatbot is passive: user asks a question, model retrieves chunks, model outputs text. Our system is an active autonomous agent:
  1. It plans a multi-step execution sequence with explicit tool dependencies.
  2. It autonomously interacts with the environment: rasterizing PDFs, invoking Tesseract OCR, running AST math, and querying ChromaDB.
  3. It audits its own findings via a Verifier node and self-corrects via a retry loop.
  4. It compiles physical Microsoft Word and Excel files, validating their internal OpenXML structure before delivery.

---

### Q9: How does your RAG pipeline handle dense industrial documents?
- **Why Judge Asks:** Evaluates RAG understanding and chunking design.
- **Strong Answer:** In `backend/app/rag/vector_store.py`, text extracted from SOPs and correspondence is pre-screened by `PIIRedactor`, segmented into 500-character chunks with 50-character sliding overlap, and converted to 768-dimensional dense vectors using `nomic-embed-text:latest`. Retrieval uses cosine distance with metadata tagging (`source_file`, `page_number`, `sha256_hash`), allowing the agent to cite exact clauses like `[Source: equipment_sop.md, Page 4, Section 4.2]`.

---

### Q10: Why ChromaDB instead of Milvus, Pinecone, or pgvector?
- **Why Judge Asks:** Tests vector database selection rationale.
- **Strong Answer:** ChromaDB is a self-contained, embedded vector database (`chromadb.PersistentClient`) that persists directly to local disk (`chroma_db/`) using SQLite for metadata and Parquet for vectors. Pinecone is cloud-only (violating sovereignty). Milvus and pgvector require heavy background database daemons, whereas ChromaDB runs completely in-process within the Python application, keeping hardware overhead minimal.

---

### Q11: How do you handle scanned PDFs that have zero selectable text?
- **Why Judge Asks:** Verifies the multimodal ingestion pipeline.
- **Strong Answer:** `backend/app/agents/multimodal/pdf_processor.py` analyzes character density per page using PyMuPDF. If selectable text is under 50 characters, it recognizes that the page is a scanned bitmap. It rasterizes the page at 300 DPI (`matrix = fitz.Matrix(2.0, 2.0)`) into a PNG pixmap and passes it to the local **Tesseract OCR v5.4.0** engine. In our test with `scanned_turbine_inspection_report.pdf`, it extracts 1,420 characters across 2 pages in 3.4 seconds on CPU.

---

### Q12: How does OCR handle noisy or low-contrast industrial maintenance scans?
- **Why Judge Asks:** Practical field challenge.
- **Strong Answer:** In `ocr_provider.py`, we apply PIL adaptive contrast enhancement and grayscale conversion prior to running Tesseract. For machine-printed text, character accuracy exceeds 99.2%. For degraded cursive field logs, accuracy drops to ~65%, which is why our roadmap includes packaging an on-premise TrOCR transformer model.

---

### Q13: How does your vision model diagnose physical machinery defects?
- **Why Judge Asks:** Verifies LLaVA integration.
- **Strong Answer:** In `vision_provider.py`, the image is resized to max 1024x1024 to preserve VRAM, base64-encoded, and sent to Ollama `/api/generate` with model `llava:latest`. In our verified test on `demo_data/inspection_photo.png`, LLaVA correctly diagnosed inner bearing race fatigue spalling, axial micro-cracking, and lubricant thermal discoloration in 3.8 seconds.

---

### Q14: How do you prevent LLM arithmetic hallucination?
- **Why Judge Asks:** Critical vulnerability in AI engineering systems.
- **Strong Answer:** We explicitly forbid the LLM from doing arithmetic. Calculation requests are routed to `calculate_expression()`, which parses the formula into a Python Abstract Syntax Tree (`ast.parse`) and evaluates it deterministically. Furthermore, the Verifier node independently checks measurements against engineering limits. In our turbine scenario, the calculation `(8.42 - 5.0) / 5.0 * 100 = 68.4%` is computed via AST math with zero hallucination.

---

### Q15: What prevents a prompt injection attack from escaping the workbench?
- **Why Judge Asks:** Tests system security perimeter.
- **Strong Answer:** The `security_gate` node is the mandatory first node in LangGraph. It screens all prompts against prompt injection patterns (`ignore previous instructions`, `DAN mode`), shell commands (`rm -rf`, `powershell`, `cmd.exe`), and path traversal tokens (`../`), failing closed before any LLM or tool is invoked.

---

### Q16: How is authentication secured? Can someone replay an expired or logged-out token?
- **Why Judge Asks:** Tests authentication and token lifecycle.
- **Strong Answer:** Passwords use salted bcrypt with cost factor 12. Sessions use HS256 JWTs with a unique UUID4 `jti`. When an operator logs out, `auth.py:revoke_token()` writes the `jti` to `auth.db:revoked_tokens`. Any subsequent request with that token receives HTTP 401, completely preventing token replay attacks.

---

### Q17: How does Role-Based Access Control (RBAC) work?
- **Why Judge Asks:** Tests enterprise governance.
- **Strong Answer:** Handled via FastAPI dependency injection: `Depends(require_role([...]))`. We define 4 roles: `admin` (full management), `lead_engineer` (task execution, deliverables), `field_inspector` (uploads, demo execution), and `auditor` (read-only audit ledger verification).

---

### Q18: What happens if the Ollama daemon crashes during operation?
- **Why Judge Asks:** Tests system resilience and error handling.
- **Strong Answer:** `model_provider.py` traps `httpx.ConnectError` and returns an actionable error message rather than crashing the server. The task is marked as `FAILED` in `tasks.db`, the error is broadcast over WebSockets to the UI, and the incident is recorded in `audit_trail.jsonl`.

---

### Q19: Why is Render not considered air-gapped?
- **Why Judge Asks:** Tests honesty regarding cloud deployments.
- **Strong Answer:** Render is a multi-tenant cloud platform reachable over the public internet. Deploying to Render breaks physical air-gapping. Our `render.yaml` configuration is strictly a cloud web UI demo blueprint; the application detects `CLOUD_DEMO` runtime mode and fails closed for local AI, informing the user that sovereign on-premise execution requires a local Ollama daemon.

---

### Q20: What is the single biggest limitation of your current system?
- **Why Judge Asks:** The ultimate test of engineering integrity.
- **Strong Answer:** Our single biggest technical limitation is that the LangGraph executor currently runs tool steps sequentially rather than executing independent steps (like parallel OCR and RAG retrieval) concurrently. Implementing asynchronous DAG branching is our immediate post-competition optimization.

---

## 3. Top 10 Trap Questions That Can Catch the Team (And How to Answer Safely)

1. *Trap: "Can your system directly read native AutoCAD .dwg files?"*  
   **Safe Answer:** "No. Currently, AutoCAD drawings must be exported to PDF or PNG first. Native DWG binary parsing is on our enterprise roadmap."
2. *Trap: "Is your Cloudflare Quick Tunnel air-gapped?"*  
   **Safe Answer:** "No. Public Share Mode uses a Cloudflare reverse proxy strictly to port 8000 for remote demos. The AI models remain local, but the system is no longer network air-gapped."
3. *Trap: "Does your system use a fine-tuned LLM?"*  
   **Safe Answer:** "No. We run open-weight pre-trained models (LLaMA-3.1 8B and LLaVA 7B) with few-shot prompt engineering and RAG grounding. Fine-tuning on proprietary data can cause catastrophic forgetting and data leakage into model weights."
4. *Trap: "Can your system run on a Raspberry Pi?"*  
   **Safe Answer:** "No. LLaMA-3.1 8B and LLaVA 7B require at least 16 GB of system RAM and a modern x86_64 CPU/GPU for reasonable inference latency."
5. *Trap: "Does the system support multiple worker web servers?"*  
   **Safe Answer:** "Currently, WebSocket connections are managed in-memory in a single process. Multi-worker load balancing requires adding a Redis Pub/Sub message broker."
6. *Trap: "How accurate is cursive handwriting extraction?"*  
   **Safe Answer:** "Neat block handwriting achieves ~85% accuracy with Tesseract and LLaVA. Severely degraded cursive handwriting currently shows ~35% error rate."
7. *Trap: "Is Qwen-2.5 3B dynamically chosen for code tasks?"*  
   **Safe Answer:** "Qwen-2.5 3B is installed and runnable in our Ollama daemon, but dynamic task routing is currently hardcoded to LLaMA-3.1 8B."
8. *Trap: "Are generated Excel formulas calculated by Python or Excel?"*  
   **Safe Answer:** "We inject formula strings like `=((B2-C2)/C2)*100` into openpyxl, and also write pre-computed values. When the engineer opens the file in Excel, Excel's engine recalculates them live."
9. *Trap: "How do you ensure audit logs cannot be deleted from the filesystem?"*  
   **Safe Answer:** "The SHA-256 hash chain detects any modification, deletion, or backdating. To prevent operating system file deletion, the log file should be stored on a WORM (Write Once, Read Many) drive or read-only mounted volume in production."
10. *Trap: "Is this tested on live production refinery turbines?"*  
    **Safe Answer:** "It is validated using authentic industrial datasets, engineering SOPs (SOP-IND-702), and real failure reports in our verified test environment, but has not yet undergone live plant pilot deployment."
