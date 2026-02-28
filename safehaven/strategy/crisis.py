"""Crisis response strategy — used in CRISIS FSM state.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class CrisisStrategy:
    """Minimal LLM interaction — directs to crisis resources."""

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a crisis-aware system prompt."""
        raise NotImplementedError  # TODO: implement in strategy upgrade

    def post_process(self, response: str) -> str:
        """Ensure response contains crisis resource references."""
        raise NotImplementedError  # TODO: implement in strategy upgrade
