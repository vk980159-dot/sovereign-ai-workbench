# 10. Complete End-to-End RAG Trace
**Status:** [VERIFIED]

```
Document File ('equipment_sop.md')
       │
       ▼ (PyMuPDF / Text Reader)
Raw Text Extracted
       │
       ▼ (PIIRedactor: regex scrub)
Cleaned Sanitized Text
       │
       ▼ (Chunking: 500 chars / 50 overlap)
Document Chunks + Metadata
       │
       ▼ (Ollama /api/embeddings: nomic-embed-text)
768-Dimensional Dense Vectors
       │
       ▼ (ChromaDB PersistentClient)
Indexed in 'sovereign_knowledge_base' (chroma_db/)
       │
       ▲
       │ (Cosine Similarity Search)
Agent Query: "vibration limit SOP-IND-702"
       │
       ▼
Retrieved Chunk: "Section 4.2: Maximum Vibration = 5.0 mm/s"
       │
       ▼ (Injected into LLaMA-3.1 Context)
Grounded Engineering Decision (Emergency Shutdown Mandate)
```
