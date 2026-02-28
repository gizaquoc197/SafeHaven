"""FSM-based risk evaluator — stateful risk assessment using finite state machine.

Implements the ``RiskEvaluator`` protocol from ``interfaces.py``.
Transitions: CALM → CONCERNED → ELEVATED → CRISIS
The FSM is stateful per session and resets on ``clear()``.
"""

from __future__ import annotations

from safehaven.models import RiskLevel, UserState


class FSMRiskEvaluator:
    """Evaluate risk using a finite state machine that tracks escalation."""

    def __init__(self) -> None:
        self._state: str = "calm"

    @property
    def state(self) -> str:
        """Current FSM state."""
        return self._state

    def evaluate(self, state: UserState) -> RiskLevel:
        """Determine risk level and advance FSM state."""
        raise NotImplementedError  # TODO: implement in FSM upgrade

    def clear(self) -> None:
        """Reset FSM to initial CALM state (new session)."""
        self._state = "calm"
