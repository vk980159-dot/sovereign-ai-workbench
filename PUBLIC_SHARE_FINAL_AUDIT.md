# Sovereign AI Workbench - Final Public Share & Hardening Audit (SIH26117)
===================================================================================

## 1. Architecture
The Sovereign AI Workbench (SIH Problem Statement: SIH26117) operates an isolated, on-premise AI runtime capable of being accessed via local network or securely shared remotely via an HTTPS reverse proxy tunnel.

```
+-----------------------------------------------------------------------------------+
| REMOTE / PUBLIC ACCESS                                                            |
|                                                                                   |
|  [ Public User Browser ]                                                          |
|           |                                                                       |
|           | HTTPS (TLS 1.3 edge termination)                                      |
|           v                                                                       |
|  [ Cloudflare Edge Network ]                                                      |
|           |                                                                       |
|           | Isolated HTTPS Quick Tunnel                                           |
|           v                                                                       |
+-----------|-----------------------------------------------------------------------+
| WINDOWS HOST MACHINE                                                              |
|           |                                                                       |
|           v                                                                       |
|  [ cloudflared.exe (127.0.0.1:8000 only) ]                                        |
|           |                                                                       |
|           v                                                                       |
|  [ FastAPI Application Core (:8000) ] <-----+ Security Guards (Host, Rate Limit,  |
|           |                                 | CSRF, Security Headers, CSP)        |
|           +---> LangGraph Agent Engine      +-------------------------------------+
|           +---> Local Document Ingestion & RAG                                    |
|           +---> Multi-format Deliverable Generator (DOCX, XLSX, PPTX, PDF)        |
|           +---> SHA-256 Audit Ledger                                              |
|           |                                                                       |
|  [ STRICT ISOLATION BARRIER ]                                                     |
|           |                                                                       |
|           +---> Local Ollama Daemon (:11434)                                      |
|           |       |-- llama3.1:latest (Deterministic Reasoning)                   |
|           |       |-- llava:latest (Multimodal Vision)                            |
|           |       |-- nomic-embed-text:latest (Semantic Embeddings)               |
|           |       +-- qwen2.5:3b-instruct (Structured Extraction)                 |
|           +---> Local Tesseract OCR Engine (v5.4.0)                               |
|           +---> Local ChromaDB Persistent Vector Store                            |
|           +---> Local SQLite Databases (auth.db, tasks.db)                        |
|                                                                                   |
|  NEVER EXPOSED PUBLICLY: Port 11434, ChromaDB, SQLite, Filesystem, PowerShell/CMD |
+-----------------------------------------------------------------------------------+
```

---

## 2. Runtime Modes
The system strictly distinguishes three conceptual operational states:

1. **`LOCAL_AIR_GAPPED`**:
   - Application runs locally on `http://127.0.0.1:8000`.
   - Ollama, ChromaDB, SQLite, and Tesseract run locally.
   - External network traffic is blocked; strict air-gap compliance is verified.
   - UI Banner: `AIR-GAPPED / ON-PREMISE VERIFIED`.

2. **`PUBLIC_SHARE`**:
   - Application is exposed through an isolated Cloudflare HTTPS tunnel.
   - All AI inference, embeddings, and vector processing remain on the host machine.
   - Public access is transparently acknowledged; zero-network claims are not made.
   - UI Banner: `PUBLIC SHARE / LOCAL AI`.
   - Explanatory Notice: *"Remote users can access the application, while AI models, knowledge base and processing remain on the host machine."*

3. **`CLOUD_DEMO`**:
   - Deployed on remote cloud container (e.g. Render).
   - Honestly indicates when local Ollama inference is offline or disconnected.
   - UI Banner: `CLOUD DEMO / LOCAL AI REQUIRED`.

---

## 3. Public URL
- **Tunnel URL Format**: `https://[subdomain].trycloudflare.com`
- **Dynamic Registration**: Captured by runner process and stored locally in `.public_share_url`.
- **Public API Documentation**: `https://[subdomain].trycloudflare.com/docs`

---

