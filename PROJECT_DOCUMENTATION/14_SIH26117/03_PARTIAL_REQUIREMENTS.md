# 03. Partially Implemented Requirements (5 / 30)
**Status:** [PARTIALLY VERIFIED]

1. **Task-Based Dynamic Model Routing:** Deterministic tool routing exists; dynamic token-complexity classifier (LLaMA vs Qwen) is not active.
2. **Handwritten Document OCR:** Reads block handwriting (~85% accuracy); cursive handwriting exhibits elevated character error rates (~35%).
3. **Engineering Drawings (CAD):** Ingests PDF/PNG schematics; native vector CAD formats (.dwg, .dxf) require prior rasterization.
4. **Semantic Chunking:** Uses 500-char sliding window chunking; semantic header-hierarchy chunking is not enabled.
5. **Sandbox Isolation:** Python in-process AST sandboxing implemented; OS-level Docker container virtualization per tool step is not used.
