"""Integration tests for ChatController with stub dependencies."""

from __future__ import annotations

from safehaven.controller.chat_controller import ChatController
from safehaven.models import (
    ConversationContext,
    EmotionLabel,
    EmotionResult,
    Message,
    RiskLevel,
    UserState,
)


class FakeDetector:
    def __init__(self, label: EmotionLabel, confidence: float) -> None:
        self._result = EmotionResult(label=label, confidence=confidence)

    def detect(self, text: str) -> EmotionResult:
        return self._result


class FakeEvaluator:
    def __init__(self, level: RiskLevel) -> None:
        self._level = level

    def evaluate(self, state: UserState) -> RiskLevel:
        return self._level


class FakeMemory:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def store_message(self, message: Message) -> None:
        self._messages.append(message)

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        return self._messages[-limit:]

    def clear(self) -> None:
        self._messages.clear()


class FakeGenerator:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, context: ConversationContext) -> str:
        return self._response


class FakeFilter:
    def validate(self, response: str, risk: RiskLevel) -> str:
        return response


class TestChatControllerIntegration:
    def test_normal_message_returns_response(self) -> None:
        controller = ChatController(
            detector=FakeDetector(EmotionLabel.HAPPY, 0.85),
            evaluator=FakeEvaluator(RiskLevel.LOW),
            memory=FakeMemory(),
            generator=FakeGenerator("Great to hear!"),
            output_filter=FakeFilter(),
        )
        result = controller.handle_message("I feel great today")
        assert result == "Great to hear!"

    def test_high_risk_returns_none(self) -> None:
        controller = ChatController(
            detector=FakeDetector(EmotionLabel.FEARFUL, 1.0),
            evaluator=FakeEvaluator(RiskLevel.HIGH),
            memory=FakeMemory(),
            generator=FakeGenerator("should not be called"),
            output_filter=FakeFilter(),
        )
        result = controller.handle_message("I want to end it all")
        assert result is None

    def test_messages_stored_in_memory(self) -> None:
        memory = FakeMemory()
        controller = ChatController(
            detector=FakeDetector(EmotionLabel.NEUTRAL, 0.3),
            evaluator=FakeEvaluator(RiskLevel.LOW),
            memory=memory,
            generator=FakeGenerator("Hello!"),
            output_filter=FakeFilter(),
        )
        controller.handle_message("Hi there")
        messages = memory.get_recent_messages()
        assert len(messages) == 2  # user + assistant
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