## 4. Local URL
- **Local Dashboard**: `http://127.0.0.1:8000`
- **Local Swagger UI**: `http://127.0.0.1:8000/docs`
- **Local Telemetry**: `ws://127.0.0.1:8000/api/v1/ws/agent-thoughts/{session_id}`

---

## 5. Render URL
- **Render Production Instance**: `https://sovereign-ai-workbench-wb96.onrender.com`
- **Render Operating State**: `CLOUD_DEMO / LOCAL AI REQUIRED` (never falsely claiming on-premise execution).

---

## 6. Authentication Status
- **Password Authentication**: Verified operational with Argon2id memory-hard hashing and HMAC session tokens.
- **Registration**: Enabled via `/register`.
- **Session Management**: Dual-mode session handling via HTTP-only cookies and Bearer token `Authorization` headers.
- **RBAC**: Enforced (`admin` vs `user` roles) on administrative routes (`/api/v1/admin/users`).

---

## 7. OAuth Status
- **Google OAuth**: Configured for permanent callback `http://127.0.0.1:8000/api/auth/google/callback`. Disabled cleanly in temporary Quick Tunnels with an explanatory notification directing users to password login.
- **GitHub OAuth**: Configured for permanent callback `http://127.0.0.1:8000/api/auth/github/callback`. Disabled cleanly in temporary Quick Tunnels.

---

## 8. WebSocket Status
- **Endpoint**: `/api/v1/ws/agent-thoughts/{session_id}` and `/ws/telemetry`
- **Protocol Switching**: Dynamic client resolution (`window.location.protocol === 'https:' ? 'wss:' : 'ws:'`) ensures immediate connectivity through HTTPS tunnels.
- **Streaming Content**: Clean execution events and thought milestones; chain-of-thought tokens are sanitized.

---

## 9. Upload Status
- **Supported Formats**: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.csv`, `.json`, `.txt`, `.md`.
- **Security Validation**:
  - File extension whitelist enforced.
  - Script/executable extensions strictly denied (`.exe`, `.bat`, `.cmd`, `.ps1`, `.dll`, `.py`, `.sh`, `.js`, `.zip`, `.tar`).
  - Filename sanitization strips path traversal patterns (`os.path.basename`).
  - Size limit enforced (25 MB max in Public Share mode; HTTP 413 on exceedance).

---

## 10. OCR Status
- **Engine**: Local Tesseract OCR v5.4.0 (Windows executable at `AppData\Local\Programs\Tesseract-OCR\tesseract.exe`).
- **Processing**: Scanned PDF pages are rasterized and processed locally by Tesseract without sending images to external cloud APIs.
- **Availability**: Truthfully reported in `/api/v1/health` and `/api/v1/ai/capabilities`.

---

## 11. Vision Status
- **Model**: Local open-weight `llava:latest` via Ollama (`127.0.0.1:11434`).
- **Processing**: Inspects technical engineering images, equipment photos, and diagrams. Fails closed with capability errors if Ollama is stopped.

---

## 12. RAG Status
- **Vector Database**: Local ChromaDB embedded store at `chroma_db/`.
- **Embeddings**: Local `nomic-embed-text:latest` model via Ollama.
- **Retrieval**: Cosine similarity top-K chunk retrieval with source attribution.

---

## 13. Agent Engine Status
- **Framework**: LangGraph multi-step agent workflow.
- **Loop**: Planner -> Security Gate -> Tool Execution -> Verification -> Synthesis.
- **Security Gate**: Filters all tool calls against policy rules before dispatching.

---

## 14. Artifact Status
- **Formats**: Microsoft Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`), and Adobe PDF (`.pdf`).
- **Storage**: Strictly confined to `generated_artifacts/`.
- **Download**: Authenticated endpoints with user isolation and path traversal guards.

---

## 15. Swagger Status
- **Offline Capability**: Fully self-hosted. Vendored assets (`swagger-ui-bundle.js`, `swagger-ui.css`) served from `/static/swagger/` with zero CDN calls.
- **URL**: `http://127.0.0.1:8000/docs` and `https://[subdomain].trycloudflare.com/docs`.

