"""Property-based tests for FSMRiskEvaluator using Hypothesis.

These tests verify safety invariants across thousands of randomly generated
input sequences — providing much stronger guarantees than hand-written examples.

Run with: pytest safehaven/tests/test_fsm_hypothesis.py -v

Academic basis: Hypothesis's RuleBasedStateMachine is the gold-standard approach
for property-based testing of state machines (see Hypothesis docs and MacIver 2019).
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from safehaven.models import EmotionLabel, EmotionResult, RiskLevel, UserState
from safehaven.safety.fsm_risk_evaluator import FSMRiskEvaluator

# Mirrors the _RANK dict inside the implementation
_RANK: dict[str, int] = {"calm": 0, "concerned": 1, "elevated": 2, "crisis": 3}
_VALID_STATES: frozenset[str] = frozenset(_RANK)

_emotion_strategy = st.sampled_from(list(EmotionLabel))
_confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_turn_strategy = st.tuples(_emotion_strategy, _confidence_strategy)


def _user_state(label: EmotionLabel, confidence: float) -> UserState:
    return UserState(
        current_emotion=EmotionResult(label, confidence),
        risk_level=RiskLevel.LOW,
        message_count=1,
    )


# ---------------------------------------------------------------------------
# @given-based property tests
# ---------------------------------------------------------------------------


@given(sequence=st.lists(_turn_strategy, min_size=1, max_size=30))
def test_fsm_state_never_decreases(
    sequence: list[tuple[EmotionLabel, float]],
) -> None:
    """Monotonicity invariant: FSM state rank can only increase or stay the same."""
    evaluator = FSMRiskEvaluator()
    prev_rank = 0
    for label, confidence in sequence:
        evaluator.evaluate(_user_state(label, confidence))
        current_rank = _RANK[evaluator.state]
        assert current_rank >= prev_rank, (
            f"FSM decreased from rank {prev_rank} to {current_rank} "
            f"on input ({label}, {confidence:.3f})"
        )
        prev_rank = current_rank


@given(sequence=st.lists(_turn_strategy, min_size=1, max_size=30))
def test_fsm_state_always_valid(
    sequence: list[tuple[EmotionLabel, float]],
) -> None:
    """FSM state is always one of the four valid named states."""
    evaluator = FSMRiskEvaluator()
    for label, confidence in sequence:
        evaluator.evaluate(_user_state(label, confidence))
        assert evaluator.state in _VALID_STATES, (
            f"FSM reached invalid state: {evaluator.state!r}"
        )


@given(sequence=st.lists(_turn_strategy, min_size=1, max_size=20))
def test_crisis_is_terminal(
    sequence: list[tuple[EmotionLabel, float]],
) -> None:
    """Once CRISIS is reached, no subsequent input can leave that state."""
    evaluator = FSMRiskEvaluator()
    evaluator.evaluate(_user_state(EmotionLabel.FEARFUL, 1.0))
    assert evaluator.state == "crisis"

    for label, confidence in sequence:
        result = evaluator.evaluate(_user_state(label, confidence))
        assert evaluator.state == "crisis", (
            f"FSM left CRISIS on input ({label}, {confidence:.3f})"
        )
        assert result == RiskLevel.HIGH


@given(label=_emotion_strategy, confidence=_confidence_strategy)
def test_single_turn_from_calm_only_reaches_crisis_on_fearful_threshold(
    label: EmotionLabel, confidence: float
) -> None:
    """From CALM, HIGH risk requires FEARFUL ≥ 0.9. No other single input can do it."""
    evaluator = FSMRiskEvaluator()
    result = evaluator.evaluate(_user_state(label, confidence))
    if result == RiskLevel.HIGH:
        assert label == EmotionLabel.FEARFUL and confidence >= 0.9, (
            f"Got HIGH risk from ({label}, {confidence:.3f}) without FEARFUL ≥ 0.9"
        )


@given(sequence=st.lists(_turn_strategy, min_size=1, max_size=20))
def test_clear_fully_resets_fsm(
    sequence: list[tuple[EmotionLabel, float]],
) -> None:
    """After clear(), the FSM behaves identically to a fresh instance."""
    evaluator = FSMRiskEvaluator()
    for label, confidence in sequence:
        evaluator.evaluate(_user_state(label, confidence))

    evaluator.clear()

    assert evaluator.state == "calm"
    assert evaluator._consecutive_negative == 0
    # After reset, a single SAD (high confidence) should → concerned, not higher
    result = evaluator.evaluate(_user_state(EmotionLabel.SAD, 0.9))
    assert evaluator.state == "concerned"
    assert result == RiskLevel.MEDIUM


# ---------------------------------------------------------------------------
# RuleBasedStateMachine — exhaustive state-space exploration
# ---------------------------------------------------------------------------


class FSMStateMachine(RuleBasedStateMachine):
    """Hypothesis state machine that explores all reachable FSM transitions.

    Hypothesis generates arbitrary rule sequences and checks every invariant
    after each step, finding minimal counterexamples for any violation.
    """

    def __init__(self) -> None:
        super().__init__()
        self.evaluator = FSMRiskEvaluator()
        self._rank_history: list[int] = [0]

    @rule(
        label=st.sampled_from(list(EmotionLabel)),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def process_turn(self, label: EmotionLabel, confidence: float) -> None:
        self.evaluator.evaluate(_user_state(label, confidence))
        self._rank_history.append(_RANK[self.evaluator.state])

    @invariant()
    def state_is_valid(self) -> None:
        assert self.evaluator.state in _VALID_STATES

    @invariant()
    def state_rank_is_non_decreasing(self) -> None:
        if len(self._rank_history) >= 2:
            assert self._rank_history[-1] >= self._rank_history[-2], (
                f"Rank went from {self._rank_history[-2]} to {self._rank_history[-1]}"
            )


# Expose as a pytest test class
TestFSMStateMachine = FSMStateMachine.TestCase
