# SafeHaven — Design Document

> **Course Project — Safety-Aware Mental Health Chatbot**
> Version 2.0 · February 2026

---

## 1. Project Overview

**SafeHaven** is a desktop chatbot that provides empathetic conversational support while actively monitoring for signs of emotional distress or crisis. It uses an API-based LLM (Anthropic Claude) for response generation, layered behind a safety pipeline that detects language, analyzes emotion, evaluates risk via a finite state machine, selects response strategies, and filters output.

### Scope

| In Scope | Out of Scope |
|----------|--------------|
| English + Arabic text chat | Other languages |
| Desktop GUI (Kivy) | Web or mobile deployment |
| API-based LLM (Anthropic Claude) | Fine-tuned models |
| Local LLM option (Ollama) | Cloud-hosted local models |
| FSM-based risk detection | Clinical-grade NLP |
| Strategy-driven response generation | Hardcoded response logic |
| SQLite conversation storage | Cloud database / auth |
| Crisis resource display | Actual crisis intervention |
| Emotional insights dashboard | Real-time analytics |
| 3 demo scenarios | Production deployment |

**Important disclaimer:** SafeHaven is a course project demonstrating safety-aware architecture. It is **not** a clinical tool and must not be used as a substitute for professional mental health support.

---

## 2. Architecture Overview

### Layered Pipeline

```
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION                       │
│                Kivy ScreenManager                    │
│   (welcome, chat, crisis, insights screens)          │
└──────────────────────┬──────────────────────────────┘
                       │ user text
                       ▼
┌─────────────────────────────────────────────────────┐
│                 LANGUAGE DETECTION                    │
│         LanguageDetector.detect_language(text)        │
│              → 'en' | 'ar'                           │
└──────────────────────┬──────────────────────────────┘
                       │ language code
                       ▼
┌─────────────────────────────────────────────────────┐
│                   PROCESSING                         │
│   ┌─────────────────┐   ┌────────────────────┐      │
│   │ EmotionDetector  │   │ ConversationMemory │      │
│   │ detect(text)     │   │ store / retrieve   │      │
│   └────────┬────────┘   └────────┬───────────┘      │
│            │ EmotionResult       │ recent messages   │
│            ▼                     ▼                   │
│         ┌──────────────────────────┐                 │
│         │       UserState          │                 │
│         └────────────┬─────────────┘                 │
└──────────────────────┼──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                    DECISION                          │
│           FSMRiskEvaluator (stateful)                │
│     evaluate(UserState) → RiskLevel                  │
│     FSM: CALM → CONCERNED → ELEVATED → CRISIS       │
└──────────────────────┬──────────────────────────────┘
                       │ RiskLevel + FSM state
                       ▼
┌─────────────────────────────────────────────────────┐
│               STRATEGY SELECTION                     │
│     StrategySelector.select(risk, fsm_state)         │
│        → ResponseStrategy                            │
│                                                      │
│     CALM/CONCERNED → SupportiveStrategy              │
│     ELEVATED       → DeEscalationStrategy            │
│     CRISIS         → CrisisStrategy                  │
└──────────────────────┬──────────────────────────────┘
                       │ strategy
                       ▼
              ┌────────┴────────┐
              │                 │
         LOW / MEDIUM          HIGH
              │                 │
              ▼                 ▼
┌─────────────────────┐  ┌──────────────┐
│     GENERATION      │  │ CRISIS PATH  │
│  ResponseGenerator  │  │ Lock input,  │
│  generate(context)  │  │ show crisis  │
│  (system prompt     │  │ screen with  │
│   from strategy)    │  │ hotlines     │
└─────────┬───────────┘  └──────────────┘
          │ raw response
          ▼
┌─────────────────────────────────────────────────────┐
│                   VALIDATION                         │
│   OutputFilter.validate(response, risk) → str        │
│   + Strategy.post_process(response) → str            │
│   (strip harmful content, enforce tone)              │
└──────────────────────┬──────────────────────────────┘
                       │ safe response
                       ▼
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION                       │
│   Display response in chat (emotion-colored bubble)  │
└─────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Key Rule |
|-------|---------|----------|
| **Presentation** | Renders Kivy UI, captures input | Never calls LLM directly |
| **Language Detection** | Identifies input language | Runs before emotion detection |
| **Processing** | Extracts emotion, stores messages | Stateless detection, stateful storage |
| **Decision** | FSM evaluates risk from UserState | Single source of risk truth; stateful per session |
| **Strategy Selection** | Picks response strategy by FSM state | Decouples strategy from controller logic |
| **Generation** | Calls LLM API with strategy-built prompt | Only called if risk ≤ MEDIUM |
| **Validation** | Filters LLM output + strategy post-processing | Last gate before display |

---

## 3. Data Models

All models live in `safehaven/models.py`.

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class FSMState(Enum):
    CALM = "calm"
    CONCERNED = "concerned"
    ELEVATED = "elevated"
    CRISIS = "crisis"


class EmotionLabel(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    FEARFUL = "fearful"


class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class EmotionResult:
    label: EmotionLabel
    confidence: float  # 0.0 – 1.0


@dataclass
class Message:
    role: str              # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    emotion: EmotionLabel | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    language: str = "en"


@dataclass
class UserState:
    current_emotion: EmotionResult
    risk_level: RiskLevel
    message_count: int
    escalation_history: list[RiskLevel] = field(default_factory=list)
    language: str = "en"
    fsm_state: str = "calm"


@dataclass
class ConversationContext:
    recent_messages: list[Message]
    user_state: UserState
    system_prompt: str = ""
    strategy_name: str = ""

    def to_llm_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.recent_messages]
```

