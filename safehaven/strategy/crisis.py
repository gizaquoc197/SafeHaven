"""Crisis response strategy — used in CRISIS FSM state.

Implements the ``ResponseStrategy`` protocol from ``interfaces.py``.
"""

from __future__ import annotations

from safehaven.models import ConversationContext


class CrisisStrategy:
    """Minimal LLM interaction — directs to crisis resources."""

    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a crisis system prompt grounded in QPR (Question, Persuade, Refer)."""
        lang = context.user_state.language
        lang_instruction = "Respond in Arabic." if lang == "ar" else "Respond in English."
        return f"""You are SafeHaven. The user may be in crisis. Use the QPR framework:

- Question: Ask directly and compassionately about their safety right now
- Persuade: Express genuine care; give them a reason to reach out for help
- Refer: Provide crisis resources clearly and immediately

Use short sentences only. Total response: 50–100 words.
Every response must include: 988 (Suicide & Crisis Lifeline) and Crisis Text Line (text HOME to 741741).
Be direct, unambiguous, and compassionate — do not minimize or redirect away from safety.
Ask whether they are safe right now and whether they have a trusted person nearby.

{lang_instruction}"""

    def post_process(self, response: str) -> str:
        """Prepend crisis resource block to every response."""
        prefix = (
            "Please reach out for immediate support:\n"
            "\u2022 Call/text 988 (Suicide & Crisis Lifeline)\n"
            "\u2022 Text HOME to 741741 (Crisis Text Line)\n\n"
        )
        return prefix + response
