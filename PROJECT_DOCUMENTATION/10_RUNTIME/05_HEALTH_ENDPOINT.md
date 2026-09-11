# 05. Runtime Health Endpoint (`GET /api/health`)
**Status:** [VERIFIED]

- **Returns:**
```json
{
  "status": "healthy",
  "runtime_mode": "LOCAL_AIR_GAPPED",
  "ollama_connected": true,
  "tesseract_installed": true,
  "chromadb_ready": true,
  "installed_models": ["llama3.1:latest", "llava:latest", "nomic-embed-text:latest"]
}
```