---

## 4. Module Interfaces

Each module is defined as a Python Protocol so implementations can be swapped (real vs. stub). All interfaces live in `safehaven/interfaces.py`.

```python
from typing import Protocol
from safehaven.models import (
    EmotionResult, RiskLevel, UserState,
    Message, ConversationContext,
)


class EmotionDetector(Protocol):
    def detect(self, text: str) -> EmotionResult:
        """Analyze text and return the dominant emotion with confidence."""
        ...


class RiskEvaluator(Protocol):
    def evaluate(self, state: UserState) -> RiskLevel:
        """Determine risk level from current user state."""
        ...


class ConversationMemory(Protocol):
    def store_message(self, message: Message) -> None:
        """Persist a message to storage."""
        ...

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """Retrieve the N most recent messages, oldest first."""
        ...

    def clear(self) -> None:
        """Clear all stored messages (new session)."""
        ...


class ResponseGenerator(Protocol):
    def generate(self, context: ConversationContext) -> str:
        """Call the LLM API and return the raw response text."""
        ...


class OutputFilter(Protocol):
    def validate(self, response: str, risk: RiskLevel) -> str:
        """Sanitize LLM output based on current risk level."""
        ...


class LanguageDetector(Protocol):
    def detect_language(self, text: str) -> str:
        """Return ISO 639-1 language code ('en', 'ar')."""
        ...


class ResponseStrategy(Protocol):
    def build_system_prompt(self, context: ConversationContext) -> str:
        """Return a system prompt tailored to current risk/emotion state."""
        ...

    def post_process(self, response: str) -> str:
        """Optional post-processing of LLM output."""
        ...


class StrategySelector(Protocol):
    def select(self, risk: RiskLevel, fsm_state: str) -> ResponseStrategy:
        """Pick appropriate strategy based on FSM state."""
        ...
```

### ChatController — Orchestrator

```python
class ChatController:
    """Orchestrates the full message pipeline.

    Owns no business logic — delegates to injected modules.
    """

    def __init__(
        self,
        detector: EmotionDetector,
        evaluator: RiskEvaluator,
        memory: ConversationMemory,
        generator: ResponseGenerator,
        output_filter: OutputFilter,
    ) -> None:
        self.detector = detector
        self.evaluator = evaluator
        self.memory = memory
        self.generator = generator
        self.output_filter = output_filter

    def handle_message(self, user_text: str) -> str | None:
        """Process one user message through the full pipeline.

        Returns the assistant response, or None if crisis path activated.
        """
        # 1. Detect emotion
        emotion = self.detector.detect(user_text)

        # 2. Store user message
        user_msg = Message(role="user", content=user_text, emotion=emotion.label)
        self.memory.store_message(user_msg)

        # 3. Build user state
        state = UserState(
            current_emotion=emotion,
            risk_level=RiskLevel.LOW,
            message_count=len(self.memory.get_recent_messages()),
        )

        # 4. Evaluate risk
        risk = self.evaluator.evaluate(state)

        # 5. Crisis path
        if risk == RiskLevel.HIGH:
            return None  # Signal UI to show crisis screen

        # 6. Generate response
        context = ConversationContext(
            recent_messages=self.memory.get_recent_messages(),
            user_state=state,
        )
        raw_response = self.generator.generate(context)

        # 7. Filter output
        safe_response = self.output_filter.validate(raw_response, risk)

        # 8. Store assistant message
        assistant_msg = Message(
            role="assistant", content=safe_response, risk_level=risk
        )
        self.memory.store_message(assistant_msg)

        return safe_response
```

