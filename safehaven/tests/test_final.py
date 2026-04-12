"""Final integration tests — validates the prompt-engineering sprint and Insights fix.

Covers:
  1. Technique-label suppression paragraph present in all 3 strategy prompts
  2. Persona passthrough for the default (empty system_prompt) persona
  3. Persona decorator invoked for non-default personas
  4. User messages stored with the evaluated risk_level (Insights timeline fix)
  5. Full wired pipeline: risk_level escalates correctly across turns
"""

from __future__ import annotations

from unittest.mock import MagicMock

from safehaven.controller.chat_controller import ChatController
from safehaven.memory.in_memory import InMemoryConversationMemory
from safehaven.models import (
    ConversationContext,
    EmotionLabel,
    EmotionResult,
    Message,
    RiskLevel,
    UserState,
)
from safehaven.personas import PERSONAS
from safehaven.safety.fsm_risk_evaluator import FSMRiskEvaluator
from safehaven.safety.language_detector import SimpleLanguageDetector
from safehaven.strategy.base import ConcreteStrategySelector
from safehaven.strategy.crisis import CrisisStrategy
from safehaven.strategy.de_escalation import DeEscalationStrategy
from safehaven.strategy.supportive import SupportiveStrategy


# ---------------------------------------------------------------------------
# Shared stubs
# ---------------------------------------------------------------------------


class _FakeDetector:
    def __init__(self, label: EmotionLabel, confidence: float) -> None:
        self._result = EmotionResult(label=label, confidence=confidence)

    def detect(self, text: str) -> EmotionResult:
        return self._result


class _FakeGenerator:
    def __init__(self, response: str = "I hear you.") -> None:
        self._response = response
        self.call_count = 0

    def generate(self, context: ConversationContext) -> str:
        self.call_count += 1
        return self._response


class _FakeFilter:
    def validate(self, response: str, risk: RiskLevel) -> str:
        return response


def _make_context(language: str = "en") -> ConversationContext:
    state = UserState(
        current_emotion=EmotionResult(EmotionLabel.NEUTRAL, 0.5),
        risk_level=RiskLevel.LOW,
        message_count=1,
        language=language,
    )
    return ConversationContext(
        recent_messages=[Message(role="user", content="Hello")],
        user_state=state,
    )


# ---------------------------------------------------------------------------
# 1. Technique-label suppression in strategy prompts
# ---------------------------------------------------------------------------

_SUPPRESSION_MARKER = "Never label, name, or identify the therapeutic techniques"
_TECHNIQUE_NAMES = [
    "Reflective listening:",
    "Affirmation:",
    "OARS:",
    "TIPP:",
    "DBT:",
    "QPR:",
]


class TestTechniqueLabelSuppression:
    """All three strategy prompts must carry the CRITICAL suppression paragraph."""

    def test_supportive_strategy_has_suppression_paragraph(self) -> None:
        prompt = SupportiveStrategy().build_system_prompt(_make_context())
        assert _SUPPRESSION_MARKER in prompt, (
            "SupportiveStrategy system prompt is missing the CRITICAL technique-label "
            "suppression paragraph."
        )

    def test_de_escalation_strategy_has_suppression_paragraph(self) -> None:
        prompt = DeEscalationStrategy().build_system_prompt(_make_context())
        assert _SUPPRESSION_MARKER in prompt, (
            "DeEscalationStrategy system prompt is missing the CRITICAL technique-label "
            "suppression paragraph."
        )

    def test_crisis_strategy_has_suppression_paragraph(self) -> None:
        prompt = CrisisStrategy().build_system_prompt(_make_context())
        assert _SUPPRESSION_MARKER in prompt, (
            "CrisisStrategy system prompt is missing the CRITICAL technique-label "
            "suppression paragraph."
        )

    def test_suppression_paragraph_forbids_key_technique_names(self) -> None:
        """The suppression paragraph itself must list the specific labels to avoid."""
        for strategy_cls in (SupportiveStrategy, DeEscalationStrategy, CrisisStrategy):
            prompt = strategy_cls().build_system_prompt(_make_context())
            for label in ("OARS:", "TIPP:", "DBT:", "QPR:"):
                assert label in prompt, (
                    f"{strategy_cls.__name__}: suppression paragraph should explicitly "
                    f"name '{label}' to discourage its use."
                )


