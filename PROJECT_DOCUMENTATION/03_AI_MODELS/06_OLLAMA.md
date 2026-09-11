# 06. Local Ollama Integration Engine
**Status:** [VERIFIED]

## 1. File Path & Architecture
`backend/app/agents/model_provider.py`: `OllamaModelProvider`

## 2. API Endpoints Consumed
- `POST http://127.0.0.1:11434/api/generate`: Raw prompt completions (used for LLaVA vision payloads).
- `POST http://127.0.0.1:11434/api/chat`: Structured conversational messages (used for planning and synthesis).
- `POST http://127.0.0.1:11434/api/embeddings`: Dense vector generation.
- `GET http://127.0.0.1:11434/api/tags`: Health and model inventory checks.

## 3. Error Handling
Traps `httpx.ConnectError`. If Ollama is not running, raises actionable error: `"Ollama is not running on 127.0.0.1:11434. Please start Ollama before executing tasks."`
