# 03. Public Share Runtime Mode
**Status:** [VERIFIED ACTIVE]

- **Implementation:** `scripts/public_share_runner.py`.
- **Reverse Proxy:** Official Cloudflare Quick Tunnel (`cloudflared.exe`) creating `https://*.trycloudflare.com`.
- **Isolation Boundary:**
  - Routes traffic **strictly to port 8000**.
  - Port 11434 (Ollama), SQLite databases, and Windows filesystem are completely unreachable.
  - UI truthfully displays `"PUBLIC SHARE / LOCAL AI"`.