# ---------------------------------------------------------------------------
# 2. Persona passthrough — default persona
# ---------------------------------------------------------------------------


class TestPersonaPassthrough:
    """Default persona has empty system_prompt → PersonaDecorator must pass through."""

    def test_default_persona_has_empty_system_prompt(self) -> None:
        assert PERSONAS["default"].system_prompt == "", (
            "Default persona must have an empty system_prompt (passthrough)."
        )

    def test_controller_default_persona_no_decoration(self) -> None:
        """With default persona active, the generator is called exactly once."""
        gen = _FakeGenerator("Clinical response.")
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.NEUTRAL, 0.5),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=gen,
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        # Default persona is active by default
        assert controller.active_persona.key == "default"
        result = controller.handle_message("Hello there")
        assert result == "Clinical response."
        # Only one LLM call — no persona rewrite
        assert gen.call_count == 1


# ---------------------------------------------------------------------------
# 3. Persona decorator invoked for non-default personas
# ---------------------------------------------------------------------------


class TestPersonaDecoratorActive:
    """Non-default personas should trigger a second LLM call (the rewrite)."""

    def _make_mock_generator(
        self,
        first_response: str = "Clinical response.",
        persona_response: str = "Persona-wrapped response.",
    ) -> MagicMock:
        gen = MagicMock()
        gen.generate.side_effect = [first_response, persona_response]
        return gen

    def test_iroh_persona_triggers_decorator_call(self) -> None:
        gen = self._make_mock_generator()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.NEUTRAL, 0.5),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=gen,
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        controller.active_persona = PERSONAS["iroh"]
        result = controller.handle_message("Hello")
        # Two calls: strategy generation + persona rewrite
        assert gen.generate.call_count == 2
        assert result == "Persona-wrapped response."

    def test_baymax_persona_triggers_decorator_call(self) -> None:
        gen = self._make_mock_generator()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.NEUTRAL, 0.5),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=gen,
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        controller.active_persona = PERSONAS["baymax"]
        controller.handle_message("Hello")
        assert gen.generate.call_count == 2

    def test_naruto_persona_triggers_decorator_call(self) -> None:
        gen = self._make_mock_generator()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.NEUTRAL, 0.5),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=gen,
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        controller.active_persona = PERSONAS["naruto"]
        controller.handle_message("Hello")
        assert gen.generate.call_count == 2

    def test_decorator_fail_open_returns_clinical_response(self) -> None:
        """If the persona LLM call throws, the clinical response is returned unchanged."""
        gen = MagicMock()
        gen.generate.side_effect = [
            "Clinical response.",
            RuntimeError("LLM unavailable"),
        ]
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.NEUTRAL, 0.5),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=gen,
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        controller.active_persona = PERSONAS["iroh"]
        result = controller.handle_message("Hello")
        assert result == "Clinical response."


# ---------------------------------------------------------------------------
# 4. Insights fix — user messages stored with evaluated risk_level
# ---------------------------------------------------------------------------


