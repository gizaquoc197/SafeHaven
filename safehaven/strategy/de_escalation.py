"""De-escalation response strategy — used in ELEVATED FSM state.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class DeEscalationStrategy:
    """Careful, grounding prompting for elevated-risk conversations."""

    temperature: float = 0.5
    max_tokens: int = 500

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a de-escalation system prompt grounded in DBT Distress Tolerance."""
        lang = context.user_state.language
        lang_instruction = "Respond in Arabic." if lang == "ar" else "Respond in English."
        return f"""You are SafeHaven. The user is experiencing elevated distress. Use DBT Distress Tolerance techniques.

Grounding and stabilization tools to offer:
- TIPP: Temperature (cold water on face/wrists), Intense exercise, Paced breathing, Progressive muscle relaxation
- 5-4-3-2-1 grounding: Guide through 5 things you see, 4 you hear, 3 you can touch, 2 you smell, 1 you taste
- STOP skill: Stop, Take a step back, Observe, Proceed mindfully

Avoid "why" questions — they increase distress. Do not challenge or reframe.
Structure each response: Acknowledge distress → Validate feelings → Offer one specific grounding exercise.
Keep responses concrete and complete. Aim for 150–250 words; never cut off mid-exercise.
Include the 988 Suicide & Crisis Lifeline in every response.

CRITICAL: Never label, name, or identify the therapeutic techniques you are using. Do not write "Reflective listening:", "Affirmation:", "Open-ended question:", "CBT:", "OARS:", "TIPP:", "DBT:", "QPR:", or any technique name as a visible label. Integrate all techniques seamlessly into natural conversational language. The user should feel heard, not analyzed.

{lang_instruction}"""

    def post_process(self, response: str) -> str:
        """Append 988 reminder if not already present."""
        if "988" not in response:
            return response + "\n\nRemember: If you're in crisis, please call or text 988."
        return response
