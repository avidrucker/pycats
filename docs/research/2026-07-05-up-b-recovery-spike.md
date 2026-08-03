# Spike — a generalized up-B / special-recovery mechanic (#574)

**Ticket:** #574 (spike; first child of #566 cluster B). **Role:** RESEARCH. **Date:** 2026-07-05. **Agent:** DRAGONFRUIT.
**Box:** ~60m. Scope the mechanic + name the seams + a DEV decomposition. *No implementation.*

---

## Recommendation (TL;DR)

**Build ONE generalized engine hook, reuse the existing `helpless` state (#184), then author per-cat up-B moves as data.** The plumbing is almost entirely already present — this is a small engine addition (a velocity burst + one statechart transition + a flag), not a new subsystem.

The mechanic, end to end:
1. Player presses up + special airborne → the special resolves to `up_b` (already wired, `move_select.py`).
2. If the resolved move is flagged a **recovery move**, apply an **upward velocity burst** (per-cat) and set a `recovery_active` flag.
3. The move plays its hitbox on the move clock (Super Jump Punch / Final Cutter / Dolphin Slash are *attacks* too — nothing new there).
4. When the move ends airborne, route to **`helpless`** (reuse #184) — locked out of actions, falling, until land or ledge-grab.
5. **Ledge-grab during recovery is FREE** — `player.py:343`'s ledge-grab gate does not exclude `helpless`, so a drifting helpless fighter already snaps to the ledge.

## Q1 — the model: generalized hook, not bespoke

Add a **recovery flag + burst params to `MoveData`** and a **generic apply step**, so any character's `up_b` (or any move) can be a recovery move by data alone:

- `MoveData.grants_recovery: bool = False` — **NOT** `recovery` (that name is already taken — `MoveData.recovery` is the move's end-lag frame count, `data.py:115`; reusing it would collide). Suggested names: `grants_recovery` / `is_up_special`.
- `MoveData.recovery_vy: float = 0.0` — the upward burst (negative = up, matching `jump_vel`).
- `MoveData.recovery_vx: float = 0.0` — optional horizontal component for an arc (Dolphin Slash is diagonal; Final Cutter near-vertical).

Per-character behaviour then lives entirely in the per-cat `up_b` MoveData (hitbox + these fields) — **generalized hook + per-cat values**, matching how the roster already differentiates everything else. Bespoke per-character code is not warranted; the only genuinely special cases (Kirby's weak multi-hit, a wall-jump-ish variant) are expressible as data or deferred.

## Q2 — integration seams (named, with file/line)

| Seam | File | Change |
|---|---|---|
| Data fields | `combat/data.py` (MoveData, ~L105–140) | add `grants_recovery` / `recovery_vy` / `recovery_vx` (defaults off → byte-stable for all existing move data) |
| Momentum apply | `entities/fighter_input.py` (special path, ~L290–306, next to the jump burst at `:174` `vel.y = jump_vel`) | on starting a special whose MoveData `grants_recovery`, set `vel.y = recovery_vy` (+ `vel.x`), and set `fighter.recovery_active = True` |
| Flag + reset | `entities/fighter.py` (mirror `air_dodge_active`, set near :381/:467/:490) | add `recovery_active`; clear on land / respawn exactly where `air_dodge_active` is cleared |
| Exit → helpless | `charts/fighter_chart.py` (mirror the air-dodge→helpless tick, ~L223–231) | when the recovery move's timer ends airborne + `recovery_active` → `helpless` (instead of `fall`) |
| Dispatch | `combat/move_select.py` | **none** — `_SPECIAL["up"]="up_b"` already routes it |
| Ledge-grab | `entities/player.py:343` | **none** — `helpless` is already not excluded, so recovery-into-ledge works |
| Action lock | `entities/fighter_input.py:172,290` | **none** — `helpless` already locks jump / attack / special (prevents recovery-chaining) |

The striking result: **only 4 of 7 seams need code**, and two of those are a field add + a flag reset. The `helpless` state (#184), the special dispatch, the ledge-grab, and the action-lock are all reused untouched.

## Q3 — composition

- **Jumps:** up-B does **not** consume a midair jump (`jumps_remaining` untouched); jumps refresh on land (`fighter.py:467`) as today. (PM: up-B is available regardless of jumps; helpless is the cost.)
- **Fast-fall (cluster C):** mutually exclusive — you cannot fast-fall while `helpless` (input gated). No conflict; fast-fall lands independently.
- **Ledge-grab:** free (above) — the recovery arc drifting into the ledge auto-snaps via the existing `force("ledge_grab")` at `player.py:440`.
- **Hitstun / edge-guard:** a hit during rise or helpless routes to `hurt`/`stun` (the `hitstun` region takes over), cancelling recovery — correct PM behaviour (recovery is interruptible).
- **Re-use lock:** a second up-B during `helpless` is already blocked (`fighter_input.py:290` excludes `helpless`) — no infinite recovery.

## Q4 — per-cat first values (source or defer)

The three up-Bs are real PM moves with sourceable data (SmashWiki / rukaidata), routed per #530 (likely research→DEV or DEV-citing-a-finding):
- **Nalio (Mario)** — *Super Jump Punch*: near-vertical, multi-hit, modest distance.
- **Birky (Kirby)** — *Final Cutter*: rise + descent-with-shockwave; Kirby's is a strong vertical.
- **Narz (Marth)** — *Dolphin Slash*: fast diagonal, disjoint sweetspot at the tip (fits the tipper identity, #290).

Exact `recovery_vy`/`vx` + hitbox values are **per-cat DEV children**, not this spike.

## Q5 — DEV decomposition (file one at a time under #566)

1. **ENGINE — recovery-move hook** (~50m). The MoveData fields + the momentum-apply + `recovery_active` flag + the statechart→helpless transition. Ships with a **generic test fighter** carrying a recovery `up_b` and a TDD test: airborne up-B sets `vel.y == recovery_vy`, state → `helpless` after the move, a second up-B is locked during helpless, and a helpless drift into a ledge grabs it. **Blocks 2–4.**
2. **DEV — Nalio up-B (Super Jump Punch)** — hitbox MoveData + sourced burst values. Blocked-by 1.
3. **DEV — Birky up-B (Final Cutter)** — blocked-by 1. (Retires part of #261 item 2.)
4. **DEV — Narz up-B (Dolphin Slash)** — blocked-by 1.

Value sourcing for 2–4 follows #530 (cite SmashWiki/rukaidata → FOUND, or a decision if no faithful number maps).

## Out of scope (unchanged)
The other three specials (neutral/side/down-B) except shared plumbing; grabs/throws (post-v1); fast-fall (cluster C) beyond the composition note above.

## Refs
Parent **#566** (cluster B) + v1 decision; assessment **#561**; **special-fall/helpless #184** (`fighter_chart.py:301`, the keystone reuse); Birky engine tracker **#261** (item 2); seams: `combat/data.py` (MoveData), `combat/move_select.py`, `entities/fighter_input.py:174/290`, `entities/fighter.py` (`air_dodge_active` pattern), `entities/player.py:343/440` (ledge-grab), `charts/fighter_chart.py:223/301`; value routing **#530**.
