"""Keyword-based EmotionDetector implementation."""

from __future__ import annotations

from pathlib import Path

from safehaven.models import EmotionLabel, EmotionResult


# Keyword lists for non-crisis emotions
_SAD_WORDS: frozenset[str] = frozenset(
    [
        "sad",
        "depressed",
        "hopeless",
        "lonely",
        "miserable",
        "heartbroken",
        "grief",
        "crying",
        "unhappy",
        "devastated",
        "overwhelmed",
        "down",
        "sorrowful",
        "gloomy",
    ]
)

_ANXIOUS_WORDS: frozenset[str] = frozenset(
    [
        "anxious",
        "worried",
        "nervous",
        "panic",
        "stressed",
        "afraid",
        "scared",
        "uneasy",
        "tense",
        "fearful",
        "dread",
        "overwhelmed",
        "restless",
        "apprehensive",
    ]
)

_ANGRY_WORDS: frozenset[str] = frozenset(
    [
        "angry",
        "furious",
        "enraged",
        "livid",
        "frustrated",
        "irritated",
        "outraged",
        "resentful",
        "hostile",
        "bitter",
        "mad",
        "annoyed",
        "infuriated",
    ]
)

_HAPPY_WORDS: frozenset[str] = frozenset(
    [
        "happy",
        "great",
        "good",
        "wonderful",
        "fantastic",
        "excited",
        "joyful",
        "grateful",
        "content",
        "cheerful",
        "amazing",
        "delighted",
        "blessed",
        "thrilled",
        "love",
        "awesome",
        "excellent",
        "glad",
        "positive",
        "pretty good",
    ]
)


class KeywordEmotionDetector:
    """Detect emotions using keyword matching against crisis list and word sets."""

    def __init__(self) -> None:
        keywords_path = (
            Path(__file__).parent.parent / "resources" / "crisis_keywords.txt"
        )
        raw = keywords_path.read_text(encoding="utf-8")
        self._crisis_keywords: list[str] = [
            line.strip().lower()
            for line in raw.splitlines()
            if line.strip()
        ]

    def detect(self, text: str) -> EmotionResult:
        """Analyze text and return the dominant emotion with confidence."""
        lower = text.lower()

        # 1. Check crisis keywords first → FEARFUL @ 1.0
        for keyword in self._crisis_keywords:
            if keyword in lower:
                return EmotionResult(label=EmotionLabel.FEARFUL, confidence=1.0)

        words = set(lower.split())

        # 2. Check emotion keyword lists
        if words & _SAD_WORDS:
            return EmotionResult(label=EmotionLabel.SAD, confidence=0.9)

        if words & _ANXIOUS_WORDS:
            return EmotionResult(label=EmotionLabel.ANXIOUS, confidence=0.9)

        if words & _ANGRY_WORDS:
            return EmotionResult(label=EmotionLabel.ANGRY, confidence=0.9)

        # Happy check: also support multi-word phrases via substring
        if words & _HAPPY_WORDS or any(
            phrase in lower for phrase in ("pretty good",)
        ):
            return EmotionResult(label=EmotionLabel.HAPPY, confidence=0.85)

        # 3. Default
        return EmotionResult(label=EmotionLabel.NEUTRAL, confidence=0.3)
