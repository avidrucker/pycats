# Dual-backend battle benchmark for pycats

> Design spec. Stand up two interchangeable state-machine backends behind
> identical battle logic, to measure whether `statecharts-py` costs frame
> budget vs. the hand-rolled FSM — **without adding any new battle mechanics**.
>
> Date: 2026-06-21. Status: approved, pre-implementation.

## 1. Goal & constraints

- **Goal:** Provide a fair, automated A/B comparison of two state-machine
  backends driving the *same* pycats battle simulation, plus a way to watch the
  battles (live or video) in addition to headless runs.
- **Hard constraint — no new mechanics:** The statechart backend only
  *re-expresses existing transitions*. Existing behavior (including quirks) is
  preserved exactly. We restructure and add test/benchmark/visualization code;
  we do not change gameplay.
- **Strict parity (decided):** Both backends, fed the same scripted inputs,
  must produce byte-identical frame-by-frame state. This isolates the
  state-machine engine as the only variable AND doubles as proof the statechart
  port is faithful.
- **Scope (decided):** Both fighters' action-state FSMs PLUS in-battle
  match/stage state (stocks, respawn, KO, match-over). Excludes the menu /
  char-select / pause screen system (app shell, not battle).
- **Architecture (decided):** In-place engine seam — swap the state engine
  inside the *real* `Player` / match logic, so we benchmark the real game, not a
  reimplementation.

### Non-goals

- Improving framerate in this work (the original "increase framerate" goal is
  explicitly *measurement first*; the state engine is almost certainly not the
  FPS bottleneck — rendering is the likely culprit, to be investigated
  separately). Adding `statecharts-py` can only add overhead, never reduce it.
- Implementing any Project M mechanics (grabs, hitstun, ledges, techs,
  multi-hit hitboxes, per-character movesets). Those are future work.
- Interactive live play through the new runner (live mode is a deterministic
  replay — see §8).

## 2. Background: current architecture (verified)

- The per-player `FSM` (`pycats/systems/fsm.py`) is purely a **state-label
  tracker**. All gameplay/physics/combat logic runs in `Player.update()` /
  `handle_actions()` / `handle_move()` *before* `self.fsm.update()` is called
  last (`player.py:388`). The FSM `table` is just ordered guards reading player
  attributes to pick the next label; no `on_enter`/`on_update` are registered.
- Guards are evaluated in document order; the **first match wins** and the FSM
  performs **exactly one** transition per frame (`break` after first match).
- `self.fsm.state` is read *during* the frame's update (e.g. `player.py:220,
  236, 246, 259, 297, 320, 323, 340, 366, 381, 405, 436, 445, 524`) and for
  rendering (`game.py:739, 843`). The label used during frame N is the one
  computed at the end of frame N-1 (a one-frame-lagged classifier).
- One state change is imperative, not table-driven: `_ko()` sets
  `self.fsm.state = "ko"` directly (`player.py:559`). `_respawn()` does *not*
  set the label; the `"ko"` table transition `→ idle` (guard `is_alive`) handles
  return.
- The `"stun"` state is currently **unreachable** via the table (no guard
  targets it; `_start_stun` only sets a timer). We preserve this quirk.
- The real playing loop (`game.py:702-709`) is a fixed sequence:
  `p.update()` ×2 → `resolve_player_push(list(players))` → `attacks.update()` →
  `combat.process_hits(players, attacks)` → `check_win_condition()`.
- No randomness anywhere; float math is deterministic. Strict parity is
  achievable with exact equality.

## 3. The `StateEngine` seam

A small protocol both backends implement:

```python
class StateEngine(Protocol):
    state: str                          # "idle","run","jump","fall","shield",
                                        # "dodge","ko","hurt","stun","attack"
    def tick(self, ctx) -> None: ...    # advance exactly one frame
    def force(self, label: str) -> None: ...  # imperative set (used by _ko)
