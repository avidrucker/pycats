# ROUNDS v1 — frame/tick-order faithfulness for the `over_time` system

**Ticket:** RESEARCH #1173 · child of the ROUNDS Mode v1 wayfinder map (#1096) / epic #347 ·
surfaced while grilling #1172 (the Leech card shape → ADR-0019).
**Role:** RESEARCH — findings + option space only; the `over_time` slot is *decided* in the
follow-on Health Regen DEV/ARC ticket, not here.
**Date:** 2026-08-04.

## Why this ticket exists

ADR-0019 splits the ROUNDS "Leech" slot into two heal cards. One of them — **Health Regen** —
is a passive per-N-frame self-heal, the first **time-driven `percent` mutator** pycats will
have. It hooks a new `systems/over_time.py`. Before the DEV build wires that into the frame
loop, we need to know **where a time-driven status effect ticks within one frame** in the Smash
engines, and whether pycats's current frame order matches — so the new call lands in the
engine-faithful, golden-deterministic slot.

## Sources read (2026-08-04)

| Source | Kind | What it grounds |
|---|---|---|
| `meleelight` — `src/main/main.js::gameTick` (VS-match branch) + `src/physics/hitDetection.js` | primary (Melee engine reimplementation, local #616) | the canonical per-frame order + the `percent += damage` application site |
| `doldecomp/melee` — `src/sysdolphin/baselib/gobj.c` / `gobjproc.c` / `gobj.h`; `src/melee/ft/fighter.c`; `src/melee/gm/gm_1A45.c` | primary (the original Melee engine, decompiled — public GitHub) | the HSD per-frame **scheduling model** (fixed `p_link` priority order) + the fighter's processing priority |
| pycats — `pycats/sim/runner.py::run_battle`, `snapshot`; `systems/hit_resolution.py::process_hits`; `systems/match_engine.py::MatchEngine.tick` | primary (this repo) | pycats's actual per-frame order today |
| `brawllib_rs` (local, Rust) | primary but **per-move only** | scripted subaction data; **not** engine-global stage order (see gaps) |

## §1 — Canonical Smash per-frame update order (CONFIRMED, meleelight)

`meleelight`'s `gameTick` main-gameplay branch runs, in this fixed order every frame:

1. `resetHitQueue()` — clear the per-frame hit queue
2. `getActiveStage().movingPlatforms()` — stage / moving-platform update
3. `destroyArticles()` → `executeArticles()` — projectile (article) lifecycle + movement
4. **per player:** `interpretInputs(i)` → `update(i)` — input read, then the character
   **state-machine + physics** (`update` → `physics(i)`); per-character **status/action timers
   tick here**
5. `checkPhantoms()` — phantom-hit resolution
6. **per player:** `hitDetect(i)` — hitbox/hurtbox **collision detection** (queues hits)
7. `executeHits(input)` — **apply damage + knockback**; this is the sole `percent`-raising site
   (`hitDetection.js`: `player[v].percent += damage`, then `getKnockback(... player[v].percent ...)`)
8. `articlesHitDetection()` → `executeArticleHits(input)` — projectile hits
9. `matchTimerTick(input)` — match timer / stock bookkeeping
10. `saveGameState(input, ports)` — freeze the frame (replay/snapshot); render runs on a
    separate `renderTick`

**Skeleton:** `input → per-character update (state+physics+timers) → hit detection →
damage+KB application → match/stock tick → snapshot`. Confirmed from primary; the `percent`
mutation is isolated to the damage-application stage (step 7), which runs **after** every
character's own update (step 4).

## §2 — Where a per-second DoT/regen lands within a frame (PARTLY CONFIRMED — the model; INFERRED — the exact slot)

**Sourcing attempt (2026-08-04, at Avi's direction to source a primary):** reached the public
Melee decompilation (`doldecomp/melee`). It confirms the **scheduling model** but not, within this
session's dig, the exact DoT-vs-collision placement.

**CONFIRMED (primary — `doldecomp/melee`):** Melee runs on the HSD **`p_link` priority scheduler**
— every game object (`HSD_GObj`) is created with a processing-order priority (`p_link`), and each
frame the engine walks the priority classes **in fixed order** (`gobj.c` iterates
`0 .. gproc_pri_max`; the match scene sets `gproc_pri_max = 0x18` in `gm_1A45.c`). Fighters are
created at **`p_link` 8** (`fighter.c`: `GObj_Create(HSD_GOBJ_CLASS_FIGHTER, 8, 0)`). So the order
in which fighter processing and collision resolution happen within a frame is a **fixed,
deterministic priority ordering** — never a same-frame race. This is the same picture meleelight
shows in code (§1): the fighter `update` pass runs, then hit detection, then damage application —
a fixed sequence.

**Still INFERRED (not pinned to a primary this session):** that a passive **status DoT/regen**
(head-flower / Lip's Stick / curry) is applied **inside the fighter's own processing pass** (at or
near `p_link` 8), and therefore **before** the hitbox-collision resolution and damage-application
of the same frame. The reasoning: these effects are per-fighter status counters carried on the
victim, so they tick when the fighter ticks; and meleelight's confirmed order already puts the
fighter `update` (where its action/status timers tick) ahead of hit detection. What was **not**
pinned is the exact decomp function applying the head-flower damage and its `p_link` relative to
the collision pass — that needs a deeper decomp dig (or a direct engine-doc source such as a
rukaidata / OpenSA dump).

**Net:** Q2's *scheduling basis* is now primary-confirmed (fixed `p_link` order; fighters at 8);
Q2's *specific slot* (DoT ticks in the fighter pass, pre-collision) remains labeled inference,
though now resting on the confirmed model + meleelight's confirmed order rather than architecture
alone.

**Consequence of the inferred slot:** on a frame where a fighter both takes a regen tick and a
hit, the engine-faithful order is **status-first** — the heal lands during the victim's update,
then the incoming hit's damage + KB compute off the post-heal percent. For Health Regen (a heal,
which *lowers* percent) this marginally lowers that frame's incoming KB. Deterministic either
way; only the ordering differs.

## §3 — pycats's current frame order (CONFIRMED, this repo)

`run_battle`'s per-frame loop runs, in order:

1. compute `fi` — controller / script inputs for the frame
2. `for p in players: p.update(fi, platforms, attacks, ledges)` — per-fighter **movement +
   physics + state transitions + attack spawning**; existing per-fighter timers
   (`dodge_timer`, `hurt_timer`, `stun_timer`, `intangible_timer`, …) **decrement here**
3. `resolve_player_push(players, platforms)` — player↔player push resolution
4. `attacks.update(platforms)` — projectile / hitbox movement
5. `hit_resolution.process_hits(players, attacks)` — hit detection **and** damage + KB
   application (`Fighter.receive_hit` / `receive_hit_invincible` — the only combat `percent`
   mutator)
6. `match.tick()` — `MatchEngine.tick` stock / phase / winner bookkeeping
7. `snapshot(players, attacks, match)` — records `round(percent, 6)` per fighter into the golden row
8. `presenter.show(...)` — render + pacing, non-sim (skipped headless / in goldens)

**Match against §1:** pycats's order maps cleanly onto the meleelight skeleton —
`input → per-fighter update (incl. timers) → hit detection+damage → match tick → snapshot`.
The only structural difference is that pycats resolves hits in **one** `process_hits` call after
the whole player loop, whereas meleelight interleaves per-player `hitDetect` then a global
`executeHits`; the **net stage order is identical** (all updates → all hits → match tick →
snapshot). **No mismatch that affects `over_time` placement.**

Note: pycats already ticks its per-fighter status timers inside `p.update` (step 2) — the same
stage the engines tick status counters. So pycats's *internal* convention already agrees with the
inferred engine slot.

## §4 — Recommended `over_time` slot + option space

Research gives a recommendation and the option space; the DEV/ARC follow-on picks the slot.

**Constraints both options satisfy:** `over_time` must run **before `snapshot`** (step 7) so the
frame's healed percent is recorded that frame, and at a **fixed point every frame** (per-fighter
frame counter, deterministic, no RNG — per ADR-0019 §4/§9).

| Option | Slot in `run_battle` | Faithfulness | Notes |
|---|---|---|---|
| **A (recommended)** | **after the `p.update` loop, before `process_hits`** (between step 2/4 and step 5) | **matches §1/§2 inferred order** — status ticks pre-hit-detection | agrees with pycats's own convention (timers tick in the update stage); a same-frame heal-then-hit computes KB off the post-heal percent |
| **B** | after `process_hits`, before `match.tick` / `snapshot` | less faithful — heal lands *after* the frame's incoming hit | still deterministic + snapshot-visible; a same-frame hit computes KB off the pre-heal percent. No KO risk from a heal (0-floor, ADR-0019 §8) |

**Recommendation: Option A** — call `over_time` immediately after the per-fighter `p.update`
loop (naturally, *inside* the same per-fighter pass, mirroring how `dodge_timer` et al. already
tick there), before `process_hits`. It is the engine-faithful slot under §2's inferred order and
it matches pycats's existing "status timers tick in the update stage" convention, so it needs no
new frame-loop stage of its own. Both options keep goldens deterministic; faithfulness is the
tiebreaker.

**Caveat on §2's basis:** Option A's faithfulness claim rests on §2's scheduling model — now
**primary-confirmed** (fixed `p_link` order, fighters at 8; `doldecomp/melee`) — plus the
**inference** that the DoT/regen ticks in the fighter pass ahead of collision. The exact
head-flower/curry damage `p_link` was **not** pinned this session. If the DEV build should commit
to slot A on a fully-pinned basis, a deeper decomp dig (the head-flower damage function + its
`p_link` vs the collision pass) or a direct engine-doc source would close it — flagged as a
residual gap, Avi's call on sufficiency.

## Evidence quality

| Finding | Basis |
|---|---|
| §1 canonical per-frame skeleton | **CONFIRMED** — meleelight primary (`gameTick` + `hitDetection.js`) |
| §2 scheduling model (fixed `p_link` order; fighters at 8) | **CONFIRMED** — `doldecomp/melee` primary (`gobj.c`, `gobjproc.c`, `gm_1A45.c`, `fighter.c`) |
| §2 DoT/regen ticks in the fighter pass, pre-collision | **INFERENCE** — resting on the confirmed model + meleelight's order; the exact head-flower/curry damage `p_link` not pinned (deeper decomp dig, or a rukaidata/OpenSA dump, would confirm) |
| §3 pycats current order | **CONFIRMED** — this repo (`run_battle`, `process_hits`, `MatchEngine.tick`, `snapshot`) |
| §4 slot recommendation | recommendation from §1+§3 (confirmed) resting on §2 (inference) for the faithfulness tiebreak |

## Out of scope

- Interval N + heal-chunk magnitudes (by-feel — #1156).
- The Leech card *shape* (decided #1172 / ADR-0019).
- Implementing `over_time.py` (the downstream Health Regen DEV build this unblocks).

## Refs

Leech shape #1172 + ADR-0019 · map #1096 · epic #347 · magnitudes #1156 ·
`docs/research/2026-08-04-rounds-novel-pct-per-second-findings.md` (§1.2 hook-site candidates) ·
meleelight (local #616) · brawllib_rs (local).
