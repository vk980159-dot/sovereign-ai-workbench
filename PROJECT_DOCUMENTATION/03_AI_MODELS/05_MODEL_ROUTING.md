# 05. Model Routing Subsystem
**Status:** [PARTIALLY VERIFIED]

## Current Routing Mechanism
The system routes requests deterministically by tool category:
- **Vision Tasks:** Automatically routed to `llava:latest` via `LocalVisionProvider`.
- **Embedding Tasks:** Automatically routed to `nomic-embed-text:latest` via `ChromaVectorStore`.
- **Reasoning & Planning Tasks:** Routed to `llama3.1:latest` via `OllamaModelProvider`.

## Identified Gap
Dynamic, complexity-based routing (e.g. routing simple math or keyword tasks to Qwen-3B vs complex multi-page planning to LLaMA-8B) is not currently implemented; reasoning defaults to LLaMA-3.1.
