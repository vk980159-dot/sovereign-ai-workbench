# 00. Runtime Architecture Overview
**Status:** [VERIFIED]

## Multi-Mode Runtime Architecture
The Sovereign AI Workbench supports 3 distinct operational modes detected dynamically in `backend/app/config.py`:
1. `LOCAL_AIR_GAPPED`: 100% on-premise execution with pure local loopback.
2. `PUBLIC_SHARE`: Secure Cloudflare Quick Tunnel routing public HTTPS strictly to port 8000.
3. `CLOUD_DEMO`: Cloud hosting blueprint (Render.com) failing closed for local AI.
