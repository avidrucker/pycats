# Dash attack (lunge / run-state attack) — V1 mechanic spec

**Ticket:** #866 (RESEARCH, area:combat). **Author:** ELDERBERRY, 2026-07-31.
**Status:** decision-ready. Downstream DEV (mechanic) + per-character data slices file
one-at-a-time after this doc.

> Filename note: #866's body names the deliverable `2026-07-21-dash-attack-mechanic-spec.md`
> (the ticket's filing-day placeholder). This doc uses its actual authoring date per the
> `docs/research/` date-prefix convention.

---

## TL;DR (the ruling this doc recommends)

- **The FSM already supports a dash-state attack.** `charts/fighter_chart.py` `dash` leaf has
  `_tick(attack_timer > 0 → "attacking")`, so a fresh A during the dash burst *already*
  routes into the attack region and back out to `idle`. **No new state is needed.**
- **The only missing wiring is move-selection.** `combat/move_select.py::resolve_move_key`
  is direction-keyed and dash-blind, so A-during-dash today resolves to the **f-tilt**
  (forward + ground A), not a dash attack. The mechanic = *teach the input→move-select seam
  that "A while in the dash/run state" selects a new `dash_attack` key*, with a partial-kit
  fallback so golden sims stay byte-identical.
- **Two behavior decisions the DEV ticket must carry** (both flagged below, each needs its
  own golden): (1) **momentum/slide** — a PM dash attack *slides forward*, which collides
  with the #898 grounded-attack **rooting**; recommend exempting `dash_attack` from the root
  so it keeps a decaying forward slide. (2) **recovery basis** — the datamined per-fighter
  "recovery" is the animation tail after the last hitbox and overstates true IASA; author
  startup + active faithfully and treat recovery as a tunable upper bound.
- **`AttackDashAir` → defer post-V1.** pycats has no airborne dash state; the air variant is
  a niche (dash off a ledge) and out of V1 scope.
- **Trigger source in V1 = the `dash` burst only.** The sustained `run` state (#808, blocked)
  does not exist yet; when it lands, extend the same trigger to `run`. One-line change, called
  out below.

---

## 1. Current state (what exists today)

### 1a. No character has a dash attack
Authored move keys across all cats (`characters/data/*.json` + the `*_cat.py` builders) are
only `jab`, tilts (`ftilt`/`utilt`/`dtilt`), aerials (`nair`/`fair`/`bair`/`uair`/`dair`),
smashes (`fsmash`/`usmash`/`dsmash`), and `neutral_b`. **There is no `dash_attack` key** and
`combat/move_select.py` has no path that emits one — its module docstring literally lists
`ground normals: jab, ftilt, utilt, dtilt (+ dash later)`. The standing TODO lives at the top
of `entities/player.py`: *"implement lunge attacks that start from run state."*

### 1b. The dash *state* machinery is already built (#388/#396/#403)
- `Fighter._start_dash(direction)` sets `dash_timer = DASH_DURATION` and
  `vel.x = direction * dash_speed`, faces that way. (`config.DASH_DURATION = 12`,
  `config.DASH_SPEED = 8` — ⚠ tuning-start values, see #813/#814 for the movement-speed
  provenance re-pin.)
- `FighterInputController._maybe_start_dash` fires it on a double-tap within
  `config.DOUBLE_TAP_WINDOW = 8` frames (#403).
- `charts/fighter_chart.py` `dash` leaf: entered while `dash_timer > 0`; exits to `walk`/`idle`
  when the burst expires. **There is no sustained `run`** — that is #808 (`blocked`).

### 1c. The FSM *already* routes dash → attack → idle
The `dash` leaf's **first** tick transition is `_tick(attack_timer > 0 → "attacking")`
(same priority position as `idle`/`walk`/`crouch`). The `attacking` region (startup→active→
recovery sub-phases, Task 4) exits on `done_attacking` to `idle` (grounded). So the state
plumbing for "attack out of dash" is **complete** — what plays is wrong, not the routing.

### 1d. The gap, precisely
When A is pressed during the dash burst, `FighterInputController.handle_actions` runs the
attack seam: `resolve_move_key(moves, direction, on_ground=True, is_special, is_smash)`, where
`direction = _move_direction(held)`. A dashing fighter holds forward → `direction = "forward"`
→ `_GROUND_A["forward"] = "ftilt"` (or the `"attack"` alias fallback). **Result today: a mid-dash
A throws the forward tilt.** The dash→attacking transition still fires (the move clock started),
so it *looks* like an attack — just the wrong one. The mechanic must make that input resolve to
`dash_attack` instead.

---

## 2. Q1 — Input seam & precedence

**How "attack while dashing/running" registers, and how it beats f-tilt / jab / f-smash.**

`resolve_move_key` currently takes `(available, direction, on_ground, is_special, is_smash)`.
Add a **state-derived** discriminator — an `in_dash` (later `in_run`) boolean the caller
computes from `p.state` / `dash_timer`, threaded into a new `is_dash_attack` selection path
(the cleanest change is a keyword arg, mirroring how `is_smash` was added in #327/#331).

**Precedence ruling (highest → lowest), the frame A is pressed:**

1. **Smash** (`ground_smash`, the dedicated smash input) — unchanged, still wins. A smash
   thrown out of a dash stays an f-smash (boost-smash / dash-cancel-smash is a *separate* PM
   tech, out of V1 scope — see §6 edge cases).
2. **Dash attack** — `is_dash_attack` when: `attack` pressed (A, **not** the smash input) AND
   the fighter is in the `dash` state (V1) / `run` state (post-#808) AND on ground AND not in
   `shield`/`dodge`/`helpless`. This **overrides the direction→tilt map** — the held forward
   direction is ignored for selection (a dash attack is direction-agnostic; you are already
   committed to the dash's facing).
3. **Direction tilt / jab** (`_GROUND_A[direction]`) — the normal grounded A, when **not** in
   dash/run. This is what f-tilt/jab/u-tilt/d-tilt keep resolving to when standing/walking.
4. **Special** — unchanged.

Rationale: in PM the initial-dash / run state has no f-tilt (you must be standing or walking to
tilt); A during dash/run is *always* the dash attack. So the state gate is authoritative and the
direction token is simply not consulted on the dash-attack path — this also sidesteps any
"forward vs neutral vs down held during a dash" ambiguity.

**Partial-kit fallback (golden-safety, critical):** if `is_dash_attack` but the character does
**not** define `dash_attack`, the seam must fall back to **exactly today's behavior** — i.e.
resolve as if `is_dash_attack` were false (direction→`ftilt`→`"attack"` alias). Every current
cat lacks `dash_attack`, so with the fallback in place **the mechanic ships a no-op for the
existing roster and the golden sims stay byte-identical** until a `dash_attack` is authored. This
is the same discipline that let #327 add smashes without disturbing partial kits.

---

## 3. Q2 — Move-select design

Add `dash_attack` to the move-key vocabulary (docstring + a constant). In `resolve_move_key`,
before the direction maps:

```
if is_dash_attack:                      # A pressed while in dash/run state (§2)
    if "dash_attack" in available:
        return "dash_attack"
    # partial-kit fallback: behave exactly as a non-dash grounded A (golden-safe)
    # → fall through to the existing direction/attack-alias path below
```

- **No new canonical entry in `_GROUND_A`/`_AIR_A`** — `dash_attack` is selected by the state
  gate, not a direction token, so it lives on its own branch (like the smash branch).
- **Fallback path is the current code**, unchanged, so undefined-`dash_attack` cats are identical.
- **Air:** V1 has no air dash-attack path (see §5 AttackDashAir), so `is_dash_attack` is only ever
  set on the ground; the air branch is untouched.

`select_move_key` (the no-fallback canonical mapper) gains a matching early `if is_dash_attack:
return "dash_attack"` so the two stay consistent (and so the `dev_log.log_unimplemented`
breadcrumb reports the right key for a not-yet-authored dash attack).

---

## 4. Q3 — FSM: transition, momentum/slide, exit

### 4a. Transition — already present
`dash` leaf `_tick(attack_timer > 0 → "attacking")`. When the DEV wiring starts the move clock
(`p._clock.start(moves["dash_attack"])`) the existing tick moves `dash → attacking` on the next
frame. **No chart edit is required for the transition itself.**

### 4b. Momentum / slide — THE behavior decision (⚠ collides with #898)
`FighterInputController.handle_move` **roots** a grounded attacker: while
`attack_timer > 0 and on_ground`, movement is locked and prior momentum bleeds off via friction
(the #898 fix, so f-tilt stays planted instead of sliding ~10px). **A dash attack is the exact
opposite** — it should *retain the dash's forward velocity and slide*. Two options:

- **Option A (recommended): exempt `dash_attack` from the #898 root.** On dash-attack start, do
  **not** zero/lock `vel.x`; let the existing ground friction decay it over the move so the
  fighter slides forward and coasts to a stop — the canonical dash-attack feel. Needs a guarded
  carve-out in `handle_move`/`fighter_physics` keyed on the live move being the dash attack
  (e.g. a `MoveData` flag `slides: bool = False`, defaulting off so nothing else changes).
- **Option B (simplest): author it rooted (no slide),** like every other grounded normal. Ships
  faster, zero physics change, but reads as a stationary lunge — noticeably un-PM.

Recommend **A**, gated behind a new `MoveData.slides` flag so the change is opt-in per move and
the golden sims for all rooted normals stay byte-identical. This is the one place the mechanic
touches physics; it deserves its own regression golden (dash → A → measured slide distance).

### 4c. Exit / IASA
`attacking` exits to `idle` on `done_attacking` (grounded). In PM a dash attack's IASA returns
you to a **standing/dash** actionable state; pycats has no `run` to return to yet (#808), so
**exit-to-`idle` is correct for V1**. When #808 lands, no chart change is needed — `idle` is a
fine neutral exit; a later polish ticket could route the exit back to `dash`/`run` if a held
direction warrants, but that is out of V1 scope.

---

## 5. Q4 — PM `AttackDash` reference data (datamined) + units

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

**Derived `MoveData` (startup / active / recovery)** — `startup = first_active − 1`,
`active = last_active − first_active + 1`, `recovery = length − last_active`:

| Cat (archetype) | startup | active | recovery | total | notes |
|---|---|---|---|---|---|
| **nalio** (Mario) | 5  | 20 | 29 | 54 | long lingering slide hitbox; single-connect |
| **birky** (Kirby) | 7  | 24 | 18 | 49 | 21 hot of 24 span → a ~3-frame gap (multi-window) |
| **gnok** (DK)     | 8  | 12 | 23 | 43 | contiguous; light-armor in PM (armor deferred, #794) |
| **narz** (Marth)  | 11 | 4  | 35 | 50 | disjoint sword poke: long startup, tiny active, long recovery |
| *fox (ref)*       | 3  | 14 | 23 | 40 | — |

**Two caveats on these numbers (candid):**
1. **`recovery` is the animation tail, not true IASA.** It is `length − last_active`, i.e. every
   animation frame after the hitbox ends — which *overstates* the actionable-recovery because PM
   moves become interruptible (IASA) before the animation finishes. Author **startup + active
   faithfully** (those are exact); treat **recovery as a tunable upper bound**, or file a
   follow-up datamine for the per-fighter IASA/interrupt frame (brawllib exposes interrupt data
   in `high_level_frame_data`) if a tighter value is wanted.
2. **`active` is the hitbox-present span, and one hitbox can span multiple frames** (Mario's 20,
   Kirby's gapped 24). For pycats' **single-connect** model (one hit per move; multi-hit is
   #879/#883, ruled post-V1), author each dash attack as **one hitbox with one active window** —
   the lingering PM hitbox becomes a single pycats hitbox over `[startup+1, startup+active]`.

**Units (#120):** hitbox `dx/dy/r` follow the same PX_PER_UNIT convention as every other
authored move — that is per-character **data**, produced in the authoring slices (§6), not part
of this mechanic spec.

---

## 6. Q5 — Edge cases (thorough)

- **Dash attack vs turnaround / reverse-dash (pivot):** pycats has no pivot / dash-dance / foxtrot
  (research #387 closed: a keyboard build does not need them for "PM parity"). A reverse-dash
  input just starts a fresh `_start_dash` in the new direction; A during it is a normal
  forward-facing dash attack. **No special turnaround handling in V1.**
- **Initial-dash vs full-run entry:** V1 triggers off the **`dash` burst state only** (there is
  no `run` — #808 blocked). The trigger predicate is written as "in dash **or** run" so that when
  #808 lands, enabling run is a one-symbol change with no move-select churn. Call this dependency
  out in the DEV ticket.
- **Momentum carry / slide distance:** see §4b — the one physics decision. Slide distance is
  emergent from the retained `vel.x` (`dash_speed`) decaying under ground friction over the move;
  it is not a separate authored number. Its regression golden is the acceptance artifact for the
  slide behavior.
- **One-connect:** dash attacks hit once — consistent with the current single-hit model and the
  #879/#883 ruling (multi-hit "B-full" is post-V1). Author one hitbox, one window.
- **Smash disambiguation:** the dedicated smash input keeps priority over the attack input the
  frame it is pressed (§2 precedence 1), so A→dash attack and the smash button→f-smash never
  collide. PM's *boost smash* (dash → down-taunt-cancel → up-smash retaining dash momentum) is a
  distinct tech and **out of V1 scope** — note it, do not build it.
- **Shield / dodge / helpless:** the attack seam already no-ops in `shield`/`dodge`/`helpless`
  (existing guard in `handle_actions`); the dash-attack path inherits that gate unchanged.
- **Air:** `is_dash_attack` is never set airborne in V1 (no air dash state), so a dash that runs
  off a ledge simply becomes a `fall`; A there is a normal aerial. See `AttackDashAir` below.

### `AttackDashAir` — ruling: **defer to post-V1**
DK (`dk_AttackDashAir.gif`, 30 f) and Kirby (`kirby_AttackDashAir.gif`, 49 f) have air
dash-attack variants; Mario/Marth/Fox do not. It only occurs when a dash crosses a ledge into
the air mid-animation — a niche pycats has no state for (no airborne dash). **Out of V1 scope;**
revisit only if/when an airborne-dash state is built. This doc makes that call explicitly, per
#866's deliverable ask.

---

## 7. Q6 — Per-character authoring plan (downstream, one-at-a-time)

Once the mechanic lands, each cat plugs in a `dash_attack` `MoveData` under its `moves` map,
using the §5 startup/active table + per-character hitbox geometry (`dx/dy/r`, damage, angle,
knockback — authored the same way as its existing normals):

1. **gnok** (DK) — already scoped as **slice 4 of #779/#794** (`AttackDash`, light-armor → author
   as a plain hit for now; startup 8 / active 12 / recovery ≤23). File first — it is the one with
   a pre-existing home.
2. **nalio** (Mario) — startup 5 / active 20 / recovery ≤29; lingering slide.
3. **birky** (Kirby) — startup 7 / active ~24 / recovery ≤18.
4. **narz** (Marth) — startup 11 / active 4 / recovery ≤35; disjoint reach.

Each is its own BDD DEV ticket (one complaint = one move), filed **after** the mechanic DEV lands
and **one at a time** per RULES. Each retrofit reds nothing until authored (the §2 fallback), and
each lands with the `dash → A → dash_attack connects` regression test.

---

## 8. Recommended downstream tickets (file one at a time, after this doc)

1. **DEV (mechanic):** thread an `is_dash_attack` discriminator through
   `fighter_input.handle_actions` → `move_select.resolve_move_key`/`select_move_key`; add the
   `dash_attack` key + partial-kit fallback; add `MoveData.slides` and exempt a sliding move from
   the #898 root (Option A). Acceptance: (a) a cat *with* a stub `dash_attack` throws it out of a
   dash and slides; (b) every existing cat's golden sim is byte-identical (fallback proof);
   (c) the dash→attacking→idle trace is unchanged.
2. **DEV (data), one per cat:** gnok (#794 slice 4) → nalio → birky → narz, as §7.
3. *(optional)* **RESEARCH follow-up:** per-fighter IASA/interrupt frame for `AttackDash` to
   replace the animation-tail recovery upper bound with the true actionable-recovery.

**Explicitly out of scope of the above:** `AttackDashAir` (deferred), boost-smash / dash-cancel
tech, pivot/dash-dance, and the sustained `run` trigger extension (rides on #808).

---

## 9. Provenance & confidence

- **Sourced (high confidence):** per-fighter `AttackDash` frame counts + hitbox-active windows
  from the brawllib_rs PM 3.6 datamine, cross-checked against the `docs/pm-reference/*-gif-index.md`
  totals (exact match). Recorded as **FOUND** when the derived startup/active land in `config`/
  `MoveData` downstream.
- **Inference / design (not sourced):** the input-precedence ruling, the move-select fallback
  shape, and the momentum/slide (Option A) recommendation are **design decisions** grounded in
  PM behavior but chosen for pycats' architecture — they are the owner's to ratify at the DEV
  stage, recorded as design rationale, not as sourced values. See [[pm-parity-cite-primary-not-inference]].
- **Caveat carried forward:** the datamined `recovery` is an animation-tail **upper bound**, not
  IASA (§5 caveat 1).

**Cross-refs:** #866 (this) · #779/#794 (gnok slice 4) · #808 (`run` state, blocked) ·
#898 (grounded-attack rooting — the slide collision) · #879/#883 (single- vs multi-hit) ·
#813/#814 (dash/run speed provenance) · #387 (pivot/dash-dance not needed) · #120 (units) ·
`charts/fighter_chart.py` `dash`/`attacking` · `combat/move_select.py::resolve_move_key` ·
`entities/fighter_input.py::handle_actions` · `entities/fighter.py::_start_dash` ·
`docs/pm-reference/*-gif-index.md`.
