"""Tests for the FSM-based risk evaluator."""

from __future__ import annotations

import pytest

from safehaven.safety.fsm_risk_evaluator import FSMRiskEvaluator


class TestFSMRiskEvaluator:
    """Test FSM state transitions and risk level mapping."""

    def test_initial_state_is_calm(self) -> None:
        evaluator = FSMRiskEvaluator()
        assert evaluator.state == "calm"

    def test_clear_resets_to_calm(self) -> None:
        evaluator = FSMRiskEvaluator()
        evaluator._state = "elevated"
        evaluator.clear()
        assert evaluator.state == "calm"
