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

    from safehaven.logging_config import setup_logging
    setup_logging()

    # Instantiate pipeline components
    from safehaven.controller.chat_controller import ChatController
    from safehaven.llm.claude_generator import ClaudeResponseGenerator
    from safehaven.memory.sqlite_memory import SQLiteMemory
    from safehaven.safety.emotion_detector import KeywordEmotionDetector
    from safehaven.safety.fsm_risk_evaluator import FSMRiskEvaluator
    from safehaven.safety.language_detector import SimpleLanguageDetector
    from safehaven.safety.output_filter import SafeOutputFilter
    from safehaven.strategy.base import ConcreteStrategySelector
    from safehaven.ui.app import SafeHavenApp

    memory = SQLiteMemory()
    detector = KeywordEmotionDetector()
    evaluator = FSMRiskEvaluator()
    language_detector = SimpleLanguageDetector()
    strategy_selector = ConcreteStrategySelector()
    generator = ClaudeResponseGenerator(api_key=api_key, model=model)
    output_filter = SafeOutputFilter()

    controller = ChatController(
        detector=detector,
        evaluator=evaluator,
        memory=memory,
        generator=generator,
        output_filter=output_filter,
        language_detector=language_detector,
        strategy_selector=strategy_selector,
    )

    app = SafeHavenApp()
    app.set_controller(controller)
    app.run()


if __name__ == "__main__":
    main()