```

- **`LegacyEngine`** wraps the existing `FSM` verbatim:
  `tick(ctx)` → `fsm.update(ctx)`, `state` → `fsm.state`,
  `force(label)` → `fsm.state = label`.
- **`StatechartEngine`** wraps a `statecharts.Session`:
  `tick(ctx)` → `session.send("tick")`; `state` → derived from the single
  atomic state in `session.configuration`; `force(label)` → `session.send(label)`
  where a global transition routes to that state (covers `_ko`).

### Player integration

- `Player` replaces `self.fsm` with `self.engine` (a `LegacyEngine` by default)
  and exposes a `Player.state` property delegating to `self.engine.state`.
- Mechanical sweep in `player.py`:
  - `self.fsm.state` (reads) → `self.state`
  - `self.fsm.state = "ko"` → `self.engine.force("ko")`
  - `self.fsm.update()` → `self.engine.tick(ctx)`
- Rendering: `p.fsm.state` → `p.state` (`game.py:739, 843`).
- Default backend stays legacy, so the shipping game is behaviorally unchanged.
- Backend chosen by constructor arg / factory; env var
  `PYCATS_STATE_BACKEND=legacy|statechart` selects it for the live game.

## 4. Statechart modeling (fidelity details)

- The chart is **flat**; atomic states are named exactly the existing labels.
- Each state's transitions mirror the legacy `table` **in the same document
  order** (first-match-wins).
- **All transitions fire on the explicit `"tick"` event; there are NO eventless
  transitions.** This guarantees run-to-completion performs *exactly one* hop
  per `send("tick")`, matching the legacy `break`-after-first behavior. Eventless
  transitions would settle to a fixpoint and could multi-hop — a divergence we
  deliberately avoid.
- **Guards close over the live `Player` instance** (exactly like the legacy
  lambdas), reading `vel`, `on_ground`, timers, and flags directly. The
  statechart **datamodel stays empty**, sidestepping the per-event
  datamodel-copy cost so the comparison is about engine machinery, not data
  plumbing.
- Quirks preserved: `"stun"` remains unreachable; no behavior is "fixed".

## 5. Match/stage engine

Same seam for match state: a 2-state machine `in_play → match_over(winner)`.

- `LegacyMatchEngine` delegates to the existing `check_win_condition()`.
- `StatechartMatchEngine` reproduces that predicate as a `"tick"`-guarded
  transition.
- Negligible perf-wise, but satisfies the "stage/app state too" scope and is
  included in parity snapshots.

## 6. Headless deterministic runner

- Set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` before pygame init —
  no window, no audio. pygame stays loaded; its cost is identical in both modes
  and cancels from the delta.
- Build platforms + two `Player`s (backend chosen by flag) + attacks group.
- Per frame, run the **exact real loop sequence** (§2): `p.update()` ×2 →
  `resolve_player_push` → `attacks.update` → `combat.process_hits` →
  `match_engine.tick`. No rendering.
- **Scripted input:** a deterministic timeline (small DSL of
  `(start_frame, end_frame, player, action)` spans) compiled to per-frame
  `InputFrame`s with correct `held` / `pressed` / `released` edges, replacing
  `core.input.poll`. One script, fed identically to both backends. The default
  script deliberately exercises every state: walk, jump, double-jump, attack,
  shield, all dodge variants, getting hit, KO, respawn.

## 7. Parity cross-check (pytest)

Each frame, snapshot:

- **per player:** `state, rect.x, rect.y, vel.x, vel.y, on_ground, percent,
  shield_hp, lives, is_alive, jumps_remaining, dodge_timer, hurt_timer,
  stun_timer, attack_timer, invulnerable_timer, facing_right, invulnerable`
- **attacks:** `(rect.x, rect.y, lifetime, owner_id)`
- **match:** `(phase, winner_id)`

Run the same script through both backends and assert the full snapshot
sequences are equal. Same code paths → exact equality (a 6-decimal rounding
hook is available if float noise ever appears). This test proves the statechart
port is faithful and guards future refactors.

## 8. Benchmark & bottleneck analysis (pytest + CLI)

