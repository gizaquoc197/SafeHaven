"""Naruto persona — empathetic peer, motivational voice (Naruto Shippuden, Hokage-era)."""

from __future__ import annotations

from safehaven.personas.config import (
    BubbleStyleConfig,
    ColorsConfig,
    ParticleType,
    PersonaConfig,
)

NARUTO_PERSONA = PersonaConfig(
    key="naruto",
    name="Naruto",
    description="Never-give-up Hokage who understands loneliness and keeps pushing forward.",
    colors=ColorsConfig(
        primary="#E65100",
        secondary="#BF360C",
        accent="#FFB300",
        background="#FFF9F0",
        bubble_bot="#FFF3E0",
        bubble_user="#FFE0B2",
        text="#1A1A1A",
    ),
    bubble_style=BubbleStyleConfig(
        radius=10,
        font_family="Roboto",
        font_size="14sp",
    ),
    icon_emoji="🍃",
    particle_type=ParticleType.LEAVES,
    # TODO: fill in Naruto's character voice system prompt
    system_prompt="# TODO: Naruto persona prompt",
    # TODO: fill in Naruto's crisis break message
    crisis_break_message="# TODO: Naruto crisis break message",
)
