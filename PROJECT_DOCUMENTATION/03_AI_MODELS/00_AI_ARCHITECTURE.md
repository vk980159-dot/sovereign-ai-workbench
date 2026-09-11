# 00. AI Model Architecture Overview
**Status:** [VERIFIED]

## Sovereign Local AI Topology
All AI capabilities in the Sovereign AI Workbench execute through open-weight models managed by a local **Ollama** daemon running on loopback `http://127.0.0.1:11434`.

```
                  [FastAPI Gateway]
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
[llama3.1:latest]   [llava:latest]   [nomic-embed-text]
  (8B Reasoning)      (7B Vision)       (Dense Vectors)
```

## Model Roles Summary
1. **LLaMA-3.1 8B Instruct:** Task planning, tool selection, synthesis, and compliance analysis.
2. **LLaVA v1.6 7B:** Photographic defect inspection and macroscopic crack diagnosis.
3. **Nomic Embed Text v1.5:** 768-dimensional dense vector embeddings for ChromaDB.
4. **Qwen-2.5 3B Instruct:** Auxiliary fast reasoning model resident on local disk.
