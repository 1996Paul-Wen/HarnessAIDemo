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
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """A single conversation session with its own state."""
    id: str
    title: str
    created_at: float = field(default_factory=time.time)
    messages: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    _on_change: Optional[callable] = field(default=None, repr=False, compare=False)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        if self._on_change:
            self._on_change(self)

    def get_history(self, n: int = 20) -> list[dict]:
        return self.messages[-n:]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "messages": self.messages,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            title=data.get("title", "Untitled"),
            created_at=data.get("created_at", 0),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Manages multiple conversation sessions with persistence."""

    def __init__(self, storage_dir: str = ".sessions"):
        self.storage_dir = storage_dir
        self._sessions: dict[str, Session] = {}
        self._active_session_id: Optional[str] = None
        os.makedirs(storage_dir, exist_ok=True)
        self._load_all()

    def create_session(self, title: str = "New Session") -> Session:
        """Create a new session and make it active."""
        session_id = str(uuid.uuid4())[:8]
        session = Session(id=session_id, title=title, _on_change=self._save)
        self._sessions[session_id] = session
        self._active_session_id = session_id
        self._save(session)
        logger.info(f"Created session: {session_id} - {title}")
        return session

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
        path = os.path.join(self.storage_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
        if self._active_session_id == session_id:
            self._active_session_id = None

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session and persist to disk."""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        session.add_message(role, content)  # _on_change callback handles _save

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a session."""
        session = self._sessions.get(session_id)
        if session:
            session.title = new_title
            self._save(session)

    def _save(self, session: Session) -> None:
        path = os.path.join(self.storage_dir, f"{session.id}.json")
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_all(self) -> None:
        if not os.path.isdir(self.storage_dir):
            return
        for fname in os.listdir(self.storage_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self.storage_dir, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                session._on_change = self._save
                self._sessions[session.id] = session
            except Exception as e:
                logger.error(f"Failed to load session {fname}: {e}")

    def __len__(self) -> int:
        return len(self._sessions)
