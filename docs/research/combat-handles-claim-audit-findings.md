# Combat "handles X" claim audit — findings (#807)

**Ticket:** #807 · **Date:** 2026-07-21 · **Agent:** GRAPE · **Codebase:** @346e3d0

## The claim under audit

A Claude agent asserted that pycats already *"handles timing, multi-hit moves,
and attacks bouncing off each other."* That one sentence bundles three combat
sub-claims stated too vaguely to confirm or refute. This audit splits it into
falsifiable, testable propositions, checks each against the source + existing
tests, and reports which parts of the agent's phrasing hold, which are
ambiguous, and which overstate what is implemented.

## Method

Ran the `verify-claims` lifecycle. Each sub-claim was decomposed into
full-sentence, falsifiable propositions, each run through the 11-criterion
admission rubric and admitted to the `battle-mechanics` ledger topic as
`PYC-C-001..007-GRAPE` (`unverified`). Evidence was gathered against the source
and the existing test suite (green at @346e3d0, 1404 passing). **No claim
carries a TRUE/FALSE verdict yet** — verification (the red-green non-vacuous
check + human ratification) is a separate, human-gated pass (see *Next steps*).
The ledger itself is git-excluded; this doc graduates the durable conclusions.

## Bottom line

| Sub-claim | Verdict shape | One-line reason |
|---|---|---|
| (a) "handles timing" | **Accurate** | Two well-tested mechanics: frame windows + hitlag freeze. |
| (b) "multi-hit moves" | **True but ambiguous** | The everyday multi-*hitbox* move hits a target **once**; real multi-hit lives in two *other* mechanisms. |
| (c) "attacks bouncing off each other" | **Overstated** | Clank exists but only **cancels** hitboxes — there is no rebound/bounce. |

## (a) "handles timing" — accurate

Two independent, well-covered mechanics answer the vague word "timing":

