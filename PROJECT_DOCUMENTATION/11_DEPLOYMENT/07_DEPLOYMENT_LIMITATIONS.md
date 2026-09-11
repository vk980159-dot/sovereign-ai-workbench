# 07. Deployment Limitations & Hardware Requirements
**Status:** [VERIFIED]

- **Recommended RAM:** 16 GB minimum (32 GB recommended for concurrent multi-model holding).
- **VRAM / GPU:** 8 GB VRAM recommended for fast 4-bit inference; automatic fallback to CPU RAM supported.
- **Disk Footprint:** ~12 GB (LLaMA 4.7 GB + LLaVA 4.7 GB + Nomic 0.5 GB + Qwen 1.9 GB).
- **Multi-Node Clusters:** Single-node workstation architecture; enterprise Kubernetes multi-worker clustering not implemented.
