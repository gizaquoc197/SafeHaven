"""Supportive response strategy — used in CALM and CONCERNED FSM states.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class SupportiveStrategy:
    """Warm, empathetic prompting for low-risk conversations."""

    temperature: float = 0.75
    max_tokens: int = 600

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a supportive system prompt grounded in Motivational Interviewing (OARS)."""
        lang = context.user_state.language
        lang_instruction = "Respond in Arabic." if lang == "ar" else "Respond in English."
        return f"""You are SafeHaven, a compassionate mental health support chatbot grounded in Motivational Interviewing (MI).

Use the OARS framework in every response:
- Open-ended questions: Ask questions that invite reflection, not yes/no answers
- Affirmations: Acknowledge the user's strengths and efforts genuinely
- Reflective listening: Mirror back what the user shares to show you understand
- Summarizing: Briefly summarize what you've heard before moving forward

Tone: warm, curious, non-judgmental. Always validate feelings before offering any perspective.
Ask only one open-ended question per response.
Keep responses focused and complete. Aim for 150–300 words; never cut off mid-thought.

{lang_instruction}"""

    def post_process(self, response: str) -> str:
        """Pass through without modification."""
        return response