- **`PYC-C-001` — frame windows.** Every move runs on a 3-phase clock
  (`MoveClock`, `combat/move_clock.py`): startup → active → recovery. The hitbox
  is live only during the active phase (`startup < frame ≤ startup+active`) and
  the move goes inactive at `frame ≥ startup+active+recovery`.
  *Evidence:* `tests/test_move_clock.py` executes both boundaries
  (`test_hitbox_spawns_exactly_once_on_first_active_frame`,
  `test_completes_at_total_then_ticks_are_noops`). *Scope:* this is the
  **default** window; per-box timing (#204) can override it.
- **`PYC-C-002` — hitlag freeze.** A connecting hit freezes **both** fighters
  for `combat/knockback.py:hitlag_frames(damage) = min(30, floor(damage×0.3846154+5))`
  frames, holding position/velocity/hitstun during the freeze.
  *Evidence:* `tests/test_hitlag.py` (formula reference values + cap + both-freeze
  + held-during-freeze). *Scope:* the per-move (h), electric (e), crouch-cancel
  (c) multipliers are all 1 today (#138).

## (b) "multi-hit moves" — true but ambiguous

"Multi-hit" collapses **three distinct mechanisms**, and the most intuitive one
does *not* multi-hit a single target:

- **`PYC-C-003` — multi-HITBOX ≠ multi-hit.** A move can carry several hitbox
  circles at once (#130), but only the **first** overlapping box (priority
  order) registers and the target is hit **exactly once**
  (`systems/combat.py:process_hits` `break`s after the first connect).
  *Evidence:* `tests/test_multi_hitbox.py`. This is the load-bearing correction:
  under the naive reading, "multi-hit" is **false** for a single target.
- **`PYC-C-004` — looping rehit.** A move/`Attack` with `rehit_rate=N` (#213)
  re-connects on a fixed N-frame cooldown across its active window — **real**
  multi-hit against one target, wired into nalio's d-air drill (`rehit_rate=4`)
  and birky (`rehit_rate=3`). *Evidence:* `tests/test_rehit_rate.py`. *Caveats:*
  the cooldown is per-`Attack` (global), not a per-target hit-ID list (→ #843,
  `post-v1`); the `rehit_rate` values are `⚠ playtest` guesses, not measured.
- **`PYC-C-005` — sequential windows.** One move can open its hitboxes across
  different frame windows (#204), each spawning a separate `Attack` on its start
  frame. *Evidence:* `tests/test_temporal_windows.py` proves the **spawning**; a
  target actually *taking* N hits is inferred (compose with `PYC-C-003`) and not
  yet directly tested (gap-closing test → #852).

So "handles multi-hit moves" is **true under `PYC-C-004`/`PYC-C-005`** and
**false** if one means "a multi-hitbox move hits a target multiple times."

## (c) "attacks bouncing off each other" — overstated

The clank mechanic exists, but "bouncing" describes behavior that is not built:

- **`PYC-C-006` — clank/priority exists.** Two overlapping active **ground**
  hitboxes of different owners are compared by a ≤9% damage window
  (`config.CLANK_PRIORITY_RANGE = 9`, sourced from SmashWiki "Priority") in
  `systems/combat.py:_resolve_clanks`: within 9% both end, else the stronger
  survives; aerials never clank. *Evidence:* `tests/test_clank.py` (5 tests).
  Notably the `9%` is the one **sourced** constant in this cluster (vs the
  `⚠ playtest` rehit values).
- **`PYC-C-007` — clank only cancels; there is no bounce.** On a clank, the only
  effect is that the losing/tied hitbox **ends** (`_negate` = `kill()` or
  `active=False`); `_resolve_clanks` sets **no** rebound, clank freeze/hitlag, or
  bounce-back on either fighter. *Evidence (query):*
  `grep -rniE 'rebound|bounce|recoil|clank.*freeze' pycats/systems/combat.py
  pycats/entities/fighter*.py pycats/combat/` finds only the `_negate` docstring
  ("no rebound state/freeze yet — #38"); every real "bounce" in pycats is a
  projectile off a platform (`Projectile.update`, #266) — a **different**
  mechanic and the likely source of the conflation.

So sub-claim (c) as worded is **not implemented**: the behavior is cancellation,
not bouncing.

## Divergence / open questions spun out (one ticket at a time)

| Ticket | Scope |
|---|---|
| #825 | Full hitlag mechanics across scenarios (multipliers, shield, invuln/intangibility, clank) — canon vs pycats |
| #829 | How canon resolves multiple hitboxes of one move overlapping a single hurtbox same-frame (damage/knockback/priority) vs pycats priority-only |
| #843 | *(post-v1)* Can a single attack hit multiple targets in PM? per-target hit-ID list vs pycats' per-`Attack` cooldown |
| #869 | Exact PM 3.6 clank/priority mechanics (window, transcendent priority, projectiles) — Brawl fallback |
| #871 | Do clanking attacks rebound/freeze fighters in PM, or only cancel? — the `PYC-C-007` gap |
| #852 | *(test)* A 2-window (#204) move deals TWO hits to a stationary target via `process_hits` — closes the `PYC-C-005` evidence gap |

## Next steps

1. **Red-green verification pass** (follow-up ticket) — for each `PYC-C-00N`,
   establish a `red-on` pin (revert-check that the cited test/query goes red
   without the behavior) to prove non-vacuity, then human-ratify TRUE/FALSE.
   Until then all seven stay `unverified`.
2. The six spun-out tickets above are filed and independent; work them one at a
   time downstream of their own findings.

## Artifacts

- Ledger topic: `claims-data/battle-mechanics/` — `PYC-C-001..007-GRAPE`
  (git-excluded; this doc is the committed graduation).
- Source audited @346e3d0: `systems/combat.py`, `combat/move_clock.py`,
  `combat/knockback.py`, `entities/attack.py`, `combat/data.py`.
- Tests cited: `test_move_clock.py`, `test_hitlag.py`, `test_multi_hitbox.py`,
  `test_rehit_rate.py`, `test_temporal_windows.py`, `test_clank.py`.
