# 04. Complete System Architecture
**Status:** [VERIFIED]

## 7-Tier Architecture Diagram

```
[ Tier 1: Client UI ]
  Vanilla HTML5 / CSS3 / ES6 Browser Dashboard & WebSocket Console
          │
          ▼
[ Tier 2: Ingress & Gateway ]
  FastAPI Application Gateway (Port 8000)
  ├── CORS & Host Filtering
  ├── Sliding-Window Rate Limiter (60 req/min, burst 10)
  └── REST & WebSocket Connection Manager
          │
          ▼
[ Tier 3: Security & Governance ]
  ├── Security Gate Node (Prompt injection, shell sanitizer, path traversal)
  ├── PII Redactor (Aadhaar, PAN, SSN, email, phone masking)
  ├── RBAC Engine (admin, lead_engineer, field_inspector, auditor)
  └── Cryptographic Audit Logger (SHA-256 hash-chain ledger)
          │
          ▼
[ Tier 4: LangGraph Agent Core ]
  StateGraph Engine:
  [START] ──► [security_gate] ──► [planner] ──► [executor] ──► [verifier] ──► [synthesizer] ──► [END]
                                                   ▲              │ (Retry loop)
                                                   └──────────────┘
          │
          ▼
[ Tier 5: Deterministic Tool Tier (16 Safe Tools) ]
  RAG Search | Document Reader | AST Calculator | Unit Converter | OCR | Vision | Table Extractor | Deliverables
          │
          ▼
[ Tier 6: Local Sovereign AI Model Tier (Ollama 11434) ]
  ├── LLaMA-3.1 8B (Text reasoning & planning)
  ├── LLaVA v1.6 7B (Multimodal image inspection)
  ├── Nomic Embed Text (768-dim vector embeddings)
  └── Qwen-2.5 3B (Auxiliary fast reasoning)
          │
          ▼
[ Tier 7: Persistence & Storage ]
  ├── SQLite auth.db & tasks.db
  ├── ChromaDB persistent vector store (chroma_db/)
  ├── Generated Deliverables (generated_artifacts/)
  └── Cryptographic Hash Chain Ledger (audit_trail.jsonl)
```
