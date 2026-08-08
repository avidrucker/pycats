# PM dash/run input-precedence — the out-of-dash/run transition table (findings + option space)

**Ticket:** #937 (RESEARCH, area:combat). **Author:** ELDERBERRY, 2026-07-31.
**Status:** **findings only.** This maps *what Project M produces* when a player feeds an input
from the **initial-dash** or **run** state, grounded in primary sources. It does **not** decide the
pycats seam or precedence — that is #930 (architect, Fork 2), which this doc feeds. Per
[[research-never-produces-spec]] the option space in Part C is surfaced, not ratified.

> **Parity, not taste.** "Which move comes out of run" is a fact about the PM/Melee engine's
> action-state precedence, not a design choice. Every claim is tagged with its confidence and
> source; PM-specific gaps are labelled, not guessed ([[pm-parity-cite-primary-not-inference]]).

---

## Sourcing & confidence key

| Tier | What it is | How I treat it |
|---|---|---|
| **primary-reimpl** | **meleelight** (`~/Documents/Study/JavaScript/meleelight`, local clone #616) — a faithful **Melee** engine reimplementation in JS. Its `characters/shared/moves/{DASH,RUN,RUNBRAKE,RUNTURN}.js` `interrupt()` functions **are** the per-frame action-state transition logic. | Strongest reachable source for the *transition/precedence* logic (per-move datamines structurally can't expose it — [[rukaidata-engine-hardcoded-limit]], [[meleelight-engine-logic-source]]). It is **Melee**, so **Melee→PM is an `(inference)`** (PM restores Melee ground movement; no PM override known). |
| **secondary** | SmashWiki (Melee/PM pages). | Citable secondary per RULES; used to corroborate the named mechanics and supply verbatim definitions. |
| **repo-grounded** | The already-sourced `docs/pm-reference/*` set (epic #147) and prior research (#373/#407/#476). | Reused, not re-derived. |

**The precedence rule.** In meleelight each state's `interrupt(p,input)` is evaluated **top-to-bottom
every frame; the first matching branch wins**. So *branch order literally is the input-precedence
order*. The tables below transcribe that order verbatim from the source.

---

# Part A — The transition tables (primary-reimpl: meleelight, Melee)

## A1. Out of **initial dash** (`DASH.js::interrupt`, priority high→low)

| # | Input condition (source token) | Produces | Notes |
|---|---|---|---|
| 1 | Shield pressed (`l`/`r` digital **or** `lA`/`rA` analog trigger) | **Shield** (`GUARDON`) | Horizontal velocity ×0.25 on entry. No skid needed. |
| 2a | Fresh **A** `&&` `timer < 4` `&&` stick hard-forward (`lsX·face ≥ 0.8`) | **Forward smash** (`FORWARDSMASH`) | The **only direction/timing-sensitive A case**: in the first ~4 dash frames with a hard-forward stick, A reads as a smash, *not* a dash attack. Velocity ×0.25. |
| 2b | Fresh **A** `+` grab modifier (shoulder held) | **Dash grab** (`GRAB`) | See A3 (grab = A+shoulder / Z). |
| 2c | Fresh **A** (otherwise) | **Dash attack** (`ATTACKDASH`) | The common case — A during dash → dash attack, regardless of held direction. |
| 3 | Jump (`x`/`y` fresh, or tap-up if tap-jump ON) | **Jumpsquat** (`KNEEBEND`) | Dash momentum carries into the jump (dash-jump); gateway to JC grab / JC up-smash (A4). |
| 4 | Fresh **B** `&&` `|lsX| > 0.6` | **Side special** (`SIDESPECIALGROUND`) | Faces the stick. |
| 5 | Taunt (`du`, d-pad up) | Appeal | — |
| 6 | `timer > 4` `&&` hard reverse tap (`checkForSmashTurn`) | **Smash-turn / dashback** (`SMASHTURN`) | The pivot/dash-dance reversal. |
| 7 | `timer > dashFrameMax` `&&` re-tap forward after neutral | **re-DASH** (foxtrot) | — |
| 8 | `timer > dashFrameMin` `&&` hold forward (`lsX·face > 0.62`) | **RUN** | The **initial-dash → run** transition. |
| 9 | `timer > framesData.DASH` (window elapsed, stick released) | **Idle** (`WAIT`) | Dash expires to stand. |

## A2. Out of **run** (`RUN.js::interrupt`, priority high→low)

| # | Input condition | Produces | Notes |
|---|---|---|---|
| 1a | Fresh **A** `+` grab modifier (shoulder held) | **Dash grab** (`GRAB`) | — |
| 1b | Fresh **A** (otherwise) | **Dash attack** (`ATTACKDASH`) | Same move as out of dash; **no separate "run attack".** No held-direction sensitivity here (unlike A1 #2a). |
| 2 | Jump | **Jumpsquat** (`KNEEBEND`) | Run momentum carries. |
| 3 | Fresh **B** `&&` `|lsX| > 0.6` | **Side special** | — |
| 4 | Fresh **B** `&&` `lsY < -0.58` (stick down) | **Down special** (`DOWNSPECIALGROUND`) | — |
| 5 | Shield (`l`/`r` or analog trigger) | **Shield** (`GUARDON`) | No velocity cut here (unlike dash); no skid needed. |
| 6 | Taunt (`du`) | Appeal | — |
| 7 | Stick to near-neutral (`|lsX| < 0.62`) | **Run brake** (`RUNBRAKE`) | The stick-release / skid path → see A5. |
| 8 | Reverse stick (`lsX·face < -0.3`) | **Run turn** (`RUNTURN`) | Turnaround out of run. |

**Two silent-omission facts** (branches that do **not** exist out of run — so the input falls through):

- **No neutral-B out of run.** Only side-B (#3) and down-B (#4) are wired. A **B with a neutral
  stick** while running matches no B branch → falls to #7 (**run-brake**); the special does not come
  out until braked. *(meleelight modelling detail — flag to firm against PM; see Gaps.)*
- **No forward-smash / up-smash / tilt out of run.** There is **no smash or tilt branch** in
  `RUN.interrupt` at all. Forward-smash is reachable only from the *early dash* (A1 #2a); otherwise
  smashes/tilts require leaving run first (brake → stand, A5) or a **jump-cancel** (A4).

## A3. Grab out of dash/run = **dash grab** (`CatchDash`)

In meleelight, grab fires as **fresh A while a shoulder trigger is held** (the shield+A / Z grab).
From dash or run this routes to the character's `GRAB` module = the **dash grab**. Corroborated:
SmashWiki [*Dash grab*](https://www.ssbwiki.com/Dash_grab) — *"Dash grab (known as **CatchDash**
internally), introduced in Super Smash Bros. Melee, which is used by grabbing while dashing… Fighters
move forward during the grab to give it longer range, but generally they have slightly more startup
and are heavier on ending lag."* A **pivot grab** is a separate turnaround grab; a **boost grab** is a
Brawl item-buffer tech (not Melee/PM-core).

## A4. Jump-cancel is the gateway to grab / up-smash out of run/dash

Because jump (A1 #3 / A2 #2) enters **jumpsquat** carrying momentum, the classic **jump-cancel**
follows: interrupt the jumpsquat with a grab or up-smash to get a **standing grab / up-smash with run
momentum**. SmashWiki [*Jump-canceled grab*](https://www.ssbwiki.com/Jump-canceled_grab): *"a
technique in Super Smash Bros. Melee where a character interrupts a dash or run with a jump, which
itself is then jump-canceled with a grab during the jumpsquat animation"* — *"using their standing
grab while maintaining some momentum from their dash."* This is **how you up-smash out of run** in
Melee/PM (there is no direct up-smash branch in run — A2).

## A5. Stick-release, crouch, and the brake/turn chain

- **Stick released / neutral:** run → **run-brake** (A2 #7) → **idle** when the brake timer elapses
  (`RUNBRAKE.interrupt`: `timer > framesData.RUNBRAKE → WAIT`). From an *initial dash*, releasing the
  stick just lets the dash expire to idle (A1 #9).
- **Crouch is not reachable directly from run.** `RUNBRAKE.interrupt` gates crouch behind the brake:
  `timer > 1 && checkForSquat (lsY < -0.69) → SQUAT`. So run → brake → (hold hard-down) → crouch.
- **Run-turn** (`RUNTURN`) flips facing at `runTurnBreakPoint`, then exits to **run** (if still
  holding forward) or **idle**. Jump interrupts it at any point.

## A6. Predicate definitions (so the thresholds above are unambiguous)

From `physics/actionStateShortcuts.js`:
- `checkForJump` = fresh `x`/`y` press, **or** (tap-jump-OFF `&&` stick-up `lsY > 0.66` from neutral).
- `checkForSquat` = `lsY < -0.69` (hard down).
- `checkForSmashTurn` = `lsX·face < -0.79` this frame `&&` `> -0.3` two frames ago (a hard reverse *tap*).
- `dashFrameMin`/`dashFrameMax` = the per-character initial-dash window (the dash-dance/foxtrot span;
  general range **7–18 f** per [pm-walk-run-dash §Q2](./2026-07-01-pm-walk-run-dash-mechanics.md)).

---

# Part B — What this answers for #930 (the parity facts)

Restating #937's eight questions with the grounded answer (dash = initial dash; run = sustained):

1. **A (plain attack)** → **dash attack**, from **both** dash and run (confirms #930 Fork 1
   "both"; SmashWiki [*Dash attack*](https://www.ssbwiki.com/Dash_attack): *"an attack performed by
   pressing the attack button while dashing"*, and *"one of the only attacks a character can use to
   interrupt their initial dash"*). **Held direction does not change it** — except the **early-dash
   forward-smash window** (A1 #2a). Tilts are **unreachable** from dash/run — so pycats resolving a
   mid-dash A to an **f-tilt** is a genuine parity bug (matches #866 §A1d).
2. **Smash while running** → **not directly reachable** except forward-smash in the first ~4 dash
   frames (A1 #2a). Otherwise you brake to stand first, **jump-cancel** (JC up-smash, A4), or use the
   **C-stick** (a dedicated smash stick — **not modelled in meleelight's dash/run interrupt**; ground
   separately, see Gaps). *(Brawl's DACUS / "boost smash" is not a Melee/PM-core mechanic.)*
3. **B while running** → **side-B** (stick sideways) or **down-B** (stick down) come out directly;
   **neutral-B falls through to run-brake** in meleelight (flag to firm — Gaps). No dash-cancel is
   required for the wired specials.
4. **Grab while running** → **dash grab** (`CatchDash`): forward-moving, longer range, more
   startup/endlag (A3). **JC grab** (A4) is the momentum-preserving standing-grab alternative.
5. **Jump while running** → **jumpsquat carrying run momentum** (dash-jump); corroborated by
   `docs/pm-reference/movement-and-tech.md` (*"a running jump keeps run speed"*).
6. **Shield while running** → **shield directly** (`GuardOn`), no skid required (dash cuts velocity
   ×0.25 on the way in; run does not). Spot-dodge / roll / wavedash then come *from* shield + stick.
7. **Down / crouch while running** → **not direct**; run-brake first, then hard-down → crouch (A5).
8. **Nothing (stick release)** → run → **run-brake → idle**; dash → **idle** when the window elapses
   (A5 / A1 #9).

Plus the structural facts #937 asked for:
- **initial-dash → run** happens when forward is held past `dashFrameMin` (A1 #8); **dash-dance**
  (reverse tap = SmashTurn) and **foxtrot** (re-tap = re-DASH) live inside the initial-dash window.
- **Dash attack is reachable from the initial dash *before* run begins** (A1 #2c) — so the mechanic
  does not depend on the `run` state existing (bears on #930 Fork 1 / #808).
- There is **no meaningful input buffer** in Melee/PM (`docs/pm-reference/input-model.md` §5) — these
  transitions are read live, frame-by-frame; the "first matching branch" precedence is per-frame.

---

# Part C — Option space for #930 Fork 2 (surfaced, not decided)

The pycats seam is `combat/move_select.py::resolve_move_key(moves, direction, on_ground, is_special,
is_smash)`, called from `entities/fighter_input.py::handle_actions`. Today it is direction-keyed and
**dash-blind**. The facts above raise these forks for the architect:

- **C1 — Precedence order to adopt.** The Melee order is *shield → (early-dash fsmash) → grab → dash
  attack → jump → specials → turn → brake*. Which subset/order does the pycats seam encode, and does
  the **dedicated smash input** (`is_smash`) keep priority over A the frame it is pressed (so a smash
  out of a dash stays an f-smash, not a dash attack)? *(This is #930 B1's precedence sub-question,
  now with the Melee ordering as the parity anchor.)*
- **C2 — The early-dash forward-smash window (A1 #2a).** Melee disambiguates dash-attack-vs-fsmash by
  **analog stick speed** in the first ~4 frames — which a **keyboard cannot express** (a key is full
  deflection instantly; [[grounded-speeds-projectplus-not-pm36]], input-model §6). Options: (a) drop
  the window and route all dash-A to dash attack, letting the explicit **smash button** carry
  f-smash; (b) emulate a timing window. Keyboard-port decision, hands to #930/#554.
- **C3 — Smash / up-smash / neutral-B / up-B out of run.** Melee reaches these only via **jump-cancel**
  or the **C-stick**, neither of which pycats models (no JC, C-stick = the dedicated smash button).
  Options: accept a reduced model (these simply aren't available out of run), or add JC. *Scope call,
  not V1-blocking for the dash attack itself.*
- **C4 — Direction sensitivity of the dash-attack seam.** Parity says **A out of run = dash attack
  irrespective of held direction** (A2 #1b). So the pycats seam should **ignore the direction token
  when in dash/run** for the plain-A case (aligns with #930 B1 "state gate overrides direction").
- **C5 — Grab/shield/jump out of dash/run.** These are downstream of the grab (Phase 4) and run
  (#808) systems; the precedence *slots* are recorded here so those systems inherit the right order,
  but they are **out of scope for the V1 dash-attack seam**.

---

## Gaps / to-firm (labelled, not guessed)

- **Melee→PM inference.** The whole precedence table is meleelight = **Melee**; PM restores Melee
  ground movement, so this is a strong `(inference)` but **not** a PM primary. Firm the *precedence
  order* against a PM codeset (Project-M-CC / OpenSA action scripts) or a PMDT changelog if a
  FOUND-tier citation is wanted before code.
- **C-stick / dedicated-smash out of run.** meleelight's dash/run `interrupt` does **not** reference
  the C-stick (`cX`/`cY`) — so its only smash-out-of-run path is the early-dash forward-smash. The
  real C-stick-smash-out-of-run behavior must be grounded from SmashWiki [*C-Stick*] / a PM source,
  not from this reimplementation.
- **Neutral-B out of run.** meleelight wires only side-B/down-B out of run; whether PM allows a
  neutral-stick B directly out of run is **unconfirmed** (the meleelight fall-through to run-brake may
  be a simplification). Firm against PM before relying on it.
- **Per-character initial-dash window** (`dashFrameMin`/`dashFrameMax`, 7–18 f) — general range known;
  exact per-archetype values are a rukaidata pull when the cats are built (#117), not needed for the
  precedence *order*.

---

## Provenance & cross-refs

- **primary-reimpl:** meleelight `characters/shared/moves/{DASH,RUN,RUNBRAKE,RUNTURN}.js::interrupt`
  + `physics/actionStateShortcuts.js` (`checkForJump/Squat/SmashTurn`). Melee; PM = `(inference)`.
- **secondary (verbatim quotes above):** SmashWiki [*Dash attack*](https://www.ssbwiki.com/Dash_attack),
  [*Dash grab*](https://www.ssbwiki.com/Dash_grab), [*Dash*](https://www.ssbwiki.com/Dash),
  [*Jump-canceled grab*](https://www.ssbwiki.com/Jump-canceled_grab).
- **repo-grounded (reused):** `docs/pm-reference/{fighter-states,movement-and-tech,input-model,grabs-throws}.md`
  (epic #147); `docs/research/2026-07-01-pm-walk-run-dash-mechanics.md` (#373/#407 — dash/run model,
  initial-dash window, no digital buffer).
- **Consumer:** **#930** (architect — Fork 2 / B1 input seam & precedence) · **#948** (research epic).
  Related: #866 (dash-attack findings — the f-tilt mis-resolve) · #808 (`run` state, blocked) · #388
  (walk/dash/run epic) · #327 (smash seam) · #554 (keyboard-port scope) · `combat/move_select.py::resolve_move_key`
  · `charts/fighter_chart.py` `dash`/`run` · `entities/fighter_input.py::handle_actions`.

**Findings only — no ratified spec.** Part C is the input to the #930 architect decision, made with a
human in the loop.
