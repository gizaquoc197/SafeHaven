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

    # --- False positive tests (sarcasm / idioms must NOT trigger crisis) ---

    def test_false_positive_dying_of_laughter(self) -> None:
        """'Dying of laughter' is a common idiom — must not trigger FEARFUL."""
        result = self.detector.detect("I'm dying of laughter at that video")
        assert result.label != EmotionLabel.FEARFUL

    def test_false_positive_exam_killing_me(self) -> None:
        """'Killing me' as hyperbole must not trigger FEARFUL."""
        result = self.detector.detect("This exam is killing me, I can't focus")
        assert result.label != EmotionLabel.FEARFUL

    def test_false_positive_dead_tired(self) -> None:
        """'Dead tired' is idiomatic — must not trigger FEARFUL."""
        result = self.detector.detect("I'm dead tired after that workout")
        assert result.label != EmotionLabel.FEARFUL

    def test_false_positive_die_of_embarrassment(self) -> None:
        """Social embarrassment hyperbole must not trigger FEARFUL."""
        result = self.detector.detect("I could die of embarrassment right now")
        assert result.label != EmotionLabel.FEARFUL

    def test_false_positive_killing_it(self) -> None:
        """'Killing it' as a positive idiom must not trigger FEARFUL."""
        result = self.detector.detect("She is absolutely killing it on stage tonight")
        assert result.label != EmotionLabel.FEARFUL

    # --- False negative tests (indirect ideation MUST be caught) ---

    def test_burden_language_caught(self) -> None:
        """'Better off without me' is a documented crisis signal and must trigger FEARFUL."""
        result = self.detector.detect("everyone would be better off without me")
        assert result.label == EmotionLabel.FEARFUL
        assert result.confidence == 1.0

    def test_giving_away_possessions_caught(self) -> None:
        """Giving away possessions is a documented warning sign per C-SSRS."""
        result = self.detector.detect("i've been giving away my things to my friends")
        assert result.label == EmotionLabel.FEARFUL

    def test_nobody_would_notice_caught(self) -> None:
        """Withdrawal/invisibility language is a documented indirect ideation signal."""
        result = self.detector.detect("no one would notice if i disappeared")
        assert result.label == EmotionLabel.FEARFUL

    # --- Known limitation tests (document genuine false negatives) ---

    def test_known_false_negative_sleep_forever(self) -> None:
        """'Go to sleep and not wake up' is NOT caught by current keywords.

        Known limitation: keyword is 'going to sleep forever'; paraphrase misses.
        This test documents the gap — not a pass criterion for detection.
        """
        result = self.detector.detect("I wish I could go to sleep and not wake up")
        # Keyword 'going to sleep forever' does not match this paraphrase
        assert result.label != EmotionLabel.FEARFUL  # known false negative

    def test_known_false_negative_no_one_would_miss(self) -> None:
        """'No one would miss me' paraphrase is NOT caught by current keywords.

        Known limitation: keyword is 'nobody would miss me'; 'no one' variant misses.
        """
        result = self.detector.detect("No one would ever miss me if I was gone")
        assert result.label != EmotionLabel.FEARFUL  # known false negative
