# Sovereign AI Workbench - Public Share Mode Guide (SIH26117)

## Overview
The **Sovereign AI Workbench** is an on-premise, secure multi-agent intelligence platform built for SIH Problem Statement **SIH26117**. 

By default, the workbench operates in **100% Air-Gapped Local Mode**, binding strictly to `127.0.0.1:8000` with zero internet access required. **Public Share Mode** allows an administrator or evaluator to temporarily share the workbench interface over an ephemeral or named Cloudflare HTTPS tunnel (`https://*.trycloudflare.com`) while ensuring **all artificial intelligence inference, OCR, RAG vector searches, and agent workflows execute 100% locally on the host machine**.

---

## Architecture

```
                                  PUBLIC INTERNET
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │ Cloudflare Edge Network (TLS Term.)   │
                     │ https://<tunnel-id>.trycloudflare.com │
                     └───────────────────┬───────────────────┘
                                         │ (Outbound WireGuard/QUIC tunnel)
                                         ▼
                             HOST WINDOWS WORKSTATION
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   cloudflared.exe (Tunnel Client)                                           │
│          │                                                                  │
│          ▼ (Forwarded HTTP/WS only to port 8000)                            │
│   FastAPI Application Gateway [127.0.0.1:8000]                              │
│   ├── In-Memory Rate Limiter (60 RPM, 15MB upload, 2 concurrent tasks)     │
│   ├── Security Headers (CSP, Frame DENY, nosniff, Referrer-Policy)          │
│   ├── User Isolation (Scoped token, path sanitization, file whitelist)      │
│   └── WebSocket Telemetry Bridge (Dynamic wss:// streaming)                 │
│          │                                                                  │
│          ├───────────────────────┬────────────────────────┐                 │
│          ▼                       ▼                        ▼                 │
│   LangGraph Agent Core     ChromaDB Vector DB      Tesseract OCR            │
│   (State & Safe Tools)     (Local Embeddings)      (v5.4.0 Engine)          │
│          │                       │                        │                 │
│          └───────────────────────┼────────────────────────┘                 │
│                                  │                                          │
│                                  ▼ (Strictly Local HTTP)                    │
│                 Ollama Local Daemon [127.0.0.1:11434]                       │
│                 ├── llama3.1:latest      (Reasoning Core)                   │
│                 ├── llava:latest         (Vision Multimodal)                │
│                 └── nomic-embed-text     (Dense Embeddings)                 │
│                                                                             │
│   [ISOLATION BARRIER] Port 11434 is NEVER mapped to Cloudflare.             │
│   SQLite databases, ChromaDB storage, and host files are never accessible.  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start: Launching Public Share Mode

### Prerequisites
1. **Ollama Daemon**: Running on `127.0.0.1:11434` with `llama3.1`, `llava`, and `nomic-embed-text`.
2. **Tesseract OCR**: Installed (v5.4.0+) and available in system PATH.
3. **Cloudflare Tunnel (`cloudflared`)**: Installed in PATH.

### Step 1: Start the Local Workbench
If the backend is not already running:
```cmd
start.bat
```
*(Or the public share runner will automatically launch the backend if offline).*

### Step 2: Launch the Public Tunnel
Run the public share launcher from Command Prompt, PowerShell, or by double-clicking:
```cmd
scripts\start_public_share.bat
```

The runner performs automated pre-flight checks:
- Verifies `cloudflared` binary
- Verifies local Ollama daemon & model tags
- Verifies local Tesseract OCR engine
- Verifies local FastAPI backend availability
- Initiates an isolated HTTPS tunnel **strictly to port 8000**
- Extracts the generated `https://*.trycloudflare.com` URL
- Writes `.public_share_url` to the workspace root
- Displays the connection banner

### Step 3: Access from Any Device
Open the generated link in any modern desktop or mobile browser:
```
https://xxxx-xxxx.trycloudflare.com
```

### Step 4: Terminate the Public Tunnel
When demonstration or evaluation is complete:
- Press `Ctrl+C` in the tunnel terminal window, OR
- Run:
  ```cmd
  scripts\stop_public_share.bat
  ```

This kills the `cloudflared.exe` process and removes `.public_share_url`. The workbench instantly reverts to local-only mode.

---

## Runtime Mode Labels & Truthful Disclosure

The Workbench dynamically reports its operational mode across all headers, metrics, and API health responses:

| Mode | Trigger Condition | Display Badge | Description |
|---|---|---|---|
| `LOCAL_AIR_GAPPED` | No public tunnel active; local Ollama connected. | `AIR-GAPPED / ON-PREMISE VERIFIED` | 100% offline, isolated to loopback. |
| `PUBLIC_SHARE` | Cloudflare tunnel active (`.public_share_url` present or `PUBLIC_SHARE_ENABLED=true`). | `🌐 PUBLIC SHARE / LOCAL AI` | Public HTTPS ingress, but 100% local AI inference. |
| `CLOUD_DEMO` | Public share active but local Ollama is offline. | `CLOUD DEMO / LOCAL AI REQUIRED` | Tunnel online, local AI daemon offline. |

