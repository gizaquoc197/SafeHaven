"""Persona registry — imports all personas and exposes the PERSONAS lookup dict."""

from __future__ import annotations

from safehaven.personas.baymax import BAYMAX_PERSONA
from safehaven.personas.config import PersonaConfig
from safehaven.personas.default import DEFAULT_PERSONA
from safehaven.personas.iroh import IROH_PERSONA
from safehaven.personas.naruto import NARUTO_PERSONA

PERSONAS: dict[str, PersonaConfig] = {
    p.key: p
    for p in [DEFAULT_PERSONA, IROH_PERSONA, BAYMAX_PERSONA, NARUTO_PERSONA]
}

__all__ = ["PERSONAS", "PersonaConfig"]
