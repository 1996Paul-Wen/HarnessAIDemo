"""Built-in tools that ship with the demo.

These tools demonstrate how to implement the BaseTool interface:
- CalculatorTool: evaluate mathematical expressions
- DateTimeTool: get current date/time
- FileOpsTool: basic file system operations (list, read)
"""
from __future__ import annotations
import os, datetime
from harness.tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Evaluate mathematical expressions safely."""
    name = "calculator"
    description = "Evaluate a mathematical expression. Supports +, -, *, /, **, %, ()."
    parameters = {"expression": "string - math expression, e.g. '2 + 3 * 4'"}

    def execute(self, expression: str = "", **kw) -> ToolResult:
        try:
            # Only allow safe math characters
            import re
            if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%\^\,]+$', expression):
                return ToolResult(False, "", "Invalid characters in expression")
            # Replace ^ with ** for power
            expr = expression.replace("^", "**")
            result = eval(expr, {"__builtins__": {}}, {})
            return ToolResult(True, str(result))
        except Exception as e:
            return ToolResult(False, "", f"Calculation error: {e}")


class DateTimeTool(BaseTool):
    """Get current date and/or time."""
    name = "datetime"
    description = "Get current date and time information."
    parameters = {"query": "string - 'date', 'time', or 'datetime'"}

    def execute(self, query: str = "datetime", **kw) -> ToolResult:
        now = datetime.datetime.now()
        if query == "date":
            return ToolResult(True, now.strftime("%Y-%m-%d (%A)"))
        elif query == "time":
            return ToolResult(True, now.strftime("%H:%M:%S"))
        else:
            return ToolResult(True, now.strftime("%Y-%m-%d %H:%M:%S (%A)"))


class FileOpsTool(BaseTool):
    """Basic file system operations (read-only for safety)."""
    name = "file_ops"
    description = "Perform file operations: 'list' files in a directory, or 'read' a file."
    parameters = {
        "operation": "string - 'list' or 'read'",
        "path": "string - file or directory path",
    }

    def execute(self, operation: str = "list", path: str = ".", **kw) -> ToolResult:
        try:
            if operation == "list":
                if os.path.isdir(path):
                    entries = os.listdir(path)
                    return ToolResult(True, "\n".join(sorted(entries)[:50]))
                return ToolResult(False, "", f"Not a directory: {path}")
            elif operation == "read":
                if os.path.isfile(path):
                    with open(path, "r") as f:
                        content = f.read(4096)
                    return ToolResult(True, content)
                return ToolResult(False, "", f"File not found: {path}")
            else:
                return ToolResult(False, "", f"Unknown operation: {operation}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def register_default_tools(registry) -> None:
    """Register all built-in tools into a ToolRegistry."""
    from harness.tools.registry import ToolRegistry
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    registry.register(FileOpsTool())
