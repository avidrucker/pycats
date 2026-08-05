# RESEARCH: scope the counter/reflect mechanic for Narz down-B Counter (#1186)

**Role:** RESEARCH spike · child of #1058 (Narz specials umbrella) / #294 (Narz epic).
**Date:** 2026-08-04 · **Depth:** moderate (cite existing PM/Melee sources; no fresh brawllib
datamine — the values needed are engine-hardcoded, see §4).

Research reports **findings + option space only**. The mechanic is *ruled* in a follow-on
ARCHITECT/decision ticket with the human, and *built* in a DEV downstream. Nothing here authors a
value or builds the mechanic.

---

## TL;DR

pycats has **no counter/reflect mechanic** — confirmed by grep across `pycats/` (only `perf_counter`,
frame counters, `collections.Counter`, and projectile bounce turn up). Building Marth's Counter needs
**three new pieces**: a timed **counter window** on the fighter (dodge/getup archetype), a **detect-
and-cancel hook** in `systems/hit_resolution.py` at the connect branch, and a **scaled retaliation
spawn** driven off a pending flag (the `process_hits` connect site has no `attack_group` handle, so
the retaliation must spawn on the next `Player.update`, mirroring `_pending_landing_spawn`).

The **mechanic shape is well-understood** and every primitive it needs already exists in the codebase
(intangibility, clank `_negate`, smash-charge `scale_hitboxes`). The **one un-pinned value** is the
PM 3.6 retaliation formula: SmashWiki's Marth (PM) text is internally contradictory (states both a
fixed 7% and "same damage and knockback of the attack being countered"), and this is **not datamine-
able** from the `.pac` (it is an engine/PSA value, like the smash-charge multiplier). That number
must be pinned against a specific primary quote **in the downstream ARC** before any value is authored.

**Recommendation: post-V1.** Counter is the most engine-invasive of Narz's specials (it adds a new
hit-resolution path, not just a hitbox), and its retaliation value is unresolved. Ship it after the
data-only / hitbox-only specials.

---

## Method

Two read-only sweeps of the worktree + the local PM/Melee sources, plus SmashWiki for the PM-specific
values:

- **Code seat** — traced the hit-resolution pipeline, intangibility model, fighter-state timed-window
  pattern, special-move dispatch, and hitbox-spawn path in `pycats/`.
- **In-repo source data** — audited `docs/` for existing Marth/Counter data and the datamine recipe's
  scope boundary.
- **Engine values** — read the Marth Counter implementation in **meleelight** (local, #616 — the
  Melee-literal reimpl) and fetched **SmashWiki** (Counterattack; Marth (PM)) for the PM-specific
  window + retaliation.

---

## 1. The mechanic (what Counter is)

Marth's down-B **Counter**: a brief stance that, if the fighter is struck during its active window,
**negates the incoming hit** and fires a **counterattack**. In Melee the counterattack is a fixed
value; PM widened the hitboxes and (per SmashWiki, with the caveat in §5) changed the retaliation.

Subaction structure (from `docs/pm-reference/marth-gif-index.md`): `SpecialLw` (stance) /
`SpecialLwHit` (riposte), with `SpecialAirLw` / `SpecialAirLwHit` airborne. Animation lengths there
are **60 / 37** frames — but these are *whole-animation* GIF lengths, **not** the counter-detection
window (that is a distinct engine/script value, see §5). Do not treat "60" as the window.

---

## 2. Where it seats in the code

### 2.1 Hit-resolution hook (`systems/hit_resolution.py`)

`process_hits(players, attacks)` is the single per-frame resolver. Frame ordering
(`screens/battle_screen.py::step`) is: all `Player.update(...)` → `resolve_player_push` →
`attacks.update` → `process_hits`. So **all FSM/fighter updates run before hits resolve**, and
`process_hits` is the only place a "was I hit this frame" signal exists.

Inside `process_hits`, the per-defender loop already has a **tangibility gate**:

```python
tang = resolve_tangibility(
    getattr(defender.fighter, "intangible", False),
    getattr(defender.fighter, "invincible_timer", 0) > 0,
)
if tang is Tangibility.INTANGIBLE or not defender.fighter.is_alive or defender is atk.owner:
    continue
```

and, when a hitbox connects (`if hit_box is not None:`), an application branch that already forks
`receive_hit_invincible` (INVINCIBLE: connects-but-zero) vs `receive_hit` (normal). **A counter is a
fourth path at this connect branch:** detect `defender.fighter.counter_active`, cancel the incoming
hit (mirror `_negate(atk)` / skip `receive_hit`), and flag a pending retaliation.

