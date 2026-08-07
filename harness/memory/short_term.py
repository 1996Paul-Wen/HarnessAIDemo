"""Short-term memory: a bounded buffer of recent messages.

This is analogous to working memory - it holds the most recent
conversation context that the model can directly reference.
When the buffer is full, oldest messages are dropped (FIFO).

Key insight: LLMs have a finite context window. Short-term memory
ensures we only send the most relevant recent messages, keeping
within token limits while maintaining conversational coherence.
"""
from __future__ import annotations
from collections import deque
from harness.memory.base import BaseMemory, MemoryItem


class ShortTermMemory(BaseMemory):
    """Buffer-based short-term memory with FIFO eviction."""

    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self._buffer: deque[MemoryItem] = deque(maxlen=capacity)

    def add(self, role: str, content: str, **metadata) -> None:
        self._buffer.append(MemoryItem(role=role, content=content, metadata=metadata))

    def get_recent(self, n: int) -> list[MemoryItem]:
        items = list(self._buffer)
        return items[-n:] if n < len(items) else items

    def search(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        # Simple keyword matching for short-term (full semantic search in long-term)
        query_words = set(query.lower().split())
        scored = []
        for item in self._buffer:
            words = set(item.content.lower().split())
            overlap = len(query_words & words)
            if overlap > 0:
                scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def clear(self) -> None:
        self._buffer.clear()

    def get_all(self) -> list[MemoryItem]:
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)
