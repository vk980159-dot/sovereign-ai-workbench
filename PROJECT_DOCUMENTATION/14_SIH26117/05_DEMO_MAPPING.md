# 05. SIH Demonstration Workflow Mapping
**Status:** [VERIFIED]

The 1-Click Judge Demo Mode (`POST /api/judge-demo`) exercises all major SIH pillars:
1. Ingests 2-page scanned turbine report (`scanned_turbine_inspection_report.pdf`).
2. Extracts measured vibration reading (8.42 mm/s) via local Tesseract OCR v5.4.0.
3. Retrieves SOP-IND-702 vibration limit (5.0 mm/s) via ChromaDB local RAG.
4. Ingests bearing photo (`inspection_photo.png`) -> LLaVA identifies inner race fatigue spalling.
5. Sandboxed AST math calculates deviation: `(8.42 - 5.0) / 5.0 * 100 = 68.4%`.
6. Verifier flags emergency shutdown clause; compiles Word approval memo, Excel calculation sheet, PowerPoint briefing, and PDF report in ~15 seconds.
