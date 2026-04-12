"""Baymax persona — clinical companion, structured assessment voice (Big Hero 6)."""

from __future__ import annotations

from safehaven.personas.config import (
    BubbleStyleConfig,
    ColorsConfig,
    ParticleType,
    PersonaConfig,
)

BAYMAX_PERSONA = PersonaConfig(
    key="baymax",
    name="Baymax",
    description="Personal healthcare companion — methodical, gentle, thorough.",
    colors=ColorsConfig(
        primary="#0288D1",
        secondary="#01579B",
        accent="#B3E5FC",
        background="#F5F9FF",
        bubble_bot="#E3F2FD",
        bubble_user="#B3E5FC",
        text="#0D1B2A",
    ),
    bubble_style=BubbleStyleConfig(
        radius=16,
        font_family="Roboto",
        font_size="14sp",
    ),
    icon_emoji="🤖",
    particle_type=ParticleType.SCAN,
    # TODO: fill in Baymax's character voice system prompt
    system_prompt="# TODO: Baymax persona prompt",
    # TODO: fill in Baymax's crisis break message
    crisis_break_message="# TODO: Baymax crisis break message",
)
