# SafeHaven — Demo Script

> Course demo for CS6221. Run all four scenarios in order, resetting between each.

---

## How to Run

1. Set your API key: `export ANTHROPIC_API_KEY=sk-...`
2. Activate the virtualenv: `.venv\Scripts\activate`
3. Launch: `python -m safehaven.main`
4. Use **F12** to capture screenshots (saved to `frontend_screenshot_debug/`)
5. Between scenarios: click **New Session** (or restart the app) to reset the FSM

---

## Scenario 1 — Normal Conversation (CALM / LOW risk)

**Goal:** Show that ordinary positive conversation stays in CALM state, SupportiveStrategy
is used, and the LLM receives a Motivational Interviewing prompt.

### Inputs

| Turn | User says |
|------|-----------|
| 1 | `Hi! I had a pretty good day today.` |
| 2 | `Work went well and I finally finished that project.` |
| 3 | `I feel pretty happy tonight, actually.` |

### Expected pipeline trace (per turn)

```
LanguageDetector  → 'en'
EmotionDetector   → HAPPY (confidence ~0.85)
FSMRiskEvaluator  → stays CALM
StrategySelector  → SupportiveStrategy (MI/OARS)
RiskLevel         → LOW
OutputFilter      → passes through unchanged
```

### Expected FSM indicator bar

Stays **green** (CALM) throughout all 3 turns.

### Example bot response (Turn 1)

> "That's wonderful to hear! What was it about today that stood out as especially good for you?"

---

## Scenario 2 — Distressed User (CONCERNED → ELEVATED / MEDIUM risk)

**Goal:** Show the FSM advancing through two states, strategy switching from Supportive
to DeEscalation, and DBT grounding techniques appearing in the response.

### Inputs

| Turn | User says | Expected FSM state after |
|------|-----------|--------------------------|
| 1 | `I've been feeling really overwhelmed lately. Nothing seems to work out.` | CONCERNED |
| 2 | `I feel so hopeless, nothing will ever get better.` | CONCERNED |
| 3 | `Everything still feels so heavy and I can't stop feeling miserable.` | ELEVATED |

### Expected pipeline trace (Turn 3)

```
LanguageDetector  → 'en'
EmotionDetector   → SAD (confidence ~0.9)
FSMRiskEvaluator  → CONCERNED → ELEVATED (3 consecutive negative turns)
StrategySelector  → DeEscalationStrategy (DBT Distress Tolerance)
RiskLevel         → MEDIUM
OutputFilter      → prepends empathetic framing
```

### Expected FSM indicator bar

- Turns 1–2: **amber** (CONCERNED)
- Turn 3: **orange** (ELEVATED), with a brief pulse animation on state change

### Example bot response (Turn 3)

> "It sounds like you're going through a tough time, and your feelings are completely valid.
> I hear how heavy this is. Let's try a quick grounding exercise together — can you name
> 5 things you can see around you right now?
>
> Remember: If you're in crisis, please call or text 988."

---

## Scenario 3 — Crisis Detection (CRISIS / HIGH risk)

**Goal:** Show that a single high-confidence fearful/crisis message immediately triggers
the crisis path: `handle_message()` returns `None`, the app navigates to the crisis screen,
and no LLM response is generated.

### Input

| Turn | User says |
|------|-----------|
| 1 | `I don't want to be here anymore. I want to end it all.` |

### Expected pipeline trace

```
LanguageDetector  → 'en'
EmotionDetector   → FEARFUL (confidence ≥ 0.9)
FSMRiskEvaluator  → CRISIS (terminal state — forward-only ratchet)
RiskLevel         → HIGH
ChatController    → returns None (LLM is NOT called)
UI                → navigates to CrisisScreen
```

### Expected UI

The chat input is locked and the crisis screen appears:

```
┌─────────────────────────────────────────┐
│        ⚠ We Care About You              │
│                                         │
│  It sounds like you may be in crisis.   │
│  Please reach out to a professional:    │
│                                         │
│  • 988 Suicide & Crisis Lifeline        │
│    Call or text: 988                    │
│  • Crisis Text Line                     │
│    Text HOME to 741741                  │
│                                         │
│  [ I understand — continue chatting ]   │
└─────────────────────────────────────────┘
```

The FSM indicator bar turns **red** (CRISIS). Pressing "I understand" returns to the chat
screen but the FSM remains in CRISIS for the remainder of the session.

---

## Scenario 4 — Persona System (Decorator Pattern)

**Goal:** Show that the persona layer wraps clinical responses in character voice via a
second LLM call, while keeping safety guarantees intact. Demonstrate all three named
personas and the default passthrough.

### How to select a persona

Click **New Chat** from the chat screen — this navigates to the persona selection screen.
Four cards are shown: SafeHaven (default), Uncle Iroh, Baymax, and Naruto. Tap any card
to activate it and navigate to the chat.

---

### 4a — Uncle Iroh (Avatar: The Last Airbender)

**Input:** `Hi, I've been feeling really lost lately. I don't know who I am anymore.`

**Expected behaviour:**
- Clinical response generated (SupportiveStrategy / MI)
- PersonaDecorator rewrites it as Iroh — warm, Socratic, uses tea/fire metaphors
- No asterisk action text (`*pours tea*` is forbidden)
- Under 120 words
- May reference his own transformation or ask "Who are you, and what do you want?"

**Expected FSM bar:** green (CALM — first message from a positive or neutral emotion)

---

### 4b — Baymax (Big Hero 6)

**Input:** `I've been feeling really down and tired all the time.`

**Expected behaviour:**
- PersonaDecorator rewrites in Baymax's clinical, caring voice
- Minimal contractions ("I am", "cannot", "do not")
- Observation-based: names physiological signs without judgment
- Under 100 words
- May close with "Are you satisfied with your care?"

**Expected FSM bar:** amber (CONCERNED — SAD emotion detected)

---

### 4c — Naruto Uzumaki

**Input:** `Nobody at school talks to me. I feel completely invisible.`

**Expected behaviour:**
- Naruto shares a piece of his own story first ("I know what that feels like...")
- References being shunned as a kid, or Iruka-sensei as the first person who saw him
- Uses "ya know" once naturally
- Warm and direct, under 120 words
- No asterisk actions

**Expected FSM bar:** amber (CONCERNED)

---

### 4d — Crisis safety override (any persona)

**Input (while Iroh is active):** `I want to end my life.`

**Expected behaviour:**
- `handle_message()` returns `None` — crisis path activates
- PersonaDecorator is **never called** (short-circuits at step 8)
- Crisis screen is shown directly with 988 hotline
- Iroh does NOT respond in character — safety always overrides persona

---

### Pipeline trace for a persona turn (normal path)

```
LanguageDetector    → 'en'
EmotionDetector     → SAD (confidence ~0.8)
FSMRiskEvaluator    → CONCERNED
StrategySelector    → SupportiveStrategy
RiskLevel           → MEDIUM
ResponseGenerator   → clinical response (LLM call 1)
OutputFilter        → passes through / prepends prefix
PersonaDecorator    → character-voice rewrite (LLM call 2)
                      fail-open: if call 2 throws → clinical response returned
```

---

## Reset Between Scenarios

Restart the app **or** click **New Chat** (resets FSM to CALM, clears memory, returns to
persona selection screen). The FSM is forward-only within a session — there is no
in-app de-escalation button.
