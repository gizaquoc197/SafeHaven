"""Tests for ConversationMemory (SQLite)."""

from __future__ import annotations

import os
import tempfile

import pytest

from safehaven.memory.sqlite_memory import SQLiteMemory
from safehaven.models import EmotionLabel, Message, RiskLevel


class TestSQLiteMemory:
    def setup_method(self) -> None:
        self._tmpfile = tempfile.NamedTemporaryFile(
            suffix=".db", delete=False
        )
        self._tmpfile.close()
        self.memory = SQLiteMemory(db_path=self._tmpfile.name)

    def teardown_method(self) -> None:
        self.memory._conn.close()
        os.unlink(self._tmpfile.name)

    def test_store_and_retrieve(self) -> None:
        msg = Message(role="user", content="hello")
        self.memory.store_message(msg)
        messages = self.memory.get_recent_messages()
        assert len(messages) == 1
        assert messages[0].content == "hello"
        assert messages[0].role == "user"

    def test_get_recent_respects_limit(self) -> None:
        for i in range(5):
            self.memory.store_message(Message(role="user", content=f"msg {i}"))
        messages = self.memory.get_recent_messages(limit=3)
        assert len(messages) == 3
        # Should be the 3 most recent, oldest first
        assert messages[0].content == "msg 2"
        assert messages[2].content == "msg 4"

    def test_clear_removes_all(self) -> None:
        self.memory.store_message(Message(role="user", content="test"))
        self.memory.clear()
        assert self.memory.get_recent_messages() == []

    def test_stores_emotion_and_risk(self) -> None:
        msg = Message(
            role="user",
            content="I feel sad",
            emotion=EmotionLabel.SAD,
            risk_level=RiskLevel.MEDIUM,
        )
        self.memory.store_message(msg)
        retrieved = self.memory.get_recent_messages()[0]
        assert retrieved.emotion == EmotionLabel.SAD
        assert retrieved.risk_level == RiskLevel.MEDIUM

    def test_oldest_first_ordering(self) -> None:
        self.memory.store_message(Message(role="user", content="first"))
        self.memory.store_message(Message(role="assistant", content="second"))
        messages = self.memory.get_recent_messages()
        assert messages[0].content == "first"
        assert messages[1].content == "second"
