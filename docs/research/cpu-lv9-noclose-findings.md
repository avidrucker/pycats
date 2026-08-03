# CPU Lv9 fireball-zoning no-close — root-cause findings (#961)

**Ticket:** #961 (child of #925 CPU-behavior-fidelity epic, problem 2). **Role:** RESEARCH
(investigate — reproduce + root-cause, no fix). Deferred here by #942 / ADR-0010 D3.
**Repro artifact:** `repros/lv9_noclose_instrument.py` (read-only; subclasses
`AttackerController`, edits no shipped code — `repros/` is gitignored).
**As-of:** `br-elderberry/pycats-961-lv9-noclose-investigate`, base `115fb6b`, 2026-08-01.

## TL;DR

The Lv9 bot never closes because it is **locked in the fireball animation ~75% of the
time by re-pressing B faster than the fireball resolves**. Two source facts combine:

1. **Cadence << move length.** The ranged-poke gate in `AttackerController._decide_combat`
   fires `special` whenever `(self._f - self._last_attack) >= self.attack_period`, and Lv9's
   `attack_period` is **10** frames. The fireball (`nalio` `neutral_b`) is a **48-frame** move
   (14 startup + 1 active + 33 recovery), and even its **startup alone is 14** frames — longer
   than the 10-frame gate.
2. **No in-progress-move guard on move start.** `entities/fighter_input.py`'s Attack/Special
   seam calls `p._clock.start(move)` gated only on `p.state not in ("shield", "dodge",
   "helpless")` — it does **not** check whether a move is already running. So the re-pressed
   `special` **restarts the fireball clock to frame 1** mid-startup.

Result: the poke cadence re-opens at frame 10, the bot re-presses B while the previous
fireball is still in startup (`move_frame`≈9), the clock resets to 1, and this repeats. The
fighter is rooted in the fireball state on 75% of frames and is **free to walk on only 12 of
1800 frames (0.7%)**. The `_decide_engage` toward-close intent *is* emitted (67% of frames) —
so the code comment's *"it still falls through to movement on non-poke frames"* is literally
true — but the engine discards that movement because the fighter is rooted, so the comment's
conclusion *"so it also closes in"* is **refuted**: the bot has almost no free frames to close.

A side effect: because the restart lands at `move_frame`≈9 — **before the active frame (15)** —
77% of B presses (93 of 121) cancel the fireball *before its projectile spawns*. The bot mostly
throws no fireball at all; it just loops the startup.

## 1. Deterministic reproduction

