"""Keyword-based EmotionDetector implementation."""

from __future__ import annotations

from pathlib import Path

from safehaven.models import EmotionLabel, EmotionResult


# ---------------------------------------------------------------------------
# Single-token keyword sets
# ---------------------------------------------------------------------------
# Note: "overwhelmed" removed from SAD and kept only in ANXIOUS — it is a
# high-arousal state (loss-of-control) that maps to anxiety, not sadness.
# "pretty good" removed from HAPPY — dead code under whitespace splitting
# (already covered by "good").
# "hopeless" kept in SAD (not in crisis_keywords.txt which uses full phrases).
# Boundary words: "upset" → SAD, "rejected" → SAD, "agitated" → ANXIOUS.
# ---------------------------------------------------------------------------

_SAD_WORDS: frozenset[str] = frozenset(
    [
        # Original (minus "overwhelmed")
        "sad", "depressed", "hopeless", "lonely", "miserable", "heartbroken",
        "grief", "crying", "unhappy", "devastated", "down", "sorrowful", "gloomy",
        # Priority-tier additions (LOW ambiguity, highly conversational)
        "bummed", "gutted", "blah", "numb", "empty", "defeated", "hollow",
        "meaningless", "abandoned", "isolated", "dejected", "disappointed",
        "disheartened", "regret", "lethargic", "weepy",
        # Boundary words
        "upset", "rejected",
    ]
)

_ANXIOUS_WORDS: frozenset[str] = frozenset(
    [
        # Original
        "anxious", "worried", "nervous", "panic", "stressed", "afraid", "scared",
        "uneasy", "tense", "fearful", "dread", "overwhelmed", "restless",
        "apprehensive",
        # Priority-tier additions (LOW ambiguity)
        "panicky", "jittery", "antsy", "freaked", "paranoid", "terrified",
        "frightened", "frantic", "dreading", "overthinking", "spiraling",
        "obsessing", "insecure", "hyperventilating", "panicking",
        # Boundary word
        "agitated",
    ]
)

_ANGRY_WORDS: frozenset[str] = frozenset(
    [
        # Original
        "angry", "furious", "enraged", "livid", "frustrated", "irritated",
        "outraged", "resentful", "hostile", "bitter", "mad", "annoyed",
        "infuriated",
        # Priority-tier additions (LOW ambiguity)
        "pissed", "fuming", "seething", "hate", "rage", "exasperated",
        "aggravated", "cranky", "grumpy", "irked", "miffed", "disgusted",
        "betrayed", "disrespected", "raging",
    ]
)

_HAPPY_WORDS: frozenset[str] = frozenset(
    [
        # Original (minus "pretty good" — dead code under whitespace splitting)
        "happy", "great", "good", "wonderful", "fantastic", "excited", "joyful",
        "grateful", "content", "cheerful", "amazing", "delighted", "blessed",
        "thrilled", "love", "awesome", "excellent", "glad", "positive",
        # Priority-tier additions (LOW ambiguity)
        "stoked", "psyched", "ecstatic", "elated", "overjoyed", "thankful",
        "hopeful", "fulfilled", "peaceful", "optimistic", "relieved", "proud",
        "pleased", "fun", "enjoy", "enthusiastic", "inspired",
    ]
)

# ---------------------------------------------------------------------------
# Multi-word phrase lists (require substring matching, not token set lookup)
# ---------------------------------------------------------------------------

_SAD_PHRASES: tuple[str, ...] = (
    "can't cope", "falling apart", "feel nothing", "feel empty",
    "don't care anymore", "giving up", "what's the point", "so alone",
    "no energy", "can't stop crying",
)

_ANXIOUS_PHRASES: tuple[str, ...] = (
    "freaking out", "on edge", "can't sleep", "can't breathe",
    "heart racing", "chest tight", "panic attack", "mind racing",
    "can't relax", "losing control", "can't stop thinking", "losing it",
)

_ANGRY_PHRASES: tuple[str, ...] = (
    "pissed off", "fed up", "had enough", "sick of", "ticked off",
    "can't stand", "losing my patience",
)

_HAPPY_PHRASES: tuple[str, ...] = (
    "over the moon", "on top of the world", "feeling great", "so happy",
    "life is good", "things are looking up",
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

        # 2. Check emotion keyword sets and phrase lists (SAD checked first)
        if (words & _SAD_WORDS) or any(phrase in lower for phrase in _SAD_PHRASES):
            return EmotionResult(label=EmotionLabel.SAD, confidence=0.9)

        if (words & _ANXIOUS_WORDS) or any(
            phrase in lower for phrase in _ANXIOUS_PHRASES
        ):
            return EmotionResult(label=EmotionLabel.ANXIOUS, confidence=0.9)

        if (words & _ANGRY_WORDS) or any(
            phrase in lower for phrase in _ANGRY_PHRASES
        ):
            return EmotionResult(label=EmotionLabel.ANGRY, confidence=0.9)

        if (words & _HAPPY_WORDS) or any(
            phrase in lower for phrase in _HAPPY_PHRASES
        ):
            return EmotionResult(label=EmotionLabel.HAPPY, confidence=0.85)

        # 3. Default
        return EmotionResult(label=EmotionLabel.NEUTRAL, confidence=0.3)
