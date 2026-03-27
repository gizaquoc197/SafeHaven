"""Concrete strategy selector — picks a ResponseStrategy based on FSM state.

Implements the ``StrategySelector`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.interfaces import ResponseStrategy
from safehaven.models import RiskLevel
from safehaven.strategy.crisis import CrisisStrategy
from safehaven.strategy.de_escalation import DeEscalationStrategy
from safehaven.strategy.supportive import SupportiveStrategy


class ConcreteStrategySelector:
    """Select the appropriate response strategy based on risk and FSM state."""

    def select(self, risk: RiskLevel, fsm_state: str) -> ResponseStrategy:
        """Pick appropriate strategy based on FSM state.

        CRISIS   → CrisisStrategy  (QPR framework, hotlines prepended)
        ELEVATED → DeEscalationStrategy  (DBT Distress Tolerance)
        CALM/CONCERNED → SupportiveStrategy  (Motivational Interviewing)
        """
        if fsm_state == "crisis":
            return CrisisStrategy()
        elif fsm_state == "elevated":
            return DeEscalationStrategy()
        else:
            return SupportiveStrategy()
