# Sim duration & termination semantics — findings (#708)

**Date:** 2026-07-20 · **Agent:** FIG · **Role:** RESEARCH · `area:watch`
**Follow-up to** #703 · **feeds** #684 (round-robin CPU-vs-CPU balance sim).

Maps what determines how long a headless sim/demo battle runs, and exactly how it
ends. Every claim is grounded in a `file :: symbol` citation; the cap-with-no-KO
outcome (Q2) is read from the code, not inferred, and confirmed by measurement (Q3).

## TL;DR

- There is exactly **one termination site**: the frame loop in
  `pycats/sim/runner.py :: run_battle` — `for f in range(frames)` with a single
  early-exit, `if stop_on_match_over and match.phase == "match_over": break`.
- So a run ends on **whichever comes first** of: (a) **frame-cap exhaustion**
  (always present; `frames` is finite per mode), or (b) a **KO-out** — a player's
  `fighter.lives` reaching 0 — but only when `stop_on_match_over=True`.
- **Termination is guaranteed** (the frame cap is always finite). **Resolution is
  not** — a match can hit the cap with **no winner** (`match.winner == 0`). There is
  **no tie / sudden-death / percent adjudication anywhere**; the cap is a bare stop.
- Measured: **same-level matchups (L1vL1, L5vL5, L9vL9) run the full 30 s cap and
  return `winner=0`** even with a lopsided percent lead; only **asymmetric** pairings
  KO-resolve within 30 s. **#684 must impose its own deterministic tiebreak** — it
  cannot read `match.winner` alone.

---

## Q1 — Every termination condition, per mode

The loop and its only exits — `pycats/sim/runner.py :: run_battle`:

```
for f in range(frames):          # (a) frame-cap exhaustion — always terminates
    ... sim step ...
    match.tick()
    ...
    if stop_on_match_over and match.phase == "match_over":   # (b) KO-out early-exit
        break
```

`frames` and `stop_on_match_over` are set by mode. Scripted-replay/`--vs`/`--match`
resolution is `watch.py :: resolve_battle_plan`; `--demo` and leveled are inline in
`watch.py :: main`. Caps are `watch.py :: VS_FRAMES / MATCH_FRAMES / REPLAY_FRAMES`.

| Mode | `frames` (cap) | `stop_on_match_over` | Terminates on |
|---|---|---|---|
| scripted replay (default) | `--frames` or `REPLAY_FRAMES` = **300** (~5 s) | **False** | frame cap **only** (KO never exits early) |
| `--demo <name>` | `--frames` or `demo_frames(demo)` or `len(frame_inputs)` | **False** | frame cap **only** (choreography length) |
| `--vs chase\|idler\|follower` | `--frames` or `VS_FRAMES` = **1800** (30 s) | **True** | cap **or** KO-out |
| leveled (`--p1-level`/`--p2-level`, overrides `--vs`) | `--frames` or `VS_FRAMES` = **1800** | **True** | cap **or** KO-out |
| `--match` | `MATCH_FRAMES` = **6000** (~100 s); **ignores `--frames`**) | **True** | cap **or** KO-out |

**The KO-out condition** (the `match_over` early-exit):
`pycats/systems/match_engine.py :: StatechartMatchEngine` transitions `in_play →
match_over` on the first `tick` where `pycats/systems/win_condition.py ::
winner_index(players) != 0`. `winner_index` is purely `fighter.lives`-based: it
returns `2` if `p1.lives <= 0`, `1` if `p2.lives <= 0`, else `0` (p1 checked first,
so a same-frame double-out resolves to player 2).

