# 01. Project Overview
**Status:** [VERIFIED]

## What is the Sovereign AI Workbench?
The Sovereign AI Workbench is an on-premise, air-gapped agentic AI workstation designed specifically for high-consequence confidential industrial engineering environments (SIH Problem Statement SIH26117).

Unlike consumer or enterprise cloud AI services (ChatGPT, Claude, Gemini, Azure AI) which stream proprietary engineering drawings, maintenance incident reports, and plant SOPs to remote third-party data centers, this workstation runs **100% locally** on the user's host PC.

## Key Operational Facts
- **Local AI Daemon:** Ollama on `127.0.0.1:11434`
- **Application Server:** FastAPI on `127.0.0.1:8000`
- **Reasoning Model:** LLaMA-3.1 8B Instruct (Meta open weights)
- **Vision Model:** LLaVA v1.6 7B (Open-weight vision-language model)
- **Dense Vector Embeddings:** Nomic Embed Text v1.5 (768 dimensions)
- **OCR Engine:** Tesseract OCR v5.4.0 (`tesseract.exe`)
- **Knowledge Base:** ChromaDB persistent local vector store (`chroma_db/`)
- **Deliverables:** Authentic Microsoft Word (.docx), Excel (.xlsx with formulas), PowerPoint (.pptx), and PDF (.pdf) files.
- **Audit Ledger:** Forward SHA-256 hash-chained tamper-evident ledger (`audit_trail.jsonl`).
- **Cloud AI Leakage:** Exactly 0.0% (Zero calls to cloud AI APIs).