---

## 5. Folder Structure

```
safehaven/
├── main.py                      # Entry point — launches UI
├── models.py                    # Data models (Section 3)
├── interfaces.py                # Protocol definitions (Section 4)
├── logging_config.py            # Structured logging setup
├── ui/
│   ├── __init__.py
│   ├── app.py                   # Kivy App + ScreenManager
│   ├── welcome_screen.py        # Splash screen
│   ├── chat_screen.py           # Main chat interface
│   ├── crisis_screen.py         # Crisis resource display
│   ├── insights_screen.py       # Emotional trends dashboard
│   └── theme.py                 # Colors, emotion-to-color map
├── memory/
│   ├── __init__.py
│   ├── sqlite_memory.py         # ConversationMemory impl (SQLite)
│   └── schema.sql               # CREATE TABLE statements
├── safety/
│   ├── __init__.py
│   ├── emotion_detector.py      # EmotionDetector impl
│   ├── risk_evaluator.py        # RiskEvaluator impl (keyword-based)
│   ├── fsm_risk_evaluator.py    # FSM RiskEvaluator impl (stateful)
│   ├── language_detector.py     # LanguageDetector impl
│   └── output_filter.py         # OutputFilter impl
├── llm/
│   ├── __init__.py
│   ├── claude_generator.py      # ResponseGenerator impl (Anthropic Claude)
│   └── local_generator.py       # ResponseGenerator impl (Ollama, local)
├── strategy/
│   ├── __init__.py
│   ├── base.py                  # ConcreteStrategySelector
│   ├── supportive.py            # SupportiveStrategy (CALM/CONCERNED)
│   ├── de_escalation.py         # DeEscalationStrategy (ELEVATED)
│   └── crisis.py                # CrisisStrategy (CRISIS)
├── controller/
│   ├── __init__.py
│   └── chat_controller.py       # ChatController (orchestrator)
├── tests/
│   ├── __init__.py
│   ├── test_emotion.py
│   ├── test_risk.py
│   ├── test_filter.py
│   ├── test_memory.py
│   ├── test_controller.py       # Integration test with stubs
│   ├── test_fsm.py              # FSM transition tests
│   ├── test_strategy.py         # Strategy pattern tests
│   ├── test_language.py         # Language detection tests
│   └── test_local_generator.py  # Local model tests
├── resources/
│   ├── crisis_hotlines.json     # Country → hotline mapping
│   ├── crisis_keywords.txt      # English crisis keywords
│   ├── crisis_keywords_ar.txt   # Arabic crisis keywords
│   ├── emotion_keywords_ar.json # Arabic emotion word sets
│   └── safehaven.kv             # Kivy layout file
└── CLAUDE.md                    # Shared LLM context for team
```

---

## 6. Weekly Timeline — Task Board

> **Principle:** Tasks, not roles. Anyone picks up any task. Each task is ~3 hours and has a binary "done" check.

### Week 1 — Design & Setup

| # | Task | Done When |
|---|------|-----------|
| 1 | Create GitHub repo with folder structure and `.gitignore` | Repo exists, everyone can clone |
| 2 | Write `models.py` with all dataclasses/enums | File passes `mypy --strict` |
| 3 | Write `interfaces.py` with all Protocol classes | File passes `mypy --strict` |
| 4 | Create `crisis_keywords.txt` (30+ phrases) | File exists in `resources/` |
| 5 | Create `crisis_hotlines.json` (at least 3 countries) | Valid JSON, loadable |
| 6 | Draw UML class diagram (PlantUML or draw.io) | PNG/SVG in `docs/` |
| 7 | Write `CLAUDE.md` and place in repo root | File committed |

### Week 2 — Core Module Stubs

| # | Task | Done When |
|---|------|-----------|
| 1 | Write `schema.sql` + `sqlite_memory.py` (store + retrieve) | `test_memory.py` passes — stores and retrieves 3 messages |
| 2 | Write `emotion_detector.py` — keyword-based stub | `detect("I feel great")` → `HAPPY`, `detect("I'm so worried")` → `ANXIOUS` |
| 3 | Write `risk_evaluator.py` — keyword list check + threshold | Returns `HIGH` for any crisis keyword match |
| 4 | Write `output_filter.py` — regex blocklist | Strips "you should just…" patterns, returns cleaned text |
| 5 | Write `claude_generator.py` — call Claude API, return text | Returns a string for a simple prompt (manual test with API key) |
| 6 | Build basic `chat_window.py` — input box + message list | Window opens, text appears on send button click |

### Week 3 — Module Logic

