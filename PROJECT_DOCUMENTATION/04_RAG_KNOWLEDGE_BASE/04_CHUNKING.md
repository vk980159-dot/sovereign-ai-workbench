# 04. Document Chunking Strategy
**Status:** [VERIFIED]

## Chunking Parameters
- **Chunk Size:** 500 characters.
- **Chunk Overlap:** 50 characters (10% sliding window).
- **Metadata Tagging:** Each chunk retains `source_file`, `page_number`, `chunk_index`, and `sha256_hash`.
- **Limitation:** Uses character-based sliding window; semantic header-aware chunking is not yet active.
