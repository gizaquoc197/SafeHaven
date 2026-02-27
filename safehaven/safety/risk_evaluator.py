"""RiskEvaluator implementation — keyword check + escalation tracking."""

from __future__ import annotations

from safehaven.models import EmotionLabel, RiskLevel, UserState


class KeywordRiskEvaluator:
    """Determine risk from user state using emotion + escalation rules."""

    def evaluate(self, state: UserState) -> RiskLevel:
        """Determine risk level from current user state.

        Rules (applied in order):
        - FEARFUL + confidence >= 0.9 → HIGH (crisis proxy)
        - 3+ consecutive MEDIUM in escalation_history → HIGH
        - SAD/ANXIOUS/ANGRY + confidence >= 0.7 → MEDIUM
        - Otherwise → LOW
        """
        emotion = state.current_emotion

        # Crisis proxy: fearful with high confidence
        if (
            emotion.label == EmotionLabel.FEARFUL
            and emotion.confidence >= 0.9
        ):
            return RiskLevel.HIGH

        # Escalation: 3+ consecutive MEDIUM entries at the tail of history
        history = state.escalation_history
        if len(history) >= 3 and all(
            r == RiskLevel.MEDIUM for r in history[-3:]
        ):
            return RiskLevel.HIGH

        # Negative emotion with sufficient confidence → MEDIUM
        if (
            emotion.label in (EmotionLabel.SAD, EmotionLabel.ANXIOUS, EmotionLabel.ANGRY)
            and emotion.confidence >= 0.7
        ):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW
