"""De-escalation response strategy — used in ELEVATED FSM state.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class DeEscalationStrategy:
    """Careful, grounding prompting for elevated-risk conversations."""

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a de-escalation system prompt."""
        raise NotImplementedError  # TODO: implement in strategy upgrade

    def post_process(self, response: str) -> str:
        """Add safety framing to the response."""
        raise NotImplementedError  # TODO: implement in strategy upgrade
