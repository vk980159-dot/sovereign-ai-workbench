# 09. Master Study Order for Students & Engineers
**Status:** [VERIFIED]

Follow this 12-level curriculum to master the entire Sovereign AI Workbench codebase:

- **Level 1: Project Basics & Configuration**
  - Read: `PROJECT_DOCUMENTATION/01_BACKEND/02_CONFIG.md` (`backend/app/config.py`)
  - What you learn: Pydantic settings, environment variables, directory initialization, runtime modes.
- **Level 2: Web Gateway & Lifecycles**
  - Read: `PROJECT_DOCUMENTATION/01_BACKEND/01_MAIN_APPLICATION.md` (`backend/app/main.py`)
  - What you learn: FastAPI factory, CORS, rate limiting middleware, startup/shutdown hooks.
- **Level 3: Security & Cryptographic Identity**
  - Read: `PROJECT_DOCUMENTATION/02_AUTH_SECURITY/01_PASSWORD_HASHING.md` & `03_JTI_REVOCATION.md`
  - What you learn: Salted bcrypt hashes, JWT generation, server-side blocklisting, anti-replay defense.
- **Level 4: Tamper-Evident Logging**
  - Read: `PROJECT_DOCUMENTATION/02_AUTH_SECURITY/12_AUDIT_LEDGER.md` (`audit_logger.py`)
  - What you learn: SHA-256 forward hash chains, genesis blocks, mathematical integrity verification.
- **Level 5: AI Model Wrapper & Ollama Integration**
  - Read: `PROJECT_DOCUMENTATION/03_AI_MODELS/00_AI_ARCHITECTURE.md` (`model_provider.py`)
  - What you learn: Local HTTP calls to Ollama on port 11434 for chat, generation, and embeddings.
- **Level 6: Deterministic Safe Tools & AST Sandboxing**
  - Read: `PROJECT_DOCUMENTATION/06_TOOLS/06_CALCULATION_TOOL.md` (`calc_tools.py`)
  - What you learn: Evaluating math safely via AST parsing without dangerous `eval()`.
- **Level 7: Multimodal Processing (OCR & Vision)**
  - Read: `PROJECT_DOCUMENTATION/07_MULTIMODAL/01_TESSERACT_OCR.md` & `04_LLAVA_VISION.md`
  - What you learn: PyMuPDF rasterization, Tesseract CLI, base64 image inspection via LLaVA.
- **Level 8: Knowledge Base & RAG**
  - Read: `PROJECT_DOCUMENTATION/04_RAG_KNOWLEDGE_BASE/00_RAG_OVERVIEW.md` (`vector_store.py`)
  - What you learn: Document chunking, Nomic embeddings, ChromaDB persistence, cosine similarity.
- **Level 9: Agent Orchestration with LangGraph**
  - Read: `PROJECT_DOCUMENTATION/05_AGENT_SYSTEM/07_LANGGRAPH.md` (`graph.py`, `nodes.py`)
  - What you learn: StateGraph state machine, planner, executor, verifier retry loops, synthesizer.
- **Level 10: Deliverable Generation & Deep Validation**
  - Read: `PROJECT_DOCUMENTATION/08_ARTIFACTS/00_ARTIFACT_OVERVIEW.md` (`docx_generator.py`, `validator.py`)
  - What you learn: Building real DOCX/XLSX/PPTX/PDF files and verifying OpenXML ZIP integrity.
- **Level 11: Real-Time Telemetry & UI**
  - Read: `PROJECT_DOCUMENTATION/09_FRONTEND/12_WEBSOCKET_UI.md` (`ws_manager.py`, `index.html`)
  - What you learn: Centralized WebSocket broadcasting, JSON telemetry streaming, live event console.
- **Level 12: SIH Evaluation & Judge Defense**
  - Read: `PROJECT_DOCUMENTATION/14_SIH26117/06_JUDGE_QUESTIONS.md`
  - What you learn: Defending the project in front of technical judges with verifiable architectural facts.
