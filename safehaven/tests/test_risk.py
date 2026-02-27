"""Tests for RiskEvaluator."""

from __future__ import annotations

from safehaven.models import EmotionLabel, EmotionResult, RiskLevel, UserState
from safehaven.safety.risk_evaluator import KeywordRiskEvaluator


class TestKeywordRiskEvaluator:
    def setup_method(self) -> None:
        self.evaluator = KeywordRiskEvaluator()

    def _state(
        self,
        label: EmotionLabel,
        confidence: float,
        history: list[RiskLevel] | None = None,
    ) -> UserState:
        return UserState(
            current_emotion=EmotionResult(label=label, confidence=confidence),
            risk_level=RiskLevel.LOW,
            message_count=1,
            escalation_history=history or [],
        )

    def test_fearful_high_confidence_returns_high(self) -> None:
        state = self._state(EmotionLabel.FEARFUL, 1.0)
        assert self.evaluator.evaluate(state) == RiskLevel.HIGH

    def test_fearful_low_confidence_returns_low(self) -> None:
        state = self._state(EmotionLabel.FEARFUL, 0.5)
        assert self.evaluator.evaluate(state) == RiskLevel.LOW

    def test_sad_high_confidence_returns_medium(self) -> None:
        state = self._state(EmotionLabel.SAD, 0.9)
        assert self.evaluator.evaluate(state) == RiskLevel.MEDIUM

    def test_anxious_returns_medium(self) -> None:
        state = self._state(EmotionLabel.ANXIOUS, 0.9)
        assert self.evaluator.evaluate(state) == RiskLevel.MEDIUM

    def test_angry_returns_medium(self) -> None:
        state = self._state(EmotionLabel.ANGRY, 0.8)
        assert self.evaluator.evaluate(state) == RiskLevel.MEDIUM

    def test_happy_returns_low(self) -> None:
        state = self._state(EmotionLabel.HAPPY, 0.85)
        assert self.evaluator.evaluate(state) == RiskLevel.LOW

    def test_neutral_returns_low(self) -> None:
        state = self._state(EmotionLabel.NEUTRAL, 0.3)
        assert self.evaluator.evaluate(state) == RiskLevel.LOW

    def test_escalation_three_consecutive_medium(self) -> None:
        history = [RiskLevel.MEDIUM, RiskLevel.MEDIUM, RiskLevel.MEDIUM]
        state = self._state(EmotionLabel.NEUTRAL, 0.3, history=history)
        assert self.evaluator.evaluate(state) == RiskLevel.HIGH

    def test_escalation_not_consecutive(self) -> None:
        history = [RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.MEDIUM]
        state = self._state(EmotionLabel.NEUTRAL, 0.3, history=history)
        assert self.evaluator.evaluate(state) == RiskLevel.LOW
