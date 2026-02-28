"""Language detection module — detects user input language.

Implements the ``LanguageDetector`` protocol from ``interfaces.py``.
Supports English ('en') and Arabic ('ar').
"""

from __future__ import annotations


class SimpleLanguageDetector:
    """Detect language based on Unicode script analysis."""

    def detect_language(self, text: str) -> str:
        """Return ISO 639-1 language code ('en', 'ar')."""
        raise NotImplementedError  # TODO: implement in multilingual upgrade