class TestInsightsRiskLevelFix:
    """User messages must be stored with the risk_level evaluated by the FSM,
    not hardcoded to RiskLevel.LOW.  This drives the Insights timeline colours.
    """

    def test_low_risk_message_stored_as_low(self) -> None:
        memory = InMemoryConversationMemory()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.HAPPY, 0.9),
            evaluator=FSMRiskEvaluator(),
            memory=memory,
            generator=_FakeGenerator(),
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        controller.handle_message("Great day!")
        user_msgs = [m for m in memory.get_recent_messages() if m.role == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0].risk_level == RiskLevel.LOW

    def test_medium_risk_message_stored_as_medium(self) -> None:
        """After FSM reaches CONCERNED/ELEVATED the stored risk_level should be MEDIUM."""
        memory = InMemoryConversationMemory()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.SAD, 0.9),
            evaluator=FSMRiskEvaluator(),
            memory=memory,
            generator=_FakeGenerator(),
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        # First negative message → CONCERNED → MEDIUM
        controller.handle_message("I feel terrible today")
        user_msgs = [m for m in memory.get_recent_messages() if m.role == "user"]
        assert user_msgs[-1].risk_level == RiskLevel.MEDIUM, (
            "First negative message should produce MEDIUM risk stored on the user message."
        )

    def test_escalation_risk_levels_reflect_fsm_progression(self) -> None:
        """Three-turn escalation: LOW → MEDIUM → MEDIUM; all stored correctly."""
        memory = InMemoryConversationMemory()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.SAD, 0.9),
            evaluator=FSMRiskEvaluator(),
            memory=memory,
            generator=_FakeGenerator(),
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )

        # Pre-escalation baseline: start in CALM
        fresh_controller = ChatController(
            detector=_FakeDetector(EmotionLabel.HAPPY, 0.9),
            evaluator=FSMRiskEvaluator(),
            memory=InMemoryConversationMemory(),
            generator=_FakeGenerator(),
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        fresh_controller.handle_message("Good day")
        baseline_msgs = [
            m for m in fresh_controller.memory.get_recent_messages() if m.role == "user"
        ]
        assert baseline_msgs[0].risk_level == RiskLevel.LOW

        # Now test escalation sequence
        controller.handle_message("I feel terrible")   # → CONCERNED, MEDIUM
        controller.handle_message("Still feeling bad") # → CONCERNED, MEDIUM
        controller.handle_message("Everything is wrong")  # → ELEVATED, MEDIUM

        all_user_msgs = [
            m for m in memory.get_recent_messages() if m.role == "user"
        ]
        assert len(all_user_msgs) == 3
        # All three are MEDIUM (CONCERNED and ELEVATED both map to RiskLevel.MEDIUM)
        for msg in all_user_msgs:
            assert msg.risk_level == RiskLevel.MEDIUM, (
                f"Expected MEDIUM, got {msg.risk_level} for message: {msg.content!r}"
            )

    def test_high_risk_user_message_stored_as_high(self) -> None:
        """Even on HIGH risk (crisis path), the user message must be stored as HIGH."""
        memory = InMemoryConversationMemory()
        controller = ChatController(
            detector=_FakeDetector(EmotionLabel.FEARFUL, 1.0),
            evaluator=FSMRiskEvaluator(),
            memory=memory,
            generator=_FakeGenerator("should not be called"),
            output_filter=_FakeFilter(),
            language_detector=SimpleLanguageDetector(),
            strategy_selector=ConcreteStrategySelector(),
        )
        result = controller.handle_message("I want to end it all")
        assert result is None  # crisis path activated
        user_msgs = [m for m in memory.get_recent_messages() if m.role == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0].risk_level == RiskLevel.HIGH, (
            "Crisis-path user message must be stored as HIGH so Insights shows a red dot."
        )


# ---------------------------------------------------------------------------
# 5. Persona voice rules smoke-check (system_prompt content)
# ---------------------------------------------------------------------------


class TestPersonaVoiceRules:
    """Verify key safety and voice rules were added to each persona's system_prompt."""

    def test_iroh_no_action_text_rule(self) -> None:
        prompt = PERSONAS["iroh"].system_prompt
        assert "NEVER use action descriptions" in prompt or "asterisk" in prompt.lower(), (
            "Iroh persona must have an explicit no-asterisk-action rule."
        )

    def test_iroh_word_limit_120(self) -> None:
        prompt = PERSONAS["iroh"].system_prompt
        assert "120" in prompt, "Iroh persona must specify a 120-word response limit."

    def test_baymax_word_limit_100(self) -> None:
        prompt = PERSONAS["baymax"].system_prompt
        assert "100" in prompt, "Baymax persona must specify a 100-word response limit."

    def test_naruto_no_action_text_rule(self) -> None:
        prompt = PERSONAS["naruto"].system_prompt
        assert "NEVER use action descriptions" in prompt or "stage directions" in prompt, (
            "Naruto persona must have an explicit no-action-text rule."
        )

    def test_iroh_has_character_context(self) -> None:
        prompt = PERSONAS["iroh"].system_prompt
        assert "Lu Ten" in prompt, "Iroh persona must include CHARACTER CONTEXT with Lu Ten backstory."

    def test_baymax_has_character_context(self) -> None:
        prompt = PERSONAS["baymax"].system_prompt
        assert "Tadashi" in prompt, "Baymax persona must include CHARACTER CONTEXT with Tadashi backstory."

    def test_naruto_has_character_context(self) -> None:
        prompt = PERSONAS["naruto"].system_prompt
        assert "Iruka" in prompt, "Naruto persona must include CHARACTER CONTEXT with Iruka-sensei."