Repro command (the epic's, unchanged):

```
watch.py --p1-level 9 --p1-char nalio --p2-char birky --seed 3
```

Headless instrumentation (same setup as `watch.py`'s leveled path → `cpu_controllers` →
`run_battle`: shared `rng=Random(3)`, `controllers=(c1, None)`, **no `ledges`**,
`stop_on_match_over=True`):

```
SDL_VIDEODRIVER=dummy PYTHONPATH=. <main-venv-python> repros/lv9_noclose_instrument.py 1800
```

Per-frame trace of P1 (Lv9 nalio), 1800 frames, seed 3:

| Metric | Value |
|---|---|
| In `fireball` move state | **1351 frames (75.1%)** |
| `special` (B) pressed | 121 frames (6.7%) |
| toward-close intent emitted by controller | 1211 frames (67.3%) |
| …of which the fighter was **free to walk** (grounded, no move running) | **12 frames (0.7%)** |
| Airborne | 308 frames (17.1%) |
| Fireball reached its active frame (`move_frame`≥15, projectile thrown) | 312 frames; max `move_frame` seen = 47 |
| Dominant gap between consecutive B presses | **10 frames** (115 of ~120 gaps) |
| B presses that restarted a fireball already mid-startup (`move_frame`≈9) | **93 of 121 (77%)** |
| adx (horizontal gap) | first 400, last 223, min 9, max 1784 |
| Move-state histogram | `fireball` 1351, `None` 289, `neutral air` 120, `forward tilt` 40 |

The window around the first B press shows the loop directly (`mf` = `move_frame`):

```
f=0  adx=400 move=None     mf=0  special=1        (fire B)
f=1  adx=400 move=fireball mf=1  toward=1 (right)  (rooted; walk input ignored)
...
f=10 adx=346 move=fireball mf=10 special=1        (attack_period reopened → re-press B)
f=11 adx=341 move=fireball mf=1  toward=1 (right)  (clock RESTARTED 10→1)
```

## 2. Root cause (grounded in source)

The lock is the interaction of a controller-side cadence and an engine-side move-start rule.

**Controller side** — `AttackerController._decide_combat`, the ranged-poke branch:

```python
if (
    "specials" in self.enabled_moves
    and abs(dy) < POKE_DY_BAND
    and self.attack_range < adx <= self.fireball_range        # 45 < adx <= 450
    and (self._f - self._last_attack) >= self.attack_period   # Lv9: >= 10
    and (self.follow_through_p >= 1.0 or ...)                 # Lv9 p=1.0 → always commits
):
    self._last_attack = self._f
    return {keys["special"]}                                  # early-return: skips _decide_engage
```

On a cadence frame this early-returns `{special}` and never reaches `_decide_engage` (the
movement/close code). On the ~9 intervening frames it *does* fall through to `_decide_engage`,
which returns a `toward` press (adx=... > `standoff`=30 → "toward"). So far the comment holds.

**Engine side** — `entities/fighter_input.py`, the Attack/Special move-selection seam:

```python
if (atk_pressed or sp_pressed or ground_smash) and p.state not in ("shield", "dodge", "helpless"):
    ...
    p._clock.start(move)          # no guard: starts even if a move is already running
```

Because the guard excludes only shield/dodge/helpless — **not** an in-progress attack — the
`special` re-pressed at cadence frame 10 restarts the fireball move clock while the fighter is
still in the fireball's startup (`move_frame`≈9, confirmed: 93/121 presses). The clock resets to
1 and the fireball never resolves. The fighter is therefore rooted in the fireball state and is
non-actionable on the very frames the controller emits `toward`, so the walk input is dropped by
the engine.

**Verdict on the comment** (`_decide_combat`, above the poke branch):
> *"it still falls through to movement on non-poke frames, so it also closes in."*

- **Confirmed:** the controller does fall through and emit `toward` on non-poke frames (67% of frames).
- **Refuted:** the bot does **not** close in — those `toward` presses are dead inputs while the
  fighter is rooted in the perpetually-restarted fireball (free-to-walk only 0.7% of frames). The
  comment conflates *"the controller emits a movement key"* with *"the fighter moves."*

The `fireball_range=450` band is not itself the cause (the poke is correctly a mid-range tool);
the cause is that the **poke cadence (10) is shorter than the fireball lockout (48, startup 14)
and the engine lets the re-press restart the move**, so the bot never leaves the poke band under
its own power.

## 3. Trigger vs. quiet conditions

- **Zone-lock (the reported no-close) triggers** whenever `45 < adx <= 450` and roughly level
  (`abs(dy) < POKE_DY_BAND`): the poke re-fires every 10 frames, restarts the fireball, and the
  bot cannot walk. This is the steady state.
- **Melee does happen, but only when knockback/drift forces `adx <= 45`** (below `attack_range`),
  where the poke gate fails and `_decide_engage`'s in-range cadence lands a `neutral air` / `forward
  tilt` (160 melee frames in the trace). The bot never *chose* to close to that range — it was
  pushed there.
- **Out-of-band `adx > 450` does not let it close either.** 120 frames had `adx > 450`, but **0**
  of them were free-to-walk — the bot was still rooted in a restarted fireball (or airborne from a
  launch; the `adx=1784` spike is a KO/launch, not an approach). So the lock survives even outside
  the poke band on this seed.
- **The default (level=None) and Lv1–8 never enter any of this**: the poke branch is gated on
  `"specials" in self.enabled_moves`, and only Lv9's `enabled_moves` contains `"specials"`.

## 4. Golden-safety constraints on a future fix

For the downstream architect → dev slice; a fix must keep the seeded/golden sims byte-identical
and stay within the known dead-code boundaries:

- **The poke branch is Lv9-only.** `"specials"` is in `enabled_moves` for **level 9 only** (and
  never for the level-less default). Any change to the poke cadence, its early-return, or a new
  "don't re-press while a move is running" controller guard **only affects Lv9** and cannot move a
  golden that doesn't run a Lv9 specials bot — but confirm no golden pins a Lv9 nalio trace.
- **Prefer a controller-side fix over the engine seam.** The missing in-progress-move guard in
  `fighter_input` (`p._clock.start` with no running-move check) is a **shared engine seam** — every
  fighter and every golden depends on the current "a fresh attack input restarts the move" behavior
  (e.g. jab-restart, buffered inputs). Changing it there risks broad golden movement. Root-causing
  points at the controller: gate the poke (and/or the whole attack cadence) on the fighter being
  **actionable / not already mid-move** so it stops re-pressing B into its own startup, leaving the
  engine seam untouched.
- **`ledges` is not plumbed to two-controller battles.** `run_battle`'s `controllers=` path calls
  `c(p1, p2, f, attacks)` with no `ledges` (confirmed; same as #927), so edge-guard / edge-hog /
  recover are dead in this repro. A fix should not assume those branches run.
- **Don't widen `standoff` or narrow `fireball_range` as the fix.** #928's Axis-2 spacing is a
  faithful reference (the epic notes the no-close is a *lock*, not a fidelity-of-spacing gap), so
  the fix should free the bot to act on its existing spacing intent, not retune the band.

This ticket root-causes only. Choosing and implementing the fix (e.g. an actionable-gate on the
poke cadence) is a downstream architect → dev slice, filed one at a time after this doc lands.

## Refs

#925 (epic, problem 2), #942 / ADR-0010 D3 (the deferral that spawned this),
#927 (`docs/research/cpu-jitter-jump-findings.md` — the investigate template),
#928 (`docs/research/pm-cpu-behavior-findings.md` — reference model),
#714 (the smash finisher that never fires because the bot never closes),
#248 (the ranged-special poke), #915 (smash-usage policy — separate track).
Source: `pycats/sim/controllers.py` (`AttackerController._decide_combat`, `LEVEL_PARAMS[9]`),
`pycats/entities/fighter_input.py` (`handle_actions` Attack/Special seam),
`pycats/sim/runner.py` (`run_battle` two-controller path).
