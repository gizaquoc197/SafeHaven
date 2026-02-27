# SafeHaven

Safety-aware mental health chatbot built with Python, Tkinter, and the Anthropic Claude API.

> **Disclaimer:** This is a CS 6221 course project — not for production or clinical use.

## Prerequisites

- **Python 3.11+**
- **Git**
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
├── controller/       # ChatController — orchestrates the pipeline
├── llm/              # Claude API response generation
├── memory/           # SQLite-backed conversation memory
├── safety/           # EmotionDetector, RiskEvaluator, OutputFilter
├── ui/               # Tkinter chat window and crisis modal
├── tests/            # pytest test suite
├── interfaces.py     # Protocol definitions
└── models.py         # Dataclass models
```

**Pipeline:** UI → EmotionDetector → RiskEvaluator → ResponseGenerator → OutputFilter → UI