**How lives reach 0 ("3-stock KO-out"):** lives start at
`pycats/config.py :: INITIAL_LIVES = 3`. Each frame,
`pycats/entities/player.py :: Player.update` calls
`fighter._outside_blast_zone()` and, if true, `fighter._ko()`
(`pycats/entities/fighter.py`), which does `self.lives -= 1`, sets
`is_alive = False`, and starts `respawn_timer = RESPAWN_DELAY_FRAMES` (2 s). Respawn
is gated on `lives > 0` (`Player.update`: `if respawn_timer <= 0 and lives > 0`), so
the **3rd** KO (lives → 0) never respawns — the fighter stays dead off-screen,
`winner_index` fires, and the match resolves. Blast zone is screen-coupled:
horizontal `BLAST_PADDING_X = 100` (temporary, #733), vertical `BLAST_PADDING = 50`.

## Q2 — Cap-with-no-KO outcome (definitive, from code)

**No winner. No tie. No sudden death. No percent adjudication. A bare stop.**

When `range(frames)` exhausts with both players still `lives > 0`:
`winner_index` has returned `0` every tick, so `match_engine` never left `in_play`;
`run_battle` returns `snaps` with the final snapshot carrying `match.phase ==
"in_play"` and `match.winner == 0`. Nothing anywhere inspects percent, stocks
remaining, or damage dealt at the cap — grep of `pycats/systems/` and
`pycats/sim/` shows the only win rule is `win_condition.winner_index`, and it is
lives-only. **A balance sim reading `match.winner` gets `0` on every unresolved
match, with no built-in way to pick a winner.**

## Q3 — CPU-level effect on duration (measured)

Method: ran `run_battle(frames=VS_FRAMES=1800, controllers=(AttackerController(L),
AttackerController(L)), stop_on_match_over=True)` headless, default cat vs default
cat, seeds 1–3, reading the final snapshot's `phase` / `winner` / `lives` / `percent`.
(Throwaway script, not committed.) `ran` = frames actually executed.

```
cap=1800f (30s), INITIAL_LIVES=3
pair    seed  ran   sec   end  winner  lives(p1/p2)  pct(p1/p2)
L1vL1   1-3   1800  30.0  CAP   0       3/3           50–60 / 70–90
L5vL5   1-3   1800  30.0  CAP   0       2–3/2–3       0 / 0–40
L9vL9   1-3   1800  30.0  CAP   0       3/3           0 / 0
L1vL9   1-3   1212  20.2  KO    2       0/3           70 / 0
L9vL1   1-3   1341  22.4  KO    1       3/0           0 / 40
L3vL6   1-2   1585–1674 26–28 KO 2      0/3           80 / 0
L3vL6   3     1800  30.0  CAP   0       1/3           50 / 0
```

Findings:
- **Same-level matchups do not KO-resolve in 30 s** — L1vL1, L5vL5, L9vL9 all ran the
  full cap and returned `winner=0`, even L1vL1 with a clear 50-vs-90% damage lead.
- **Higher level does NOT mean faster KO.** L9vL9 is the *least* violent (both fighters
  finish at 0% — a defensive, low-damage standoff), so mirror matches at high level are
  the *most* likely to reach the cap unresolved.
- **Only asymmetric pairings resolve by KO** (the stronger bot 3-stocks the weaker),
  landing ~20–28 s — but even a 3-vs-6 gap can still hit the cap (L3vL6 seed 3).
- L1vL9 / L9vL1 are seed-invariant here: the losing bot never lands a hit, so there is
  no rng divergence to change the outcome.

Implication: a round-robin matrix at the current 30 s cap would leave its **entire
diagonal (and any near-mirror) unresolved** — precisely the cells a balance sim most
needs a verdict on.

## Q4 — Termination guarantee (post-#292 / #368)

**Termination of the run is guaranteed** — `for f in range(frames)` is finite; no
input can produce an infinite loop. **KO-resolution is not guaranteed**, and the two
fixes named in the ticket are AI-side mitigations, not engine guarantees:

- **#292** (`pycats/sim/controllers.py`, ~L762): a leveled, tilt-capable bot converts
  a neutral grounded attack into a **forward-tilt**. Rationale in-code: the bot
  converges to a standoff and throws the neutral **jab**, a *set-knockback* move whose
  launch is fixed regardless of victim percent — so it "can NEVER KO … the loser
  juggled past 1400 % with all stocks." The f-tilt is percent-scaling, so it can
  finish. **Gated to leveled bots with tilts enabled**; level-less/Lv1-jab paths are
  byte-identical (golden-safe).
- **#368** (`pycats/sim/controllers.py`, ~L784, "anti-stall backstop"): **leveled-only,
  deterministic**. Detects a no-progress lock (moved < `ANTI_STALL_MOVE_PX` and no
  percent change within ~1.5 s) and injects one toward-target action to break a limit
  cycle. Guards the #292 non-resolving standoff (per `docs/pm-reference/cpu-ai.md`).

Neither applies to **level-less** controllers or the **`--vs` archetype** bots
(chase/idler/follower), and neither makes KO *certain* even for leveled bots — Q3 shows
same-level leveled mirrors still reach the cap. So: **always terminates (cap); may
return `winner=0`.** No remaining infinite-loop edge exists; the open edge is
*non-resolution*, which is by design (the cap catches it) and is #684's problem to
adjudicate.

## Q5 — Recommendation for #684 (round-robin balance sim)

Because the engine declares **no winner at the cap**, a round-robin matrix cannot rely
on `match.winner` — it must compute its own **deterministic tiebreak** from the final
snapshot. Recommended rules:

1. **Fixed stocks + hard frame cap.** Keep `INITIAL_LIVES = 3`; run every cell to a
   fixed cap. Consider a cap **longer than 30 s** for the matrix (Q3: 30 s leaves
   same-level cells unresolved) — but a longer cap only *reduces* unresolved cells, it
   never eliminates them (high-level mirrors may never KO), so a tiebreak is mandatory
   regardless of cap.
2. **Deterministic cap-time tiebreak**, computed from the last `PlayerSnap`
   (`pycats/sim/runner.py :: PlayerSnap` — fields available: `lives`, `percent`):
   rank by **(stocks remaining desc, then own percent asc)**; if still tied, fall back
   to a fixed order mirroring `winner_index` (player-2-wins-double-out), or record the
   cell as a genuine **draw**. Do **not** leave it as `winner=0`.
3. **Seed every match** (`watch.py --seed`, #166) and store the seed per cell so any
   result is re-watchable — already supported; Q3 shows some cells are seed-invariant,
   which is fine.
4. **Read resolution from `(phase, winner)` + the tiebreak, not `winner` alone.**
   `phase == "match_over"` ⇒ trust `winner`; `phase == "in_play"` at the cap ⇒ apply
   rule 2.

## Proposed follow-ups (file one-at-a-time, downstream of this doc)

- **DEV (#684 dependency):** implement the cap-time tiebreak helper (stocks → percent →
  fixed fallback) reading the final `PlayerSnap`, with a unit test on a
  cap-with-no-KO fixture. This is the missing piece #684 needs and is the natural
  first child once #684 unblocks.
- **Decision (optional):** should the *live game* also adjudicate a timed-out match
  (percent/stocks), or is bare-stop-with-no-winner acceptable outside the balance sim?
  Out of scope here; only the sim needs a verdict today.

## Out of scope (per ticket)

Changing duration/termination behavior; the #684 implementation itself. This doc
maps and recommends only.

## Refs

- Loop / terminators: `pycats/sim/runner.py :: run_battle`, `:: PlayerSnap`.
- Caps / mode mapping: `watch.py :: VS_FRAMES / MATCH_FRAMES / REPLAY_FRAMES`,
  `:: resolve_battle_plan`, `:: main`.
- Win rule: `pycats/systems/match_engine.py :: StatechartMatchEngine`,
  `pycats/systems/win_condition.py :: winner_index`.
- KO / lives / respawn: `pycats/entities/player.py :: Player.update`,
  `pycats/entities/fighter.py :: _outside_blast_zone / _ko`,
  `pycats/config.py :: INITIAL_LIVES / RESPAWN_DELAY_FRAMES / BLAST_PADDING(_X)`.
- AI resolution mitigations: `pycats/sim/controllers.py` (#292 forward-tilt ~L762;
  #368 anti-stall ~L784); `docs/pm-reference/cpu-ai.md`.
- Prior: #61 (`--vs` = 30 s or 3-stock KO, whichever first), #292, #368, #703/#702.
- Consumer: **#684** (round-robin CPU-vs-CPU balance sim).
