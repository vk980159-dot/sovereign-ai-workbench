# 02. Configuration Management (`backend/app/config.py`)
**Status:** [VERIFIED]

## 1. File Path
`backend/app/config.py`

## 2. File Purpose
Manages global configuration parameters, environment variable overrides, directory paths, and runtime mode definitions using Pydantic `BaseSettings`.

## 3. Why This File Exists
Eliminates hardcoded credentials, URLs, and directory paths across the codebase, allowing clean configuration via `.env` files.

## 4. Key Configuration Variables
- `OLLAMA_BASE_URL`: Defaults to `http://127.0.0.1:11434`.
- `DEFAULT_LLM_MODEL`: Defaults to `llama3.1:latest`.
- `VISION_MODEL`: Defaults to `llava:latest`.
- `EMBEDDING_MODEL`: Defaults to `nomic-embed-text:latest`.
- `SECRET_KEY`: Cryptographic signing key for JWT tokens.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default session lifespan (480 minutes).
- `RUNTIME_MODE`: `LOCAL_AIR_GAPPED` | `PUBLIC_SHARE` | `CLOUD_DEMO`.

## 5. Security & Error Handling
Validates configuration on startup; raises descriptive `ValidationError` if required settings are malformed. Provides fallback secret key in development mode with warning in logs.
