# Sovereign AI Workbench
**Smart India Hackathon (SIH 2026) | Problem Statement ID: SIH26117**  
*Secure On-Premise Multi-Agent Intelligence*

---

## 🏛️ Executive Summary

The **Sovereign AI Workbench** is an ultra-secure, air-gapped, multi-agent AI environment designed for defense, national security, intelligence agencies, and critical infrastructure. It functions with **100% local execution and ZERO external cloud dependencies**.

### Key Architectural Tenets:
1. **Air-Gap Strict Enforcement**: Built-in network policy validator guarantees that no inference, storage, or telemetry call can resolve outside loopback (`127.0.0.1`) or verified local subnets.
2. **Sovereign Multi-Agent Engine**: A 4-Agent LangGraph State Machine (`Retriever` ➔ `Analyst` ➔ `Auditor` ➔ `Reporter`) with automated self-correction loops when hallucination confidence falls below 80%.
3. **Defense-in-Depth PII & Secret Redaction**: Real-time masking of emails, IP addresses, secret keys, JWTs, AWS credentials, Aadhaar IDs, and PAN cards using regex and Presidio before data touches the LLM context or vector store.
4. **Tamper-Evident SHA-256 Audit Trail**: Append-only cryptographic micro-ledger (`audit_trail.jsonl`) chaining previous hashes from genesis to guarantee deterministic provenance.
5. **On-Premise Vector Memory**: Embedded persistent ChromaDB with local Sentence-Transformers embeddings (`all-MiniLM-L6-v2`) with sliding-window chunking (500 chars, 50 overlap).
6. **Unified Industrial Dashboard**: Standalone dark-themed dashboard featuring real-time WebSocket agent thought streaming, drag-and-drop document ingestion, visual pipeline node state graph, and boardroom-ready executive report rendering.

---

## 📐 Multi-Agent Topology & State Graph

```
                   [ User Query ]
                         │
                         ▼
             ┌───────────────────────┐
             │    NODE 1: RETRIEVER  │  ◄── ChromaDB Vector Search
             │ (PII Masking + Audit) │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │    NODE 2: ANALYST    │  ◄── Ollama Local (llama3.1 / qwen2.5)
             │ (Technical Synthesis) │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │    NODE 3: AUDITOR    │  ◄── Strict Fact-Checking & JSON Verdict
             │  (Hallucination Gate) │
             └───────────┬───────────┘
                         │
               [ Confidence >= 80%? ]
                ├── NO (Loop < 3) ──► (Re-route to ANALYST with Critique)
                └── YES 
                         │
                         ▼
             ┌───────────────────────┐
             │    NODE 4: REPORTER   │  ◄── Executive Synthesis
             │ (Citations + PII Scrub)│
             └───────────┬───────────┘
                         │
                         ▼
            [ Boardroom Final Report ]
```

---

## 📂 Directory Layout

```
sovereign-antigravity-workbench/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI entry point with CORS, REST, and WebSocket streaming
│   │   ├── config.py              # Configuration manager for Ollama, ChromaDB, and Security
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── pii_redactor.py    # Automatic PII/Sensitive data masking engine
│   │   │   └── audit_logger.py    # SHA-256 local cryptographic event logger
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py    # Local ChromaDB manager with chunking and similarity search
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── state.py           # TypedDict AgentState definition for LangGraph
│   │   │   ├── nodes.py           # Ingestion, Analysis, Auditor, and Reporter node logic
│   │   │   └── graph.py           # LangGraph StateGraph assembly and workflow execution
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── router.py          # /upload, /query, and /ws/agent-thoughts API routes
│   │       └── models.py          # Pydantic models for request/response validation
├── frontend/
│   └── index.html                 # Enterprise-grade Dashboard (Embedded Tailwind/Industrial UI)
├── requirements.txt               # Pinned Python dependencies for 100% offline installation
├── start.sh                       # One-click launch script for Linux/macOS
└── start.bat                      # One-click launch script for Windows
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) running locally:
  ```bash
  ollama serve
  ollama pull llama3.1
  ```

### 2. One-Click Launch

**On Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

**On Windows:**
```cmd
start.bat
```

### 3. Access Workbench
- **Interactive Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Live WebSocket Stream**: `ws://127.0.0.1:8000/api/v1/ws/agent-thoughts/{session_id}`

---

## 🔒 Verification & Compliance Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/upload` | POST | Upload PDF/TXT, redacts PII, indexes chunks, writes audit log |
| `/api/v1/query` | POST | Dispatches 4-agent LangGraph workflow |
| `/api/v1/audit/verify` | GET | Validates entire SHA-256 hash chain from genesis block |
| `/api/v1/audit/logs` | GET | Returns recent cryptographic audit trail records |
| `/api/v1/health` | GET | System health, vector count, and air-gap enforcement check |
| `/api/v1/ws/agent-thoughts/{id}` | WS | Bidirectional real-time streaming terminal |
