"""Tests for OutputFilter."""

from __future__ import annotations

from safehaven.models import RiskLevel
from safehaven.safety.output_filter import SafeOutputFilter


class TestSafeOutputFilter:
    def setup_method(self) -> None:
        self.filt = SafeOutputFilter()

    def test_low_risk_passes_through(self) -> None:
        text = "That sounds wonderful! Tell me more."
        assert self.filt.validate(text, RiskLevel.LOW) == text

    def test_medium_risk_prepends_empathetic_framing(self) -> None:
        text = "I hear you."
        result = self.filt.validate(text, RiskLevel.MEDIUM)
        assert result.startswith(
            "It sounds like you're going through a tough time"
        )
        assert result.endswith("I hear you.")

    def test_strips_medication_dosage_lines(self) -> None:
        text = "Here is some advice.\nTake 500mg of aspirin daily.\nStay hydrated."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "500mg" not in result
        assert "Stay hydrated" in result

    def test_strips_self_harm_method_lines(self) -> None:
        text = "I understand.\nHere is how to harm yourself.\nPlease be safe."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "how to harm" not in result
        assert "Please be safe" in result

    def test_strips_kill_method_line(self) -> None:
        text = "I understand.\nHere is a way to kill yourself.\nPlease call 988."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "way to kill" not in result
        assert "Please call 988" in result

    def test_strips_step_by_step_suicide_line(self) -> None:
        text = "Take care.\nStep-by-step suicide method below.\nYou are not alone."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "step-by-step" not in result.lower()
        assert "You are not alone" in result

    def test_strips_instructions_self_harm_line(self) -> None:
        text = "Here are instructions for self-harm.\nPlease reach out instead."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "instructions" not in result
        assert "reach out" in result

    def test_multiple_harmful_patterns_all_stripped(self) -> None:
        # "200mg" matches dosage pattern; "how to harm" matches harm-method pattern
        text = "Take 200mg of this medication.\nHere is how to harm yourself.\nYou deserve support."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert "200mg" not in result
        assert "how to harm" not in result
        assert "You deserve support" in result

    def test_harmless_number_not_stripped(self) -> None:
        text = "You mentioned 3 things bothering you. Let's explore them."
        result = self.filt.validate(text, RiskLevel.LOW)
        assert result == text
