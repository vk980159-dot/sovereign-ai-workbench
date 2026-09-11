# 09. Document Metadata & Citation Tracking
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/multimodal/evidence.py`: `EvidenceCorrelator`

## 2. Citation Schema
Every retrieved snippet is tagged with an evidence anchor: `[Source: equipment_sop.md, Page 4, Section 4.2]`.
These citations are injected into the final Word and PDF deliverables, enabling engineers to verify where every factual claim originated.