### 2.2 The retaliation spawn (deferred one frame)

`process_hits` has **no `attack_group` handle**, so it cannot spawn the counterattack directly. The
established pattern is a pending flag consumed on the next `Player.update` — exactly how
`_pending_landing_spawn` → `_spawn_move_hitbox(attack_group)` works today. The retaliation would set
e.g. `fighter.pending_counter_hit = <captured incoming params>` in `process_hits`, and a sibling of
`_spawn_move_hitbox` would spawn the `SpecialLwHit` attack next frame.

### 2.3 The counter window state (fighter + statechart)

Follows the **dodge/getup archetype** exactly:
- a timer field on `Fighter` (`counter_timer`, + a `counter_active` flag), like `dodge_timer`;
- a starter `Fighter.start_counter()`, like `_start_dodge` / `start_getup_roll`;
- a decrement in `tick_timers()` / `tick_action_timers()` (both called from
  `Player._tick_timers_and_getup`);
- a `counter` leaf in `charts/fighter_chart.py::build_fighter_chart` with
  `on("force_counter", "counter")` hoisted to the `action` compound, forced from `fighter_input`.

**Important:** do **not** reuse the `intangible` flag. `intangible` = pass-through with **no hit
registered** — the opposite of what Counter needs (Counter must *detect* the hit to scale from it).
The counter window is its own state that intercepts at the connect branch.

### 2.4 Dispatch (`combat/move_select.py`, `entities/fighter_input.py`)

`down_b` is **already a canonical special key** (`_SPECIAL["down"] = "down_b"`), and holding
down + special already resolves to direction `"down"`. But a pure data-move only spawns a hitbox;
Counter needs custom engine behavior, so `handle_actions` must either read a new `MoveData` flag
(precedent: `grants_recovery` / `chargeable` / `landing_spawn`) or special-case `key == "down_b"` to
call `Fighter.start_counter()` + `p.engine.force("force_counter")`.

### 2.5 Reusable primitives (all already in the codebase)

| Need | Existing primitive |
|---|---|
| Cancel an incoming hitbox | clank `_negate(atk)` in `hit_resolution.py` |
| "Connects but I'm unaffected" | INVINCIBLE `receive_hit_invincible` branch |
| Scale a retaliation hitbox's damage/KB | `scale_hitboxes(boxes, fraction)` (smash-charge path in `player.py::_spawn_move_hitbox`) |
| Deferred spawn off a pending flag | `_pending_landing_spawn` → `_spawn_move_hitbox` |
| Timed active window + intangibility | dodge / getup-roll timer + `intangible` archetype |

The scaled-retaliation requirement maps **directly** onto `scale_hitboxes` — the same primitive
smash-charge uses to scale a hitbox by a captured fraction.

---

## 3. The counter window model — options

