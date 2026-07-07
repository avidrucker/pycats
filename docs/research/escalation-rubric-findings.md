# An effective escalation rubric for ticket decision evaluation (findings)

**Ticket:** #653 (standalone research; motivated by the #651 review). **Role:** RESEARCH.
**Scope:** synthesize the rubric — survey prior art, state the decision, derive dimensions,
recommend a scoring shape, work real examples. **Out:** writing the production rubric doc
(downstream WRITER ticket, named in §7), ratifying it, changing any tooling. As of 2026-07-06.

## TL;DR

- We already own **three** of the four pieces an escalation rubric needs, but they answer
  **different** questions and none of them answers "**is this decision worth formalizing, and
  how reversible is it?**":
  - **ICE** (`pmtools ice`, spec #199) scores *priority once you've decided to act*.
  - **RULES → "Changing values"** gates *evidence* (sourced vs game-feel) and gives the
    accept/decline endpoints (`vapid`/`wont-do`).
  - **yegor-personas authority ladder** decides *who ratifies*.
  - **Missing: reversibility / cost-if-wrong** — the one dimension #632's churn was actually
    about.
- **The central finding:** the expensive churn #632 measured (smash-charge = 5 tickets to
  settle one value) was a **one-way door treated as a two-way door** — a low-reversibility,
  high-blast-radius value booked `FOUND` on weak evidence (#581), then unwound. An effective
  escalation rubric's job is to catch exactly that mis-classification *before* the premature
  commit.
- **Recommended shape: a two-stage rubric.** Stage 1 is a new *escalate-or-not gate*
  (reversibility × evidence × blast radius → escalate / just-decide / decline). Stage 2 reuses
  **ICE** for *priority* of whatever Stage 1 escalates. The **personas ladder** assigns the
  authority + ticket type. This adds one genuinely new axis (reversibility) and *composes*
  the three tools we already have rather than replacing them.

## 1. The escalation decision, stated precisely

**Input:** a candidate — a value, a design decision, or a guardrail proposal (e.g. Child B
#651's) — together with its current evidence.

**Outputs** (the rubric must produce all three):
1. **Disposition** — `escalate` | `just-decide-and-note` | `decline`.
2. **If escalate: ticket type** — `decision:` ticket · ADR · RULE · DEV.
3. **If escalate: priority** — where it sits in the queue.

Today these are answered ad-hoc ("you decide" hand-offs), which is one source of the churn.

## 2. Prior-art survey — what we already have, and each piece's gap

| Tool | Question it answers | Contribution to escalation | Gap for escalation |
|---|---|---|---|
| **ICE** — `pmtools ice`, spec `docs/research-spec-199-ice-scoring.md` | "Which actionable ticket next?" | The **priority** axis: `I×C×E` (I 3/2/1/0.5/0.25, C 1.0/0.8/0.5, E 10/7/5/3/1), under **bug→blocker→ICE** | Says nothing about *whether to escalate* or *reversibility*; evidence enters only weakly as "Confidence". **Also: the ICE store is disabled in pycats** (`pmtools ice`→"ice store disabled"), so the score is a hand-computed advisory, not live. |
| **RULES → "Changing values"** | "May this value change, and on what basis?" | The **evidence gate** (must cite research/data **or** a designer decision) + the **endpoints** (`wont-do`/`vapid` for game-feel; precedent #489) + **ticket-type routing** (picking a surrogate is a `decision:` ticket, #491/#530) | Binary accept/decline; no urgency, no reversibility weighting, no "how big is the blast radius" |
| **yegor-personas authority ladder** | "Who decides / how do we converge?" | The **authority** axis: requirements → binary gate → objective measure → reporter → architect → no-compromise | Assumes the decision is already worth making; doesn't *score* escalation-worthiness |
| **ADR mechanism** — `docs/adr/` (template `0000`, e.g. ADR-0003) | "How do we durably record a made architectural decision?" | The **target artifact** an escalated architectural decision lands in | It's an output format, not a decision *criterion* |

**Read-across:** we have priority (ICE), evidence (RULES), authority (personas), and a
record format (ADR). We do **not** have a criterion for *reversibility / cost-if-wrong* —
and that is the axis #632's churn turned on.

## 3. The missing dimension, grounded in #632

`docs/research/decision-churn-findings.md` found the costly failure mode is
**"sourced-when-guessed"**: `SMASH_CHARGE_*` was registered `FOUND` at the base-game/Brawl
values (#581), tests were written against it, then #595→#599 had to reverse it to the PM
values and #627 cleaned up the exposed test — **5 tickets for one value.** By contrast, the
most value-*revised* constants (`DODGE_SPEED`, `GROUND_FRICTION`) cost **zero** tickets.

The difference is **reversibility × commitment**, not revision count:
- A value that is cheap to change later (a two-way door) can be set on a guess and corrected
  freely — near-zero churn cost.
- A value booked as *authoritative* (`FOUND`) with **tests and downstream tickets depending
  on it** is a one-way door: undoing it means reversing the registration **and** the
  dependents. Booking it on weak evidence is what converts a cheap fix into a 5-ticket arc.

So the rubric's decisive new axis is **reversibility / cost-if-wrong** (classic one-way-door
vs two-way-door decision framing), which no existing tool scores.

## 4. Recommended rubric shape — two stages

### Stage 1 — Escalate-or-not gate (the new part)

Score the candidate on three dimensions, each justified by a #632 case:

| Dimension | Question | Grounded in (#632) |
|---|---|---|
| **Reversibility / cost-if-wrong** | If we commit and it's wrong, how expensive to undo? (code + tests + dependent tickets) | smash-charge: **low** reversibility (registered `FOUND` + tests) → the 5-ticket unwind |
| **Evidence strength** | Sourced/derived, designer-chosen, or a game-feel guess? | #581 booked a **guess as `FOUND`** — the anti-pattern the gate must catch |
| **Blast radius** | How many values / tickets / tests does it gate? | smash-charge gated KO + damage + the charge-bar tests (#627) |

**Gate logic:**
- **High cost-if-wrong (low reversibility) OR high blast radius, AND evidence not yet strong**
  → **escalate**: open a sourcing-gated `decision:`/research ticket **before** committing;
  do **not** book `FOUND` until the evidence bar is met. *(This is the rung that would have
  stopped #581.)*
- **Low cost-if-wrong (two-way door)** → **just-decide-and-note**: pick it, record it
  `TUNED`/`GUESS`, move on. Escalating here is the ticket-tax #632 warns against — most of the
  52 never-revised constants live here.
- **Game-feel only, no faithful source, no designer decision** → **decline** (`vapid`/
  `wont-do`) per RULES → "Changing values" (precedent #489).

### Stage 2 — Priority (reuse ICE)

Whatever Stage 1 escalates is ranked by **ICE** (`I×C×E`, spec #199), under the existing
**bug → blocker → ICE** order. Reversibility/blast-radius from Stage 1 map naturally onto ICE
**Impact**; evidence strength informs **Confidence**. No new priority machinery — the rubric
*feeds* ICE, it doesn't replace it.

### Authority (reuse the personas ladder)

The **yegor-personas authority ladder** picks *who ratifies and the ticket type*:
requirements/spec settles it → no escalation; a surrogate pick with no faithful value →
**architect/designer** `decision:` ticket (#491 precedent); an architectural decision →
**ADR**; a process guardrail → **RULE**.

## 5. Worked examples (real past tickets)

| Candidate | Reversibility | Evidence | Blast radius | Rubric verdict | What actually happened |
|---|---|---|---|---|---|
| **`SMASH_CHARGE_*`** (#581→#599) | **Low** (booked `FOUND` + tests) | **Weak** at #581 (base-game/Brawl guess labelled sourced) | **High** (KO, damage, #627 test) | **Stage 1 = escalate + sourcing-gate before booking `FOUND`** → blocks the premature #581 registration, collapsing the 5-ticket arc | one-way door treated as reversible → 5-ticket unwind (the churn) |
| **`GRAVITY`** (#384, `FOUND`) | n/a | **Strong** (PM Mario 0.095 u/f² cited + derivation) | High | evidence bar met first time → **book `FOUND` directly, no escalation** | set once, never churned ✅ |
| **`DOUBLE_TAP_WINDOW`** bump (#489) | High (cheap) | **Fails** — game-feel, no faithful PM value (#407) | Low | **decline (`vapid`)** — escalation endpoint = decline | declined `wont-do`/`vapid` ✅ (matches RULES) |
| **surrogate pick** (e.g. #491) | Low (once chosen) | No faithful value exists | Medium | **escalate to a `decision:` ticket** → ratified choice becomes `TUNED` | exactly the RULES routing for "picking a surrogate is a decision" |

The rubric reproduces the *correct* dispositions the project reached by hand (GRAVITY,
#489, #491) **and** would have prevented the one it got wrong (#581 premature `FOUND`).

## 6. Why this is "effective" (design criteria met)

- **Adds exactly one new axis** (reversibility) and **composes** the three tools we already
  own — low adoption cost, no new dependency, no tooling change.
- **Every dimension traces to a measured #632 case** — not abstract.
- **Two-way-door fast path** keeps the common case (a `TUNED` guess) ceremony-free, so the
  rubric *reduces* the ticket tax rather than adding to it.
- **Endpoints already exist** (`FOUND`/`TUNED`, `vapid`/`wont-do`, `decision:`, ADR, RULE) —
  the rubric routes into the current machinery, it doesn't invent new states.

## 7. Follow-up WRITER ticket — scope (named, NOT filed here)

> **docs(rules): draft the escalation rubric — a working decision-evaluation aid** ·
> `documentation`/`area:tracker` · WRITER
>
> Turn this findings doc into a **one-page working rubric** agents/humans apply at
> filing/decision time: the Stage-1 escalate-or-not decision tree (reversibility × evidence ×
> blast radius → escalate/just-decide/decline), the Stage-2 ICE hand-off, the authority-ladder
> routing to ticket type, and a filled worked-example table. Land it as a `docs/` rubric page
> and/or a RULES.md "Escalation rubric" section. Out of scope: ratifying it as a RULE
> (a `decision:` step after the draft), and enabling the ICE store.

## 8. Method / sources (reproducible)

- Prior art read directly: `docs/research-spec-199-ice-scoring.md` (ICE scales/formula/order,
  `pmtools ice`), `RULES.md` → "Changing values" (basis gate, `vapid`/`wont-do`, #489/#491/#530),
  `docs/adr/` (ADR mechanism), the **yegor-personas** authority ladder.
- Churn evidence: `docs/research/decision-churn-findings.md` (#632) — smash-charge 5-ticket
  arc, the value-revision vs effort-cost split, GRAVITY set-once.
- `pmtools ice score` confirmed the ICE store is **disabled** in pycats (advisory only).
- Reversibility framing = the standard one-way-door / two-way-door decision distinction
  (general decision theory), applied to the #632 data — labelled as the organizing lens, not a
  repo/canon claim.

## 9. Refs

Motivated by the **#651** review. Churn data **#632**. Prior art: ICE spec **#199**
(`pmtools ice`), RULES.md → "Changing values" (#489/#491/#530), `docs/adr/` (ADR-0003),
yegor-personas ladder. Umbrella context **#631**. Feeds a downstream WRITER ticket (§7).