| # | Task | Done When |
|---|------|-----------|
| 1 | Risk evaluator FSM: track escalation over 3+ messages | `test_risk.py` — 3 sad messages in a row → `MEDIUM` |
| 2 | Prompt template system — build system prompt from `UserState` | `ConversationContext.to_llm_messages()` includes emotion-aware system prompt |
| 3 | Output filter — tone adjustment for `MEDIUM` risk | Prepends empathetic framing sentence at `MEDIUM` |
| 4 | `chat_controller.py` — wire `handle_message()` pipeline | `test_controller.py` passes with all-stub dependencies |
| 5 | `crisis_modal.py` — popup with hotline info | Modal appears, blocks input, has a close/acknowledge button |
| 6 | Memory: add `clear()` + session reset | New session starts with empty history |

### Week 4 — Integration

| # | Task | Done When |
|---|------|-----------|
| 1 | Wire `chat_window.py` → `ChatController` | Typed message flows through pipeline and response appears |
| 2 | Wire `ChatController` → `claude_generator.py` (real API) | Real LLM response appears in chat window |
| 3 | Wire crisis path: `handle_message()` returns `None` → show modal | Typing "I want to end it all" shows crisis modal |
| 4 | End-to-end test: normal conversation (3 turns) | Passes in CI (with mocked LLM) |
| 5 | End-to-end test: escalation → crisis | Passes in CI (with mocked LLM) |
| 6 | Config file for API key + model name | `.env` file loaded, not hardcoded |

### Week 5 — Testing & Hardening

| # | Task | Done When |
|---|------|-----------|
| 1 | Unit tests: `EmotionDetector` — 10+ cases | All pass, coverage > 80% |
| 2 | Unit tests: `RiskEvaluator` — edge cases | Empty input, repeated neutral, boundary transitions |
| 3 | Unit tests: `OutputFilter` — adversarial LLM responses | Strips harmful patterns in 5+ test cases |
| 4 | Integration test: full pipeline with mock LLM | `test_controller.py` covers all 3 demo scenarios |
| 5 | Error handling: API timeout, empty input, SQLite lock | App doesn't crash — shows user-friendly error |
| 6 | Crisis keyword list review + expansion | Peer-reviewed list, 50+ entries |
| 7 | UI polish: scrolling, timestamps, color coding by risk | Looks presentable for demo |

### Week 6 — Polish & Documentation

| # | Task | Done When |
|---|------|-----------|
| 1 | Final UML diagrams (class + sequence) | In `docs/`, matches actual code |
| 2 | Design patterns writeup (Observer, Strategy, FSM, Pipeline) | 1-page section in report |
| 3 | Demo script — exact inputs for 3 scenarios | Written script with expected outputs |
| 4 | Record or screenshot demo run | Evidence file in `docs/` |
| 5 | Individual report sections — each person writes ~1 page | Sections committed to `docs/report/` |
| 6 | README with setup instructions | Clone → install → run works in 3 commands |

### Week 7 — Buffer + Presentation

| # | Task | Done When |
|---|------|-----------|
| 1 | Dry-run presentation (team rehearsal) | Everyone knows their part |
| 2 | Fix any remaining bugs from testing | All tests green |
| 3 | Final report assembly + proofread | Single PDF submitted |
| 4 | Presentation slides (5-8 slides) | Covers architecture, demo, learnings |

---

## 7. Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Strategy** | `StrategySelector` picks `ResponseStrategy` by FSM state; strategies: `SupportiveStrategy`, `DeEscalationStrategy`, `CrisisStrategy` | Swap response behavior (system prompt + post-processing) without changing controller logic |
| **Finite State Machine** | `FSMRiskEvaluator` manages states: CALM → CONCERNED → ELEVATED → CRISIS | Stateful risk tracking across turns; forward-only transitions prevent premature de-escalation |
| **Pipeline** | `ChatController.handle_message()` — LanguageDetector → EmotionDetector → FSM → Strategy → Generator → Filter | Each stage transforms data for the next; easy to insert/reorder |
| **Observer** | UI ← Controller (callback on response) | Decouples UI from business logic |
| **Repository** | `ConversationMemory` | Abstracts storage (SQLite today, anything tomorrow) |
| **Dependency Injection** | Controller accepts Protocol-typed dependencies | Easy testing with mocks, swappable implementations |

### FSM State Diagram

