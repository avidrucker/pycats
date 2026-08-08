# Findings — does a single move's sequential hit-windows re-hit the same target in PM 3.6?

> **Ticket:** #879 (RESEARCH, `area:combat`). **Date:** 2026-07-28. **Agent:** GRAPE.
> **Canon:** Project M 3.6. **Status:** FOUND (primary-grounded).
> Part of the parity doc set — front door: [`../project-m-parity.md`](../project-m-parity.md).
> Downstream of the #807 combat-claims audit; sibling of #829/#843. Feeds a downstream
> ARCHITECT decision (see "Next steps"). Unblocks #852 / the PYC-C-005 outcome half in #872.

## Question

Within a **single move**, when its hitboxes are active across more than one window
(an early + late "sex kick", or a jab that continues into a second hit), does PM 3.6
let those windows **re-hit the same target**, or is there a per-target hit-ID that makes
them mutually exclusive? And does pycats' current model match?

## Answer (short)

**PM 3.6 tracks "already hit" per attacker, and a move re-hits a given target only when
its hitbox *set* is emptied (all boxes deleted) and re-created — or an explicit rehit
fires. A hitbox that stays present and merely changes its damage over frames (the
sex-kick early→late transition) does NOT re-hit: the target takes the clean hit *or* the
late hit, never both.** A jab combo hits the same target twice because **jab1 and jab2 are
separate subactions**, each with a fresh hit-list — not because one subaction has two windows.

