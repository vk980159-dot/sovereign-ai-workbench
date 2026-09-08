"""
Local Tool Registry & Base Architecture (SIH26117).
Provides modular registration, execution contracts, schema validation,
and permission enforcement for all safe on-premise tools.
"""

from typing import Dict, Any, Callable, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.security.audit_logger import audit_logger


class ToolResult(BaseModel):
    """Encapsulates the deterministic outcome of a tool execution."""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


class ToolDefinition(BaseModel):
    """Declarative specification for an authorized sovereign tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    permission_level: str = "user"  # "user" or "admin"
    risk_level: str = "low"         # "low", "medium", "high"
    read_only: bool = True
    handler: Any = None             # Callable handler


class ToolRegistry:
    """
    Central registry managing authorized tool instances.
    Enforces security screening and audit hashing for every execution.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register_tool(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "permission_level": t.permission_level,
                "risk_level": t.risk_level,
                "read_only": t.read_only
            }
            for t in self._tools.values()
        ]

    async def execute_tool(
        self,
        name: str,
        inputs: Dict[str, Any],
        user_role: str = "user",
        user_id: Optional[str] = None
    ) -> ToolResult:
        from app.agents.security_gate import security_gate
        start_time = datetime.now(timezone.utc)

        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Tool '{name}' is not registered."
            )

        # 1. RBAC check
        if tool.permission_level == "admin" and user_role != "admin":
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error="Permission Denied: Administrative privileges required."
            )

        # 2. Security Gate check
        safe, reason = security_gate.validate_tool_call(name, inputs, user_role=user_role)
        if not safe:
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=f"Security Policy Rejection: {reason}"
            )

        # 3. Execution
        try:
            handler = tool.handler
            import inspect
            if inspect.iscoroutinefunction(handler):
                result_data = await handler(**inputs)
            else:
                result_data = handler(**inputs)

            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0

            # 4. Record to cryptographic audit ledger
            audit_logger.log_event(
                event_type="TOOL_EXECUTION",
                agent_name="ToolRegistry",
                action=name.upper(),
                details={"status": "SUCCESS", "elapsed_ms": round(elapsed_ms, 2)},
                input_data=str(inputs)[:200],
                output_data=str(result_data)[:200]
            )

            return ToolResult(
                tool_name=name,
                success=True,
                output=result_data,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
            audit_logger.log_event(
                event_type="TOOL_EXECUTION",
                agent_name="ToolRegistry",
                action=name.upper(),
                details={"status": "FAILED", "error": str(e)},
                input_data=str(inputs)[:200],
                output_data="ERROR"
            )
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=round(elapsed_ms, 2)
            )


# Global registry singleton
default_tool_registry = ToolRegistry()
