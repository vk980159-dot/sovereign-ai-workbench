# 01. LLaMA-3.1 8B Instruct Model
**Status:** [VERIFIED ACTIVE]

- **Model Tag:** `llama3.1:latest` (Meta LLaMA-3.1 8B Instruct)
- **Quantization:** Q4_K_M (4-bit medium quantization, ~4.7 GB disk size)
- **Where Loaded:** Local Ollama daemon (`http://127.0.0.1:11434/api/chat`)
- **Where Called:** `backend/app/agents/planner.py`, `nodes.py` (synthesizer)
- **Why Used:** State-of-the-art open-weight instruction following, structured JSON emission, and engineering reasoning.
- **Context Window:** 8,192 tokens.
- **Task Types:** Task planning, tool parameter generation, document summarization, executive memo drafting.
