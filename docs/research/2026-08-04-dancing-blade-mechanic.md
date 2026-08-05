# Narz side-B = Marth Dancing Blade — mechanic scoping (spike #1185)

Spike for **#1185** (child of the Narz-specials umbrella **#1058** / Narz epic **#294**).
Scopes the engine mechanic **Dancing Blade** needs before any DEV. **Findings + option
space only** — the mechanic is ruled in a follow-on ARCHITECT/decision with the human
(per RULES → "research never produces a spec"); nothing here decides a shape or authors a
value.

## TL;DR

- Dancing Blade is a **multi-input directional combo chain**: an initial side-B, then up to
  **3 follow-up presses**, each follow-up branching on the held stick direction into a
  different hit. pycats has **no combo-input state machine** — confirmed against
  `combat/move_select.py` (one input context → one move key) and the dispatch in
  `entities/fighter_input.py` (`handle_actions`), which since #1087 **drops** any special
  re-press while a move is running (`p.current_move is None` gate). Dancing Blade needs the
  **opposite** of that drop for its own follow-up window.
- The mechanic decomposes into **three orthogonal pieces**, each with a real seam already in
  the tree to model it: (1) a **per-step advance window** (precedent: the `dash_input_window`
  double-tap timer, #388/#403), (2) a **direction-branched next-step lookup** (precedent: the
  `resolve_move_key` direction table), (3) **chain state on the fighter** (which step, whether
  the window is open) plus a **dispatch carve-out** in the `current_move is None` guard.
- The **subaction inventory is already datamined** and committed in
  `docs/pm-reference/marth-gif-index.md` (brawllib_rs PM 3.6): step count, per-step branch set,
  and animation **frame lengths** are `FOUND`. What is **not** yet sourced: per-branch
  **hitboxes / damage / angles** (rukaidata or SmashWiki, a downstream DEV sourcing task) and
  the per-step **advance-window frame bounds** (a mechanic-timing value — SmashWiki / decomp /
  meleelight; not a frame-length the manifest carries). Both are flagged, neither guessed.
