# 05. Master AI Model Index
**Status:** [VERIFIED]

| Model Tag | Provider / Engine | Architecture | Parameters | Resident Location | Actual Usage |
|-----------|-------------------|--------------|------------|-------------------|--------------|
| `llama3.1:latest` | Ollama (`/api/chat`) | Meta LLaMA-3.1 Q4_K_M | 8.03 Billion | `~/.ollama/models` | Task planning, tool schema generation, executive text synthesis |
| `llava:latest` | Ollama (`/api/generate`) | CLIP-ViT-L/14 + Vicuna | 7.06 Billion | `~/.ollama/models` | Photographic machinery defect inspection, crack diagnosis |
| `nomic-embed-text:latest`| Ollama (`/api/embeddings`)| Dense transformer | 137 Million | `~/.ollama/models` | 768-dim dense embeddings for ChromaDB RAG |
| `qwen2.5:3b-instruct` | Ollama (`/api/chat`) | Qwen-2.5 Q4_K_M | 3.09 Billion | `~/.ollama/models` | Auxiliary fast reasoning model (Downloaded, runnable) |
