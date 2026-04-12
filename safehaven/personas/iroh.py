"""Uncle Iroh persona — wise mentor, CBT/Socratic voice (Avatar: TLA)."""

from __future__ import annotations

from safehaven.personas.config import (
    BubbleStyleConfig,
    ColorsConfig,
    ParticleType,
    PersonaConfig,
)

IROH_PERSONA = PersonaConfig(
    key="iroh",
    name="Uncle Iroh",
    description="Wise tea-loving mentor who guides with warmth and gentle wisdom.",
    colors=ColorsConfig(
        primary="#8B5E3C",
        secondary="#C4965A",
        accent="#E8C67A",
        background="#FFF8F0",
        bubble_bot="#FAEBD7",
        bubble_user="#E8C67A",
        text="#3E2723",
    ),
    bubble_style=BubbleStyleConfig(
        radius=12,
        font_family="Roboto",
        font_size="14sp",
    ),
    icon_emoji="☕",
    particle_type=ParticleType.STEAM,
    # TODO: fill in Iroh's character voice system prompt
    system_prompt="# TODO: Uncle Iroh persona prompt",
    # TODO: fill in Iroh's crisis break message
    crisis_break_message="# TODO: Iroh crisis break message",
)
