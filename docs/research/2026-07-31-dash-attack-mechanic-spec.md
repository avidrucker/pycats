# Dash attack (lunge / run-state attack) — V1 findings + option space

**Ticket:** #866 (RESEARCH, area:combat). **Author:** ELDERBERRY, 2026-07-31.
**Status:** **findings only.** This doc reports evidence (current-state catalogue + datamined PM
frame data) and the **design option space**. It does **not** ratify a spec: every design choice
below is an **OPEN option**, and the decisions are deferred to architect ticket **#930** (to be
made with a human in the loop). Nothing here is settled. The spec, once #930 decides, then drives
the downstream DEV work.

> Filename note: #866's body names the deliverable `2026-07-21-dash-attack-mechanic-spec.md`
> (the ticket's filing-day placeholder). This doc uses its actual authoring date per the
> `docs/research/` date-prefix convention. (Title says "findings", not "spec", per the
> research→architect→spec pipeline.)

---

## Summary of findings (evidence, not a recommendation)

- **The FSM already supports a dash-state attack.** `charts/fighter_chart.py` `dash` leaf has
  `_tick(attack_timer > 0 → "attacking")`, so a fresh A during the dash burst *already* routes
  into the attack region and back out to `idle`. No new state appears to be needed for the
  transition itself.
- **The gap is move-selection.** `combat/move_select.py::resolve_move_key` is direction-keyed and
  dash-blind, so A-during-dash today resolves to the **f-tilt** (forward + ground A), not a dash
  attack. Any dash-attack mechanic has to teach the input→move-select seam about the dash/run
  state.
- **A momentum/slide tension exists.** A PM dash attack slides forward, but the #898 fix **roots**
  grounded attackers. Whether the dash attack is exempted (slides) or rooted is an open design
  fork (§B3).
- **PM `AttackDash` frame data is datamined** for the four archetypes + Fox (below), with lengths
  cross-checked exactly against the reference GIF indexes.

These are observations. The forks they raise are enumerated as options in **Part B** for #930.

---

# Part A — Findings (evidence)

## A1. Current state (what exists today)

### A1a. No character has a dash attack
Authored move keys across all cats (`characters/data/*.json` + the `*_cat.py` builders) are
only `jab`, tilts (`ftilt`/`utilt`/`dtilt`), aerials (`nair`/`fair`/`bair`/`uair`/`dair`),
smashes (`fsmash`/`usmash`/`dsmash`), and `neutral_b`. **There is no `dash_attack` key** and
`combat/move_select.py` has no path that emits one — its module docstring literally lists
`ground normals: jab, ftilt, utilt, dtilt (+ dash later)`. The standing TODO lives at the top
of `entities/player.py`: *"implement lunge attacks that start from run state."*

### A1b. The dash *state* machinery is already built (#388/#396/#403)
- `Fighter._start_dash(direction)` sets `dash_timer = DASH_DURATION` and
  `vel.x = direction * dash_speed`, faces that way. (`config.DASH_DURATION = 12`,
  `config.DASH_SPEED = 8` — ⚠ tuning-start values, see #813/#814 for the movement-speed
  provenance re-pin.)
- `FighterInputController._maybe_start_dash` fires it on a double-tap within
  `config.DOUBLE_TAP_WINDOW = 8` frames (#403).
- `charts/fighter_chart.py` `dash` leaf: entered while `dash_timer > 0`; exits to `walk`/`idle`
  when the burst expires. **There is no sustained `run`** — that is #808 (`blocked`).

### A1c. The FSM already routes dash → attack → idle
The `dash` leaf's **first** tick transition is `_tick(attack_timer > 0 → "attacking")`
(same priority position as `idle`/`walk`/`crouch`). The `attacking` region (startup→active→
recovery sub-phases, Task 4) exits on `done_attacking` to `idle` (grounded). So the state
plumbing for "attack out of dash" is already present — what plays is wrong, not the routing.

### A1d. The gap, precisely
When A is pressed during the dash burst, `FighterInputController.handle_actions` runs the
attack seam: `resolve_move_key(moves, direction, on_ground=True, is_special, is_smash)`, where
`direction = _move_direction(held)`. A dashing fighter holds forward → `direction = "forward"`
→ `_GROUND_A["forward"] = "ftilt"` (or the `"attack"` alias fallback). **Result today: a mid-dash
A throws the forward tilt.** The dash→attacking transition still fires (the move clock started),
so it *looks* like an attack — just the wrong one.

### A1e. The #898 rooting constraint
`FighterInputController.handle_move` **roots** a grounded attacker: while
`attack_timer > 0 and on_ground`, movement is locked and prior momentum bleeds off via friction
(the #898 fix, so f-tilt stays planted instead of sliding ~10px). This is the constraint a
sliding dash attack would run into (see the fork in §B3).

## A2. PM `AttackDash` reference data (datamined)

**Method:** brawllib_rs over the PM 3.6 dataset (Brawl base `-d …/brawl-dump/DATA/files`,
PM overlay `-m …/pm36-sd`), throwaway example `examples/dash_attack_frames.rs` (models
`first_active_frames.rs`): per fighter, the `AttackDash` subaction's frame count, first
hitbox frame, last hitbox frame, and count of hot frames. See
[[brawllib-datamine-env-live]] for the pipeline.

**Raw datamine (frames, 60 fps — same tick rate as pycats, so 1:1):**

| PM fighter (cat) | length | first-active | last-active | hot frames |
|---|---|---|---|---|
| Mario (**nalio**)  | 54 | 6  | 25 | 20 |
| Kirby (**birky**)  | 49 | 8  | 31 | 21 |
| DK (**gnok**)      | 43 | 9  | 20 | 12 |
| Marth (**narz**)   | 50 | 12 | 15 | 4  |
| Fox (reference)    | 40 | 4  | 17 | 14 |

**Cross-check:** every `length` matches the total-frame column in the `docs/pm-reference/
*-gif-index.md` `AttackDash` rows exactly (Mario 54, Kirby 49, DK 43, Marth 50, Fox 40) →
high confidence the datamine and the reference GIFs agree.

**Derived (startup / active / recovery)** — `startup = first_active − 1`,
`active = last_active − first_active + 1`, `recovery = length − last_active`:

| Cat (archetype) | startup | active | recovery | total | notes |
|---|---|---|---|---|---|
| **nalio** (Mario) | 5  | 20 | 29 | 54 | long lingering slide hitbox; single-connect |
| **birky** (Kirby) | 7  | 24 | 18 | 49 | 21 hot of 24 span → a ~3-frame gap (multi-window) |
| **gnok** (DK)     | 8  | 12 | 23 | 43 | contiguous; light-armor in PM (armor deferred, #794) |
| **narz** (Marth)  | 11 | 4  | 35 | 50 | disjoint sword poke: long startup, tiny active, long recovery |
| *fox (ref)*       | 3  | 14 | 23 | 40 | — |

**Two caveats on these numbers:**
1. **`recovery` is the animation tail, not true IASA.** It is `length − last_active`, i.e. every
   animation frame after the hitbox ends — which *overstates* the actionable-recovery because PM
   moves become interruptible (IASA) before the animation finishes. `startup` and `active` are
   exact; `recovery` is an upper bound. A follow-up datamine could pull the per-fighter
   IASA/interrupt frame (brawllib exposes interrupt data in `high_level_frame_data`) if a tighter
   value is wanted — that choice is a #930 option (§B4).
2. **`active` is the hitbox-present span, and one hitbox can span multiple frames** (Mario's 20,
   Kirby's gapped 24). pycats' current model is single-connect (multi-hit is #879/#883, post-V1),
   which bears on how the lingering PM hitbox maps to a pycats hitbox (§B7).

**Units (#120):** hitbox `dx/dy/r` would follow the same PX_PER_UNIT convention as every other
authored move — per-character **data**, produced in the authoring slices, not part of the mechanic.

---

# Part B — Design option space (for #930 to decide)

Each item is an **open fork**, presented with the options and their tradeoffs. **None is
recommended or ratified here** — these are the inputs to the architect decision.

## B1. Input seam & precedence
**Question:** should "A while in the dash/run state" be a **state gate** that overrides the
direction→tilt map (so a held-forward A becomes the dash attack, not an f-tilt), and what is the
precedence vs the dedicated smash input, f-tilt, and jab?
- **Option — state gate overrides direction:** thread an `is_dash_attack` discriminator (from
  `p.state`/`dash_timer`) into `resolve_move_key`; when set, ignore the direction token and select
  `dash_attack`. Matches PM (no f-tilt exists in the dash/run state). Tradeoff: adds a state
  dependency to a currently pure, direction-only seam.
- **Option — direction-aware dash attack:** keep consulting direction (e.g. only forward+A is a
  dash attack). Tradeoff: diverges from PM and reintroduces the "forward vs neutral vs down held
  during a dash" ambiguity.
- **Precedence sub-question:** does the dedicated smash input keep priority over A the frame it is
  pressed (so a smash out of a dash stays an f-smash, not a dash attack)? PM's boost-smash is a
  separate tech (§B6) — in scope or not.

## B2. Move-select shape & partial-kit fallback
**Question:** how does an undefined `dash_attack` fall back so existing goldens stay byte-identical?
- **Option — add a `dash_attack` key on its own branch** (like the smash branch), with the
  fallback = "behave exactly as a non-dash grounded A" (direction→`ftilt`→`"attack"` alias). Every
  current cat lacks `dash_attack`, so the mechanic ships a no-op for the roster and goldens are
  unchanged until one is authored (same discipline as #327 smashes). Tradeoff: none obvious; this
  is the low-risk shape.
- **Open detail:** whether `select_move_key` (the no-fallback mapper) also learns `dash_attack`
  so the `dev_log.log_unimplemented` breadcrumb reports the right key.

## B3. Momentum / slide vs #898 rooting — the key behavior fork
**Question:** a PM dash attack **slides forward**, but #898 **roots** grounded attackers. Which
wins?
- **Option A — exempt the dash attack so it slides:** on start, do not zero/lock `vel.x`; let
  ground friction decay it so the fighter slides and coasts (canonical dash-attack feel). Would
  need a guarded carve-out (e.g. a new `MoveData.slides` flag, default off) in
  `handle_move`/`fighter_physics`. Tradeoff: the one place the mechanic touches physics; needs its
  own regression golden (dash → A → measured slide distance).
- **Option B — author it rooted (no slide),** like every other grounded normal. Tradeoff: ships
  simplest, zero physics change, but reads as a stationary lunge (less PM-faithful).

## B4. Recovery basis
**Question:** author against the datamined **animation-tail** recovery (upper bound) now, or pull
true per-fighter **IASA/interrupt** frames first?
- **Option — use animation-tail recovery now** (author `startup`+`active` exact, `recovery` as a
  tunable upper bound). Faster; risks a slightly-too-long recovery.
- **Option — datamine IASA first** (a small follow-on) for a faithful recovery. Slower; tighter.

## B5. `AttackDashAir` (air dash-attack)
**Question:** in V1 or deferred? DK (`dk_AttackDashAir.gif`, 30 f) and Kirby
(`kirby_AttackDashAir.gif`, 49 f) have it; Mario/Marth/Fox do not. It only occurs when a dash
crosses a ledge into the air, and pycats has no airborne dash state.
- **Option — defer post-V1** (no airborne dash state to hang it on; niche). Tradeoff: a small
  faithfulness gap for DK/Kirby.
- **Option — include** (build an air dash-attack path). Tradeoff: needs an airborne-dash state
  first; larger scope.

## B6. Trigger source in V1
**Question:** trigger off the **`dash` burst state only**, or gate on the sustained **`run`** state?
- **Option — `dash` burst only:** `run` does not exist yet (#808, blocked). Writing the predicate
  as "in dash **or** run" makes enabling run a one-symbol change later.
- **Option — wait for `run` (#808):** couples V1 dash attack to a blocked ticket.

## B7. One-connect vs multi-hit authoring
**Question:** author each dash attack as a single hitbox / single connect?
- **Option — single-connect** (one hitbox over `[startup+1, startup+active]`), consistent with the
  current model and the #879/#883 ruling (multi-hit "B-full" is post-V1). The lingering PM hitbox
  (Mario 20 f, Kirby gapped) collapses to one pycats hitbox. Tradeoff: loses PM's multi-window
  nuance until multi-hit lands.

## B8. Other edge cases surfaced (context for the decisions)
- **Turnaround / reverse-dash (pivot):** pycats has no pivot/dash-dance/foxtrot (#387 closed —
  a keyboard build doesn't need them). A reverse-dash just starts a fresh `_start_dash`; likely no
  special handling, but the decision rides on B1.
- **Exit / IASA:** `attacking` exits to `idle` on `done_attacking`; with no `run` to return to
  (#808), exit-to-`idle` is the natural V1 behavior. A later polish could route back to `dash`/`run`.
- **Shield / dodge / helpless:** the attack seam already no-ops in these states; the dash-attack
  path would inherit that gate.

---

## Provenance & confidence

- **Findings (high confidence):** per-fighter `AttackDash` frame counts + hitbox-active windows
  from the brawllib_rs PM 3.6 datamine, cross-checked against the `docs/pm-reference/*-gif-index.md`
  totals (exact match). These would be recorded as **FOUND** when derived values land downstream.
- **Design (undecided):** everything in **Part B** is an **open option** for #930 — an inference
  or design choice grounded in PM behavior but **not ratified**. It is surfaced, not recommended.
  See [[pm-parity-cite-primary-not-inference]] and [[research-never-produces-spec]].
- **Caveat carried forward:** the datamined `recovery` is an animation-tail **upper bound**, not
  IASA (§A2 caveat 1).

**Cross-refs:** #866 (this findings ticket) · **#930 (architect — where Part B is decided)** ·
#779/#794 (gnok slice 4) · #808 (`run` state, blocked) · #898 (grounded-attack rooting — the slide
constraint) · #879/#883 (single- vs multi-hit) · #813/#814 (dash/run speed provenance) · #387
(pivot/dash-dance not needed) · #120 (units) · `charts/fighter_chart.py` `dash`/`attacking` ·
`combat/move_select.py::resolve_move_key` · `entities/fighter_input.py::handle_actions` ·
`entities/fighter.py::_start_dash` · `docs/pm-reference/*-gif-index.md`.
