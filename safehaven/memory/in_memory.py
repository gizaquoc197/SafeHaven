"""In-memory ConversationMemory — second concrete Repository backend.

Demonstrates the Repository pattern with two interchangeable backends:
- SQLiteMemory: persistent storage (production)
- InMemoryConversationMemory: ephemeral storage (testing / session-less contexts)

Both implement the ``ConversationMemory`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import Message


class InMemoryConversationMemory:
    """Store conversation messages in-memory (non-persistent).

    Used for testing and session-less contexts where persistence is not needed.
    Demonstrates the Repository pattern — callers interact with the same
    ConversationMemory protocol regardless of which backend is in use.
    """

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def store_message(self, message: Message) -> None:
        """Append message to in-memory store."""
        self._messages.append(message)

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Return the N most recent messages, oldest first."""
        return self._messages[-limit:]

    def clear(self) -> None:
        """Clear all stored messages."""
        self._messages.clear()
