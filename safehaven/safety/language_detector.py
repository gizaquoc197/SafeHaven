"""Language detection module — detects user input language.

Implements the ``LanguageDetector`` protocol from ``interfaces.py``.
Supports English ('en') and Arabic ('ar').
"""

from __future__ import annotations


class SimpleLanguageDetector:
    """Detect language based on Unicode script analysis."""

    def detect_language(self, text: str) -> str:
        """Return ISO 639-1 language code ('en' or 'ar').

        Uses Unicode block analysis: if more than 30% of characters fall in
        the Arabic script range (U+0600–U+06FF), returns 'ar'; otherwise 'en'.
        """
        if not text.strip():
            return "en"
        arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        ratio = arabic_chars / len(text)
        return "ar" if ratio > 0.3 else "en"
