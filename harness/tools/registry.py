"""Tool registry - central catalog for all available tools.

The ToolRegistry is the single source of truth for what tools
are available to the agent. It provides:
- Registration and lookup of tools by name
- Listing all tools (for system prompt generation)
- Executing tools by name with error handling
"""
from __future__ import annotations
import logging
from typing import Optional
from harness.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for managing tools.

    The agent loop uses this to:
    1. Get tool descriptions for the system prompt
    2. Look up and execute tools the model calls
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        if tool.name in self._tools:
            logger.warning(f"Overwriting tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def execute(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name with the given arguments.

        Returns a ToolResult. If the tool is not found or execution
        fails, returns a ToolResult with success=False.
        """
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' not found. Available: {list(self._tools.keys())}",
            )
        try:
            return tool.execute(**arguments)
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return ToolResult(success=False, output="", error=str(e))

    def get_tools_description(self) -> str:
        """Generate a combined description of all tools for the system prompt."""
        if not self._tools:
            return "No tools available."
        lines = [tool.to_description() for tool in self._tools.values()]
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