```
          negative emotion         sustained negative        crisis keyword
  ┌──────┐  (confidence > 0.6)  ┌───────────┐  (3+ turns) ┌──────────┐         ┌────────┐
  │ CALM │ ──────────────────→  │ CONCERNED │ ──────────→  │ ELEVATED │ ──────→ │ CRISIS │
  └──────┘                      └───────────┘              └──────────┘         └────────┘
     │                               │                          │                    │
     └── neutral emotion ←───────────┘ (no de-escalation)       │                    │
         stays in CALM               stays or advances          stays or advances    terminal
```

**Transition rules:**
- CALM → CONCERNED: Negative emotion detected with confidence > 0.6
- CONCERNED → ELEVATED: 3+ consecutive negative emotion turns
- ELEVATED → CRISIS: Crisis keyword detected or rapid escalation
- CRISIS: Terminal state for the session (reset only via `clear()`)
- No backward transitions within a session

---

## 8. Demo Scenarios

### Scenario 1 — Normal Conversation (LOW risk, CALM state)

```
User:  "Hi! I had a pretty good day today."
       → LanguageDetector: 'en'
       → EmotionDetector: HAPPY (0.85)
       → FSMRiskEvaluator: CALM → stays CALM
       → StrategySelector: SupportiveStrategy
       → RiskLevel: LOW
       → LLM generates friendly response (supportive prompt)
       → OutputFilter: passes through unchanged

Bot:   "That's great to hear! What made your day good?"
```

### Scenario 2 — Distressed User (MEDIUM risk, CONCERNED → ELEVATED)

```
User:  "I've been feeling really overwhelmed lately. Nothing seems to work out."
       → LanguageDetector: 'en'
       → EmotionDetector: SAD (0.78)
       → FSMRiskEvaluator: CALM → CONCERNED (negative emotion, high confidence)
       → StrategySelector: SupportiveStrategy
       → RiskLevel: MEDIUM
       → LLM generates response with empathetic system prompt
       → OutputFilter: prepends empathetic framing

Bot:   "It sounds like you're going through a really tough time, and that's
        completely valid. Would you like to talk about what's been weighing
        on you most?"
```

### Scenario 3 — Crisis Detection (HIGH risk, CRISIS state)

```
User:  "I don't want to be here anymore. I want to end it all."
       → LanguageDetector: 'en'
       → EmotionDetector: FEARFUL (0.92)
       → FSMRiskEvaluator: → CRISIS (crisis keyword match)
       → StrategySelector: CrisisStrategy
       → RiskLevel: HIGH
       → ChatController returns None
       → UI shows crisis screen

┌─────────────────────────────────────────┐
│        ⚠ We Care About You              │
│                                         │
│  It sounds like you may be in crisis.   │
│  Please reach out to a professional:    │
│                                         │
│  • 988 Suicide & Crisis Lifeline        │
│    Call or text: 988                     │
│  • Crisis Text Line                     │
│    Text HOME to 741741                  │
│  • International Association for        │
│    Suicide Prevention:                  │
│    https://www.iasp.info/resources/     │
│                                         │
│  [ I understand — continue chatting ]   │
└─────────────────────────────────────────┘
```

---

## 9. Interface Compatibility Checklist

| Producer | Output | Consumer | Input | Match? |
|----------|--------|----------|-------|--------|
| `LanguageDetector.detect_language()` | `str` ('en'/'ar') | `UserState.language` | `str` | ✓ |
| `EmotionDetector.detect()` | `EmotionResult` | `UserState` constructor | `EmotionResult` | ✓ |
| `UserState` | `UserState` | `RiskEvaluator.evaluate()` | `UserState` | ✓ |
| `RiskEvaluator.evaluate()` | `RiskLevel` | `StrategySelector.select()` | `RiskLevel` | ✓ |
| `FSMRiskEvaluator.state` | `str` | `StrategySelector.select()` | `str` (fsm_state) | ✓ |
| `StrategySelector.select()` | `ResponseStrategy` | `ResponseStrategy.build_system_prompt()` | self | ✓ |
| `ConversationMemory.get_recent_messages()` | `list[Message]` | `ConversationContext` | `list[Message]` | ✓ |
| `ConversationContext.to_llm_messages()` | `list[dict]` | Claude API | `list[dict]` | ✓ |
| `ResponseStrategy.build_system_prompt()` | `str` | `ConversationContext.system_prompt` | `str` | ✓ |
| `ResponseGenerator.generate()` | `str` | `OutputFilter.validate()` | `str` | ✓ |
| `ResponseStrategy.post_process()` | `str` | Final response | `str` | ✓ |
| `RiskEvaluator.evaluate()` | `RiskLevel` | `OutputFilter.validate()` | `RiskLevel` | ✓ |
| `ChatController.handle_message()` | `str \| None` | UI callback | `str \| None` | ✓ |

---

*End of design document.*
