from __future__ import annotations

from typing import Protocol

from safehaven.models import (
    ConversationContext,
    EmotionResult,
    Message,
    RiskLevel,
    UserState,
)


class EmotionDetector(Protocol):
    def detect(self, text: str) -> EmotionResult:
        """Analyze text and return the dominant emotion with confidence."""
        ...


class RiskEvaluator(Protocol):
    def evaluate(self, state: UserState) -> RiskLevel:
        """Determine risk level from current user state.

        Rules:
        - HIGH if crisis keywords detected or escalation pattern
        - MEDIUM if negative emotion with high confidence
        - LOW otherwise
        """
        ...


class ConversationMemory(Protocol):
    def store_message(self, message: Message) -> None:
        """Persist a message to storage."""
        ...

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Retrieve the N most recent messages, oldest first."""
        ...

    def clear(self) -> None:
        """Clear all stored messages (new session)."""
        ...


class ResponseGenerator(Protocol):
    def generate(self, context: ConversationContext) -> str:
        """Call the LLM API and return the raw response text.

        Raises:
            ConnectionError: If the API is unreachable.
            ValueError: If context is empty.
        """
        ...


class OutputFilter(Protocol):
    def validate(self, response: str, risk: RiskLevel) -> str:
        """Sanitize LLM output based on current risk level.

        - Strip any content that contradicts safety guidelines.
        - At MEDIUM risk, prepend empathetic framing.
        - At HIGH risk, this method should not be called (crisis path).
        Returns the filtered response string.
        """
        ...