> [!IMPORTANT]
> **No False Air-Gap Claims**: When Public Share Mode is active, the system **NEVER** displays "AIR-GAPPED". The dashboard displays an informational banner explicitly stating:
> *"Local AI remains on this machine. Public users access this application through a secure HTTPS tunnel. This is a public demonstration mode, not an air-gapped environment."*

---

## Security Architecture & Threat Isolation

### 1. Loopback Daemon Isolation (Port 11434)
The Cloudflare tunnel command executed by `public_share_runner.py` is hardcoded to:
```cmd
cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate
```
Port `11434` (Ollama) is **never exposed**. Internet clients cannot send raw inference requests, inspect Ollama configuration, or pull models.

### 2. In-Memory Rate Limiting
To prevent denial-of-service or GPU resource exhaustion from external requests:
- **Max Requests Per Minute**: 60 requests/min per IP. Exceeding requests receive `HTTP 429 Too Many Requests`.
- **Max Upload Size**: 15 MB per file. Payloads larger than 15 MB receive `HTTP 413 Payload Too Large`.
- **Max Concurrent Tasks**: 2 active agent generation tasks per user/session. Additional submissions receive `HTTP 429`.

### 3. File Upload & Execution Protection
- **Extension Whitelist**: `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.ppt`, `.csv`, `.txt`, `.md`, `.json`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`.
- **Executable Blacklist**: `.exe`, `.bat`, `.cmd`, `.ps1`, `.vbs`, `.sh`, `.bash`, `.dll`, `.so`, `.dylib`, `.py`, `.js`, `.zip`, `.tar`, `.gz`, `.rar`, etc.
- Files are saved with cryptographically random UUIDs; original file names are sanitized to prevent directory traversal attacks (`../`).

### 4. User Isolation for Deliverables & Artifacts
- Non-admin users can only retrieve artifacts and documents associated with their user ID.
- Attempts to download foreign artifacts or access raw system paths yield `HTTP 404 Not Found` or `HTTP 403 Forbidden`.

### 5. Security Headers
All responses through FastAPI include:
- `Content-Security-Policy`: Disallows unauthorized script injections; permits local/tunnel `wss://` and inline dashboard assets.
- `X-Frame-Options: DENY`: Mitigates clickjacking.
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts leak of query parameters to third parties.

---

## Zero External AI Verification

To verify that **ZERO external cloud AI services** are called during public demonstrations:

1. **Environment Check**:
   The backend inspects environment variables on startup. The following must all be empty:
   `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `AZURE_OPENAI_API_KEY`, `GROQ_API_KEY`, `COHERE_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`, `PERPLEXITY_API_KEY`.
2. **Runtime Health Audit**:
   `GET /api/v1/health` returns:
   ```json
   {
     "status": "ONLINE_SECURE",
     "runtime_mode": "PUBLIC_SHARE",
     "runtime_label": "PUBLIC SHARE / LOCAL AI",
     "zero_external_ai": true,
     "external_ai_calls": 0,
     "public_share": {
       "active": true,
       "public_url": "https://xxxx.trycloudflare.com",
       "local_url": "http://127.0.0.1:8000",
       "ai_runtime": "LOCAL",
       "zero_external_ai": true
     }
   }
   ```
3. **Public Share Endpoint**:
   `GET /api/v1/runtime/public-share` returns complete tunnel and isolation telemetry for auditing.

---

## Optional: Named Cloudflare Tunnel (Custom Domain)

If a permanent custom domain is preferred over ephemeral `trycloudflare.com` links:

1. Authenticate with Cloudflare:
   ```cmd
   cloudflared tunnel login
   ```
2. Create a named tunnel:
   ```cmd
   cloudflared tunnel create sovereign-workbench
   ```
3. Route DNS to your custom domain:
   ```cmd
   cloudflared tunnel route dns sovereign-workbench demo.yourdomain.gov.in
   ```
4. Configure `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <TUNNEL-UUID>
   credentials-file: C:\Users\<Username>\.cloudflared\<TUNNEL-UUID>.json
   ingress:
     - hostname: demo.yourdomain.gov.in
       service: http://127.0.0.1:8000
     - service: http_status:404
   ```
5. Set environment variable:
   ```cmd
   set PUBLIC_BASE_URL=https://demo.yourdomain.gov.in
   set PUBLIC_SHARE_ENABLED=true
   ```
6. Run:
   ```cmd
   cloudflared tunnel run sovereign-workbench
   ```

---

## GitHub OAuth in Public Mode

When running in Public Share Mode, GitHub OAuth redirect URIs must match the active public tunnel URL:
1. Copy your public tunnel URL: `https://xxxx.trycloudflare.com`.
2. In GitHub Developer Settings (OAuth Apps), update:
   - **Homepage URL**: `https://xxxx.trycloudflare.com`
   - **Authorization callback URL**: `https://xxxx.trycloudflare.com/api/v1/auth/github/callback`
3. The backend automatically detects the public tunnel URL and generates the appropriate OAuth authorization redirect.
