"""ChatController — orchestrates the full message pipeline."""

from __future__ import annotations

from safehaven.interfaces import (
    ConversationMemory,
    EmotionDetector,
    OutputFilter,
    ResponseGenerator,
    RiskEvaluator,
)
from safehaven.models import (
    ConversationContext,
    Message,
    RiskLevel,
    UserState,
)


class ChatController:
    """Orchestrates the full message pipeline.

    Owns no business logic — delegates to injected modules.
    """

    def __init__(
        self,
        detector: EmotionDetector,
        evaluator: RiskEvaluator,
        memory: ConversationMemory,
        generator: ResponseGenerator,
        output_filter: OutputFilter,
    ) -> None:
        self.detector = detector
        self.evaluator = evaluator
        self.memory = memory
        self.generator = generator
        self.output_filter = output_filter

    def handle_message(self, user_text: str) -> str | None:
        """Process one user message through the full pipeline.

        Returns the assistant response, or None if crisis path activated.
        """
        # 1. Detect emotion
        emotion = self.detector.detect(user_text)

        # 2. Store user message
        user_msg = Message(role="user", content=user_text, emotion=emotion.label)
        self.memory.store_message(user_msg)

        # 3. Build user state
        state = UserState(
            current_emotion=emotion,
            risk_level=RiskLevel.LOW,
            message_count=len(self.memory.get_recent_messages()),
        )

        # 4. Evaluate risk
        risk = self.evaluator.evaluate(state)

        # 5. Crisis path
        if risk == RiskLevel.HIGH:
            return None  # Signal UI to show crisis modal

        # 6. Generate response
        context = ConversationContext(
            recent_messages=self.memory.get_recent_messages(),
            user_state=state,
        )
        raw_response = self.generator.generate(context)

        # 7. Filter output
        safe_response = self.output_filter.validate(raw_response, risk)

        # 8. Store assistant message
        assistant_msg = Message(
            role="assistant", content=safe_response, risk_level=risk
        )
        self.memory.store_message(assistant_msg)

        return safe_response
