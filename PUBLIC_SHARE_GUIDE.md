# Sovereign AI Workbench - Public Share Mode Guide (SIH26117)
========================================================================

## 1. Prerequisites
Before initiating Public Share Mode, ensure the following local sovereign dependencies are satisfied on this Windows host:

1. **Python Environment**:
   - Python virtual environment at `venv\` with all required backend packages.
2. **Local Ollama Daemon**:
   - Ollama running locally at `http://127.0.0.1:11434`.
   - Verified models installed:
     - `llama3.1:latest` (Deterministic industrial reasoning & synthesis)
     - `llava:latest` (Multimodal image inspection & OCR verification)
     - `nomic-embed-text:latest` (Local semantic embeddings)
     - `qwen2.5:3b-instruct` (Fast structured extraction)
3. **Local Tesseract OCR**:
   - Tesseract v5.4+ installed locally (e.g. `AppData\Local\Programs\Tesseract-OCR\tesseract.exe` or `C:\Program Files\Tesseract-OCR\tesseract.exe`).
4. **Cloudflare Tunnel Binary**:
   - `cloudflared.exe` located in `venv\Scripts\cloudflared.exe` or accessible in system `PATH`.

---

## 2. Start Backend
In standard standalone mode, the backend can be launched via:
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
However, the automated Public Share runner automatically detects whether the backend is already running and will spawn it safely if needed.

---

## 3. Start Public Share
To launch Public Share Mode with an isolated Cloudflare HTTPS tunnel:

### Using Batch Script:
```cmd
scripts\start_public_share.bat
```

### Using PowerShell:
```powershell
.\scripts\start_public_share.ps1
```

### Using Python:
```powershell
.\venv\Scripts\python.exe scripts\public_share_runner.py
```

The runner performs automated pre-flight checks:
- Verifies `cloudflared` binary
- Probes local Ollama daemon on `127.0.0.1:11434`
- Verifies local Tesseract OCR engine
- Verifies local FastAPI backend on `127.0.0.1:8000`
- Opens an isolated tunnel **ONLY to port 8000** (never port 11434, never ChromaDB, never SQLite)
- Writes the registered URL into `.public_share_url`

---

## 4. Find Public URL
Upon connection, the runner prints the active status banner:

```text
========================================
SOVEREIGN AI WORKBENCH
PUBLIC SHARE READY
========================================

LOCAL:
http://127.0.0.1:8000

PUBLIC:
https://xxxxx.trycloudflare.com

MODE:
PUBLIC_SHARE / LOCAL AI

BACKEND:
ONLINE

OLLAMA:
ONLINE

CHROMA:
ONLINE

OCR:
ONLINE

VISION:
ONLINE

========================================
```

The public link is also stored at `.public_share_url` in the repository root for programmatic inspection.

---

## 5. Login
1. Open the generated `https://xxxxx.trycloudflare.com` URL on any remote device (mobile, laptop, or second network).
2. Unauthenticated traffic is redirected automatically to `/login`.
3. Sign in using local sovereign credentials:
   - **Default Administrator**: `admin` / `SovereignAdmin2026!`
   - Or click **Create Account** (`/register`) to register a new sovereign identity.
4. Social OAuth (Google / GitHub) is intentionally marked unavailable for temporary Quick Tunnels because random hostnames cannot be pre-registered in OAuth developer consoles.

---

## 6. Test AI
1. Navigate to the **Agent Workbench** tab.
2. Enter an industrial query, for example:
   > "Inspect turbine thermal deviation, cross-reference SOP-IND-702, calculate safety exceedance, and produce signed compliance note."
3. The query executes 100% locally on the host's Ollama `llama3.1` model.
4. External AI API calls remain strictly **0**.

---

## 7. Test Upload & OCR
1. Navigate to **Knowledge Base** or **Multimodal Ingestion**.
2. Upload a scanned technical document (PDF, PNG, JPG).
3. The document is processed locally:
   - Scanned PDF rendered into raster page images
   - Local Tesseract OCR extracts text on-premise
   - Text chunks embedded with `nomic-embed-text`
   - Stored in local ChromaDB vector collection
4. No document bytes leave the host machine.

---

## 8. Test Artifact Deliverables
1. Run an agent task requesting `DOCX`, `XLSX`, `PPTX`, or `PDF` output.
2. The deliverable engine generates authentic office documents inside `generated_artifacts/`.
3. Click the download link in the interface to retrieve the file securely over HTTPS.
4. Strict filename sanitization and user isolation prevent path traversal.

---

## 9. Stop Server
To terminate Public Share Mode and close external access:
- Press `Ctrl+C` in the runner terminal window.
- Or execute:
  ```cmd
  scripts\stop_public_share.bat
  ```
The tunnel is closed immediately, `cloudflared` is terminated, `.public_share_url` is deleted, and the workbench returns to 100% local-only operation.

---

## 10. Security Controls & Guarantees
- **Port Isolation**: Ollama (`11434`), ChromaDB, SQLite, and raw Windows shell are **NEVER exposed**. Only FastAPI port 8000 receives tunnel traffic.
- **Host Header Validation**: Malicious Host injection headers (e.g. `evil.com`) are rejected with HTTP 400 Bad Request.
- **In-Memory Rate Limiting**: Remote IPs are limited to 120 requests/minute (configurable via `PUBLIC_MAX_REQUESTS_PER_MINUTE`).
- **Security Headers**: Strict `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and Content Security Policy with WebSocket allowances.
- **Zero Cloud AI Leakage**: All reasoning and embedding occur on loopback `127.0.0.1`.

---

## 11. Quick Tunnel Limitations
Cloudflare Quick Tunnels (`trycloudflare.com`) provide zero-configuration HTTPS sharing for testing and demonstrations:
- URLs are dynamic and change on every runner restart.
- Cannot be registered in Google/GitHub OAuth developer consoles for production social login.
- Cloudflare edge network terms apply to public traffic transit.

---

## 12. Stable Named Tunnel Setup (Production Sharing)
For a permanent, stable URL (e.g. `https://ai.example.com`):
1. Authenticate `cloudflared`:
   ```cmd
   cloudflared tunnel login
   ```
2. Create a named tunnel:
   ```cmd
   cloudflared tunnel create sovereign-workbench
   ```
3. Route DNS to your custom domain:
   ```cmd
   cloudflared tunnel route dns sovereign-workbench ai.example.com
   ```
4. Set environment variable:
   ```env
   PUBLIC_BASE_URL=https://ai.example.com
   ```
5. Register `https://ai.example.com/api/auth/google/callback` and `https://ai.example.com/api/auth/github/callback` in OAuth developer portals to enable social login on your custom domain.
