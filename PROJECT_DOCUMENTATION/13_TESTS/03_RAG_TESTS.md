# 03. RAG & Knowledge Base Test Suite
**Status:** [VERIFIED]

- **File:** `backend/tests/test_multimodal_deliverables.py`, `test_pii.py`
- **Tests Covered:**
  - `test_chromadb_embedding_and_retrieval`: Validates cosine similarity search.
  - `test_pii_redaction_prior_to_indexing`: Confirms Aadhaar/PAN masking.
  - `test_grounding_verification`: Asserts claims are anchored in SOP chunks.
