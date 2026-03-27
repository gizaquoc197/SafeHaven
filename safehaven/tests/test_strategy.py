"""Tests for the strategy pattern implementation."""

from __future__ import annotations

from safehaven.models import (
    ConversationContext,
    EmotionLabel,
    EmotionResult,
    Message,
    RiskLevel,
    UserState,
)
from safehaven.strategy.base import ConcreteStrategySelector
from safehaven.strategy.crisis import CrisisStrategy
from safehaven.strategy.de_escalation import DeEscalationStrategy
from safehaven.strategy.supportive import SupportiveStrategy


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


class TestSupportiveStrategy:
    def test_post_process_passthrough(self) -> None:
        assert SupportiveStrategy().post_process("Hello there!") == "Hello there!"

    def test_build_system_prompt_returns_nonempty(self) -> None:
        prompt = SupportiveStrategy().build_system_prompt(_make_context())
        assert len(prompt) > 0

    def test_build_system_prompt_contains_empathy_keywords(self) -> None:
        prompt = SupportiveStrategy().build_system_prompt(_make_context()).lower()
        assert any(kw in prompt for kw in ("listen", "reflect", "validat", "open"))

    def test_build_system_prompt_english_instruction(self) -> None:
        prompt = SupportiveStrategy().build_system_prompt(_make_context("en"))
        assert "English" in prompt

    def test_build_system_prompt_arabic_instruction(self) -> None:
        prompt = SupportiveStrategy().build_system_prompt(_make_context("ar"))
        assert "Arabic" in prompt


class TestDeEscalationStrategy:
    def test_build_system_prompt_returns_nonempty(self) -> None:
        prompt = DeEscalationStrategy().build_system_prompt(_make_context())
        assert len(prompt) > 0

    def test_build_system_prompt_contains_grounding_keywords(self) -> None:
        prompt = DeEscalationStrategy().build_system_prompt(_make_context()).lower()
        assert any(kw in prompt for kw in ("ground", "breath", "calm", "tipp", "distress"))

    def test_post_process_appends_988_when_missing(self) -> None:
        result = DeEscalationStrategy().post_process("I hear you.")
        assert "988" in result

    def test_post_process_no_duplicate_when_988_present(self) -> None:
        response = "Please call 988 if needed."
        result = DeEscalationStrategy().post_process(response)
        assert result.count("988") == 1

    def test_build_system_prompt_arabic_instruction(self) -> None:
        prompt = DeEscalationStrategy().build_system_prompt(_make_context("ar"))
        assert "Arabic" in prompt


class TestCrisisStrategy:
    def test_build_system_prompt_returns_nonempty(self) -> None:
        prompt = CrisisStrategy().build_system_prompt(_make_context())
        assert len(prompt) > 0

    def test_build_system_prompt_contains_988(self) -> None:
        prompt = CrisisStrategy().build_system_prompt(_make_context())
        assert "988" in prompt

    def test_post_process_prepends_resources(self) -> None:
        result = CrisisStrategy().post_process("You are not alone.")
        assert result.startswith("Please reach out")

    def test_post_process_contains_crisis_text_line(self) -> None:
        result = CrisisStrategy().post_process("You are not alone.")
        assert "741741" in result

    def test_build_system_prompt_arabic_instruction(self) -> None:
        prompt = CrisisStrategy().build_system_prompt(_make_context("ar"))
        assert "Arabic" in prompt


class TestConcreteStrategySelector:
    def test_calm_returns_supportive(self) -> None:
        assert isinstance(
            ConcreteStrategySelector().select(RiskLevel.LOW, "calm"),
            SupportiveStrategy,
        )

    def test_concerned_returns_supportive(self) -> None:
        assert isinstance(
            ConcreteStrategySelector().select(RiskLevel.MEDIUM, "concerned"),
            SupportiveStrategy,
        )

    def test_elevated_returns_deescalation(self) -> None:
        assert isinstance(
            ConcreteStrategySelector().select(RiskLevel.MEDIUM, "elevated"),
            DeEscalationStrategy,
        )

    def test_crisis_returns_crisis_strategy(self) -> None:
        assert isinstance(
            ConcreteStrategySelector().select(RiskLevel.HIGH, "crisis"),
            CrisisStrategy,
        )
