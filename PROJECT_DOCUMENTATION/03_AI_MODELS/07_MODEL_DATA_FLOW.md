# 07. Model Data Flow & Prompt Pipeline
**Status:** [VERIFIED]

## Prompt Lifecycle
1. User prompt passes through `security_gate.py` (pre-model sanitization).
2. `planner.py` constructs few-shot engineering prompt detailing the 16 safe tools and JSON schema.
3. Dispatched over local loopback HTTP to Ollama `127.0.0.1:11434/api/chat`.
4. Ollama streams tokens back -> `model_provider.py` aggregates response and computes latency.
5. Response parsed into structured Pydantic plan objects. Zero telemetry transmitted externally.
