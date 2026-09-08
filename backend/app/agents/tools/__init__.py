"""
Tool Registry Package Initialization (SIH26117).
Registers all safe local tools into default_tool_registry.
"""

from .base import default_tool_registry, ToolDefinition, ToolResult
from .doc_tools import (
    local_document_search,
    local_document_reader,
    file_metadata,
    text_extractor,
    structured_data_reader
)
from .calc_tools import calculation_tool
from .artifact_tools import output_writer
from .sandbox_tools import sandbox_code_runner
from .verify_tools import verification_tool
from .deliverable_tools import (
    generate_docx_approval_note,
    generate_xlsx_calculation_sheet,
    generate_pptx_presentation,
    generate_pdf_report
)
from .multimodal_tools import (
    multimodal_document_reader,
    table_analyzer_tool
)

# Register Tool 1: local_document_search
default_tool_registry.register_tool(ToolDefinition(
    name="local_document_search",
    description="Searches local ChromaDB knowledge base for semantic evidence chunks.",
    input_schema={"query": "string", "top_k": "integer (optional)"},
    output_schema={"documents": "list", "count": "integer"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=local_document_search
))

# Register Tool 2: local_document_reader
default_tool_registry.register_tool(ToolDefinition(
    name="local_document_reader",
    description="Reads supported text or PDF documents from authorized local directories.",
    input_schema={"filename": "string", "max_characters": "integer (optional)"},
    output_schema={"content": "string", "characters": "integer", "sha256": "string"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=local_document_reader
))

# Register Tool 3: file_metadata
default_tool_registry.register_tool(ToolDefinition(
    name="file_metadata",
    description="Inspects file size, type, and SHA-256 cryptographic hash.",
    input_schema={"filename": "string"},
    output_schema={"size_bytes": "integer", "sha256": "string", "extension": "string"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=file_metadata
))

# Register Tool 4: text_extractor
default_tool_registry.register_tool(ToolDefinition(
    name="text_extractor",
    description="Extracts raw text content from PDF and text documents.",
    input_schema={"filename": "string"},
    output_schema={"content": "string", "characters": "integer"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=text_extractor
))

# Register Tool 5: calculation_tool
default_tool_registry.register_tool(ToolDefinition(
    name="calculation_tool",
    description="Performs deterministic arithmetic and mathematical calculations.",
    input_schema={"expression": "string"},
    output_schema={"result": "number", "status": "string"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=calculation_tool
))

# Register Tool 6: structured_data_reader
default_tool_registry.register_tool(ToolDefinition(
    name="structured_data_reader",
    description="Parses local CSV and JSON files safely.",
    input_schema={"filename": "string", "delimiter": "string (optional)", "max_rows": "integer (optional)"},
    output_schema={"format": "string", "rows": "list", "header": "list"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=structured_data_reader
))

# Register Tool 7: output_writer
default_tool_registry.register_tool(ToolDefinition(
    name="output_writer",
    description="Generates verifiable report or recommendation artifacts in designated output directory.",
    input_schema={"filename": "string", "content": "string", "title": "string (optional)"},
    output_schema={"filename": "string", "filepath": "string", "sha256": "string", "size_bytes": "integer"},
    permission_level="user",
    risk_level="medium",
    read_only=False,
    handler=output_writer
))

# Register Tool 8: verification_tool
default_tool_registry.register_tool(ToolDefinition(
    name="verification_tool",
    description="Verifies claims against evidence and checks artifact integrity.",
    input_schema={"claims": "list", "evidence_texts": "list", "artifact_filename": "string (optional)"},
    output_schema={"passed": "boolean", "claims_verified": "integer"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=verification_tool
))

# Register Tool 9: sandbox_code_runner
default_tool_registry.register_tool(ToolDefinition(
    name="sandbox_code_runner",
    description="Executes Python code in an isolated temporary sandbox with timeout and restrictions.",
    input_schema={"code": "string", "language": "string (optional)", "timeout_seconds": "number (optional)"},
    output_schema={"success": "boolean", "stdout": "string", "stderr": "string"},
    permission_level="user",
    risk_level="high",
    read_only=False,
    handler=sandbox_code_runner
))

# Register Tool 10: generate_docx_approval_note
default_tool_registry.register_tool(ToolDefinition(
    name="generate_docx_approval_note",
    description="Generates an authentic Word (.docx) Approval Note with styled layout, tables, watermark, and SHA-256 integrity hash.",
    input_schema={"title": "string", "reference_doc": "string", "executive_summary": "string", "findings": "list", "sop_comparison": "string", "risks": "list", "recommendations": "list"},
    output_schema={"filename": "string", "file_path": "string", "artifact_type": "string", "sha256": "string", "size_bytes": "integer"},
    permission_level="user",
    risk_level="medium",
    read_only=False,
    handler=generate_docx_approval_note
))

# Register Tool 11: generate_xlsx_calculation_sheet
default_tool_registry.register_tool(ToolDefinition(
    name="generate_xlsx_calculation_sheet",
    description="Generates an authentic Excel (.xlsx) Calculation Workbook with active formulas, styled headers, and evidence auditing tab.",
    input_schema={"title": "string", "rows_data": "list", "summary_calculations": "dict (optional)", "evidence_records": "list (optional)"},
    output_schema={"filename": "string", "file_path": "string", "artifact_type": "string", "sha256": "string", "size_bytes": "integer"},
    permission_level="user",
    risk_level="medium",
    read_only=False,
    handler=generate_xlsx_calculation_sheet
))

# Register Tool 12: generate_pptx_presentation
default_tool_registry.register_tool(ToolDefinition(
    name="generate_pptx_presentation",
    description="Generates an authentic PowerPoint (.pptx) briefing deck with dark slate theme, KPI cards, and citation tracking.",
    input_schema={"title": "string", "executive_summary": "string", "findings": "list", "risks": "list", "recommendations": "list"},
    output_schema={"filename": "string", "file_path": "string", "artifact_type": "string", "sha256": "string", "size_bytes": "integer"},
    permission_level="user",
    risk_level="medium",
    read_only=False,
    handler=generate_pptx_presentation
))

# Register Tool 13: generate_pdf_report
default_tool_registry.register_tool(ToolDefinition(
    name="generate_pdf_report",
    description="Generates an authentic PDF Compliance Report using ReportLab with clean styling, table formatting, and SHA-256 verification.",
    input_schema={"title": "string", "executive_summary": "string", "findings": "list", "sop_comparison": "string", "recommendations": "list"},
    output_schema={"filename": "string", "file_path": "string", "artifact_type": "string", "sha256": "string", "size_bytes": "integer"},
    permission_level="user",
    risk_level="medium",
    read_only=False,
    handler=generate_pdf_report
))

# Register Tool 14: multimodal_document_reader
default_tool_registry.register_tool(ToolDefinition(
    name="multimodal_document_reader",
    description="Reads multimodal documents including native PDFs, scanned PDFs (with local OCR), images, and structured documents.",
    input_schema={"filename": "string", "task_id": "string (optional)"},
    output_schema={"found": "boolean", "filename": "string", "doc_type": "string", "extracted_text_preview": "string", "evidence_count": "integer"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=multimodal_document_reader
))

# Register Tool 15: table_analyzer_tool
default_tool_registry.register_tool(ToolDefinition(
    name="table_analyzer_tool",
    description="Parses and summarizes structured tables (CSV, JSON) and extracts statistical metrics.",
    input_schema={"filename": "string", "max_rows": "integer (optional)"},
    output_schema={"format": "string", "row_count": "integer", "summary": "dict"},
    permission_level="user",
    risk_level="low",
    read_only=True,
    handler=table_analyzer_tool
))

