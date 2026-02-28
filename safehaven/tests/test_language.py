"""Tests for language detection."""

from __future__ import annotations

from safehaven.safety.language_detector import SimpleLanguageDetector


class TestSimpleLanguageDetector:
    """Test language detection for English and Arabic."""

    def test_detector_instantiates(self) -> None:
        detector = SimpleLanguageDetector()
        assert detector is not None
