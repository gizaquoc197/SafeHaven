"""Supportive response strategy — used in CALM and CONCERNED FSM states.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class SupportiveStrategy:
    """Warm, empathetic prompting for low-risk conversations."""

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a supportive system prompt."""
        raise NotImplementedError  # TODO: implement in strategy upgrade

    def post_process(self, response: str) -> str:
        """Pass through without modification."""
        return response
