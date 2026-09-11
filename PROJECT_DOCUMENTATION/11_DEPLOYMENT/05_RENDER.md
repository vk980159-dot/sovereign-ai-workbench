# 05. Render Cloud Blueprint (`render.yaml`)
**Status:** [VERIFIED]

- **Service Type:** Web Service (`env: python`).
- **Build Command:** `pip install -r requirements.txt`.
- **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.
- **Air-Gap Guardrail:** Fails closed if Ollama daemon is unreachable; displays sovereign local AI warning banner.
