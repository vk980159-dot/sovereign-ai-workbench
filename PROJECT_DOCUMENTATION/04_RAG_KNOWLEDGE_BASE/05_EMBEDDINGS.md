# 05. Dense Vector Embeddings
**Status:** [VERIFIED]

## Embedding Generation
- **Model:** `nomic-embed-text:latest` running locally via Ollama.
- **Dimensionality:** 768 dimensions per vector.
- **Normalization:** Vectors are L2-normalized, allowing cosine similarity to be computed as an inner product.
- **Batching:** Chunks are embedded in batches of 16 to optimize local VRAM/RAM utilization.
