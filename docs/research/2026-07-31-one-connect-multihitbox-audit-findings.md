# One-connect audit — does pycats enforce one hit per move-instance across a move's multiple hitboxes? (#943)

**Role:** RESEARCH (code-behavior audit, grounded in pycats source + executed evidence — not PM canon).
**Feeds:** #930 Fork 7 (one-connect V1 default). **Date:** 2026-07-31. **Agent:** ELDERBERRY.

## Question

#930 Fork 7 decided **one-connect** — one hit per move-instance against a target — as the V1
default. This audit determines whether pycats actually enforces it across a move's multiple
hitboxes, under which configurations a single move connects more than once, and whether any of
that is unintended.

## TL;DR

**One-connect for a plain move IS enforced, by two independent, able-to-fail guards.** A move
connects more than once against one target only in three deliberate, authored ways: separate
**temporal windows** (#204), a **`rehit_rate`** cadence (#213), or — the inverse — is collapsed
back to one hit by a shared **`set_id`** (#888). No unintended multi-hit path was found for a
plain (single-window, no-`rehit_rate`, no-`set_id`) move. The #879 double-hit offenders are all
fixed. Two side findings: a **stale code comment** in `process_hits`, and several **smash**
moves that multi-hit purely by current authoring (a canon question for #944).

---

## The enforcement site

All hit resolution is in `pycats/systems/combat.py::process_hits`, which loops
`for atk in attacks: for defender in players:`. The one-connect behavior rests on three guards,
each isolated and revert-checked below.

### Guard A — first-box-wins within one frame (multi-box, single window)

```python
hit_box = next((box for (cx, cy, r, box) in boxes if circles_overlap(...)), None)
if hit_box is not None:
    ... receive_hit ...
    break
```

`boxes` is the move's priority-ordered hitbox list (`atk.resolved`, #130). `next()` selects the
**first** overlapping box only; a defender overlapping two boxes of the same move takes **one**
hit, from the higher-priority box. This is `PYC-C-003-GRAPE`.

**Revert-check (executed, #943):** replacing the `next()` short-circuit with a loop that applies
**every** overlapping box (removing the first-box-wins and the trailing `break`) makes
`tests/test_multi_hitbox.py::test_overlapping_boxes_hit_once_in_priority_order` red —
`assert defender.hits_received == 1` fails with **`assert 2 == 1`**. Restored immediately (no
residual diff). This is the `red-on` pin `PYC-C-003` previously lacked.

### Guard B — one connect per move-instance across frames

```python
elif atk.disappear_on_hit:
    atk.kill()
else:
    atk.active = False   # only one hit allowed
```

After a connect, a non-looping Attack is deactivated (or killed), so it cannot connect again on
later frames of its own active window.

**Revert-check (executed, #943):** replacing `atk.active = False` with `pass` makes
`tests/test_rehit_rate.py::test_non_looping_attack_hits_once` red — the 20-frame-lifetime plain
Attack re-hits every frame: **`assert 20 == 1`**. Restored immediately.

### Guard C — set_id dedup across a move's temporal windows (B-full, #888)

Different temporal windows (#204) spawn **separate** `Attack`s (see below), so without further
help a stationary target would be hit once per window. B-full dedup consults the owner's
per-move-instance registry:

```python
set_id = getattr(hit_box, "set_id", None)
if set_id is not None:
    registry = getattr(atk.owner, "hit_registry", None)   # -> MoveClock.hit_registry
    if registry is not None:
        already = registry.setdefault(set_id, set())
        if id(defender) in already:
            continue          # same set already hit this target
        already.add(id(defender))
```

`Player.hit_registry` delegates to `MoveClock.hit_registry` (`pycats/entities/player.py`), which
`MoveClock.start()`/`reset()` clears — so a `set_id` integer is scoped to one move-instance and
shared across that move's windows' Attacks. Boxes sharing a `set_id` hit a target **once**; a
different `set_id`, or `None`, re-hits. This is `PYC-C-003`/`PYC-C-005`'s resolution knob.

**Able-to-fail (existing, verified green):**
`tests/test_bfull_ground_hit_once.py::test_engine_dedup_is_what_changed` drives the same synthetic
two-window move: `set_id=None` → **2 hits**, shared `set_id=1` → **1 hit**. Over-reach reddens the
2-hit half; an ignored `set_id` reddens the 1-hit half.

---

## Q1 — Same-window, multiple boxes: ≤1 connect per target? **Yes (verified).**

Guard A + Guard B. `PYC-C-003` confirmed, and its owed `red-on` revert-check is now executed
(Guard A above). Standing regression tests: `test_multi_hitbox.py`
(`test_overlapping_boxes_hit_once_in_priority_order`, `test_non_first_hitbox_can_connect`),
`test_rehit_rate.py::test_non_looping_attack_hits_once`.

## Q2 — Different windows (separate Attacks): can both connect, and is it intended?

**Yes, both connect against a stationary target — by design.** `MoveClock._compute_windows`
groups hitboxes by their `[active_start, active_end]` window and fires each on its own start
frame; `player.py` spawns **one `Attack` per window** (Design B, #951, may spawn several on one
start frame via `extra_spawns`). Separate Attacks each carry the one-connect guards **individually**,
so absent a shared `set_id` a two-window move deals two hits (`PYC-C-005-GRAPE`). This is the
intended substrate for sequential multi-hit moves (jab1→jab2, multi-hit aerials).

**#852 disposition:** this audit **executes** the 2-window→2-hits scenario as evidence
(`test_engine_dedup_is_what_changed`'s `set_id=None` half, and the enumeration below). Whether a
**standing regression test on a shipped 2-window move** is owed remains **#852's** scope (still
OPEN) — not absorbed here.

## Q3 — The #879 double-hit: same mechanism? State of #883/#888? Guarded?

**Yes — #879 was exactly this mechanism** (the #204 per-window model spawning a separate Attack
per clean/late window, double-hitting a stationary target). Resolved two ways, both with
able-to-fail guards:

- **Flatten (#911, ruling #893):** the 5 lingering aerials (`nalio.bair`/`uair`,
  `birky.nair`/`bair`/`uair`) collapsed to **one** window over the full active span, with
  placeholder averaged values (marked `human-designer-temporary-placeholder-values-for-v1-only`).
  Guard: `tests/test_flatten_lingering_aerials.py` (one-window + one-spawn + one-hit, revert-red).
- **B-full set_id (#888, ruling #883, narrowed by #893):** birky's 4 ground clean/late moves
  (`utilt`, `fsmash`, `usmash`, `dsmash`) keep two windows but tag every box `set_id=1`, so the
  set hits once. Guard: `tests/test_bfull_ground_hit_once.py` (data + engine, revert-red).

`#883` (ARCHITECT ruling) and `#888` (DEV impl) are both **CLOSED**. The #879 offenders were
re-verified in current shipped data: `birky.nair` and `nalio.bair` are now single-window (1 hit);
`birky.utilt` is two-window `set_id=1` (1 hit). All fixed.

## Q4 — Any unintended multi-hit path? **None for a plain move.**

Q4 as scoped asks about a **plain** (single-window, no-`rehit_rate`) move. Guards A + B enforce
one hit there, both revert-checked. No configuration of box count, geometry, or facing defeats
them (facing only re-resolves circle centres; the registry keys on `set_id` + `id(defender)`,
facing-independent; multiple Attacks sharing a `set_id` dedup order-independently within a frame
via the shared registry).

Multi-hit therefore occurs **only** through the three deliberate mechanisms. Full census of every
shipped move that connects more than once, or loops, or is deduped (driven through `MoveClock` +
`process_hits`):

| Move | windows | set_id | rehit_rate | connects | mechanism |
|------|:---:|:---:|:---:|:---:|-----------|
| `birky.utilt` | 2 | 1 | — | **1** | set_id dedup (#888) |
| `birky.fsmash` | 2 | 1 | — | **1** | set_id dedup (#888) |
| `birky.usmash` | 2 | 1 | — | **1** | set_id dedup (#888) |
| `birky.dsmash` | 2 | 1 | — | **1** | set_id dedup (#888) |
| `nalio.dair` | 2 | — | 4 | loop | rehit cadence (#213) |
| `birky.dair` | 1 | — | 3 | loop | rehit cadence (#213) |
| `gnok.jab` | 2 | — | — | **2** | independent windows (#204) |
| `gnok.nair` | 2 | — | — | **2** | independent windows (#204) |
| `gnok.fair` | 2 | — | — | **2** | independent windows (#204) |
| `gnok.bair` | 2 | — | — | **2** | independent windows (#204) |
| `birky.fair` | 3 | — | — | **3** | independent windows (#204) |
| `nalio.fair` | 2 | — | — | **2** | independent windows (#204) |
| `nalio.usmash` | 2 | — | — | **2** | independent windows (#204) |
| `nalio.dsmash` | 2 | — | — | **2** | independent windows (#204) |
| `narz.dsmash` | 2 | — | — | **2** | independent windows (#204) |

(Every move not listed is single-window, no set, no rehit → one hit.) No move carries a **mixed**
`set_id` (some boxes tagged, some not) — set tagging is well-formed everywhere.

**These multi-window/no-set_id hits are authoring, not engine leaks** — the engine does exactly
what #204 specifies. Whether each move's **canonical hit count** is right (should `nalio.fair`
hit twice? should smashes multi-hit at all?) is a **PM-parity** question and is **out of scope**
here → it is #944's remit. Flagged as candidates worth #944 scrutiny, without ruling:
`nalio.usmash`, `nalio.dsmash`, `narz.dsmash` (single-strike smashes that currently deal two
hits), and `nalio.fair` (a Melee/PM Mario fair is a single strong hit). `gnok.jab` (DK's
two-hit jab) and `birky.fair` (Kirby's three-hit fair) read as canonically intended.

---

## Side findings (candidate follow-ups — filed one at a time, downstream)

1. **Stale comment in `process_hits`.** The Guard-C block comments read *"set_id is None on every
   existing move, so this branch is inert until a move is authored with sets (golden-safe)."* This
   is now **false** — `birky.utilt`/`fsmash`/`usmash`/`dsmash` ship `set_id=1` and the branch is
   live (it is what makes them hit once). Doc-only drift; a one-line comment fix. Candidate DEV.
2. **Single-hit move hits at most one defender (multi-target simplification).** After the first
   connect, Guard B deactivates the Attack, so a plain move cannot hit a **second** overlapping
   defender in the same frame (the `break` exits the defender loop and `atk.active=False` ends the
   Attack). This is the one-connect-per-*target* invariant working as intended, but it also caps a
   move at one *target* total — a possible multi-target parity gap (Melee hitboxes hit all
   overlapping targets). **Out of scope** for #943 (one-connect-per-target), recorded for
   visibility; a parity question if pursued.

## Conclusion for #930 Fork 7

**One-connect (one hit per move-instance per target) is genuinely enforced** for plain moves, by
two independent guards now both pinned able-to-fail, plus a set_id dedup for authored clean/late
multi-window moves. Multi-hit exists only where an author asked for it (temporal windows or
`rehit_rate`). Fork 7's "one-connect default" holds in the code as decided. The remaining open
threads are parity/authoring (#944), a test-coverage gap (#852), and a stale comment — none of
which contradict the default.

## Cross-refs

#930 (Fork 7) · `PYC-C-003`/`PYC-C-005`/`PYC-C-004` (unverified-claims ledger; location per the
#946 relocation caveat) · #130 (multi-hitbox ≠ multi-hit) · #204 (temporal windows) · #213
(rehit-rate) · #879/#883/#888/#911 (double-hit defects, ruling, fixes) · #893 (designer ruling) ·
#951 (Design B same-start windows) · #852 (2-window-deals-2-hits standing test — still owed there)
· #944 (post-V1 dash/multi-hit parity) · `pycats/systems/combat.py::process_hits` ·
`pycats/combat/move_clock.py::MoveClock` · `pycats/entities/player.py` (`hit_registry`).