- **V1-vs-post-V1 is left open** for the human ruling (#1058 does not pin it). The mechanic is
  the largest of the four Narz specials; a **recommended shape** and a **reduced-scope V1
  option** are both laid out below.

---

## 0. What Dancing Blade is (mechanic shape)

Marth's side-B is a **combo chain of up to 4 sequential hits**, driven by **up to 4 special
presses**:

- **Press 1** — the opener (`SpecialS1`). One hit, no direction branch.
- **Presses 2–4** — each is a *follow-up*: pressing special again **within an input window**
  after the previous hit advances the chain to the next step; the **held direction at that
  press** selects which variant of the step fires (up / side / down). Letting the window
  lapse (or not pressing) **ends** the chain into the previous step's recovery.

Each step is its own short animation with its own hitbox(es); the chain is a *sequence of
single-dispatch moves stitched by an input window*, not one long timeline. This is exactly the
hook pycats lacks: today a move is one `MoveData` → one `MoveClock` timeline, and a re-press
mid-move is dropped.

> Sourcing note: the branch structure and "press-again-within-a-window, branched by direction"
> behavior is the well-documented Melee/PM Marth mechanic, corroborated by the **subaction
> inventory** below (a datamined `SpecialS{2,3,4}{Hi,S,Lw}` fan-out only exists because each
> step branches by direction). Exact per-step window bounds are a value to source (§3), not
> asserted here.

---

## 1. State model

The chain is a small state machine layered **on top of** the existing move clock. One live
step is always a normal `MoveData` on the `MoveClock`; the chain state tracks *where in the
sequence we are* and *whether a follow-up is currently accepted*.

**State (proposed to live on `Fighter`, mirroring `dash_input_window`/`dash_input_dir`):**

| Field | Meaning |
|---|---|
| `chain_move` (or a small enum/key) | which chain this is + which **step** is live (`None` = not in a chain) |
| `chain_advance_window` | frames remaining in which a follow-up press is accepted (a countdown, armed when a step's window opens, decremented in `Fighter.tick_timers` exactly like `dash_input_window`) |

**Transitions:**

- **Start** — side-B pressed, not already in a chain, `current_move is None` → start step 1
  (`SpecialS1`), set `chain_move = step1`. The advance window arms when step 1 reaches its
  follow-up-accept frame (see §3 — a value to source; **not** necessarily frame 0).
- **Advance** — special pressed again while `chain_advance_window > 0` and the step has a
  successor → read the held direction token (`FighterInput._move_direction`, up/down/forward/
  back → the branch), resolve the **next step's MoveData** for that branch, `MoveClock.start()`
  it, bump `chain_move` to the new step, re-arm the window. **This is the dispatch carve-out**:
  the #1087 hard-drop (`current_move is None`) must let a special re-press through *when a chain
  advance is pending*.
- **Cancel / reset (chain ends)** — any of: the advance window lapses with no press; the current
  step is the last (`SpecialS4*`, no successor); the fighter is hit (`receive_hit` — input is
  already gated during hitstun, so the chain state must be cleared there like the smash-charge
  is); the fighter leaves the actionable ground/air state the chain requires. On any of these,
  clear `chain_move`/`chain_advance_window` and let the live step finish into its own recovery.

**Open state-model questions (for the ARC ruling, not decided here):**

- **Does the advance window open during a step's active/hit frames, its recovery, or a bespoke
  sub-window?** Melee/PM allows buffering the next input fairly early; the exact bound is a
  value to source (§3). The model above keeps it a single per-step countdown so the answer is a
  *number*, not a structural change.
- **Airborne chain** — the manifest carries a full `SpecialAirS*` set (§2), so the chain exists
  in the air. Is the airborne chain **in scope** (its own drift/gravity handling) or is a
  ground-only V1 acceptable? (Recommended split in §4.)
- **Step-2 branch asymmetry** — the datamine shows step 2 = **{Hi, Lw}** (2 variants) but steps
  3–4 = **{Hi, S, Lw}** (3 variants). So step 2 has **no distinct "side" subaction**; a
  neutral/forward press at step 2 must map to one of Hi/Lw (or to a default). Which one the
  "side/neutral" input resolves to at step 2 is a **branch-table question** for the DEV, flagged
  by the inventory — see §2.

---

## 2. Datamined subactions (`FOUND` — frame lengths only)

From `docs/pm-reference/marth-gif-index.md` (brawllib_rs PM 3.6 datamine, already committed).
**Frame counts are animation lengths (`FOUND`)**; they are the total subaction length, **not**
the hitbox-active window and **not** the advance-input window (those are §3).

Ground chain:

| Step | Branch | Subaction | Frames |
|---|---|---|---|
| 1 | — (opener) | `SpecialS1` | 30 |
| 2 | up | `SpecialS2Hi` | 45 |
| 2 | down | `SpecialS2Lw` | 45 |
| 3 | up | `SpecialS3Hi` | 52 |
| 3 | side | `SpecialS3S` | 51 |
| 3 | down | `SpecialS3Lw` | 45 |
| 4 | up | `SpecialS4Hi` | 51 |
| 4 | side | `SpecialS4S` | 66 |
| 4 | down | `SpecialS4Lw` | 61 |

Airborne chain (`SpecialAirS*`, same shape; differs only at `S3Lw` 55 vs 45):

`SpecialAirS1` 30 · `SpecialAirS2Hi` 45 · `SpecialAirS2Lw` 45 · `SpecialAirS3Hi` 52 ·
`SpecialAirS3S` 51 · `SpecialAirS3Lw` 55 · `SpecialAirS4Hi` 51 · `SpecialAirS4S` 66 ·
`SpecialAirS4Lw` 61.

**Reads for the DEV:**

- **Step count = 4** (1 opener + 3 follow-ups). **Max chain depth is fixed** — bounds the state
  machine (no unbounded loop, unlike the d-air rehit).
- **Branch set per step:** step 1 none; **step 2 = {up, down}** (no side subaction); steps 3–4 =
  {up, side, down}. The DEV's branch table must decide what a side/neutral press does *at step 2*
  (map to Hi or Lw) — surfaced by the inventory, ruled downstream.
- **Not in the manifest** (values a downstream sourcing pass must supply, like the Dolphin Slash
  pass `docs/research/2026-08-01-narz-dolphin-slash-sourcing.md` did for its move): per-branch
  **hitbox geometry, damage %, launch angle, BKB/KBG**, and the per-step **hitbox-active window**.
  Source via **rukaidata** (scripted per-move hitbox data) and/or **SmashWiki Marth (PM 3.6)**;
  the datamine recipe is `docs/tooling-brawllib-rs-datamine-recipe.md`.

---

## 3. The one value the manifest cannot give: the advance window

The chain's defining timing — **"how long after step N's press is a follow-up accepted"** — is a
**mechanic-timing value**, not an animation length, so it is absent from the frame-length
manifest. It must be sourced before DEV:

- **Candidates:** SmashWiki Marth Dancing Blade frame data (PM 3.6 / Melee), the Melee decomp,
  or **meleelight** (the local engine-logic reference, #616) if it models Marth's side-B script.
- **Status if unsourced:** it would be a `GUESS`/`decision` under #530 (a bare game-feel number
  is declined). This spike does **not** guess it.
- **Shape:** whatever the source says, it lands as **one integer per step** (a
  `chain_advance_window` arm value), so sourcing it does not change the state model — only fills
  in the countdown.

---

## 4. Where it seats in the engine (option space)

Three real seams already model the three pieces. The recommendation reuses all three rather than
building a bespoke subsystem.

### 4a. Advance window — reuse the `dash_input_window` timer pattern

`Fighter.dash_input_window` (armed on a directional press, decremented in `Fighter.tick_timers`,
checked on the next input edge; `DOUBLE_TAP_WINDOW = 8`) is the **exact** shape the chain needs:
a stateless per-frame countdown that gates "did the next input arrive in time". Add
`chain_advance_window` (+ the step marker) to the same `tick_timers` list.

- **Option A (recommended):** new `chain_advance_window` / `chain_move` fields on `Fighter`,
  ticked alongside `dash_input_window`. Minimal, mirrors an existing, tested pattern.
- **Option B:** a standalone `ChainClock`/`ComboState` object beside `MoveClock`. More
  encapsulated but new surface; unwarranted for a fixed-depth-4 chain.

### 4b. Direction-branched next-step lookup — extend the `move_select` table idea

The next step is a pure function of `(current_step, held_direction)`. This is the same "direction
token → key" mapping `combat/move_select.py` already does, just keyed on step too.

- **Option A (recommended):** a small **chain table** — `{step: {direction: next_move_key}}` —
  living beside `_SPECIAL` in `move_select.py` (or as data on the fighter, see 4d). Pure,
  testable, no engine state. Encodes the step-2 asymmetry (§2) explicitly.
- **Option B:** a `next_on_input` field **on `MoveData`** pointing at successor move keys per
  direction. Puts the chain graph in the data schema (`combat/data.py`); heavier schema change,
  couples every `MoveData` to a chain concept it doesn't need.

### 4c. Dispatch carve-out — the `current_move is None` guard

The Attack/Special block in `handle_actions` fires only when `p.current_move is None` (the #1087
hard-drop). Dancing Blade needs a **narrow** exception: while `chain_move` is set **and**
`chain_advance_window > 0` **and** the step has a successor, a special re-press **advances** the
chain instead of being dropped. Everything else (a re-press with the window closed, a re-press on
the last step, a non-chain move) keeps the #1087 drop unchanged — so no other move's
commitment/IASA behavior moves.

### 4d. Where the chain graph lives (data vs. code)

Narz is JSON-backed (`characters/data/narz.json`); its `moves` today has **no** `side_b`
(confirmed — the mechanic is unbuilt). Two homes for the chain graph:

- **Option A (recommended):** the chain steps are **individual `MoveData` entries** under
  descriptive keys (e.g. `side_b`, `side_b_2_up`, …) and the **step→direction→key graph** is a
  small structure (in `move_select.py` or a sibling), referenced by the dispatch. Keeps
  `MoveData` unchanged; the graph is code/data next to the existing direction table.
- **Option B:** a new `chain`/`next_on_input` block **in the fighter JSON schema**. Most
  general (a future chained move reuses it) but expands the editor + hydrate + round-trip
  surface (`combat/data.py`, the #792 editor) — a larger blast radius than V1 needs.

---

## 5. Recommended shape + V1-vs-post-V1

**Recommended mechanic shape** (for the ARC ruling to accept/amend, not a decision here):

> Reuse three existing seams — a `chain_advance_window` timer (4a-A, like `dash_input_window`),
> a `{step: {direction: key}}` chain table beside `_SPECIAL` (4b-A), and a narrow carve-out in
> the `current_move is None` dispatch guard (4c). The chain steps are ordinary `MoveData`
> entries in `narz.json` (4d-A). No `MoveData`/JSON-schema change; no bespoke subsystem.

**V1-vs-post-V1 (open — the human rules it):** two coherent scopes.

- **Reduced V1** — **ground chain only**, and optionally **fewer than 4 steps** (e.g. opener +
  one branch) to prove the state machine + carve-out with the least data-sourcing. Airborne
  chain and full depth deferred. Smallest surface; still needs the advance-window value (§3) and
  step hitbox data for the steps it ships.
- **Full move** — all 4 steps, both ground and air, full branch tables. Larger sourcing load
  (9 ground + 9 air branch animations' worth of hitbox data) but the complete mechanic.

Either way, **DEV is gated on §3 (the advance-window value) and the per-branch hitbox sourcing**
— both `FOUND`-or-`decision` under #530, neither guessable. This spike unblocks the ARC; the ARC
unblocks a DEV filed one at a time downstream.

---

## 6. Confidence / provenance summary

| Claim | Status | Basis |
|---|---|---|
| No combo-input state machine exists today | **Verified** | `combat/move_select.py`, `entities/fighter_input.py` (`handle_actions`, `current_move is None` gate), `combat/move_clock.py` read this session |
| Step count = 4; branch set per step (2 = {Hi,Lw}, 3–4 = {Hi,S,Lw}) | **`FOUND`** | `docs/pm-reference/marth-gif-index.md` (brawllib_rs PM 3.6) |
| Per-subaction animation **frame lengths** | **`FOUND`** | same manifest |
| "Press again within a window, branched by held direction" chain behavior | **Corroborated inference** | documented Melee/PM Marth mechanic + the datamined per-direction subaction fan-out; exact windows unsourced |
| Per-branch hitbox / damage / angle / KB | **Not sourced (downstream)** | needs rukaidata / SmashWiki (like the Dolphin Slash pass) |
| Per-step **advance-window** frame bounds | **Not sourced (downstream)** | mechanic-timing value; SmashWiki / decomp / meleelight |
| Recommended engine seams (timer / table / dispatch carve-out) | **Recommendation, not a ruling** | maps to `dash_input_window`, `_SPECIAL`, the #1087 guard |

## Refs

Umbrella **#1058** · Narz epic **#294** / scope **#290** (`docs/research-spec-290-narz-marth-pm.md`)
· dispatch `combat/move_select.py`, `entities/fighter_input.py` · MoveData `combat/data.py` ·
move clock `combat/move_clock.py` · window-timer precedent `dash_input_window` (#388/#403,
`entities/fighter.py`) · subaction manifest `docs/pm-reference/marth-gif-index.md` · datamine
recipe `docs/tooling-brawllib-rs-datamine-recipe.md` · sibling sourcing precedent
`docs/research/2026-08-01-narz-dolphin-slash-sourcing.md` (#1063) · value routing **#530** ·
Counter sibling spike **#1186**.
