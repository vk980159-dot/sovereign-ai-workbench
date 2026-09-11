# 04. Local LLaVA v1.6 Vision Inspection Engine
**Status:** [VERIFIED]

- **File Path:** `backend/app/agents/multimodal/vision_provider.py`: `LocalVisionProvider`
- **Endpoint:** `http://127.0.0.1:11434/api/generate` with model `llava:latest`.
- **Defect Detection Capabilities:** Analyzes bearing photos, identifying fatigue spalling, axial micro-cracking, and lubricant thermal degradation in 3.8 seconds on host hardware.
