"""Session Manager - manages multiple independent conversation sessions.

A Session represents an isolated conversation with its own:
- Conversation history (short-term memory)
- Long-term memory (persistent across the session)
- Metadata (creation time, title, etc)

The SessionManager allows:
- Creating multiple sessions
- Switching between sessions (like browser tabs)
- Listing all sessions
- Deleting sessions

Storage format (Append-Only JSONL):
  Each session uses two files under the storage directory:
    - <id>/meta.json       Session metadata (id, title, timestamps, etc.)
    - <id>/messages.jsonl  One JSON line per message, append-only (O(1) writes)

Why multi-session matters:
- Different topics need different contexts
- Users often work on multiple things simultaneously
- Each session maintains its own state
- Prevents context pollution between unrelated conversations

Analogy: Sessions are like different rooms in a house.
You have a "coding room" and a "writing room" - each has
its own tools and context.
"""
from __future__ import annotations
import json, os, time, uuid, logging
from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from harness.memory.base import BaseMemory

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """A single conversation session with its own state."""
    id: str
    title: str
    created_at: float = field(default_factory=time.time)
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    memory: Optional[Any] = field(default=None, repr=False, compare=False)
    _on_message: Optional[callable] = field(default=None, repr=False, compare=False)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to in-memory history and persist via callback."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        self.messages.append(msg)
        if self._on_message:
            self._on_message(msg)

    def get_history(self, n: int = 20) -> list[dict]:
        return self.messages[-n:]

    def to_dict(self) -> dict:
        """Serialize metadata only (messages live in JSONL)."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            title=data.get("title", "Untitled"),
            created_at=data.get("created_at", 0),
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Manages multiple conversation sessions with append-only persistence.

    Storage layout (one directory per session)::

        .sessions/
          global_memory.json  - shared across all sessions (user preferences, facts)
          <session_id>/
            meta.json       - session metadata (rewritten on title/metadata change)
            messages.jsonl  - one JSON object per line, append-only
            memory.json     - isolated long-term memory for this session
    """

    def __init__(self, storage_dir: str = ".sessions"):
        self.storage_dir = storage_dir
        self._sessions: dict[str, Session] = {}
        self._active_session_id: Optional[str] = None
        self._global_memory: Optional[Any] = None
        os.makedirs(storage_dir, exist_ok=True)
        self._load_all()

    # -- Public API -----------------------------------------------------------

    def create_session(self, title: str = "New Session") -> Session:
        """Create a new session and make it active."""
        session_id = str(uuid.uuid4())[:8]
        session = Session(id=session_id, title=title)
        self._bind_session(session)
        self._sessions[session_id] = session
        self._active_session_id = session_id
        self._save_meta(session)
        logger.info(f"Created session: {session_id} - {title}")
        return session

    def get_memory(self, session_id: Optional[str] = None) -> "BaseMemory":
        """Get the memory instance for a session (lazy-initialized, isolated per session).

        If session_id is None, uses the active session.
        Each session gets its own HybridMemory with a dedicated storage file,
        ensuring no memory leakage between sessions.
        """
        sid = session_id or self._active_session_id
        if sid is None:
            raise ValueError("No active session and no session_id provided")
        session = self._sessions.get(sid)
        if session is None:
            raise ValueError(f"Session not found: {sid}")
        if session.memory is None:
            from harness.memory.hybrid import HybridMemory
            storage_path = os.path.join(
                self._session_dir(session), "memory.json"
            )
            session.memory = HybridMemory(storage_path=storage_path)
        return session.memory

    @property
    def global_memory(self) -> "BaseMemory":
        """Get the global memory shared across all sessions (lazy-initialized).

        Global memory stores user-level knowledge that applies to every session:
        - User preferences ("I prefer concise answers")
        - User facts ("I'm a senior backend engineer")
        - Cross-cutting knowledge useful regardless of session topic
        """
        if self._global_memory is None:
            from harness.memory.hybrid import HybridMemory
            storage_path = os.path.join(self.storage_dir, "global_memory.json")
            self._global_memory = HybridMemory(storage_path=storage_path)
        return self._global_memory

    def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Search across global + session memory, returning combined results.

        Returns a list of dicts with 'source' ('global' or 'session') and
        'content' keys, deduplicated and sorted by relevance.
        """
        sid = session_id or self._active_session_id
        seen_contents: set[str] = set()
        results: list[dict] = []

        # 1. Global memory results (shared across sessions)
        for item in self.global_memory.search(query, top_k=top_k):
            if item.content not in seen_contents:
                seen_contents.add(item.content)
                results.append({"source": "global", "content": item.content, "role": item.role})

        # 2. Session-specific memory results
        if sid and sid in self._sessions:
            session_mem = self._sessions[sid].memory
            if session_mem is not None:
                for item in session_mem.search(query, top_k=top_k):
                    if item.content not in seen_contents:
                        seen_contents.add(item.content)
                        results.append({"source": "session", "content": item.content, "role": item.role})

        return results[:top_k]

    def switch_session(self, session_id: str) -> Session:
        """Switch to a different session."""
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        self._active_session_id = session_id
        return self._sessions[session_id]

    def get_active(self) -> Optional[Session]:
        """Get the currently active session."""
        if self._active_session_id:
            return self._sessions.get(self._active_session_id)
        return None

    def list_sessions(self) -> list[Session]:
        """List all sessions."""
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its stored data."""
        self._sessions.pop(session_id, None)
        session_dir = os.path.join(self.storage_dir, session_id)
        for fname in ("meta.json", "messages.jsonl", "memory.json"):
            path = os.path.join(session_dir, fname)
            if os.path.exists(path):
                os.remove(path)
        if os.path.isdir(session_dir):
            try:
                os.rmdir(session_dir)
            except OSError:
                pass  # directory not empty, leave it
        if self._active_session_id == session_id:
            self._active_session_id = None

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session (in-memory + append to JSONL log)."""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        session.add_message(role, content)  # callback handles JSONL append

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a session."""
        session = self._sessions.get(session_id)
        if session:
            session.title = new_title
            self._save_meta(session)

    # -- Persistence ----------------------------------------------------------

    def _bind_session(self, session: Session) -> None:
        """Inject the JSONL append callback into a session."""
        session._on_message = lambda msg: self._append_message(session, msg)

    def _session_dir(self, session: Session) -> str:
        """Return (and create) the storage directory for a session."""
        path = os.path.join(self.storage_dir, session.id)
        os.makedirs(path, exist_ok=True)
        return path

    def _messages_path(self, session: Session) -> str:
        return os.path.join(self._session_dir(session), "messages.jsonl")

    def _meta_path(self, session: Session) -> str:
        return os.path.join(self._session_dir(session), "meta.json")

    def _save_meta(self, session: Session) -> None:
        """Write session metadata to meta.json."""
        path = self._meta_path(session)
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def _append_message(self, session: Session, msg: dict) -> None:
        """Append a single message as one JSON line to messages.jsonl (O(1))."""
        path = self._messages_path(session)
        with open(path, "a") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def _load_all(self) -> None:
        if not os.path.isdir(self.storage_dir):
            return

        for name in os.listdir(self.storage_dir):
            full = os.path.join(self.storage_dir, name)

            # --- New format: <id>/ directory with meta.json + messages.jsonl ---
            if os.path.isdir(full):
                meta_path = os.path.join(full, "meta.json")
                if not os.path.exists(meta_path):
                    continue
                try:
                    with open(meta_path) as f:
                        session = Session.from_dict(json.load(f))
                    # Replay messages from JSONL log
                    msgl_path = os.path.join(full, "messages.jsonl")
                    if os.path.exists(msgl_path):
                        with open(msgl_path) as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    session.messages.append(json.loads(line))
                    self._bind_session(session)
                    self._sessions[session.id] = session
                except Exception as e:
                    logger.error(f"Failed to load session dir {name}: {e}")
                continue

            # --- Legacy format: <id>.json single file (backward compat) ---
            if name.endswith(".json"):
                try:
                    with open(full) as f:
                        data = json.load(f)
                    session = Session.from_dict(data)
                    session.messages = data.get("messages", [])
                    self._bind_session(session)
                    self._sessions[session.id] = session
                except Exception as e:
                    logger.error(f"Failed to load legacy session {name}: {e}")

    def __len__(self) -> int:
        return len(self._sessions)
