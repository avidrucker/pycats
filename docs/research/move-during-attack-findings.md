# Horizontal movement during an attack's active / recovery frames (ground + air)

**Ticket:** #922 (research) · **Role:** RESEARCH · **area:combat**
**Question:** Can a fighter move left/right while mid-attack — on the ground vs. in the
air, in the startup / active / recovery phases? This is a **behavior audit** of the
as-implemented code; it proposes no changes.

## TL;DR

| Medium | Startup | Active | Recovery |
|--------|---------|--------|----------|
| **Ground** | No new walk (input-locked); residual momentum bleeds off | No new walk (input-locked); residual momentum bleeds off | No new walk (input-locked); residual momentum bleeds off |
| **Air** | Full air drift (unchanged) | Full air drift (unchanged) | Full air drift (unchanged) |

- **On the ground, a fighter cannot walk during *any* phase of a normal attack.** The
  lock spans the whole move (startup + active + recovery), not just the active window.
- **Residual-only:** friction still runs, so momentum the fighter *already had* when the
  move started keeps sliding it, decaying by half each frame — but it can't add or
  redirect movement with new input.
- **In the air, nothing changed:** an aerial attack keeps full left/right air drift in
  every phase. The rooting is `on_ground`-gated.

## Why the phases collapse into one answer

The movement lock reads `attack_timer`, and `attack_timer` runs for the *entire* move —
all three phases — not just the active window. From `pycats/combat/move_clock.py`:

> `remaining == total - frame` (i.e. the legacy `attack_timer` equals `total - move_frame`).

> The active window is `startup < frame <= startup + active` and the move completes
> (becomes inactive) when `frame >= startup + active + recovery`.

So `total == startup + active + recovery`, and `attack_timer > 0` is true from the move's
first frame through the last recovery frame. Any gate written as `attack_timer > 0`
therefore treats startup, active, and recovery identically — which is why the grid above
has one grounded answer, not three.

## Ground: input-locked for the whole move (the #898 rooting)

`FighterInput.handle_move` (`pycats/entities/fighter_input.py`) passes `locked=True` to
`step_horizontal` whenever a grounded attack clock is running:

```python
locked=p.state
in (
    "shield",
    "crouch",
    "helpless",
    "smash_charge",
)  # no walking while shielding/crouching (#124), helpless (#184), or charging a smash (#327/3a)
# A grounded normal roots the fighter (#898): `handle_actions` starts
# the move, then this runs the SAME frame — held left/right must not
# apply walk speed ...
or (p.attack_timer > 0 and p.fighter.on_ground),
```

`handle_move` is called every non-hitstun frame from `Player.update`
(`pycats/entities/player.py`):

```python
if not dodge_initiated:
    self.handle_move(held)
```

## Residual momentum: friction still bleeds, input can't add

`locked` only suppresses the *walk-speed assignment*; friction (step 1 of
`step_horizontal`, `pycats/systems/movement.py`) always runs first:

```python
# 1) friction
vel = apply_horizontal_friction(vel, on_ground)
...
if not locked:
    if press_left:
        vel.x = -move_speed
    elif press_right:
        vel.x = move_speed
```

So a fighter that was walking or dashing when the move started keeps sliding, decaying by
`GROUND_FRICTION` each frame (`pycats/core/physics.py`, `apply_horizontal_friction`):
`vel.x *= factor` with `GROUND_FRICTION = 0.5`, snapping to 0 once `abs(vel.x) <
VEL_DEADZONE` (`0.05`). From a full walk (`MOVE_SPEED = 6`) that is:
`6 → 3 → 1.5 → 0.75 → 0.375 → 0.1875 → 0.094 → 0.047 < 0.05 → 0` — about **7 frames** of
slide, and fewer from a slower start. New left/right input during those frames does
nothing; the fighter cannot re-accelerate or reverse until the move ends.

## Air: unchanged — full drift in every phase

The grounded lock is `and p.fighter.on_ground`, so an airborne attacker never trips it.
With `locked=False`, `step_horizontal` applies `vel.x = ±move_speed` on a held direction
exactly as in normal flight, subject to `AIR_FRICTION = 0.85`. An aerial's startup,
active, and recovery frames therefore keep full horizontal air control. The inline
rationale is explicit:

> `on_ground`-gated so airborne attacks keep their air drift.

## Boundaries / observations (not rulings)

- **This audit matches #898's stated intent.** #898's comment says a grounded normal
  should root the fighter (a forward-tilt should not slide ~10px) while friction bleeds
  prior momentum and aerial drift is untouched — which is exactly what the code does. No
  gap found between observed behavior and intent.
- **Separate locks exist for non-attack states** and are out of scope here: hitstun
  (`hurt_timer`/`stun_timer`) skips `handle_move` and decays via `KNOCKBACK_DECAY`;
  waveland landing-lag skips it and applies friction directly; `shield`/`crouch`/
  `helpless`/`smash_charge` lock via the `p.state` branch above. These are not attack
  active/recovery frames.
- **No PM-parity judgment is made here** on whether grounded rooting is correct vs.
  Project M — that stays a separate question. This doc reports current pycats behavior
  only.
- **Downstream (file one-at-a-time if pursued):** any bot-controller work that wants a
  grounded fighter to close distance mid-attack must do it *before* the move starts or via
  a different mechanic (pivot / dash / short-hop), because grounded walk input is inert
  for the whole move. This is the concrete constraint #903 was missing.

## Sources

- `pycats/entities/fighter_input.py` — `FighterInput.handle_move` (the `locked` set + `attack_timer > 0 and on_ground` gate)
- `pycats/entities/player.py` — `Player.update` (calls `handle_move` each non-hitstun frame)
- `pycats/systems/movement.py` — `step_horizontal` (friction-then-input order; `locked` suppresses only the walk assignment)
- `pycats/core/physics.py` — `apply_horizontal_friction` (`GROUND_FRICTION = 0.5`, `AIR_FRICTION = 0.85`, `VEL_DEADZONE = 0.05`)
- `pycats/config.py` — `MOVE_SPEED = 6`
- `pycats/combat/move_clock.py` — phase model (`attack_timer == total - frame`, `total == startup + active + recovery`)

**Refs:** #898 (grounded-attack rooting), #903 (wont-do — the vague bot-trajectory ticket
this audit re-scopes), #292 (prior forward-tilt walk-during-attack behavior).
