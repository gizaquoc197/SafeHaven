"""SQLite-backed ConversationMemory implementation."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from importlib import resources as pkg_resources
from pathlib import Path

from safehaven.models import EmotionLabel, Message, RiskLevel


class SQLiteMemory:
    """Persist conversation messages in a local SQLite database."""

    def __init__(self, db_path: str = "safehaven.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._run_schema()

    def _run_schema(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        self._conn.executescript(schema_sql)

    def store_message(self, message: Message) -> None:
        """Persist a message to storage."""
        self._conn.execute(
            "INSERT INTO messages (role, content, timestamp, emotion, risk_level) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                message.role,
                message.content,
                message.timestamp.isoformat(),
                message.emotion.value if message.emotion else None,
                message.risk_level.value,
            ),
        )
        self._conn.commit()

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Retrieve the N most recent messages, oldest first."""
        cursor = self._conn.execute(
            "SELECT role, content, timestamp, emotion, risk_level "
            "FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        messages: list[Message] = []
        for row in reversed(rows):
            emotion = EmotionLabel(row["emotion"]) if row["emotion"] else None
            messages.append(
                Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    emotion=emotion,
                    risk_level=RiskLevel(row["risk_level"]),
                )
            )
        return messages

    def clear(self) -> None:
        """Clear all stored messages (new session)."""
        self._conn.execute("DELETE FROM messages")
        self._conn.commit()
