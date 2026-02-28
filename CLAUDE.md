# SafeHaven — CLAUDE.md

## Project

SafeHaven is a safety-aware mental health chatbot (Python, Kivy, Anthropic Claude API). Course project — not for production use. Supports English and Arabic.

## Architecture

Pipeline: **UI (Kivy) → LanguageDetector → EmotionDetector → FSM RiskEvaluator → StrategySelector → ResponseGenerator → OutputFilter → UI**

`ChatController.handle_message` returns `None` on HIGH risk — UI must show crisis screen, not a text response.

## FSM States

`CALM → CONCERNED → ELEVATED → CRISIS`

- **CALM**: Normal conversation, low risk signals
- **CONCERNED**: Mild negative emotion detected, monitoring
- **ELEVATED**: Sustained negative emotion or escalation pattern
- **CRISIS**: Crisis keywords detected or rapid escalation

Transitions are forward-only within a session (no backwards movement). Reset on `clear()`.

## Strategy Pattern

Strategy is selected by FSM state via `StrategySelector`:

| FSM State | Strategy | Behavior |
|-----------|----------|----------|
| CALM / CONCERNED | `SupportiveStrategy` | Warm, empathetic prompting |
| ELEVATED | `DeEscalationStrategy` | Grounding, safety-aware prompting |
| CRISIS | `CrisisStrategy` | Minimal LLM, directs to resources |

## Multilingual

- `LanguageDetector` detects input language ('en', 'ar') before emotion detection
- Per-language keyword files: `crisis_keywords.txt` / `crisis_keywords_ar.txt`
- Per-language emotion words: `emotion_keywords_ar.json`

## Conventions

- Python 3.11+, `mypy --strict` must pass
- Modules implement **Protocols** from `interfaces.py` — don't subclass, just match the signature
- All data models live in `models.py` as dataclasses, not dicts
- Tests: `pytest`, always mock the LLM
- Crisis keywords in `resources/crisis_keywords.txt` (English) and `resources/crisis_keywords_ar.txt` (Arabic), one per line
- Emotion keywords for Arabic in `resources/emotion_keywords_ar.json`

## MCP Servers

- **SQLite** (project, `.mcp.json`): queries `safehaven.db` — the conversation storage database

## Gotchas

- Never call the LLM directly from UI code — always go through `ChatController`
- All crisis-related logic goes through `RiskEvaluator`, not ad-hoc keyword checks
- Strategy selection goes through `StrategySelector`, not hardcoded if/else
- FSM is stateful — lives for the session, reset on `clear()`
