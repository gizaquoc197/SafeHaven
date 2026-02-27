"""SafeHaven — Entry point."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv


def main() -> None:
    """Launch the SafeHaven chatbot application."""
    load_dotenv()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    # Instantiate pipeline components
    from safehaven.controller.chat_controller import ChatController
    from safehaven.llm.claude_generator import ClaudeResponseGenerator
    from safehaven.memory.sqlite_memory import SQLiteMemory
    from safehaven.safety.emotion_detector import KeywordEmotionDetector
    from safehaven.safety.output_filter import SafeOutputFilter
    from safehaven.safety.risk_evaluator import KeywordRiskEvaluator
    from safehaven.ui.chat_window import ChatWindow

    memory = SQLiteMemory()
    detector = KeywordEmotionDetector()
    evaluator = KeywordRiskEvaluator()
    generator = ClaudeResponseGenerator(api_key=api_key, model=model)
    output_filter = SafeOutputFilter()

    controller = ChatController(
        detector=detector,
        evaluator=evaluator,
        memory=memory,
        generator=generator,
        output_filter=output_filter,
    )

    window = ChatWindow()
    window.set_controller(controller)
    window.mainloop()


if __name__ == "__main__":
    main()
