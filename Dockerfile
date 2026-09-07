# ==============================================================================
# Sovereign AI Workbench - Production Dockerfile (SIH26117)
# Multi-Agent Intelligence System - Cloud Web Service Deployment
# ==============================================================================

FROM python:3.11-slim

# Prevent python from writing pyc bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=10000 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production-cloud \
    AIR_GAP_STRICT_MODE=false

WORKDIR /app

# Install minimal OS dependencies for building native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY .env.example .
COPY README.md .

# Create unprivileged application user and persistent data mount directory
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

USER appuser

# Expose default cloud port (Render uses $PORT)
EXPOSE 10000

# Health check to ensure FastAPI responds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-10000}/api/v1/health || exit 1

# Start production server binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