---

## 16. Security Status
- **HTTP Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self' ... connect-src 'self' ws: wss: http: https:`
- **Direct Path Blocking**:
  - Requests for `/.env`, `/backend/.env`, `/database.db`, `/tasks.db`, `/auth.db`, `/chroma_db/` are denied.

---

## 17. Rate Limiting Status
- **Implementation**: Sliding-window in-memory rate limiter with concurrent task guard.
- **Threshold**: 120 req/min (configurable via `PUBLIC_MAX_REQUESTS_PER_MINUTE`).
- **Response**: HTTP 429 Too Many Requests with `Retry-After: 10`.
- **IP Extraction**: Cloudflare `CF-Connecting-IP` prioritized over unverified headers.

---

## 18. Host Validation
- **Policy**: Only `127.0.0.1`, `localhost`, `testserver`, configured Render domains, and valid `*.trycloudflare.com` hostnames are permitted.
- **Defenses**: Unrecognized external Host headers are rejected with HTTP 400 Bad Request.

---

## 19. Tests Summary
Comprehensive unit and integration testing across:
- `test_public_share_hardening.py` (Host validation, offline Swagger, rate limiting, upload restrictions, secret path protection, runtime modes)
- `test_agent_engine.py` (LangGraph agent pipeline, safe tool execution)
- `test_audit.py` (SHA-256 tamper-evident micro-ledger)
- `test_auth.py` (Argon2 password hashing, session tokens, JTI revocation)
- `test_deployment.py` (Air-gap vs cloud mode compliance)
- `test_judge_demo.py` (SIH26117 judge demonstration mode)
- `test_multimodal_deliverables.py` (OCR, vision, and DOCX/XLSX/PPTX/PDF creation)
- `test_pii.py` (Zero-data leakage PII redactor)
- `test_public_share.py` (Tunnel runner and metadata tracking)
- `test_runtime_hardening.py` (Host and boundary enforcement)

---

## 20. Exact Test Counts
- **Total Tests**: 91 automated tests.
- **Pass Rate**: 100% PASSING (91/91).
- **Regressions**: 0.

---

## 21. Known Limitations
- Host Windows machine must remain powered on and connected for remote users to access the local AI runtime.
- Deep reasoning queries with `llama3.1` require sufficient CPU/GPU RAM on the host machine.

---

## 22. Quick Tunnel Limitations
- `trycloudflare.com` URLs are ephemeral and rotate when the runner restarts.
- Not suited for production OAuth callback pre-registration.

---

## 23. Stable Named Tunnel Recommendation
For permanent team or enterprise access:
1. Run `cloudflared tunnel create sovereign-workbench`.
2. Map a custom domain (e.g. `ai.organization.com`).
3. Set `PUBLIC_BASE_URL=https://ai.organization.com`.

---

## 24. Git Status
- Working tree preserved; changes confined to public share hardening and audit documentation.

---

## 25. Files Changed
- `backend/app/config.py`: Added `ALLOWED_HOSTS`, `is_host_allowed`, and `PUBLIC_BASE_URL` enhancements.
- `backend/app/main.py`: Added Host validation, clean 429 JSON responses for rate limiting, and local offline Swagger UI.
- `backend/app/api/models.py`: Added `public_share`, `temporary_tunnel`, and `notice` to `OAuthProvidersResponse`.
- `backend/app/api/router.py`: Hardened OAuth routes for temporary public share mode.
- `backend/app/security/rate_limiter.py`: Prioritized `CF-Connecting-IP`.
- `frontend/login.html`: Added quick tunnel notices for OAuth buttons and error mapping.
- `scripts/public_share_runner.py`: Enhanced pre-flight binary detection and Phase 4 status banner.
- `scripts/start_public_share.ps1`: Added PowerShell public share launcher.
- `backend/tests/test_public_share_hardening.py`: Added 11 new public share and security tests.
- `PUBLIC_SHARE_GUIDE.md`: Comprehensive operator guide.
- `PUBLIC_SHARE_FINAL_AUDIT.md`: Final architectural and technical verification report.
