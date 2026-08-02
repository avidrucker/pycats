# CPU attack-input mashing — where it happens, and the option space to prevent it

**Ticket:** #1071 (RESEARCH · area:combat / combat:cpu) — child of #925 (CPU-behaviour epic),
generalising problem-2 (Lv9 fireball no-close) whose investigate (#961) and canon anchor
(#1060) are closed.
**Scope:** findings + option space **only**. No code or value change. Both candidate fix
seams are catalogued; **neither is chosen here** — that is the downstream architect/decision
ticket **#1079** (RULES: research never produces a spec).
**Primary sources:** the code itself (quoted below), and #1060 for the PM re-fire floor.

---

## TL;DR

Two independent seams let a fighter re-trigger a move it is already committed to:

1. **Controller (CPU-only).** `AttackerController` emits every attack/special/smash input
   on a cadence gated by `attack_period` and its own `_last_attack` timestamp — it **never
   checks the bot's own actionability** (`a.current_move` / `a.attack_timer`). So a leveled
   bot re-presses into a move that is still running.
2. **Engine (everyone — CPU and human).** `fighter_input.handle_actions` starts a move with
   `p._clock.start(move)` gated only on `p.state not in ("shield", "dodge", "helpless")`.
   During an active move `p.state == "attack"`, which passes that guard, and
   `MoveClock.start()` unconditionally resets the frame counter to 0 — so **any re-press
   restarts the running move to frame 1** instead of being ignored.

Together they produce the #961 Lv9 lock: attack_period=10 re-presses B into a 48-frame
fireball, the clock restarts before the move resolves, and the bot is rooted ~75% of frames.
PM ignores attack inputs during uninterruptible frames until the move's IASA (~40f for the
fireball, #1060); pycats gates at neither seam.

---

## 1. Where it happens (both seams, grounded in code)

### 1a. Controller seam — `pycats/sim/controllers.py`, `AttackerController`

Every attack-emitting branch gates on the **cadence** (`attack_period` vs `self._last_attack`,
the frame the bot last *emitted* an attack) and on follow-through probability. **None** reads
the bot's own move state (`a.current_move`, `a.attack_timer`). The relevant branches
(all inside `_decide_combat` / `_decide_engage`):

| Branch (issue) | Emits | Gate | Level reach |
|---|---|---|---|
| Ranged fireball poke (#248) | `{keys["special"]}` | `(self._f - self._last_attack) >= self.attack_period` | `"specials"` → **Lv9 only** |
| Edge-guard special/melee (#413) | `{keys["special"]}` / `{keys["attack"]}` | same `cadence` local | Lv5+ (special mode Lv9) |
| Whiff-punish (#274) | `{keys["attack"]}` | **bypasses cadence** — fires immediately in recovery | Lv5+ |
| Cadenced attack → f-tilt/f-smash (#292/#714) | `{keys["attack"]}` / `{keys["smash"], toward}` | `(self._f - self._last_attack) >= self.attack_period` | any leveled bot |

The fireball poke, verbatim (`_decide_combat`):

```python
if (
    "specials" in self.enabled_moves
    and abs(dy) < POKE_DY_BAND
    and self.attack_range < adx <= self.fireball_range
    and (self._f - self._last_attack) >= self.attack_period
    and (self.follow_through_p >= 1.0 or self.rng.random() < self.follow_through_p)
):
    self._last_attack = self._f
    return {keys["special"]}
```

`self._last_attack` is set when the input is *emitted*, not when the move *completes* or
becomes *actionable*. At Lv9 `attack_period == 10` (`LEVEL_PARAMS[9]`), so the gate re-opens
10 frames after the previous press — far inside the 48-frame fireball (14 startup + 1 active +
33 recovery). The cadenced normal attack (`_decide_engage`) has the identical structure:

```python
if in_range and reacted and (self._f - self._last_attack) >= self.attack_period:
```

**Root property:** the controller's re-fire floor is `attack_period`, a per-level cadence
knob unrelated to the committed move's length or its actionable frame. There is no
"am I still mid-move?" predicate anywhere in the attack branches.

### 1b. Engine seam — `pycats/entities/fighter_input.py`, `handle_actions`

The Attack/Special/smash branch (move-selection seam #143):

```python
if (atk_pressed or sp_pressed or ground_smash) and p.state not in ("shield", "dodge", "helpless"):
    ...
    key = resolve_move_key(p.fighter_data.moves, direction, p.fighter.on_ground, is_special, is_smash)
    if key is not None:
        move = p.fighter_data.moves[key]
        ...
        else:
            p._clock.start(move)
            p.fighter.record_attack_made()
```

The only guard is `p.state not in ("shield", "dodge", "helpless")`. During an active move the
fighter's state is **`"attack"`** — confirmed in `state_engine_sc.py`:

```python
# The attacking region (startup/active/recovery sub-phases) collapses to
# the single flat label "attack" ...
if self._session.in_state("attacking"):
    return "attack"
```

`"attack"` is not in the excluded set, so a fresh attack/special press **during** a running
move passes the guard and reaches `p._clock.start(move)`. `MoveClock.start()`
(`pycats/combat/move_clock.py`) has no in-progress guard — it unconditionally rewinds:

```python
def start(self, move: MoveData) -> None:
    """Begin executing ``move`` from frame 0."""
    self._move = move
    self._frame = 0
    self._windows = self._compute_windows(move)
    self._spawned_starts = set()
    self.hit_registry = {}
```

**Root property:** move-start is idempotent-unsafe — re-pressing attack mid-move resets
`_frame` to 0 and recomputes the hitbox windows, restarting the move rather than being
ignored. This is **not CPU-specific**: a human masher hits the same seam.

### 1c. The two seams compounding (the #961 Lv9 fireball lock)

Instrumented trace, Lv9 nalio vs birky, seed 3, 1800 frames
(`docs/research/cpu-lv9-noclose-findings.md`):

| Observable | Value |
|---|---|
| In `fireball` move state | 1351 frames (**75.1%**) |
| `special` (B) pressed | 121 frames (6.7%) |
| Free to walk (grounded, no move running) | **12 frames (0.7%)** |
| Dominant gap between consecutive B presses | **10 frames** (115 of ~120 gaps) |
| B presses that restarted a fireball already mid-startup | **93 of 121 (77%)** |
| Fireball reached its active frame (projectile actually thrown) | 312 frames |

The controller re-opens at frame 10 (seam 1a), the engine restarts the clock 10→1 (seam 1b),
and the loop repeats — the bot is rooted and the fireball rarely reaches its active frame.

---

## 2. Option space per seam (no decision)

### 2a. Controller — an actionability / mid-move gate

Add a "not committed" predicate to the attack-emitting branches so the bot does not press a
new attack while its own move is running (or before that move's actionable frame):

- **Signal available:** `a.current_move is not None` / `a.attack_timer > 0` (both are live
  `Player` properties derived from the `MoveClock`; `move_frame` gives progress). No new state
  needed.
- **Where the floor comes from:** replace (or AND) the `attack_period` cadence with the
  committed move's own actionable frame. For a move with an IASA (interrupt frame), that is
  the IASA; for the fireball, #1060 measured **~40f** (animation 49f, IASA 40) as the PM
  re-fire floor. pycats `nalio.neutral_b` currently has no IASA field and runs its full 48
  frames, so the practical floor today is "move complete" (`current_move is None`).
- **Expression choices:** (i) skip the attack branch entirely while `current_move is not
  None`; (ii) skip until `move_frame >= IASA` once an IASA exists; (iii) keep `attack_period`
  but clamp it to `max(attack_period, move_length_or_IASA)`. These differ in how aggressively
  a high level may buffer the next input.

### 2b. Engine — an in-progress-move guard on move-start

Add a guard so a fresh attack/special press during an uninterruptible move is **ignored**
rather than restarting the clock:

- **Signal available:** `p._clock.is_active` (`MoveClock.is_active` → `self._move is not None`),
  or `p.attack_timer > 0`, or `move_frame < IASA` once IASA data exists.
- **Placement choices:** (i) extend the line-331 state guard to also bail when a move is
  active; (ii) guard the `p._clock.start(move)` call itself; (iii) gate on IASA so a
  late-in-recovery input can interrupt (true PM special-cancel / IASA behaviour) while an
  early input is dropped.
- **Buffering variant:** instead of dropping the press, buffer it to fire on the actionable
  frame (PM input-buffer behaviour). Larger scope; noted for completeness, not required to
  stop the restart.

### 2c. Their interaction — is one sufficient?

- The **engine guard alone** stops the restart churn for *everyone* (CPU and human) — it is
  the correctness floor. With it, the controller could still *emit* wasted presses, but they
  would be ignored, so the bot would no longer be rooted; it would fall through to movement.
- The **controller gate alone** stops the CPU from emitting the wasted presses (cleaner CPU
  behaviour, less controller-side work), but leaves the engine restart reachable by a human
  masher or any other input source.
- **Both** gives PM-faithful behaviour at the source (bot doesn't mash) and at the seam
  (engine ignores a mid-move press regardless of who sent it). Whether V1 wants one or both,
  and whether the engine guard should be a hard drop or an IASA-aware interrupt, is the
  downstream architect's call — **#1079** — this ticket only maps the space.

---

## 3. Performance angle

The wasted work is the restart churn, not extra rendering. Each mid-move re-press that reaches
`p._clock.start(move)` re-runs `MoveClock._compute_windows(move)` (a dict-building pass over
the move's hitboxes) and resets `_spawned_starts` / `hit_registry` — then the move ticks from
frame 0 again. In the pinned repro that is happening on the order of the **93 restarts / 1800
frames** measured in #961 (plus every non-restarting re-press that still calls `start()`), and
the fighter never leaves the fireball state to do anything useful on ~75% of frames.

The churn is bounded and small in absolute CPU terms (a handful of dict comprehensions over a
one-hitbox move), so the primary cost is **behavioural, not throughput**: the bot burns its
whole engagement rooted in a move that never resolves. A guard at either seam removes the
redundant `start()` calls and lets the bot progress. (Moderate-depth estimate from the #961
instrumentation; a fresh restarts/sec + `start()`-calls/frame measurement is a Thorough-depth
follow-up, not run here.)

---

## 4. Correctness / PM-faithfulness

- **PM ignores attack inputs during uninterruptible frames.** A move runs to its IASA before a
  new attack can start; #1060 grounded the fireball's floor at **~40 frames** (PM 3.6 datamine:
  SpecialN length 49, IASA 40). pycats gates at neither seam, so a re-press both re-emits
  (controller) and restarts (engine) well inside that floor.
- **Which seam makes pycats faithful:** the **engine guard** is what makes the *mechanic*
  PM-faithful — a mid-move press being ignored (or buffered to IASA) is exactly PM. The
  **controller gate** makes the *CPU* faithful — a skilled CPU does not throw inputs it cannot
  act on. Full fidelity wants the engine to enforce the rule and the CPU to respect it.
- **The engine restart is wrong for a human too.** Because the guard is at the shared
  `handle_actions` seam and keys only on `p.state`, a **human** mashing attack during their own
  move also restarts it — un-PM-like for any player, not just the bot. That widens the engine
  seam's motivation beyond CPU behaviour (it is a general input-handling correctness gap), and
  is the reason the engine change is *not* golden-neutral by construction (see §5).

---

## 5. Golden-safety (per seam)

- **Controller gate (2a).** CPU-side only.
  - The **fireball/specials** branch is `"specials"`-gated → **Lv9 only**; a non-Lv9 golden
    never enters it, so gating it cannot move a level-less or low-level golden.
  - The **cadenced-attack** branch (`_decide_engage`) fires for **any leveled bot**, so adding
    an actionability gate there *could* change leveled-bot goldens (a leveled bot whose
    `attack_period` currently lets it re-press mid-move would stop doing so). The **level-less
    default path** (`level=None`) has no `"specials"` and a distinct spacing/attack path — it
    must be verified byte-identical, but is the likely-safe case. **Flag:** enumerate the
    leveled-bot sim goldens and confirm which (if any) move before committing a controller gate.
- **Engine guard (2b).** Touches the **shared** move-start seam — every fixed-input golden and
  the render-parity oracle route move-start through `handle_actions` → `p._clock.start`. Any
  golden whose frozen input list re-presses attack during an active move will change. **This
  change is not golden-neutral by construction** and must be verified byte-identical across the
  full suite (sim goldens + `test_battle_screen_render.py` render parity); any golden that moves
  has to be inspected to confirm the new (PM-faithful, non-restarting) behaviour is the intended
  one, not a regression. Spell this out as a hard gate on the downstream DEV ticket.

---

## Sources

- **Controller:** `pycats/sim/controllers.py` — `AttackerController` (`_decide_combat`,
  `_decide_engage`), `LEVEL_PARAMS[9]` (attack_period=10).
- **Engine:** `pycats/entities/fighter_input.py` — `handle_actions` Attack/Special branch;
  `pycats/combat/move_clock.py` — `MoveClock.start`; `pycats/systems/state_engine_sc.py` —
  the `"attack"` state label.
- **PM re-fire floor:** `docs/research/pm-mario-fireball-cadence-findings.md` (#1060) —
  fireball IASA ~40f.
- **Compounded repro + numbers:** `docs/research/cpu-lv9-noclose-findings.md` (#961).

## Caveats

- Moderate depth: seams grounded in verbatim code; perf described from the #961 instrumentation
  rather than freshly measured. A restarts/sec + `start()`-calls/frame instrumentation and a
  sweep of every `AttackerController` attack branch's golden exposure are Thorough-depth
  follow-ups.
- IASA-aware options assume per-move IASA data that `nalio.neutral_b` does not yet carry (no
  IASA field today → the practical controller/engine floor is "move complete"). Wiring IASA
  into `MoveData` is its own downstream slice.
