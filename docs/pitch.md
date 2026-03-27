# SafeHaven — Verified Project Pitch

> Verified against Claude Research analysis of prior art (March 2026).
> Use this framing in slides, demo, and report. See citations below.

---

## The Pitch (use this verbatim)

"SafeHaven demonstrates how classical Gang of Four design patterns — Strategy, Pipeline,
FSM, Observer, Repository, and Dependency Injection — can be systematically composed to
create a formally architected safety-aware mental health chatbot. Commercial systems like
Wysa implement crisis detection, and recent work (MindfulDiary, CHI 2024) applies FSMs to
therapeutic dialogue flow — but no prior work formally applies GoF patterns to this domain,
or uses FSM states to model risk levels with monotonic escalation constraints. SafeHaven's
contribution is architectural and pedagogical: proving that well-known design patterns,
deliberately composed, address safety gaps identified in peer-reviewed evaluations of
existing chatbots (Pichowicz et al., Scientific Reports 2025 found zero adequate crisis
responses among 29 chatbots tested)."

---

## What Is Genuinely Novel (confirmed, no prior art)

1. **FSM with risk-level states** — existing FSM chatbots (MindfulDiary, ChaCha) use states
   for therapy *phases* (initiation → exploration → conclusion), never for *risk levels*.
   SafeHaven's CALM → CONCERNED → ELEVATED → CRISIS is architecturally distinct.

2. **Forward-only "ratchet" constraint** — risk can only escalate within a session, never
   de-escalate. No published system documents this constraint.

3. **GoF patterns formally applied to chatbot safety** — no published academic paper has
   ever explicitly applied Strategy, Pipeline, Observer, Repository, or DI to chatbot
   architecture. Commercial tools (NeMo Guardrails, LangChain) do it implicitly.
   SafeHaven does it named, documented, and deliberate.

4. **Strategy Pattern for risk-adaptive response selection** — selecting response behavior
   (empathetic listening vs. grounding vs. crisis redirection) based on FSM risk state has
   no formal prior art despite implicit use in commercial systems.

---

## What NOT to Claim

- "Existing mental health chatbots lack safety-aware architecture" — OVERSTATED.
  Wysa detects 82% of crises via AI (Wysa global study, 2024, 19,950 users).
  Woebot uses scripted (non-generative) conversations as a deliberate safety choice.
  Replika switches to a curated retrieval model when self-harm is detected.

- "First to use FSMs in mental health chatbots" — FALSE.
  MindfulDiary (CHI 2024) and ChaCha (CHI 2024) both use FSMs for dialogue management.

- "Novel crisis detection" — the detection capability is not the novelty.
  The *architectural pattern* for handling it is.

---

## Key Citations for Slides and Report

| Claim | Source |
|-------|--------|
| Existing chatbots still inadequate despite safety features | Pichowicz, Kotas & Piotrowski, "Performance of mental health chatbot agents in detecting and managing suicidal ideation," *Scientific Reports* 15:31652 (2025) — 0 of 29 chatbots met "adequate" crisis response criteria |
| Prior FSM work uses therapy phases, not risk levels | Kim et al., "MindfulDiary: Harnessing Large Language Model to Support Psychiatric Patients' Journaling," CHI 2024 (dl.acm.org/doi/10.1145/3613904.3642937) |
| No GoF patterns in chatbot/AI literature | Suresh, "Beyond the Gang of Four: Practical Design Patterns for Modern AI Systems," InfoQ (May 2025) — extends GoF to AI with *new* patterns, confirming the GoF gap |
| Cumulative risk escalation is an open problem SafeHaven addresses | "TherapyProbe: Generating Design Knowledge for Relational Safety in Mental Health Chatbots," arXiv 2602.22775 (February 2026) — explicitly calls for cumulative risk scoring and escalation-to-crisis protocols |
| Commercial chatbots have safety features but remain clinically inadequate | Martinengo et al., "Suicide prevention and depression apps' suicide risk assessment," *BMC Medicine* 17:231 (2019) — only 5 of 69 apps offered all six recommended suicide prevention strategies |

---

## Strong Framing Points for Q&A

- **"Why not just use Wysa?"** — Wysa's safety logic is a black box. You cannot inspect,
  test, extend, or swap it. SafeHaven's pipeline is fully transparent, unit-tested at every
  stage, and any component can be replaced without touching the others (Dependency Injection).

- **"How is this different from MindfulDiary?"** — MindfulDiary's FSM models conversation
  *phases*. When a user expresses suicidal ideation, it triggers a binary block. SafeHaven's
  FSM models *risk level* — the system tracks escalation across turns and adapts its entire
  response strategy, not just blocks or allows.

- **"Why GoF patterns specifically?"** — Because this is a software engineering course.
  The contribution is demonstrating that patterns taught in this class solve a real safety
  problem in a domain where existing tools are ad hoc and systematically evaluated as
  insufficient.

- **"TherapyProbe (Feb 2026) calls for exactly what we built"** — A paper published one
  month before our submission explicitly identifies "Crisis Escalation Failure" as a safety
  anti-pattern and recommends cumulative risk scoring with escalation-to-crisis protocols.
  SafeHaven is a direct implementation of that recommendation.
