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
