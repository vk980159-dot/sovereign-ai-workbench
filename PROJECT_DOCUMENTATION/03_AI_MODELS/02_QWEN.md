# 02. Qwen-2.5 3B Instruct Model
**Status:** [INSTALLED BUT NOT ACTIVELY USED]

- **Model Tag:** `qwen2.5:3b-instruct` (Alibaba Qwen-2.5 3B Instruct)
- **Quantization:** Q4_K_M (~1.9 GB disk size)
- **Where Loaded:** Present in local Ollama storage (`~/.ollama/models`)
- **Status Audit:** The model is physically downloaded and runnable in Ollama. However, `backend/app/agents/model_provider.py` hardcodes `default_model = "llama3.1:latest"`.
- **Intended Role:** Fast, low-latency reasoning for simple single-step classification tasks where 8B parameter overhead is unnecessary.