**What it intercepts.** Three scopes, smallest first:
- **A — grounded melee hits only** (matches meleelight's Melee model; simplest). Projectiles and
  grabs pass or are ignored.
- **B — melee + projectiles** (reflect/absorb projectiles too). More engine surface: projectiles
  resolve through the same `process_hits` connect branch, so the detect hook covers them, but the
  "counterattack vs reflect-the-projectile" question opens up.
- **C — melee + projectiles + grabs.** pycats has **no grab system** (`docs/research-spec-290`
  lists grabs as deferred), so grab-countering is moot until grabs exist — **out of scope** by
  construction.

**Window timing.** meleelight (Melee literal) models the detect window via the clank system: the
detection hitbox is active `timer` **5–30** (`DOWNSPECIALGROUND.js`), the stance interrupts at
`timer > 59`, and on a successful counter (`onClank`) it transitions to `DOWNSPECIALGROUND2` with
`intangibleTimer = 16` and the riposte hitbox active `timer` **4–11**. SmashWiki Marth (PM) reports
PM intangibility on **frames 1–8** and a wider hitbox set. (Frame-numbering conventions differ
between the two sources — the ARC should pin one convention.)

---

## 4. Datamine reachability (why no fresh brawllib run)

`docs/tooling-brawllib-rs-datamine-recipe.md` datamines **per-character subaction scripts** — it can
give the `SpecialLwHit` riposte hitbox's own `damage/bkb/kbg/angle` and the animation frame lengths.
Its scope-boundary section is explicit that it does **NOT** expose **engine-hardcoded globals**
("smash charge duration/multiplier, air-dodge velocity, etc. live in the engine / common data, not in
subaction scripts"). **The counter-detection window and the retaliation formula behave exactly like
the smash-charge multiplier it names as out-of-scope** — so a fresh datamine cannot close the gap.
These route to meleelight / doldecomp / PM codeset / SmashWiki instead (per
`docs/pm-reference/where-to-find-source-data.md`).

`docs/research/pm36-fighter-attributes.csv` is movement attributes only — no Counter columns.

---

## 5. The retaliation value — the one open gap (must be pinned in the ARC)

The PM 3.6 retaliation formula is **not cleanly resolved** and **not in-repo**:

- **Melee** (SmashWiki *Counterattack*, verbatim): *"In Melee, Marth's Counter does 7%, regardless
  of the attack."* — a **fixed** 7%, not a multiplier.
- **meleelight** (Melee reimpl) uses a **fixed** riposte hitbox (`charHitboxes.downspecialground2`) —
  it does **not** scale from the intercepted hit, consistent with the fixed-7% Melee model. So
  meleelight gives the **window mechanics** but **not** any multiplier.
- **PM 3.6** (SmashWiki *Marth (PM)*): the fetched text is **internally contradictory** — it states
  both a fixed **7%** *and* *"the counterattack has the same damage and knockback of the attack being
  countered."* It also notes PM changes: larger/added hitboxes, transcendent priority, intangibility
  frames 1–8, and a **1.2× hitlag** multiplier.

This contradiction is a **grounding gap**, not a settled value. Per the cite-primary-not-inference
discipline (ADR-0003; #520→#537), the exact PM 3.6 retaliation (fixed vs mirrored vs scaled, and the
number/floor) must be pinned against a **specific primary quote** — PMDT changelog / PM codeset
(`~/Documents/Study/reference/Project-M-CC/`, #664) or a corroborated SmashWiki sentence — **before**
any value is authored. Whatever it resolves to gets a `FieldStatus`/`Status` in `combat/data.py`
(per-move data), or a `TUNING_PROVENANCE` row if it becomes a global scalar.

---

## 6. Option space + recommended shape

**Recommended shape (for the ARC to accept or amend):**
1. **Scope A** to start — grounded melee hits only (matches the Melee model; smallest engine surface).
   Leave projectile-countering (Scope B) as a follow-up; grab-countering (C) is moot until grabs exist.
2. **New `counter` fighter state** on the dodge/getup archetype (`counter_timer` + `counter_active`,
   `start_counter()`, chart leaf `force_counter`) — **do not** overload `intangible`.
3. **Detect-and-cancel** at the `process_hits` connect branch (fourth path beside INTANGIBLE-skip and
   INVINCIBLE-register); capture the incoming hit's params, `_negate`-equivalent the incoming hit, set
   a **pending retaliation flag**.
4. **Deferred retaliation spawn** on the next `Player.update` via a `_spawn_move_hitbox` sibling, using
   `scale_hitboxes` if the pinned value turns out to be a multiplier (or a fixed hitbox if it is fixed).
5. **Value gate:** the retaliation formula (§5) is pinned in the ARC against a primary quote before a
   DEV authors it.

**V1 vs post-V1:** the research recommendation was **post-V1** (Counter is the most engine-invasive of
Narz's specials — a new hit-resolution path plus a new fighter state, versus the data/hitbox-only
specials — and its central value is unresolved). **Human ruling (2026-08-04): Counter is V1.** The
open retaliation value (§5) therefore becomes a **V1 blocker** — it must be pinned in the ARC before
the DEV can author it, rather than being deferrable.

---

## 7. Out of scope (unchanged from the ticket)

- Building the mechanic or authoring values (downstream, after the mechanic is ruled).
- The sibling specials — the Shield Breaker ARC and the Dancing Blade spike.
- Grab-countering — no grab system exists.

---

## Refs

Umbrella #1058 · Narz epic #294 / scope #290 · hit resolution `systems/hit_resolution.py` · dispatch
`combat/move_select.py` + `entities/fighter_input.py` · spawn `entities/player.py::_spawn_move_hitbox`
+ `entities/attack.py` · tangibility `combat/tangibility.py` · state `entities/fighter.py` +
`charts/fighter_chart.py` · datamine recipe `docs/tooling-brawllib-rs-datamine-recipe.md` · source map
`docs/pm-reference/where-to-find-source-data.md` · subaction map `docs/pm-reference/marth-gif-index.md`
· provenance ADR-0003 · value routing #530 · meleelight #616 · PM codeset #664.

**Primary sources cited:** meleelight `src/characters/marth/moves/DOWNSPECIALGROUND{,2}.js` (Melee
literal) · SmashWiki *Counterattack* (Melee 7% fixed) · SmashWiki *Marth (PM)* (PM window/hitbox
changes; retaliation value **contradictory — flagged for ARC**).
