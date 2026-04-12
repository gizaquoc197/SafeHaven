"""Tests for PersonaDecorator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from safehaven.persona_decorator import PersonaDecorator, _make_persona_context
from safehaven.personas import PERSONAS
from safehaven.personas.config import ParticleType, PersonaConfig
from safehaven.personas.default import DEFAULT_PERSONA


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_stub_persona(
    key: str = "stub",
    system_prompt: str = "You are a stub character.",
    crisis_break_message: str = "BREAK_CHARACTER",
) -> PersonaConfig:
    """Create a minimal PersonaConfig for testing."""
    from safehaven.personas.config import BubbleStyleConfig, ColorsConfig

    return PersonaConfig(
        key=key,
        name="Stub",
        description="Test persona",
        colors=ColorsConfig(
            primary="#000000",
            secondary="#111111",
            accent="#222222",
            background="#FFFFFF",
            bubble_bot="#EEEEEE",
            bubble_user="#DDDDDD",
            text="#000000",
        ),
        bubble_style=BubbleStyleConfig(radius=8, font_family="Roboto", font_size="14sp"),
        icon_emoji="🧪",
        particle_type=ParticleType.NONE,
        system_prompt=system_prompt,
        crisis_break_message=crisis_break_message,
    )


def _mock_generator(return_value: str = "DECORATED") -> MagicMock:
    gen = MagicMock()
    gen.generate.return_value = return_value
    return gen


# ---------------------------------------------------------------------------
# _make_persona_context helper
# ---------------------------------------------------------------------------


def test_make_persona_context_sets_system_prompt() -> None:
    ctx = _make_persona_context("MY_PROMPT", "rewrite this")
    assert ctx.system_prompt == "MY_PROMPT"


def test_make_persona_context_single_user_message() -> None:
    ctx = _make_persona_context("PROMPT", "hello")
    messages = ctx.to_llm_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "hello" in messages[0]["content"]


# ---------------------------------------------------------------------------
# wrap_response — passthrough cases
# ---------------------------------------------------------------------------


def test_default_persona_is_passthrough() -> None:
    """Default persona (empty system_prompt) must never call the generator."""
    gen = _mock_generator()
    dec = PersonaDecorator(DEFAULT_PERSONA, gen)
    result = dec.wrap_response("clinical text", emotion="sad", risk_state="calm")
    assert result == "clinical text"
    gen.generate.assert_not_called()


def test_empty_system_prompt_is_passthrough() -> None:
    persona = _make_stub_persona(system_prompt="")
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    result = dec.wrap_response("original", emotion="anxious", risk_state="elevated")
    assert result == "original"
    gen.generate.assert_not_called()


# ---------------------------------------------------------------------------
# wrap_response — crisis guard
# ---------------------------------------------------------------------------


def test_crisis_state_breaks_character_with_message() -> None:
    persona = _make_stub_persona(crisis_break_message="I must be direct now.")
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    result = dec.wrap_response("call 988", emotion="fearful", risk_state="crisis")
    assert result == "I must be direct now.\n\ncall 988"
    gen.generate.assert_not_called()


def test_crisis_state_no_break_message_returns_raw() -> None:
    persona = _make_stub_persona(crisis_break_message="")
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    result = dec.wrap_response("call 988", emotion="fearful", risk_state="crisis")
    assert result == "call 988"
    gen.generate.assert_not_called()


# ---------------------------------------------------------------------------
# wrap_response — normal (non-crisis) path
# ---------------------------------------------------------------------------


def test_non_crisis_calls_generator_once() -> None:
    persona = _make_stub_persona()
    gen = _mock_generator(return_value="In my character voice: clinical text")
    dec = PersonaDecorator(persona, gen)
    result = dec.wrap_response("clinical text", emotion="sad", risk_state="calm")
    assert result == "In my character voice: clinical text"
    gen.generate.assert_called_once()


def test_non_crisis_passes_system_prompt_to_context() -> None:
    persona = _make_stub_persona(system_prompt="Be wise.")
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    dec.wrap_response("text", emotion="neutral", risk_state="concerned")
    ctx = gen.generate.call_args[0][0]
    assert ctx.system_prompt == "Be wise."


def test_non_crisis_rewrite_request_contains_raw_response() -> None:
    persona = _make_stub_persona()
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    dec.wrap_response("my clinical text", emotion="anxious", risk_state="elevated")
    ctx = gen.generate.call_args[0][0]
    user_content = ctx.to_llm_messages()[0]["content"]
    assert "my clinical text" in user_content


def test_non_crisis_rewrite_request_includes_emotion() -> None:
    persona = _make_stub_persona()
    gen = _mock_generator()
    dec = PersonaDecorator(persona, gen)
    dec.wrap_response("text", emotion="angry", risk_state="calm")
    ctx = gen.generate.call_args[0][0]
    user_content = ctx.to_llm_messages()[0]["content"]
    assert "angry" in user_content


# ---------------------------------------------------------------------------
# wrap_response — fail-open on generator exception
# ---------------------------------------------------------------------------


def test_generator_exception_returns_raw_response() -> None:
    persona = _make_stub_persona()
    gen = MagicMock()
    gen.generate.side_effect = RuntimeError("API down")
    dec = PersonaDecorator(persona, gen)
    result = dec.wrap_response("clinical text", emotion="sad", risk_state="calm")
    assert result == "clinical text"


# ---------------------------------------------------------------------------
# PERSONAS registry
# ---------------------------------------------------------------------------


def test_personas_dict_contains_all_keys() -> None:
    assert set(PERSONAS.keys()) == {"default", "iroh", "baymax", "naruto"}


def test_all_personas_have_correct_key_field() -> None:
    for key, persona in PERSONAS.items():
        assert persona.key == key


def test_default_persona_is_passthrough() -> None:  # type: ignore[no-redef]
    assert PERSONAS["default"].system_prompt == ""
    assert PERSONAS["default"].particle_type == ParticleType.NONE


def test_character_personas_have_particle_types() -> None:
    assert PERSONAS["iroh"].particle_type == ParticleType.STEAM
    assert PERSONAS["baymax"].particle_type == ParticleType.SCAN
    assert PERSONAS["naruto"].particle_type == ParticleType.LEAVES


def test_personas_are_frozen() -> None:
    with pytest.raises(AttributeError):
        PERSONAS["iroh"].key = "hacked"  # type: ignore[misc]
