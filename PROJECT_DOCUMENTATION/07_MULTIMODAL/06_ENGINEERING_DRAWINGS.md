# 06. Engineering Drawings & Schematics
**Status:** [PARTIALLY VERIFIED]

- **Current Implementation:** PyMuPDF rasterization + LLaVA visual inspection on PDF/PNG schematics.
- **Verified Capabilities:** Inspects component callouts, pipe diagrams, and crack locations in raster diagrams.
- **Identified Gap:** Does not parse native vector CAD formats (.dwg, .dxf, STEP) directly without prior conversion to PDF or raster image.
