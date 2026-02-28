"""Concrete strategy selector — picks a ResponseStrategy based on FSM state.

Implements the ``StrategySelector`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.interfaces import ResponseStrategy
from safehaven.models import RiskLevel


class ConcreteStrategySelector:
    """Select the appropriate response strategy based on risk and FSM state."""

    def select(self, risk: RiskLevel, fsm_state: str) -> ResponseStrategy:
        """Pick appropriate strategy based on FSM state."""
        raise NotImplementedError  # TODO: implement in strategy upgrade
