# 04. LLaVA v1.6 7B Multimodal Vision Model
**Status:** [VERIFIED ACTIVE]

- **Model Tag:** `llava:latest` (LLaVA-v1.6 7B)
- **Architecture:** CLIP-ViT-L/14 visual encoder + Vicuna-7B LLM
- **Where Loaded:** Local Ollama daemon (`http://127.0.0.1:11434/api/generate`)
- **Where Called:** `backend/app/agents/multimodal/vision_provider.py`
- **Why Used:** Enables visual defect analysis entirely locally without uploading photos to Google Vision or AWS Rekognition.
- **Task Types:** Detecting surface fatigue, cracks, corrosion, and thermal burns in equipment photos.
