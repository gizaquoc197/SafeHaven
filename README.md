# SafeHaven

Safety-aware mental health chatbot built with Python and the Anthropic Claude API. Implements the **Stateful Safety Pipeline (SSP)** — six Gang of Four design patterns composed to create a formally architected, risk-adaptive conversational system.

> **Disclaimer:** This is a CS 6221 course project — not for production or clinical use.

## Prerequisites

- **Python 3.11+**
- **Git**
- **Kivy system dependencies** — see [Kivy installation guide](https://kivy.org/doc/stable/gettingstarted/installation.html) for your platform
- (Optional) [uv](https://docs.astral.sh/uv/) for faster dependency management
- (Optional) [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) for MCP server integration

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd SafeHaven

# Create and activate a virtual environment
python -m venv .venv

# Windows (Git Bash / MSYS2)
source .venv/Scripts/activate

# macOS / Linux
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# For local model support (Ollama)
pip install -e ".[local]"

# Configure environment variables
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY

# Run the application
python -m safehaven.main
```

## Development

```bash
# Type checking (strict mode)
python -m mypy --strict safehaven/

# Run tests
python -m pytest
```

All tests mock the LLM — no API key needed to run the test suite.

## Claude Code Setup (Optional)

The project includes a `.mcp.json` that auto-loads the **SQLite MCP server** for querying `safehaven.db` (conversation storage).

To add the **Context7 MCP server** (user-scope, provides library documentation):

```bash
claude mcp add --transport http --scope user context7 https://mcp.context7.com/mcp
```

## Project Structure

```
safehaven/
├── controller/              # ChatController — orchestrates the SSP pipeline
├── llm/
│   ├── claude_generator.py  # ResponseGenerator impl (Anthropic Claude)
│   └── local_generator.py   # ResponseGenerator impl (Ollama, local)
├── memory/
│   ├── sqlite_memory.py     # ConversationMemory impl (SQLite — production)
│   └── in_memory.py         # ConversationMemory impl (in-memory — testing)
├── safety/
│   ├── emotion_detector.py  # EmotionDetector impl
│   ├── fsm_risk_evaluator.py # FSMRiskEvaluator — active, stateful, forward-only
│   ├── language_detector.py # SimpleLanguageDetector — Arabic Unicode detection
│   ├── risk_evaluator.py    # KeywordRiskEvaluator (kept for reference)
│   └── output_filter.py     # OutputFilter impl
├── strategy/
│   ├── base.py              # ConcreteStrategySelector
│   ├── supportive.py        # SupportiveStrategy — CALM/CONCERNED (MI/OARS)
│   ├── de_escalation.py     # DeEscalationStrategy — ELEVATED (DBT/TIPP)
│   └── crisis.py            # CrisisStrategy — CRISIS (QPR)
├── ui/
│   ├── app.py               # Kivy App + ScreenManager
│   ├── welcome_screen.py    # Splash/welcome screen
│   ├── chat_screen.py       # Chat interface — FSM color bar, emotion bubbles
│   ├── crisis_screen.py     # Crisis resources display
│   ├── insights_screen.py   # Emotion dashboard (DashboardViewModel + Observer)
│   └── theme.py             # Colors, emotion-to-color map, FSM risk colors
├── tests/                   # pytest test suite (86 tests)
├── resources/
│   ├── crisis_keywords.txt      # English crisis keywords (58 entries)
│   ├── crisis_keywords_ar.txt   # Arabic crisis keywords (32 entries)
│   ├── crisis_hotlines.json     # Country → hotline mapping
│   └── emotion_keywords_ar.json # Arabic emotion word sets
├── logging_config.py        # Structured logging setup
├── interfaces.py            # Protocol definitions
└── models.py                # Dataclass models
```

## Pipeline (SSP — Stateful Safety Pipeline)

```
UI (Kivy) → LanguageDetector → EmotionDetector → FSMRiskEvaluator → StrategySelector → ResponseGenerator → OutputFilter → UI
```

FSM states: `CALM → CONCERNED → ELEVATED → CRISIS` (forward-only, resets on `clear()`)

## Design Patterns

| Pattern | Where | Status |
|---------|-------|--------|
| **Strategy** | `ConcreteStrategySelector` picks strategy by FSM state (MI / DBT / QPR) | Implemented |
| **FSM** | `FSMRiskEvaluator` — forward-only ratchet across CALM→CONCERNED→ELEVATED→CRISIS | Implemented |
| **Pipeline** | `ChatController.handle_message()` — 11-step SSP | Implemented |
| **Observer** | `DashboardViewModel(EventDispatcher)` + UI ← Controller callback | Implemented |
| **Repository** | `ConversationMemory` — two backends: SQLite + InMemory | Implemented |
| **Dependency Injection** | Controller accepts Protocol-typed dependencies | Implemented |
