"""Long-term memory: persistent storage with TF-IDF retrieval.

Long-term memory persists across sessions and uses a retrieval
mechanism to find relevant memories. This implementation uses
TF-IDF (Term Frequency - Inverse Document Frequency) for
keyword-based semantic search.

In production systems, this would use vector embeddings + a
vector database (e.g., FAISS, Pinecone, Chroma). The TF-IDF
approach here demonstrates the concept without heavy dependencies.

Key insight: Not all memories are equally relevant to every query.
The retrieval step is crucial - it determines which past experiences
inform the current response.
"""
from __future__ import annotations
import json, math, os, logging
from collections import Counter
from harness.memory.base import BaseMemory, MemoryItem

logger = logging.getLogger(__name__)


class LongTermMemory(BaseMemory):
    """Persistent long-term memory with TF-IDF retrieval."""

    def __init__(self, storage_path: str = "memory_store.json"):
        self.storage_path = storage_path
        self._items: list[MemoryItem] = []
        self._load()

    def add(self, role: str, content: str, **metadata) -> None:
        item = MemoryItem(role=role, content=content, metadata=metadata)
        self._items.append(item)
        self._save()

    def get_recent(self, n: int) -> list[MemoryItem]:
        return self._items[-n:]

    def search(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        """TF-IDF based retrieval."""
        if not self._items:
            return []

        query_terms = query.lower().split()
        n_docs = len(self._items)
        # Compute IDF for each term
        doc_freq = Counter()
        for item in self._items:
            words = set(item.content.lower().split())
            for w in query_terms:
                if w in words:
                    doc_freq[w] += 1

        scores = []
        for item in self._items:
            words = item.content.lower().split()
            tf = Counter(words)
            score = 0.0
            for term in query_terms:
                if term in tf:
                    term_tf = tf[term] / len(words)
                    idf = math.log((n_docs + 1) / (doc_freq.get(term, 0) + 1)) + 1
                    score += term_tf * idf
            scores.append((score, item))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scores[:top_k] if score > 0]

    def clear(self) -> None:
        self._items.clear()
        self._save()

    def get_all(self) -> list[MemoryItem]:
        return list(self._items)

    def _save(self) -> None:
        try:
            data = [
                {"role": i.role, "content": i.content,
                 "timestamp": i.timestamp, "metadata": i.metadata}
                for i in self._items
            ]
            with open(self.storage_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            self._items = [
                MemoryItem(
                    role=d["role"], content=d["content"],
                    timestamp=d.get("timestamp", 0),
                    metadata=d.get("metadata", {}),
                )
                for d in data
            ]
            logger.info(f"Loaded {len(self._items)} items from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")

    def __len__(self) -> int:
        return len(self._items)
