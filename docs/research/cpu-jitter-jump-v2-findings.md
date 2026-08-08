# CPU jumpy+jittery — corrected root-cause findings (#966)

> **Supersedes the root cause in [#927](https://github.com/avidrucker/pycats/issues/927)**
> (`docs/research/cpu-jitter-jump-findings.md`) and the fix approach in **#959 / ADR-0010 D1**.
> A correction note is posted on #927 pointing here.

## TL;DR

The "jumpy + jittery" the human sees in leveled CPU bots has **two dominant causes**, and
**neither is the eaten-press lock #927 root-caused**:

1. **Jumpy = a reflexive jump-frequency policy.** The jump-toward gate in
   `AttackerController._decide_engage` (`pycats/sim/controllers.py`) fires whenever a foe is
   even slightly above and horizontally near, keeping the bot airborne **64% of a 600-frame
   fight**. The old "hold `up` for the first `JUMP_UP_STUCK_MAX` (90) frames" behavior was
   *accidentally throttling* the takeoff rate (one press edge per continuous hold); ADR-0010
   D1 (#959) removed that throttle and **tripled takeoffs (8 → 21)** — it made this facet
   worse, which is why the eyeball rejected it.
2. **Jittery = horizontal spacing oscillation with no hysteresis.** The spacing rule in the
   same method uses a hard **±8px deadband**, is **re-decided every frame**, and **commits to
   no movement** — so at Lv7 `standoff=32` the bot overshoots and flaps toward → none → away
   **~119 times / 600 frames**. #927 never named this; D1 left it essentially unchanged
   (119 → 115).

The fix is **not** a faster jump re-arm. It is a game-design smoothing decision (hysteresis
deadband + a jump *purpose* gate / cooldown + movement commitment), filed downstream as an
architect → dev slice after this doc. There is **no fresh primary research to do** — frame-level
CPU input cadence is a documented `[GAP]` (#928, Axis 1); PM has no CPU-AI primary source.

## 1. Deterministic reproduction + metrics harness

**Repro:** `watch.py --p1-level 7 --p2-level 7 --p1-char nalio --p2-char birky --seed 1`
(the #925 eyeball repro). Leveled controllers are built by `cpu_controllers()` in `watch.py`
→ `AttackerController(attacker_num=N, level=L, rng=rng)`, driven by `run_battle()` in
`pycats/sim/runner.py`.

**Harness (gitignored, under `repros/`):**

- `repros/jitter_metrics.py` — monkeypatches `AttackerController.decide`, runs a 600-frame
  seed-pinned `run_battle`, and prints, for P1: airborne frames, jump **takeoffs** (grounded→air
  transitions), `up`-pressed frames, and **horizontal state toggles** (left/right/none
  transitions). Parameterizable by level, seed, and char-pair.
- `repros/jitter_metrics_trace.py` — the same instrumentation with a per-frame dump
  (frame, state, on_ground, vel.y, jumps_remaining, dy, adx, up-pressed, key-set) for reading
  branch attribution directly.

Both need `PYTHONPATH=.` and `SDL_VIDEODRIVER=dummy`; run with the main-repo interpreter
(worktrees have no `.venv`). They are the reusable measurement rig this ticket contributes;
any downstream fix is judged against them **and** the D5 eyeball bar.

### Measured (P1, 600 frames, Lv7 vs Lv7, seed 1)

| metric | current main (no D1) | after #959 D1 (superseded branch) |
|---|---|---|
| jump takeoffs | **8** | **21** |
| airborne frames | **382 (64%)** | 486 (81%) |
| `up`-pressed frames | 129 | 15 |
| horizontal L/R/none toggles | **119** | 115 |

Current-main figures reconfirmed in this worktree (`repros/jitter_metrics.py`,
`airborne=382 takeoffs=8 up_press=129 horiz_state_toggles=119`); D1 figures are from the
preserved #959 branch (`br-banana/pycats-959-child-of-925-fix-cpu` @ `068759d`, not merged).

## 2. Facet 1 — the jump-frequency policy (jumpy)

**Where.** `AttackerController._decide_engage`, the jump-toward block guarded by
`dy < -FOE_ABOVE_DY and a.fighter.on_ground and adx < JUMP_UP_NEAR_ADX`
(`FOE_ABOVE_DY = 30`, `JUMP_UP_NEAR_ADX = 120` — module constants in `pycats/sim/controllers.py`).

**Mechanism.** A jump spends only on a fresh **press edge**: `FighterInput.handle_actions`
(`pycats/entities/fighter_input.py`) reads `pressed = input_frame.pressed` (keys freshly down
*this* frame) and does `jump_pressed = self._pressed(pressed, "up")`. So **holding `up` every
frame produces exactly one jump edge** — a continuous hold self-throttles to one takeoff per
grounded episode. The current-main gate holds `up` continuously for the first
`JUMP_UP_STUCK_MAX = 90` frames (then pulses on odd counts), so it inherits that throttle.

**Why it reads as jumpy anyway.** The *trigger condition* is permissive: any foe ≥30px above
and within 120px horizontally arms it. In a live Lv7 mirror the target is frequently in that
window, so the bot re-arms a hop each time it lands — **64% airborne** on current main even
with the throttle. The behavior is a *policy* choice (jump-toward-any-slightly-elevated-foe),
not a stuck-press artifact.

**Why D1 made it worse.** ADR-0010 D1 (#959) re-armed the press the instant the bot was
grounded-and-jumpable, converting each cadence frame into a live edge. That **removed the
accidental throttle**: takeoffs 8 → 21, airborne 64% → 81%. The eyeball reads more airtime as
*more* jumpy — the opposite of the goal. A faster re-arm is the wrong lever; the trigger needs
a **purpose gate** (only jump when a jump actually closes vertical distance to a reachable
target / platform) and/or a **cooldown**.

## 3. Facet 2 — horizontal spacing oscillation (jittery)

**Where.** The spacing rule at the top of `AttackerController._decide_engage`:

```
move = None
if adx > self.standoff + 8:
    move = toward
elif adx < self.standoff - 8 and not press_in:
    move = away
```

**Mechanism.** Three properties compound:
- **Hard ±8px deadband** around `self.standoff`, with **no hysteresis** — the same threshold
  governs entering and leaving the "close in" / "back off" states, so the bot chatters across
  the boundary instead of settling.
- **Re-decided every frame** from scratch (`move` starts `None` each call) — there is no
  movement commitment / minimum-dwell, so a one-frame overshoot immediately reverses.
- **Tight target gap** at higher levels: `standoff` is 45/40/35/**32**/30 for Lv1/3/5/7/9
  (`LEVEL_PARAMS`, `pycats/sim/controllers.py`), and `attack_period` tightens 48/36/24/16/10 —
  so a Lv7 bot wants to sit 32px away and re-evaluates aggressively, overshooting the ±8 band
  and flapping toward → none → away **~119×/600f**.

**Not touched by #927 or D1.** #927's root cause and D1's change are entirely in the
jump-toward block; the spacing rule is unchanged (toggles 119 → 115). This is a distinct,
untouched cause of the visible jitter.

**The lever.** Hysteresis (separate enter/exit thresholds, e.g. close when `adx >
standoff + outer`, stop when `adx < standoff + inner`), plus a movement-commitment / dwell so
the bot holds a chosen direction for a few frames before re-deciding.

## 4. Trigger vs. quiet conditions

- **Facet 1 fires** whenever the target sits ≥`FOE_ABOVE_DY` above and within `JUMP_UP_NEAR_ADX`
  horizontally while the bot is grounded — common in a live mirror because knockback and the
  opponent's own hops keep putting the foe slightly overhead. It **quiets** when the target is
  level or far horizontally (gate condition false → `_jump_up_stuck` resets to 0).
- **Facet 2 oscillates** whenever `adx` hovers near `standoff` (the intended resting gap) — i.e.
  most of an engaged fight. It **settles** only when the bot is pushed well outside the band
  (pure approach) or is pressing in during a punish (`press_in` suppresses the back-off half).
- The two **interact**: a hop (facet 1) changes `adx`/`dy` on landing, re-triggering the spacing
  chatter (facet 2), which repositions under the foe and re-arms the hop. The compound reads as
  a twitchy in-place bounce rather than a deliberate approach.

## 5. Golden-safety constraints on a future fix

- The **sim goldens / render-parity oracle don't run a controller at all**: `run_battle` with no
  controller drives players from a scripted `default_timeline` (`pycats/sim/runner.py`), so
  `test_battle_screen_render` and the sim goldens never touch `AttackerController`. Separately,
  the **level-less `AttackerController` path (`level=None`) has its own byte-identity contract** —
  exercised by the explicit `# level=None` cases (`test_anti_stall_backstop`, `test_ai_edge_guard`)
  — and every level-specific behavior (smash #714, tilt-convert #292, anti-stall #368, reactive
  spacing #277) already branches on `self.level is not None` / `self.reactive_spacing`. Any
  smoothing fix must be **level-gated the same way**, so both the scripted goldens and the
  level-less controller tests stay byte-identical.
- The spacing rule's `press_in` half is already `reactive_spacing`-gated (level-less default
  never evaluates it). A hysteresis change must preserve the level-less arm exactly.
- Because the values chosen (deadband widths, cooldown length, dwell frames) have **no canon
  source** (#928 Axis 1 is a `[GAP]`), they must be logged as `DIVERGENCE` in the value registry
  when the downstream decision picks them, and ratified against the D5 eyeball bar — not asserted
  as PM-faithful.

## Downstream

This ticket **root-causes only**. Next steps, filed one at a time after this doc lands:
1. A **game-design decision** (architect / decision ticket, `--role ARC`) that picks the
   smoothing model: hysteresis deadband + jump purpose-gate/cooldown + movement commitment,
   with the specific numbers logged `DIVERGENCE` and judged against `repros/jitter_metrics.py`
   **and** the eyeball. ADR-0010 D1 is a candidate for supersession there.
2. A **DEV slice** implementing the ratified model, level-gated, with an able-to-fail regression
   test and the metrics harness as the acceptance check, closed only after human eyeball-OK.

## Refs

#925 (epic, problem 1), #927 (superseded root cause + instrumentation template; correction note
posted), #959 (superseded DEV fix — branch preserved `@068759d`, not merged), ADR-0010 (D1 shown
counterproductive), #928 (`docs/research/pm-cpu-behavior-findings.md` — Axis 1 reference model;
per-level cadence `[GAP]`), #369/#367 (the jump-toward pulse mechanism), #338 (evade roll — the
eaten-press #927 over-weighted), #277/#343/#444 (reactive spacing / committal approach).
