# 06. Comprehensive Runtime Comparison
**Status:** [VERIFIED]

| Dimension | LOCAL_AIR_GAPPED | PUBLIC_SHARE | CLOUD_DEMO |
|-----------|------------------|--------------|------------|
| Ingress Network | `127.0.0.1:8000` | `https://*.trycloudflare.com` | `https://*.onrender.com` |
| Egress Allowed | NONE (0.0%) | Loopback response | Outbound to Ollama host |
| Ollama Location | Host PC (11434) | Host PC (11434) | External Ollama Host |
| Tesseract OCR | Local Windows Path | Local Windows Path | Linux package in container |
| UI Mode Badge | `LOCAL AIR-GAPPED` | `PUBLIC SHARE / LOCAL AI` | `CLOUD DEMO` |
| Security Perimeter| Maximum Isolation | Rate Limiter + Port 8000 Proxy | HTTPS Gateway |
