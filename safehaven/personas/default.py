"""Default SafeHaven persona — passthrough, no character voice wrapping."""

from __future__ import annotations

from safehaven.personas.config import (
    BubbleStyleConfig,
    ColorsConfig,
    ParticleType,
    PersonaConfig,
)

DEFAULT_PERSONA = PersonaConfig(
    key="default",
    name="SafeHaven",
    description="SafeHaven's default voice — warm, clinical, neutral.",
    colors=ColorsConfig(
        primary="#5C6BC0",
        secondary="#7E57C2",
        accent="#FFC107",
        background="#FAFAFA",
        bubble_bot="#B0BEC5",
        bubble_user="#E8EAF6",
        text="#212121",
    ),
    bubble_style=BubbleStyleConfig(
        radius=8,
        font_family="Roboto",
        font_size="14sp",
    ),
    icon_emoji="🌿",
    particle_type=ParticleType.NONE,
    # Empty system_prompt → PersonaDecorator treats this as passthrough.
    system_prompt="",
    # Unused for the default persona — included for interface completeness.
    crisis_break_message="",
)
