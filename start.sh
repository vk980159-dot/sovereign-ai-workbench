#!/usr/bin/env bash
# ==============================================================================
# Sovereign On-Premise Agentic AI Workbench (SIH26117)
# One-Click Air-Gapped Launch Script (POSIX / Linux / macOS)
# ==============================================================================

set -e

echo "========================================================================"
echo "    SOVEREIGN AI WORKBENCH - 100% LOCAL AIR-GAPPED BOOT"
echo "========================================================================"

# 1. Environment & Directory Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH"
export WORKBENCH_AIR_GAP_STRICT_MODE="True"
export HF_HUB_OFFLINE="1"
export TRANSFORMERS_OFFLINE="1"

# 2. Verify Python Runtime
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[SYSTEM] Python Runtime Detected: v$PY_VERSION"

# 3. Virtual Environment Setup
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating local isolated virtual environment 'venv'..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[SETUP] Activated virtual environment."

# 4. Dependency Verification
echo "[SETUP] Verifying pinned dependencies from requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 5. Local Ollama Inference Daemon Check
OLLAMA_URL="${WORKBENCH_OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL_NAME="${WORKBENCH_DEFAULT_MODEL:-llama3.1}"
EMBED_MODEL="${WORKBENCH_EMBEDDING_MODEL_NAME:-nomic-embed-text}"

echo "[INFERENCE] Probing local Ollama instance at $OLLAMA_URL..."
if curl -s --connect-timeout 2 "$OLLAMA_URL/api/tags" > /dev/null; then
    echo "[INFERENCE] ✓ Local Ollama daemon is active."
    # Ensure model is available
    if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL_NAME"; then
        echo "[INFERENCE] Pulling local model '$MODEL_NAME' (First-time local caching)..."
        ollama pull "$MODEL_NAME" || true
    fi
    if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "$EMBED_MODEL"; then
        echo "[INFERENCE] Pulling local embedding model '$EMBED_MODEL'..."
        ollama pull "$EMBED_MODEL" || true
    fi
else
    echo "[WARNING] Ollama daemon is not responding at $OLLAMA_URL."
    echo "          Please start Ollama in another terminal: 'ollama serve'"
    echo "          Proceeding in fallback mode..."
fi

# 6. Launch Sovereign Backend & Dashboard
echo "========================================================================"
echo "  [SUCCESS] LAUNCHING SOVEREIGN WORKBENCH SERVER"
echo "  Access Dashboard:   http://127.0.0.1:8000"
echo "  API Documentation:  http://127.0.0.1:8000/docs"
echo "  WebSocket Stream:   ws://127.0.0.1:8000/api/v1/ws/agent-thoughts/{id}"
echo "========================================================================"

cd "$SCRIPT_DIR/backend"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --log-level info
