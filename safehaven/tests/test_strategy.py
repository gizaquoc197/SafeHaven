"""Tests for the strategy pattern implementation."""

from __future__ import annotations

from safehaven.strategy.supportive import SupportiveStrategy


class TestSupportiveStrategy:
    """Test the supportive response strategy."""

    def test_post_process_passthrough(self) -> None:
        strategy = SupportiveStrategy()
        assert strategy.post_process("Hello there!") == "Hello there!"
