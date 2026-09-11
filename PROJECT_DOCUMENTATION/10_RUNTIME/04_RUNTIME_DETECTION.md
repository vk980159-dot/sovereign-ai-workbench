# 04. Runtime Detection Logic
**Status:** [VERIFIED]

- **File Path:** `backend/app/config.py`: `get_runtime_mode()`
- **Detection Rules:**
  - If `CLOUDFLARE_TUNNEL_ACTIVE=true` -> `PUBLIC_SHARE`.
  - If `RENDER=true` or `ENVIRONMENT=production` -> `CLOUD_DEMO`.
  - Otherwise -> `LOCAL_AIR_GAPPED`.
