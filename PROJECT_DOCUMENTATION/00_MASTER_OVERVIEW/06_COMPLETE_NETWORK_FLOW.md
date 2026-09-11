# 06. Complete Network Flow
**Status:** [VERIFIED]

## Network Topologies by Runtime Mode

### 1. Local Air-Gapped Mode (Default Industrial Deployment)
```
[Browser Client on Workstation]
        │
        ├── HTTP REST Requests ──► http://127.0.0.1:8000
        └── WebSocket Frames    ──► ws://127.0.0.1:8000/ws/tasks/{id}
                                             │
                                             ▼
                                    FastAPI Server (PID xxxx)
                                             │
                                             ├── HTTP Calls ──► http://127.0.0.1:11434 (Local Ollama)
                                             ├── Subprocess ──► Tesseract OCR CLI (tesseract.exe)
                                             └── Local Disk ──► auth.db, tasks.db, chroma_db/
```
*Zero packets leave the network interface. Disconnecting Ethernet/Wi-Fi has zero impact on functionality.*

### 2. Public Share Mode (Remote Demonstration)
```
[Remote Judge Browser]
        │
        ▼ (Public HTTPS)
[Cloudflare Edge: https://xxxx.trycloudflare.com]
        │
        ▼ (Encrypted Tunnel Stream)
[cloudflared.exe Daemon on Windows PC]
        │
        ▼ (Strict Local Loopback Proxy to Port 8000 ONLY)
[FastAPI Server: 127.0.0.1:8000]
        │
        ├── Rate Limiting Middleware (60 req/min)
        └── Agent Engine
                 │
                 ├── Ollama Port 11434 (STRICTLY LOCAL - NOT ROUTED)
                 ├── ChromaDB & SQLite (STRICTLY LOCAL - NOT ROUTED)
                 └── Windows Filesystem (STRICTLY LOCAL - NOT ROUTED)
```
