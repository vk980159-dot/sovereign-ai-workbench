# 03. Image Preprocessing & Transformation
**Status:** [VERIFIED]

- **File Path:** `backend/app/agents/multimodal/ocr_provider.py`, `vision_provider.py`
- **Processing Operations:**
  - Converts RGBA/color images to grayscale for OCR contrast enhancement.
  - Automatically downsizes high-resolution inspection photos exceeding 1024x1024 to preserve VRAM during LLaVA inference.
  - Converts image bytes to Base64 data strings for JSON transport to Ollama.
