# Smash attacks + the charge mechanic — scoping spec (#328)

> First child of the smash-attacks epic **#327**. Architect-mode scoping (yegor-architect):
> decides the **input seam**, **charge model**, and **schema**, and decomposes into ordered
> ≤60-min courier tasks — **no code in this ticket**. Date: 2026-06-30. Agent: DRAGONFRUIT.
> `area:combat`. Grounded in `combat/move_select.py`, `entities/fighter_input.py:187-204`,
> `combat/data.py`, `combat/move_clock.py`.

## TL;DR — the two decisions that shape everything

1. **Split the epic: input/routing FIRST, charge SECOND.** "Smashes" and "charge" are two
   concerns. An *uncharged* smash is just a `MoveData` under a new move key, fired like a tilt —
   nearly zero risk. *Charge* (hold to power up) is an orthogonal engine mechanic layered on top.
   So uncharged smashes ship and get playtested before any charge complexity lands.
2. **Use a dedicated "smash" input (the c-stick analog), NOT a hold-A threshold.** Today every
   move fires on the frame **attack is pressed** (`fighter_input.py:189`). A hold-A charge would
   force **tilts to fire on release**, changing their timing/feel and churning the goldens — a
   non-starter. A separate smash input leaves the "fire on press" model and all tilt timing
   **untouched**, so it is trivially golden-stable.

**Golden-safety (Q5) — decisive, holds for every slice:** the sim/golden path loads the **default
cat** (which gets no smash move) and the scripted controllers **never press the smash input**, so
nothing below changes a golden. The one schema addition (Q3) is an *optional field defaulted off*,
so every existing `MoveData` stays byte-identical.

---

## Decisions (with rejected alternatives)

### Q2 — Input seam: how is a smash distinguished from a tilt? → **a dedicated `smash` input**
Add a fourth action binding (`smash`, per player) alongside `attack`/`special`/`shield`. Smash +
direction → an `fsmash`/`usmash`/`dsmash` move key via a new `_SMASH` map in `move_select.py`;
routed in `handle_actions` beside the existing attack/special branch (`fighter_input.py:187-204`).

- **Rejected — hold-A threshold** (press A, fire tilt on release, smash if held past a window):
  forces every tilt onto fire-on-release, changing tilt timing + feel and risking the goldens;
  entangles the charge concern with the tilt concern. The single biggest reason to avoid it.
- **Rejected — attack+special chord** (no new binding): ergonomically awkward and collision-prone
  (accidental double-press), and it overloads the special button. A new binding is cheap and explicit.
- **Rejected — tap-direction+A heuristic**: pycats has no multi-frame input-history seam; fragile.

The dedicated input is the c-stick analog (PM-faithful in spirit) and keeps the concern isolated.

### Q1 — Charge model (slice 3, after uncharged smashes) → **continuous hold-to-accumulate**
While the `smash` input is **held** (a new `smash_charge` hold state), a charge fraction
`c ∈ [0, 1]` accumulates over `SMASH_CHARGE_FRAMES`; on **release** (or reaching max) the smash
fires with `c` captured. At the Attack spawn point (`player.update`, when the active window opens),
each spawned `Hitbox`'s `damage`/`base_knockback`/`knockback_growth` scale by
`1 + c*(SMASH_CHARGE_SCALE − 1)` (uncharged `c=0` → authored base; full `c=1` → base × SCALE).

- **Rejected — discrete charge levels** (e.g. 3 steps): simpler but less smooth; PM charge is
  continuous. Not worth a distinct model.
- **Rejected — scale at authoring time**: charge is inherently runtime (depends on hold duration).

### Q3 — Schema: new fields vs runtime multiplier? → **one optional `MoveData.chargeable: bool` + a config constant**
- Slice 1–2 (input + uncharged smashes): **zero schema change** — a smash is a `MoveData` under a
  new key, identical shape to a tilt.
- Slice 3 (charge): add **`MoveData.chargeable: bool = False`** (marks a move as accepting charge)
  and a global **`config.SMASH_CHARGE_SCALE`** (the full-charge multiplier, ⚠ playtest; PM ≈ 1.4).
  At spawn, a chargeable move's hitboxes are scaled via `dataclasses.replace` (Hitbox stays frozen).
  `chargeable` defaults `False`, so **every existing `MoveData` is byte-identical** → goldens safe.
- **Rejected — per-`Hitbox` charge fields** (`charge_damage`/…): bloats the hot primitive for a
  niche; the global scale covers v1. Per-move tuning can add a `charge_scale` override later if needed.

### Q4 — Angleable f-smash (up/down-angle)? → **out of scope; a later slice**
Angling needs another input nuance (a held up/down while smashing forward) and variant hitboxes.
Defer to a `#327` child after the base smashes + charge land. v1 smashes are straight f/u/d.

