# 06. Cloudflare Quick Tunnel (`cloudflared`)
**Status:** [VERIFIED ACTIVE]

- **Executable:** `cloudflared.exe` v2026.7.3.
- **Command:** `cloudflared tunnel --url http://127.0.0.1:8000`.
- **Subdomain:** Ephemeral `https://*.trycloudflare.com` assigned dynamically.
- **Security:** Strictly forwards traffic to port 8000; internal ports (11434) and filesystem are never exposed.
