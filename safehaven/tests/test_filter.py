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