### Q6 — FSM / timing → **uncharged reuses the attack state; charge adds one hold state**
- **Uncharged smash (slices 1–2):** reuses the existing `attacking`→`"attack"` state + move clock
  exactly like a tilt. **No new state.**
- **Charge (slice 3):** a new `smash_charge` leaf (a pre-swing hold) entered on smash-press, exited
  on release — at which point `player.update` captures `c`, starts the smash on the move clock, and
  drops the hold. This mirrors the driven-state pattern (prone/getup, ledge-hang): a
  `charge_timer`/`charge_fraction` on `Fighter`, ticked in `player.update`, read by a chart guard.
  Charge happens **before** the move clock starts (the swing is the normal move afterward), so the
  move-clock invariant (#71) is untouched.

---

## Ordered slice plan (courier tasks, ≤60 min each; file one at a time under #327)

| # | Slice | Deliverable | Risk |
|---|---|---|---|
| **1** | **Smash input + routing** | A `smash` control binding (settings + the two default keymaps + `watch.py`); `_SMASH = {forward: fsmash, up: usmash, down: dsmash}` + `select/resolve_move_key` handling `is_smash`; route smash-press in `handle_actions`. Test: `resolve_move_key(..., is_smash=True)` → the smash keys, with tilt fallback unchanged. **No move data, no charge.** | S — pure seam, golden-safe |
| **2** | **Nalio's smashes (uncharged)** | Author Nalio `fsmash`/`usmash`/`dsmash` `MoveData` (PM3.6 Mario, rukaidata) under the new keys — one move per sub-slice if large. Data-only, reachable via slice 1. | S — data, like the tilts |
| **3** | **Charge mechanic (engine)** | `MoveData.chargeable` + `config.SMASH_CHARGE_SCALE`; `smash_charge` state + `charge_timer`/`charge_fraction` on `Fighter`; accumulate-on-hold + scale-at-spawn; mark the smashes chargeable. Tests: `c=0` == authored, `c=1` == base×SCALE, able-to-fail. | M — new state + spawn-time scaling |
| **4** | **Narz's tipper smashes** (and other archetypes) | Author each cat's smashes (Narz's are 2-box tippers — his f-smash is the archetype's signature KO). One move per slice. | S — data |
| **5** | **Angleable f-smash** (optional) | up/down-angle input + variant hitboxes. | M — input nuance |
| **6** | **CPU/AI smash usage** (deferred) | Teach leveled bots to charge/throw smashes (cf. #248/#250). | M — AI |

**First DEV child to file:** slice 1 (smash input + routing). It unblocks everything and is
golden-safe with no move data.

---

## Architect deliverables (yegor)

**Scope status (PBS):**
1. Input seam / routing — **designed, 0% built** (slice 1).
2. Per-character smash move data — **designed, 0%** (slices 2, 4).
3. Charge mechanic — **designed, 0%** (slice 3).
4. Angleable smashes — **scoped-out for v1** (slice 5).
5. AI integration — **deferred** (slice 6).

**Issues (current):**
1. No smash input exists — the whole feature is blocked on slice 1.
2. `watch.py`/char-select keymaps must gain the `smash` binding or `--p*-char` smashes are unreachable in the harness.
3. Nalio/Narz smash *values* still need a rukaidata datamine at authoring time (like the tilts' ⚠ playtest).

**Risks (probability × impact):**
1. **Charge state interacts with dodge/shield/hitstun cancels** (M × M) — a charging fighter hit mid-charge must exit cleanly. *Mitigation:* the `smash_charge` state uses the same interrupt guards as `attacking`; slice 3 tests a hit-during-charge.
2. **Keyboard ergonomics of a 4th action key** (M × L) — two players × (4 dirs + attack + special + shield + smash) crowds the keyboard. *Mitigation:* it's a config choice; document defaults, revisit if playtest complains.
3. **Golden drift if a smash is ever added to the default cat** (L × H) — would cascade like the ledge goldens. *Mitigation:* the plan keeps the default cat smash-free; a test guards `"fsmash" not in default.moves`.

## Rejected alternatives (summary)
Hold-A charge (churns tilt timing) · attack+special chord (ergonomics) · tap-direction heuristic
(no input history) · discrete charge levels (less faithful) · per-Hitbox charge fields (bloat) ·
angleable smashes in v1 (deferred).

## Termination / next step
This spec lands with the decisions + ordered slice plan. **Next:** file slice 1 (smash input +
routing) as the first DEV child of #327 — a competent courier can implement it from this doc with
no further design questions.

## Refs
Epic #327; seam `combat/move_select.py` (#143), `entities/fighter_input.py:187-204`, `combat/data.py`
(`MoveData`/`Hitbox`), `combat/move_clock.py` (#71); archetype specs #119/#290; golden byte-stability
#80; `docs/pm-reference/moveset-and-frame-data.md` (charge moves); canonical PM3.6 (rukaidata).