**pycats diverges for lingering aerials.** pycats models every temporal window (#204) as a
**separate `Attack`** with independent per-`Attack` hit tracking and **no per-target hit-ID
shared across a move's windows**, so a stationary target overlapping both windows of a
two-window move takes **two** hits. That is correct for a multi-hit drag (fair) or a jab,
and **wrong for a sex kick** (birky nair, birky utilt), which in canon hits once.

## The canonical mechanism (primary-grounded)

Two layers: the **data** rule (what the PM 3.6 `.pac` subaction scripts encode) and the
**engine** rule (how the runtime applies it).

### Data layer — a hitbox belongs to a *set*, and re-hit needs an empty→create

`brawllib_rs` runs the actual PM 3.6 subaction scripts. On every `CreateHitBox`, it decides
whether that hitbox *set* is allowed to re-hit — verbatim (`src/script_runner.rs`,
`EventAst::CreateHitBox`, ~L1000, `@` brawllib_rs HEAD, read 2026-07-28):

```rust
// Force rehit if no existing hitboxes.
// Both DeleteAllHitboxes and DeleteHitbox on the last hitbox will trigger rehit.
// http://localhost:8000/PM3.6/Squirtle/subactions/SpecialHi.html?frame=11
let mut empty_set = true;
for hitbox in self.hitboxes.iter().filter_map(|x| x.clone()) {
    if let CollisionBoxValues::Hit(hitbox) = hitbox.values
        && hitbox.set_id == args.set_id
    {
        empty_set = false;
    }
}
if empty_set
    && let Some(rehit) = self.hitbox_sets_rehit.get_mut(args.set_id as usize)
{
    *rehit = true;
}
```

So the re-hit flag for a set (`hitbox_sets_rehit[set_id]`) is turned on **only** when a
`CreateHitBox` for that set happens while the set is currently **empty** (its boxes were all
deleted). A `CreateHitBox` that **overwrites** a still-present box of the same set (the
sex-kick early→late transition) leaves `empty_set == false` → **no rehit** → one hit.

### Engine layer — one shared "already-hit" list per attacker, reset at boundaries

`meleelight` implements the runtime hit-resolution state machine. The "already hit" list is
**per attacker**, checked **once per victim before any hitbox is tested** — verbatim
(`src/physics/hitDetection.js`, `hitDetect`, ~L29, read 2026-07-28):

```js
// check if victim is already in hitList
var inHitList = false;
for (var k = 0; k < player[p].hitboxes.hitList.length; k++) {
    if (i == player[p].hitboxes.hitList[k]) { inHitList = true; break; }
}
if (!inHitList) { /* ...only now are p's hitboxes tested against victim i... */
    // on a connect:  player[p].hitboxes.hitList.push(i);
}
```

The list is cleared by `turnOffHitboxes`, which runs at move/action-state boundaries
(`src/physics/actionStateShortcuts.js`, ~L180, read 2026-07-28):

```js
export function turnOffHitboxes (p){
  player[p].hitboxes.active = [false,false,false,false];
  player[p].hitboxes.hitList = [];
}
```

and a single victim is spliced back out when a rehit is due
(`hitDetection.js`, `checkPhantoms` / rehit path, ~L1112). Net rule: **a target is hit at
most once per continuous hitbox lifetime; re-hit needs a set empty→create, an explicit
rehit timer, or crossing into a new subaction (which resets the list).**

## The two shipped structures, from PM 3.6 data

| Case | PM 3.6 structure (primary) | Same target hit… |
|---|---|---|
| **Lingering aerial** — Kirby `AttackAirN` | one subaction; `CreateHitBox` set 0 at **f3** (dmg 12) and again at **f9** (dmg 9) with **no `DeleteAllHitBoxes` between** — only at f29 (move end). Overwrite → `empty_set` false → no rehit. | **once** (clean XOR late) |
| **Lingering utilt** — Kirby `AttackHi3` | one subaction; `CreateHitBox` set 0 at **f4** (dmg 8) and again at **f8** (dmg 6), **no delete between** — only at f10 (end). | **once** |
| **Jab combo** — `Attack11`/`Attack12`/`Attack13` | **separate subactions** (rukaidata groups them under a distinct "Jabs" section; roster-wide naming). Each is a fresh subaction → fresh hit-list. | **multiple** (intended) |

Sources: rukaidata PM3.6 verbatim script events (Kirby `AttackAirN`, `AttackHi3`; jab
subaction split confirmed on the character-general `Attack11`/`Attack12` scheme, read
2026-07-28), applied through the `brawllib_rs` re-hit rule above.

## How pycats models it — and where it diverges

pycats' `MoveClock` (`pycats/combat/move_clock.py`) groups a move's hitboxes into temporal
windows by `(active_start, active_end)` and **spawns each window as a separate `Attack`** on
its start frame (`tick`). `process_hits` (`pycats/systems/combat.py`) then enforces "one hit
per `Attack` per target" — but **each window is its own `Attack`**, and there is **no
per-target hit-ID shared across a move's windows**. So N windows over one target → up to N hits.

| pycats move | Structure | pycats hits a stationary target | PM 3.6 | Verdict |
|---|---|---|---|---|
| `_BIRKY_NAIR` (`birky_cat.py`) | 2 windows: early f3-6 dmg 12, late f7-29 dmg 9 | **2** (12 + 9 = 21%) | **1** (Kirby `AttackAirN` overwrite) | **DIVERGENCE** |
| `_BIRKY_UTILT` (`birky_cat.py`) | 2 windows: early f4-5 dmg 8, late f6-10 dmg 6 | **2** (8 + 6 = 14%) | **1** (Kirby `AttackHi3` overwrite) | **DIVERGENCE** |
| `_NALIO_BAIR` (`nalio_cat.py`) | 2 windows: clean f6-8, late f9-17 (Sakurai) | **2** | **1** (Mario `AttackAirB` clean→late sex kick) | **DIVERGENCE** |
| `_GNOK_JAB` (`gnok_cat.py`) | 2 windows: jab1 f3-6, jab2 f10-14 | **2** | **2** (separate subactions) | matches — but by coincidence of model, not structure |
| `_BIRKY_FAIR` (`birky_cat.py`) | 3 windows (WDSK drag hits + finisher) | **3** | **multi** (drag/linking multihit) | matches (genuine multihit) |

The birky nair/utilt window timings mirror the Kirby subactions they cite, so the double-hit
is an **unintended fidelity gap**, not a designed two-hit move. In live 1v1 it is usually
masked — the early hit's knockback removes the target before the late window — but a
stationary or knockback-immobile target (exactly #852's setup) eats both.

**The architectural crux:** pycats has **one** authoring construct (per-box temporal windows
on one `MoveData` → independent `Attack`s) that is forced to represent **two canonically
distinct** structures — a continuous-hitbox **one-hit** lingering aerial and a
separate-subaction / delete→recreate **multi-hit** move. Its model always behaves like the
multi-hit one, so it is wrong for the sex kick. pycats already has the canonical primitive in
`rehit_rate` (mirrors `hitbox_sets_rehit`), but no notion of a per-target hit-ID / hitbox
**set** shared across windows.

## Falsifiable restatement

- **FALSE if:** a PM 3.6 lingering aerial re-hits a target that stays inside both its clean
  and late windows (would need a `DeleteAllHitBoxes` between the windows, or an explicit
  rehit). The Kirby `AttackAirN`/`AttackHi3` scripts show no such delete → one hit.
- **DIVERGENCE holds if:** pycats' birky nair deals two hits to a target overlapping both
  windows. `MoveClock` spawns two `Attack`s and `process_hits` has no cross-`Attack`
  per-target dedup → it does. (This is what #852 would pin — see below.)

## Next steps (downstream, file one at a time — NOT filed by this ticket)

1. **ARCHITECT decision** — filed as **#883**: how should a move express that its windows
   **share** a per-target hit-ID (one hit — sex kick) vs. are **independent** hits (jab /
   drag multihit)? Candidate models for the architect to weigh — *not decided here*:
   - **(A) per-move-instance hit-ID** — a single `MoveData` never hits a target twice across
     its windows; author jab combos as separate moves / a chained move.
   - **(B) per-hitbox set + rehit flag** — mirror Brawl's `set_id` + `hitbox_sets_rehit`:
     windows in the same set share the hit-list (sex kick = one set → one hit); a jab / drag
     uses distinct sets or a rehit (→ multiple). Most canon-faithful; reuses `rehit_rate`.
   - **(C) accept the divergence for V1** — knockback masks it live; document it and defer.
2. **#852** — its asserted `hits_received == 2` is canon-**wrong** for a sex-kick move; retarget
   to the decided count (or supersede) once (1) lands. Already flagged on #852.
3. **Lingering-aerial over-hit** — a candidate fidelity bug in **`_BIRKY_NAIR`, `_BIRKY_UTILT`,
   `_NALIO_BAIR`** (all canon one-hit sex kicks that pycats double-hits); gated on the (1)
   decision — file as a DEV/bug ticket after the model is chosen (don't fix ahead of the
   decision). Audit *all* two-window moves at that point: a two-window move diverges only if
   canon intends **one** hit (sex kick); genuine multihits (`_BIRKY_FAIR` drag, jab combos)
   are correct as independent windows.

## Evidence map

Add a row to [`../project-m-rules-by-category.md`](../project-m-rules-by-category.md) →
Hit-resolution: *"Same-move re-hit / hitbox-set hit-ID — a hitbox set hits a target once;
re-hit needs set empty→create or explicit rehit; sex-kick overwrite = one hit"* — **FOUND**,
sources brawllib_rs `script_runner.rs` + rukaidata Kirby `AttackAirN`/`AttackHi3` + meleelight
`hitDetection.js`; pycats **DIVERGENCE** for lingering aerials (this doc).
