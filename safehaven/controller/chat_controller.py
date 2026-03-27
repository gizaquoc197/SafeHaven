"""ChatController — orchestrates the full message pipeline."""

from __future__ import annotations

from safehaven.interfaces import (
    ConversationMemory,
    EmotionDetector,
    LanguageDetector,
    OutputFilter,
    ResponseGenerator,
    RiskEvaluator,
    StrategySelector,
)
from safehaven.models import (
    ConversationContext,
    EmotionLabel,
    Message,
    RiskLevel,
    UserState,
)


class ChatController:
    """Orchestrates the full message pipeline.

    Owns no business logic — delegates to injected modules.
    Implements the Stateful Safety Pipeline (SSP) architecture.
    """

    def __init__(
        self,
        detector: EmotionDetector,
        evaluator: RiskEvaluator,
        memory: ConversationMemory,
        generator: ResponseGenerator,
        output_filter: OutputFilter,
        language_detector: LanguageDetector | None = None,
        strategy_selector: StrategySelector | None = None,
    ) -> None:
        self.detector = detector
        self.evaluator = evaluator
        self.memory = memory
        self.generator = generator
        self.output_filter = output_filter
        self.language_detector = language_detector
        self.strategy_selector = strategy_selector
        self._last_emotion: EmotionLabel | None = None

    @property
    def fsm_state(self) -> str:
        """Current FSM state label — used by UI for color indicator."""
        if hasattr(self.evaluator, "state"):
            return self.evaluator.state  # type: ignore[attr-defined]
        return "calm"

    @property
    def last_emotion(self) -> EmotionLabel | None:
        """Emotion detected on the last user message — used by UI for bubble color."""
        return self._last_emotion

    def handle_message(self, user_text: str) -> str | None:
        """Process one user message through the full SSP pipeline.

        Returns the assistant response, or None if crisis path activated.
        """
        # 1. Detect language
        language = "en"
        if self.language_detector is not None:
            language = self.language_detector.detect_language(user_text)

        # 2. Detect emotion
        emotion = self.detector.detect(user_text)
        self._last_emotion = emotion.label

        # 3. Store user message
        user_msg = Message(
            role="user", content=user_text, emotion=emotion.label, language=language
        )
        self.memory.store_message(user_msg)

        # 4. Build user state (include escalation history from memory)
        recent = self.memory.get_recent_messages()
        escalation_history = [
            m.risk_level for m in recent if m.role == "user"
        ]
        state = UserState(
            current_emotion=emotion,
            risk_level=RiskLevel.LOW,
            message_count=len(recent),
            escalation_history=escalation_history,
            language=language,
            fsm_state=self.fsm_state,
        )

        # 5. Evaluate risk
        risk = self.evaluator.evaluate(state)

        # 6. Crisis path
        if risk == RiskLevel.HIGH:
            return None  # Signal UI to show crisis screen

        # 7. Select strategy and build system prompt
        system_prompt = ""
        strategy_name = ""
        if self.strategy_selector is not None:
            strategy = self.strategy_selector.select(risk, self.fsm_state)
            strategy_name = type(strategy).__name__
            context_for_prompt = ConversationContext(
                recent_messages=recent,
                user_state=state,
            )
            system_prompt = strategy.build_system_prompt(context_for_prompt)

        # 8. Generate response
        context = ConversationContext(
            recent_messages=recent,
            user_state=state,
            system_prompt=system_prompt,
            strategy_name=strategy_name,
        )
        raw_response = self.generator.generate(context)

        # 9. Filter output
        safe_response = self.output_filter.validate(raw_response, risk)

        # 10. Post-process via strategy
        if self.strategy_selector is not None:
            strategy = self.strategy_selector.select(risk, self.fsm_state)
            safe_response = strategy.post_process(safe_response)

        # 11. Store assistant message
        assistant_msg = Message(
            role="assistant", content=safe_response, risk_level=risk
        )
        self.memory.store_message(assistant_msg)

        return safe_response

    def clear(self) -> None:
        """Reset session state — clears memory and FSM."""
        self.memory.clear()
        if hasattr(self.evaluator, "clear"):
            self.evaluator.clear()  # type: ignore[attr-defined]
        self._last_emotion = None
