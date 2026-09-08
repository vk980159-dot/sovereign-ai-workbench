"""
Security Gate & Policy Enforcement Node (SIH26117).
Validates all user tasks and tool operations prior to execution.
Enforces read-only safety, path traversal protection, sandboxed execution,
and denies arbitrary filesystem deletion, shell commands, or external network requests.
"""

import os
import re
from typing import Tuple, Dict, Any, Optional
from app.config import settings, BASE_DIR
from app.security.audit_logger import audit_logger

FORBIDDEN_COMMAND_PATTERNS = [
    re.compile(r"\b(rm|del|rmdir|erase|format|mkfs)\b", re.IGNORECASE),
    re.compile(r"\b(curl|wget|nc|netcat|ssh|ftp|scp)\b", re.IGNORECASE),
    re.compile(r"\b(shutdown|reboot|poweroff|halt)\b", re.IGNORECASE),
    re.compile(r"\b(__import__|os\.system|subprocess\.Popen|pty\.spawn)\b", re.IGNORECASE),
    re.compile(r"\b(shutil\.rmtree|os\.remove|os\.unlink|open\s*\(.*['\"][wa\+])\b", re.IGNORECASE)
]


class SecurityGate:
    """
    Autonomous sovereign security and policy enforcement engine.
    Ensures least privilege and strict containment across all agent activities.
    """

    ALLOWED_READ_EXTENSIONS = {".txt", ".pdf", ".md", ".json", ".csv", ".log"}

    def __init__(self):
        self.allowed_base_dirs = [
            os.path.abspath(settings.UPLOAD_DIR),
            os.path.abspath(settings.DEMO_DATA_DIR),
            os.path.abspath(settings.OUTPUT_DIR),
            os.path.abspath(BASE_DIR)
        ]

    def _is_safe_path(self, target_path: str, allow_root: bool = False) -> Tuple[bool, str]:
        """Validates that a filesystem path does not escape designated directories."""
        if ".." in target_path or target_path.startswith("/") and not os.path.isabs(target_path):
            return False, "Path traversal pattern detected (relative navigation '..' forbidden)."

        try:
            abs_target = os.path.abspath(target_path)
        except Exception as e:
            return False, f"Invalid filesystem path: {str(e)}"

        # Check if inside any allowed directory
        is_inside = any(abs_target.startswith(base) for base in self.allowed_base_dirs)
        if not is_inside:
            return False, f"Access denied: Path '{target_path}' is outside designated workspace boundaries."

        return True, "Path authorized."

    def validate_task(self, query: str, user_role: str = "user") -> Tuple[bool, str]:
        """
        Validates the incoming user query for safety violations or destructive requests.
        """
        lower_q = query.lower()

        # Check for explicitly forbidden system destructive operations
        if any(p.search(lower_q) for p in FORBIDDEN_COMMAND_PATTERNS[:3]):
            audit_logger.log_event(
                event_type="SECURITY_DECISION",
                agent_name="SecurityGate",
                action="TASK_REJECTED",
                details={"query": query[:200], "reason": "Destructive system command detected"},
                input_data=query[:100],
                output_data="DENIED"
            )
            return False, "Security Policy Violation: Destructive operations are strictly prohibited."

        audit_logger.log_event(
            event_type="SECURITY_DECISION",
            agent_name="SecurityGate",
            action="TASK_APPROVED",
            details={"user_role": user_role},
            input_data=query[:100],
            output_data="ALLOWED"
        )
        return True, "Task approved by Sovereign Security Gate."

    def validate_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_role: str = "user"
    ) -> Tuple[bool, str]:
        """
        Validates individual tool calls against policy rules.
        """
        # 1. READ / KNOWLEDGE SEARCH TOOLS: Allowed by default
        if tool_name in ("local_document_search", "calculation_tool", "verification_tool"):
            return True, "Operation authorized."

        # 2. DOCUMENT READING TOOLS: Strict path containment check
        if tool_name in ("local_document_reader", "file_metadata", "text_extractor", "structured_data_reader"):
            filepath = tool_input.get("filename") or tool_input.get("path") or ""
            if not filepath:
                return False, "Missing required target filename."
            
            # Resolve relative filenames inside DEMO_DATA_DIR or UPLOAD_DIR
            if not os.path.isabs(filepath):
                # Simple filename, verify it does not contain separators
                if os.path.sep in filepath or "/" in filepath or ".." in filepath:
                    return False, "Path traversal characters detected."
                return True, "File read authorized."

            safe, msg = self._is_safe_path(filepath)
            if not safe:
                audit_logger.log_event(
                    event_type="SECURITY_DECISION",
                    agent_name="SecurityGate",
                    action="TOOL_CALL_DENIED",
                    details={"tool": tool_name, "reason": msg},
                    input_data=filepath,
                    output_data="DENIED"
                )
                return False, msg
            return True, "Operation authorized."

        # 3. OUTPUT GENERATION TOOL: Strictly confined to OUTPUT_DIR
        if tool_name == "output_writer":
            filename = tool_input.get("filename", "")
            if not filename or os.path.sep in filename or "/" in filename or ".." in filename:
                return False, "Invalid artifact filename. Must be a clean base filename."
            return True, "Output artifact generation authorized."

        # 4. SANDBOX CODE EXECUTION: Allowed with restrictions
        if tool_name == "sandbox_code_runner":
            code = tool_input.get("code", "")
            for pattern in FORBIDDEN_COMMAND_PATTERNS:
                if pattern.search(code):
                    audit_logger.log_event(
                        event_type="SECURITY_DECISION",
                        agent_name="SecurityGate",
                        action="TOOL_CALL_DENIED",
                        details={"tool": tool_name, "reason": "Restricted execution pattern detected"},
                        input_data=code[:100],
                        output_data="DENIED"
                    )
                    return False, "Code contains restricted system execution patterns."
            return True, "Sandboxed execution authorized."

        # Check registered tools in tool registry
        from app.agents.tools.base import default_tool_registry
        reg_tool = default_tool_registry.get_tool(tool_name)
        if reg_tool:
            if reg_tool.permission_level == "admin" and user_role != "admin":
                return False, "Administrative privileges required."
            return True, f"Authorized tool '{tool_name}'."

        # Unknown tool or unhandled operation
        return False, f"Unknown or unauthorized tool '{tool_name}'."


# Global security gate singleton
security_gate = SecurityGate()
