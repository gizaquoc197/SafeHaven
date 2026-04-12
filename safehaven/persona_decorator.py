"""PersonaDecorator — wraps a clinical response in a character voice via a second LLM call.

Design constraints
------------------
* Does NOT import any specific persona module — operates on whatever PersonaConfig it
  receives, so adding new personas requires zero changes here.
* Does NOT touch the FSM, emotion detection, or strategy selection.
* Runs AFTER strategy.post_process() and BEFORE memory.store_message() in handle_message.
* Fails open — if the LLM call raises, the original clinical response is returned intact.
"""

from __future__ import annotations

from safehaven.interfaces import ResponseGenerator
from safehaven.models import (
    ConversationContext,
    EmotionLabel,
    EmotionResult,
    Message,
    RiskLevel,
    UserState,
)
from safehaven.personas.config import PersonaConfig


def _make_persona_context(system_prompt: str, rewrite_request: str) -> ConversationContext:
    """Build a minimal ConversationContext suitable for a persona-rewrite LLM call.

    Uses a dummy UserState (NEUTRAL / LOW) so the existing ClaudeResponseGenerator
    can be reused without adding a new LLM interface.
    """
    dummy_state = UserState(
        current_emotion=EmotionResult(label=EmotionLabel.NEUTRAL, confidence=0.0),
        risk_level=RiskLevel.LOW,
        message_count=1,
    )
    return ConversationContext(
        recent_messages=[Message(role="user", content=rewrite_request)],
        user_state=dummy_state,
        system_prompt=system_prompt,
        temperature=0.8,
        max_tokens=600,
    )


class PersonaDecorator:
    """Wraps a therapeutic response in a character's voice.

    Injected with a ``ResponseGenerator`` so it can make a second LLM call
    without bypassing the existing abstraction.

    Usage::

        decorator = PersonaDecorator(persona=PERSONAS["iroh"], generator=generator)
        decorated = decorator.wrap_response(raw, emotion="sad", risk_state="concerned")
    """

    def __init__(self, persona: PersonaConfig, generator: ResponseGenerator) -> None:
        self.persona = persona
        self._generator = generator

    def wrap_response(
        self,
        raw_response: str,
        emotion: str,
        risk_state: str,
    ) -> str:
        """Return ``raw_response`` wrapped in the persona's voice.

        Args:
            raw_response: The fully post-processed clinical response text.
            emotion:      Current emotion label string (e.g. "sad", "anxious").
            risk_state:   Current FSM state string ("calm", "concerned",
                          "elevated", "crisis").

        Returns:
            The persona-voiced response, or ``raw_response`` unchanged if:

            * ``risk_state`` is ``"crisis"`` — break character, prepend
              ``crisis_break_message`` if provided.
            * ``persona.system_prompt`` is empty — passthrough (default persona).
            * The LLM call raises any exception — fail-open.
        """
        # 1. Crisis guard — break character, prepend the persona's crisis message.
        #    Defensive: the controller's crisis gate (risk == HIGH → return None) fires
        #    before the decorator runs, but this handles any future edge case where
        #    fsm_state=="crisis" reaches us.
        if risk_state == "crisis":
            if self.persona.crisis_break_message:
                return self.persona.crisis_break_message + "\n\n" + raw_response
            return raw_response

        # 2. Passthrough guard — empty system_prompt means no persona layer.
        if not self.persona.system_prompt:
            return raw_response

        # 3. Build the rewrite request for the LLM.
        rewrite_request = (
            f"The following is a therapeutic response to someone feeling {emotion}. "
            "Rewrite it in your character's voice while preserving ALL therapeutic "
            "content, clinical accuracy, and any crisis resources verbatim. "
            "Do not add advice, opinions, or information beyond what is already present. "
            "Keep roughly the same length.\n\n"
            f"Response to rewrite:\n{raw_response}"
        )
        context = _make_persona_context(
            system_prompt=self.persona.system_prompt,
            rewrite_request=rewrite_request,
        )

        # 4. Call the LLM — fail open on any error.
        try:
            return self._generator.generate(context)
        except Exception:
            return raw_response
