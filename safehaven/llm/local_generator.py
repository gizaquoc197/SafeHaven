"""Local model response generator — uses Ollama for offline LLM inference.

Implements the ``ResponseGenerator`` protocol from ``interfaces.py``.
Requires the ``ollama`` package (install with ``pip install safehaven[local]``).
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class LocalModelGenerator:
    """Generate responses using a local Ollama model."""

    def __init__(self, model_name: str = "llama3.2") -> None:
        self._model = model_name

    def generate(self, context: ConversationContext) -> str:
        """Call local Ollama model and return response text."""
        raise NotImplementedError  # TODO: implement in local model upgrade
