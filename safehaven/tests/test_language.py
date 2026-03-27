"""Tests for language detection."""

from __future__ import annotations

from safehaven.safety.language_detector import SimpleLanguageDetector


class TestSimpleLanguageDetector:
    """Test language detection for English and Arabic."""

    def test_detector_instantiates(self) -> None:
        assert SimpleLanguageDetector() is not None

    def test_english_text_returns_en(self) -> None:
        assert SimpleLanguageDetector().detect_language("Hello, how are you today?") == "en"

    def test_arabic_text_returns_ar(self) -> None:
        assert SimpleLanguageDetector().detect_language("مرحبا كيف حالك") == "ar"

    def test_mixed_mostly_arabic_returns_ar(self) -> None:
        # Predominantly Arabic text with a few Latin chars
        assert SimpleLanguageDetector().detect_language("أريد المساعدة help") == "ar"

    def test_mixed_mostly_english_returns_en(self) -> None:
        assert SimpleLanguageDetector().detect_language("Hello world مرحبا") == "en"

    def test_empty_string_returns_en(self) -> None:
        assert SimpleLanguageDetector().detect_language("") == "en"

    def test_whitespace_only_returns_en(self) -> None:
        assert SimpleLanguageDetector().detect_language("   ") == "en"

    def test_numbers_only_returns_en(self) -> None:
        assert SimpleLanguageDetector().detect_language("12345") == "en"

    def test_arabic_crisis_phrase_returns_ar(self) -> None:
        assert SimpleLanguageDetector().detect_language("أريد أن أموت") == "ar"
