# SafeHaven — CLAUDE.md

## Commit Style

Never add `Co-Authored-By` or any AI attribution lines to commit messages in this repo.

## Project

SafeHaven is a safety-aware mental health chatbot (Python, Anthropic Claude API). Course project — not for production use. Supports English and Arabic.

## Architecture

The architecture is named the **Stateful Safety Pipeline (SSP)** — use this name in docs and presentations.

**Active pipeline:** `UI (Kivy) → LanguageDetector → EmotionDetector → FSMRiskEvaluator → StrategySelector → ResponseGenerator → OutputFilter → UI`

`ChatController.handle_message` returns `None` on HIGH risk — UI must show crisis screen, not a text response.

## FSM States

`CALM → CONCERNED → ELEVATED → CRISIS`

- **CALM**: Normal conversation, low risk signals
- **CONCERNED**: First negative emotion detected (confidence > 0.6)
- **ELEVATED**: 3+ consecutive negative emotion turns
- **CRISIS**: FEARFUL emotion (confidence ≥ 0.9) — terminal state for the session

Transitions are forward-only within a session (no backwards movement). Reset on `clear()`.
`FSMRiskEvaluator` uses `_RANK` dict for monotonic enforcement — `_transition_to()` asserts `_RANK[new] >= _RANK[current]`.

## Strategy Pattern

Strategy is selected by FSM state via `ConcreteStrategySelector`:

| FSM State | Strategy | Clinical Framework |
|-----------|----------|--------------------|
| CALM / CONCERNED | `SupportiveStrategy` | Motivational Interviewing (OARS) |
| ELEVATED | `DeEscalationStrategy` | DBT Distress Tolerance (TIPP/5-4-3-2-1) |
| CRISIS | `CrisisStrategy` | QPR (Question, Persuade, Refer) |

Never instantiate strategies directly in the controller — always go through `StrategySelector`.

## Multilingual

- `SimpleLanguageDetector` is active — Arabic detected via Unicode ratio (U+0600–U+06FF chars > 30%)
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
- Never instantiate strategies directly in the controller — always go through `StrategySelector`
- FSM is stateful — lives for the session, reset on `clear()`. `FSMRiskEvaluator` is the active evaluator (`KeywordRiskEvaluator` is kept for reference but no longer wired)
- `InMemoryConversationMemory` (`memory/in_memory.py`) is the second Repository backend — use it in tests instead of inline `FakeMemory`
