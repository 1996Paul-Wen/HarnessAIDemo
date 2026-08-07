"""Hybrid memory: combines short-term and long-term memory.

This is the recommended memory implementation for production use.
It maintains:
- Short-term buffer for recent conversation context
- Long-term store for persistent knowledge

When building context, it merges both sources:
1. Short-term provides the most recent messages (always included)
2. Long-term provides relevant past memories (retrieved by search)

This mirrors how human memory works: you always remember what
was just said (short-term), and sometimes recall older experiences
that are relevant to the current topic (long-term retrieval).
"""
from __future__ import annotations
from harness.memory.base import BaseMemory, MemoryItem
from harness.memory.short_term import ShortTermMemory
from harness.memory.long_term import LongTermMemory


class HybridMemory(BaseMemory):
    """Combines short-term buffer with long-term persistent storage."""

    def __init__(
        self,
        short_term_capacity: int = 20,
        storage_path: str = "memory_store.json",
    ):
        self.short_term = ShortTermMemory(capacity=short_term_capacity)
        self.long_term = LongTermMemory(storage_path=storage_path)

    def add(self, role: str, content: str, **metadata) -> None:
        self.short_term.add(role, content, **metadata)
        # Only persist user and assistant messages to long-term
        if role in ("user", "assistant"):
            self.long_term.add(role, content, **metadata)

    def get_recent(self, n: int) -> list[MemoryItem]:
        return self.short_term.get_recent(n)

    def search(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        # Search long-term memory for relevant past experiences
        return self.long_term.search(query, top_k)

    def get_relevant_context(self, query: str, n_recent: int = 10, n_relevant: int = 3) -> str:
        """Build a context string combining recent and relevant memories.

        This is the key method used by the context manager:
        1. Include the n most recent messages (short-term)
        2. Include relevant past memories (long-term retrieval)
        """
        parts = []

        # Recent conversation
        recent = self.get_recent(n_recent)
        if recent:
            parts.append("## Recent Conversation")
            for item in recent:
                parts.append(f"{item.role}: {item.content}")

        # Relevant long-term memories
        relevant = self.search(query, top_k=n_relevant)
        # Filter out items already in recent
        recent_contents = {item.content for item in recent}
        relevant = [r for r in relevant if r.content not in recent_contents]
        if relevant:
            parts.append("")
            parts.append("## Relevant Past Memories")
            for item in relevant:
                parts.append(f"- {item.content}")

        return "\n".join(parts)

    def clear(self) -> None:
        self.short_term.clear()
        self.long_term.clear()

    def get_all(self) -> list[MemoryItem]:
        return self.long_term.get_all()

    def __len__(self) -> int:
        return len(self.short_term) + len(self.long_term)
