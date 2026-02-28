"""UI theme definitions — colors, fonts, and emotion-to-color mapping.

Shared across all Kivy screens for consistent visual styling.
"""

from __future__ import annotations

from safehaven.models import EmotionLabel

# Emotion → color mapping for message bubbles
EMOTION_COLORS: dict[EmotionLabel, str] = {
    EmotionLabel.NEUTRAL: "#B0BEC5",
    EmotionLabel.HAPPY: "#81C784",
    EmotionLabel.SAD: "#64B5F6",
    EmotionLabel.ANXIOUS: "#FFB74D",
    EmotionLabel.ANGRY: "#E57373",
    EmotionLabel.FEARFUL: "#CE93D8",
}

# General UI colors
PRIMARY_COLOR = "#5C6BC0"
BACKGROUND_COLOR = "#FAFAFA"
SURFACE_COLOR = "#FFFFFF"
TEXT_COLOR = "#212121"
TEXT_SECONDARY = "#757575"
