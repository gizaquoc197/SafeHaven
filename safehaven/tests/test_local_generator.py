"""Tests for the local model generator (Ollama)."""

from __future__ import annotations

from safehaven.llm.local_generator import LocalModelGenerator


class TestLocalModelGenerator:
    """Test local model generator instantiation and configuration."""

    def test_default_model_name(self) -> None:
        gen = LocalModelGenerator()
        assert gen._model == "llama3.2"

    def test_custom_model_name(self) -> None:
        gen = LocalModelGenerator(model_name="mistral")
        assert gen._model == "mistral"
