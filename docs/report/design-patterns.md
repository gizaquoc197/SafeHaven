# SafeHaven — Design Patterns

SafeHaven applies six classical software design patterns. Each was chosen both for
engineering soundness and because it maps directly onto a clinical safety requirement.

---

## 1. Strategy

**Where:** `safehaven/strategy/` — `ConcreteStrategySelector`, `SupportiveStrategy`,
`DeEscalationStrategy`, `CrisisStrategy`

`ConcreteStrategySelector.select(risk, fsm_state)` returns a `ResponseStrategy`
object at runtime based on the current FSM state. The controller never names a
concrete strategy class — it holds only the `ResponseStrategy` protocol interface.

Each strategy encapsulates a distinct clinical framework:

| FSM State | Strategy | Clinical Basis |
|-----------|----------|----------------|
| CALM / CONCERNED | `SupportiveStrategy` | Motivational Interviewing — OARS (Open questions, Affirmations, Reflective listening, Summarizing) |
| ELEVATED | `DeEscalationStrategy` | DBT Distress Tolerance — TIPP and 5-4-3-2-1 grounding |
| CRISIS | `CrisisStrategy` | QPR (Question, Persuade, Refer) |

**Engineering benefit:** adding a fourth strategy (e.g., for a new FSM state) requires
only a new class and one `elif` in the selector — the controller is untouched.

---

## 2. Finite State Machine (FSM)

**Where:** `safehaven/safety/fsm_risk_evaluator.py` — `FSMRiskEvaluator`

The FSM tracks four escalation states: `CALM → CONCERNED → ELEVATED → CRISIS`.
A `_RANK` dict (`{"calm": 0, "concerned": 1, "elevated": 2, "crisis": 3}`) is used
by `_transition_to()`, which asserts `_RANK[new] >= _RANK[current]`, enforcing a
**forward-only (monotonic) ratchet constraint** — the risk level can never decrease
within a session.

Transition rules:
- **CALM → CONCERNED:** any negative emotion (SAD/ANXIOUS/ANGRY) with confidence > 0.6
- **CONCERNED → ELEVATED:** 3 consecutive negative-emotion turns
- **any → CRISIS:** FEARFUL emotion with confidence ≥ 0.9 (skip-state allowed)
- **CRISIS:** terminal — only `clear()` (new session) can reset it

**Clinical basis:** mirrors real escalation-to-crisis triage protocols where a
clinician never downgrade risk mid-session without a formal reassessment.

---

## 3. Pipeline

**Where:** `safehaven/controller/chat_controller.py` — `ChatController.handle_message()`

The controller implements a 12-step linear pipeline where each step has a single
responsibility and passes its output to the next:

```
1.  LanguageDetector.detect_language()
2.  EmotionDetector.detect()
3.  ConversationMemory.get_recent_messages()  ← load history for FSM escalation_history
4.  Build UserState
5.  FSMRiskEvaluator.evaluate()
6.  ConversationMemory.store_message()        ← user message stored WITH evaluated risk_level
7.  ConversationMemory.get_recent_messages()  ← reload so LLM sees current user turn
8.  [HIGH risk] → return None                ← early exit, LLM never called
9.  StrategySelector.select() + build_system_prompt()
10. ResponseGenerator.generate()
11. OutputFilter.validate() + ResponseStrategy.post_process()
12. PersonaDecorator.wrap_response()          ← passthrough for default persona
    + store_message() + return
```

Step 8 is a critical safety gate: when risk is HIGH, the pipeline short-circuits and
the UI displays the crisis screen instead of an LLM response. This ensures the LLM
is **never invoked** for a user in crisis.

Step 6 is equally important for correctness: storing the user message *after*
evaluation ensures that the `risk_level` field reflects the actual evaluated risk
(not the `RiskLevel.LOW` default), which is what the Insights dashboard reads to
render the escalation timeline.

---

## 4. Observer

**Where:** `safehaven/ui/insights_screen.py` — `DashboardViewModel`, `InsightsScreen`

`DashboardViewModel` extends Kivy's `EventDispatcher` and exposes four observable
properties (`message_count`, `emotion_counts`, `current_risk`, `risk_history`).
`InsightsScreen` binds callback methods to each property via `bind()`. When
`DashboardViewModel.refresh()` updates a property, Kivy automatically fires the
bound callback, which redraws the relevant chart or counter — with no polling loop.

`ChatScreen` also registers an observer: after each `handle_message()` call it
invokes `_update_fsm_bar()`, which repaints the 6px state indicator bar and pulses
an animation to signal the state change to the user.

---

## 5. Repository

**Where:** `safehaven/interfaces.py` (`ConversationMemory` protocol),
`safehaven/memory/sqlite_memory.py`, `safehaven/memory/in_memory.py`

`ConversationMemory` is a structural protocol (not a base class) with three methods:
`store_message()`, `get_recent_messages()`, `clear()`. Two concrete backends exist:

- **`SQLiteMemory`** — persists to `safehaven.db`; used in production
- **`InMemoryConversationMemory`** — stores in a list; used in all tests

The controller holds only a `ConversationMemory`-typed reference. Swapping the
backend requires zero changes to the controller or any strategy.

---

## 6. Decorator

**Where:** `safehaven/persona_decorator.py` — `PersonaDecorator`

`PersonaDecorator` wraps the `ResponseGenerator` protocol and adds a second LLM
call that rewrites the clinical response in a character's voice. The controller holds
a `PersonaDecorator` instance alongside the base generator and calls
`wrap_response(raw_response, emotion, risk_state)` as the final step before storing
and returning the response.

Four concrete personas are registered in `safehaven/personas/`:

| Persona | Character | Design constraint |
|---------|-----------|-------------------|
| `default` | Passthrough — no decoration | Empty `system_prompt` triggers bypass |
| `iroh` | Uncle Iroh (Avatar) | No asterisk actions; ≤ 120 words |
| `baymax` | Baymax (Big Hero 6) | Clinical tone, minimal contractions; ≤ 100 words |
| `naruto` | Naruto Uzumaki | Story-first empathy; ≤ 120 words |

The Decorator pattern is the correct choice here because it adds persona-specific
behaviour *around* the existing response without modifying the generator or the
controller — both remain unchanged regardless of which persona is active.

**Safety behaviour:**
- If `risk_state == "crisis"` the decorator breaks character and prepends a
  plain-language crisis acknowledgment before the clinical response.
- If the 2nd LLM call throws for any reason, the original clinical response is
  returned unchanged (fail-open).

---

## 7. Dependency Injection

**Where:** `safehaven/controller/chat_controller.py` — `ChatController.__init__()`

All seven service dependencies are injected via constructor parameters typed as
protocols (`EmotionDetector`, `RiskEvaluator`, `ConversationMemory`,
`ResponseGenerator`, `OutputFilter`, `LanguageDetector`, `StrategySelector`).
The active persona is set after construction via the `active_persona` property
(which builds or clears the `PersonaDecorator` automatically). The controller
imports no concrete implementation — only `safehaven.interfaces` and
`safehaven.models`.

This enables the test suite (150+ tests) to inject lightweight stubs (`FakeDetector`,
`FakeGenerator`, etc.) without patching, mocking libraries, or modifying production
code. It also made it straightforward to swap `KeywordRiskEvaluator` for
`FSMRiskEvaluator` as the active evaluator without touching any other module.
