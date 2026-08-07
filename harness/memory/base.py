"""Base classes for the memory system.

Memory is what gives the agent continuity across turns and sessions.
The memory system has two levels:
- Short-term: recent conversation context (like working memory)
- Long-term: persistent knowledge and facts (like episodic memory)

Each memory item stores the message data plus optional metadata
for retrieval (timestamps, importance scores, embeddings, etc).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class MemoryItem:
    """A single item stored in memory."""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class BaseMemory(ABC):
    """Abstract base class for memory implementations."""

    @abstractmethod
    def add(self, role: str, content: str, **metadata) -> None:
        """Store a new item in memory."""
        ...

    @abstractmethod
    def get_recent(self, n: int) -> list[MemoryItem]:
        """Get the n most recent items."""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        """Search memory for items relevant to the query."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all memory."""
        ...

    @abstractmethod
    def get_all(self) -> list[MemoryItem]:
        """Get all items in memory."""
        ...

    def get_context_string(self) -> str:
        """Format recent memory as a string for the prompt."""
        items = self.get_recent(20)
        if not items:
            return ""
        lines = []
        for item in items:
            lines.append(f"{item.role}: {item.content}")
        return "\n".join(lines)
