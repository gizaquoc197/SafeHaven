"""Tests for EmotionDetector."""

from __future__ import annotations

from safehaven.models import EmotionLabel
from safehaven.safety.emotion_detector import KeywordEmotionDetector


class TestKeywordEmotionDetector:
    def setup_method(self) -> None:
        self.detector = KeywordEmotionDetector()

    # Crisis keywords → FEARFUL
    def test_crisis_keyword_returns_fearful(self) -> None:
        result = self.detector.detect("I want to end it all")
        assert result.label == EmotionLabel.FEARFUL
        assert result.confidence == 1.0

    def test_crisis_keyword_case_insensitive(self) -> None:
        result = self.detector.detect("I have been thinking about SUICIDE")
        assert result.label == EmotionLabel.FEARFUL

    # SAD
    def test_sad_keyword(self) -> None:
        result = self.detector.detect("I feel so sad today")
        assert result.label == EmotionLabel.SAD
        assert result.confidence == 0.9

    # ANXIOUS
    def test_anxious_keyword(self) -> None:
        result = self.detector.detect("I'm so worried about everything")
        assert result.label == EmotionLabel.ANXIOUS
        assert result.confidence == 0.9

    # ANGRY
    def test_angry_keyword(self) -> None:
        result = self.detector.detect("I am so angry right now")
        assert result.label == EmotionLabel.ANGRY
        assert result.confidence == 0.9

    # HAPPY
    def test_happy_keyword(self) -> None:
        result = self.detector.detect("I feel great today")
        assert result.label == EmotionLabel.HAPPY
        assert result.confidence == 0.85

    # NEUTRAL (default)
    def test_neutral_default(self) -> None:
        result = self.detector.detect("Tell me about the weather")
        assert result.label == EmotionLabel.NEUTRAL
        assert result.confidence == 0.3

    # Design doc scenarios
    def test_design_doc_scenario_happy(self) -> None:
        result = self.detector.detect("I feel great")
        assert result.label == EmotionLabel.HAPPY

    def test_design_doc_scenario_anxious(self) -> None:
        result = self.detector.detect("I'm so worried")
        assert result.label == EmotionLabel.ANXIOUS

    def test_crisis_dont_want_to_be_here(self) -> None:
        result = self.detector.detect(
            "I don't want to be here anymore. I want to end it all."
        )
        assert result.label == EmotionLabel.FEARFUL
        assert result.confidence == 1.0
