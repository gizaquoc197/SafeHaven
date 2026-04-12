"""PersonaConfig — immutable data model for a SafeHaven character persona."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class ParticleType(str, Enum):
    """Ambient particle effect displayed while a persona is active."""

    STEAM = "STEAM"
    SCAN = "SCAN"
    LEAVES = "LEAVES"
    NONE = "NONE"


class ColorsConfig(TypedDict):
    """Hex colour strings for every themed UI surface."""

    primary: str
    secondary: str
    accent: str
    background: str
    bubble_bot: str
    bubble_user: str
    text: str


class BubbleStyleConfig(TypedDict):
    """Visual styling applied to message bubbles."""

    radius: int
    font_family: str
    font_size: str


@dataclass(frozen=True)
class PersonaConfig:
    """Immutable configuration for a single character persona.

    ``frozen=True`` ensures personas are value objects — they can be
    compared by content and safely shared across threads.
    """

    key: str
    """Unique identifier used as the dict key in PERSONAS (e.g. "iroh")."""

    name: str
    """Human-readable display name shown in the persona selection screen."""

    description: str
    """One-line summary shown beneath the name on the selection screen."""

    colors: ColorsConfig
    """Full colour palette applied to the chat UI when this persona is active."""

    bubble_style: BubbleStyleConfig
    """Corner radius and typography for message bubbles."""

    icon_emoji: str
    """Unicode emoji used as a placeholder avatar (e.g. ☕ for Iroh)."""

    particle_type: ParticleType
    """Ambient particle effect while the persona is active."""

    system_prompt: str
    """Persona-layer system prompt prepended to the LLM rewrite call.

    Empty string ("") means passthrough — no persona wrapping applied.
    """

    crisis_break_message: str
    """What the character says when breaking character for a crisis response.

    Prepended verbatim before the raw clinical response; not LLM-processed.
    """
