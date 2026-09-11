# 00. Deployment Architecture Overview
**Status:** [VERIFIED]

## Deployment Topologies
The Sovereign AI Workbench supports multiple deployment environments:
1. **Windows Local Workstation (Native Python):** Primary recommended deployment for industrial workstations with direct GPU/CPU access.
2. **Containerized Deployment (Docker):** Standard container build via `Dockerfile` for air-gapped on-premise Linux servers.
3. **Public Share Mode (Cloudflare Quick Tunnel):** Automated temporary reverse proxy for remote stakeholder evaluations.
4. **Cloud Demo (Render):** Cloud-hosted UI/Gateway blueprint (`render.yaml`).