- Run N frames (configurable, e.g. 10k–100k) per backend with snapshotting
  **off**; time with `time.perf_counter`.
- Report per backend: total time, mean / median / p95 / p99 per-frame µs,
  **simulated FPS** (1/mean), and the **statechart − legacy delta** in µs/frame
  and as **% of the 16.67 ms (60 FPS) budget**.
- **Bucketed timing** for bottleneck analysis: separately time `engine.tick` vs
  the `p.update` physics body vs `combat/push`, so we see whether the state
  engine is even a meaningful slice of the frame.
- A `bench.py` CLI prints the table; a `@pytest.mark.slow` test asserts the
  harness runs.

## 9. Presentation modes (watch / video)

The runner takes a pluggable **presenter**, so the same deterministic replay can
be:

- **`headless`** — no output (parity / benchmark). Default.
- **`live`** — open a real pygame window and render the replay at 60 FPS so it
  is watchable; backend selectable. Inputs are the *scripted* timeline (a
  replay), not interactive, keeping it deterministic and identical to what was
  benchmarked.
- **`video`** — render each frame to a Surface and encode to mp4/gif. Optional
  dependency `imageio-ffmpeg`; skipped gracefully if absent.

To enable this cleanly, **extract a
`render_battle(surface, players, platforms, attacks)` function** from game.py's
playing branch. This is a targeted improvement, not scope creep: the *pause*
branch (`game.py:824-852`) currently **duplicates** that draw code, so the
extraction de-duplicates game.py and gives the live/video presenters a single
shared renderer.

## 10. Dependency wiring & config

- `statecharts-py` installed editable into the env
  (`pip install -e ../statecharts-py`) so it imports as `statecharts`.
  Documented in the repo README. (Sibling repo at
  `../statecharts-py`; pure Python, Python 3.10+, zero core deps.)
- Backend + presentation mode selected by explicit runner args; env var
  `PYCATS_STATE_BACKEND=legacy|statechart` selects the backend for the live
  game. Game default = legacy.
- Optional: `imageio-ffmpeg` for video export only.

## 11. New / changed files (rough)

```
pycats/systems/state_engine.py      # Protocol + LegacyEngine + StatechartEngine
pycats/systems/match_engine.py      # match-phase backends
pycats/statecharts/fighter_chart.py # flat chart mirroring the FSM table
pycats/sim/runner.py                # headless/live/video runner + presenters
pycats/sim/input_script.py          # scripted-input DSL + default battle script
pycats/render_battle.py             # extracted shared renderer (or kept in game.py)
bench.py                            # CLI benchmark table
tests/test_parity.py                # byte-identical cross-check
tests/test_benchmark.py             # @slow timing harness
--- changed ---
pycats/entities/player.py           # self.fsm -> self.engine, Player.state property
pycats/game.py                      # use Player.state; use render_battle() in
                                    #   both playing and pause branches
```

## 12. Risks & mitigations

- **Parity drift from the engine swap.** Mitigated by `test_parity.py` asserting
  byte-identical snapshots; the legacy backend literally reuses the existing
  `FSM`, so legacy behavior is unchanged by construction.
- **statecharts-py multi-hop vs single-hop.** Mitigated by the all-`"tick"`,
  no-eventless modeling (§4).
- **Hidden non-determinism.** None found (no RNG; deterministic floats). Rounding
  hook available as a safety net.
- **pygame requiring a display in CI.** Mitigated by `SDL_VIDEODRIVER=dummy`.
- **Touching `Player` could regress the live game.** Mitigated by keeping legacy
  as default and the mechanical, behavior-preserving nature of the sweep.

## 13. Success criteria

1. `test_parity.py` passes: legacy and statechart backends produce identical
   snapshot sequences over the full default script.
2. `bench.py` produces a per-backend table with per-frame µs, simulated FPS, the
   statechart−legacy delta (µs and % of budget), and the per-bucket breakdown.
3. The battle can be watched live and/or exported to video from the same
   deterministic replay.
4. The shipping game (default legacy backend) behaves exactly as before.
