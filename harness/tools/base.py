"""Base classes for the tool system.

Tools are the way the agent interacts with the external world.
Each tool has:
- A name (used by the model to reference it)
- A description (shown to the model so it knows when to use it)
- A parameter schema (tells the model what arguments to provide)
- An execute method (runs the actual logic)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolResult:
    """Result of executing a tool.

    Attributes:
        success: Whether execution succeeded
        output: The result data (string shown to the model)
        error: Error message if success is False
    """
    success: bool
    output: str
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all tools.

    To create a custom tool, subclass this and implement:
    - name, description, parameters (class attributes)
    - execute(**kwargs) -> ToolResult
    """

    name: str = ""
    description: str = ""
    parameters: dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given arguments."""
        ...

    def to_description(self) -> str:
        """Generate a human-readable description for the system prompt.

        This text is inserted into the prompt so the LLM knows:
        - What the tool does
        - What arguments it accepts
        - When to use it
        """
        params_str = ", ".join(
            f"{k}: {v}" for k, v in self.parameters.items()
        )
        return f"- {self.name}({params_str}): {self.description}"

    def to_schema(self) -> dict:
        """Generate a JSON schema-like dict for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
