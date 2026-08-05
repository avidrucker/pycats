# Ledge-hang (#14) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a PM-style ledge-hang state — automatic grab at a solid stage edge, a timed intangible hang, neutral getup (up), drop (down/away), and timeout — with a one-occupant lockout per edge.

**Architecture:** Self-contained fighter behavior (Architecture A). A small `Ledge` value (built from thick platforms) carries per-edge `occupied_by`. `Player.update` runs grab detection + hang-driving after `step_physics` (mirroring the prone/getup blocks) and triggers the chart via `engine.force("ledge_grab")`. A new `ledge_hang` leaf in the fighter statechart is entered by the hoisted `force_ledge_grab` event and exits on `grabbed_ledge is None`.

**Tech Stack:** Python, pygame-ce (`pygame.Rect`), statecharts-py, pytest.

## Global Constraints

- **No new dependency** — stdlib + already-vendored deps only.
- **Goldens are byte-stable** unless a change is intended and reviewed per `tests/golden/REGEN_PROTOCOL.md` (Task 7 decides ledge-in-sim).
- **Every test must be able to fail** (red without the code, green with it).
- New tuning constants are ⚠ playtest starting points, provenance-commented in `config.py`.
- Run tests with: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest <args>` (worktrees have no `.venv` — use the main repo interpreter).
- Commit style: `feat(entities): …` / `test(entities): …`; reference `#14`. Do NOT put `Closes #14` until Task 8.

---

## File Structure

- **Create** `pycats/entities/ledge.py` — `Ledge` dataclass-like value + `ledges_from_platforms(platforms)`; geometry helpers (`catch_rect`, `hang_topleft`, `getup_topleft`, `facing_toward_stage`, `away_dir`).
- **Modify** `pycats/config.py` — `LEDGE_CATCH_W/H`, `LEDGE_HANG_FRAMES`, `LEDGE_REGRAB_LOCKOUT_FRAMES`.
- **Modify** `pycats/entities/fighter.py` — fields `grabbed_ledge`, `ledge_hang_timer`, `ledge_regrab_lockout_timer`.
- **Modify** `pycats/charts/fighter_chart.py` — `ledge_hang` leaf + hoisted `on("force_ledge_grab", "ledge_hang")`.
- **Modify** `pycats/systems/state_engine_sc.py` — add `"ledge_hang"` to `LABELS`.
- **Modify** `pycats/entities/player.py` — `update(..., ledges=())`; grab-detection + hang-driving block; helper `_update_ledge_hang`.
- **Modify** `pycats/battle_screen.py`, `pycats/sim/runner.py` — build ledges from platforms, pass to `update` (sim gated by Task 7).
- **Create** `tests/test_ledge_hang.py` — all new tests.

LEFT-edge convention: off-stage is to the **left**; fighter faces **right** when hanging; "away" = hold **left**. RIGHT-edge mirrors.

---

### Task 1: `Ledge` value + geometry + `ledges_from_platforms`

**Files:**
- Create: `pycats/entities/ledge.py`
- Modify: `pycats/config.py` (append constants)
- Test: `tests/test_ledge_hang.py`

**Interfaces:**
- Produces:
  - `LEFT = "left"`, `RIGHT = "right"` (module constants).
  - `class Ledge` with attrs `side: str`, `ax: int`, `ay: int` (corner anchor), `occupied_by` (default `None`), and methods:
    - `catch_rect() -> pygame.Rect`
    - `hang_topleft(size) -> tuple[int,int]` (size = `(w, h)`)
    - `getup_topleft(size) -> tuple[int,int]`
    - `facing_right() -> bool`
    - `away_held(left_held, right_held) -> bool`
  - `ledges_from_platforms(platforms) -> list[Ledge]` — one LEFT + one RIGHT per `thin == False` platform.
- Consumes: `config.LEDGE_CATCH_W`, `config.LEDGE_CATCH_H`.

- [ ] **Step 1: Append constants to `pycats/config.py`** (after the `WAVEDASH_LANDING_LAG` block, near the dodge constants):

```python
# Ledge-hang (#14). ⚠ playtest starting points (no published PM px values; pycats
# scale). LEDGE_HANG_FRAMES doubles as the intangibility window for v1 (decay-on-
# regrab is deferred). Catch region is a box hanging off the solid-stage corner.
LEDGE_CATCH_W = 24    # px outward from the edge corner the catch box spans
LEDGE_CATCH_H = 64    # px downward from the lip the catch box spans
LEDGE_HANG_FRAMES = 120          # ~2s @60fps before auto-release (timeout)
LEDGE_REGRAB_LOCKOUT_FRAMES = 30 # post-release frames grab is suppressed
```

- [ ] **Step 2: Write the failing test** in `tests/test_ledge_hang.py`:

```python
import pygame
import pytest
from pycats.entities.ledge import Ledge, LEFT, RIGHT, ledges_from_platforms
from pycats.entities.platform import Platform
from pycats import config


def _thick(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=False)


def _thin(x, y, w, h):
    return Platform(pygame.Rect(x, y, w, h), thin=True)


def test_ledges_from_platforms_only_thick_yields_two_edges():
    plats = [_thick(80, 410, 800, 80), _thin(0, 300, 150, 20)]
    ledges = ledges_from_platforms(plats)
    sides = sorted(l.side for l in ledges)
    assert sides == [LEFT, RIGHT]                 # exactly the thick platform's 2 edges
    left = next(l for l in ledges if l.side == LEFT)
    right = next(l for l in ledges if l.side == RIGHT)
    assert (left.ax, left.ay) == (80, 410)        # top-left corner
    assert (right.ax, right.ay) == (880, 410)     # top-right corner


def test_catch_rect_sits_off_stage_side_and_below_lip():
    left = Ledge(LEFT, 80, 410)
    r = left.catch_rect()
    assert r.right == 80 and r.left == 80 - config.LEDGE_CATCH_W   # left of corner
    assert r.top == 410 and r.height == config.LEDGE_CATCH_H        # lip and below
    right = Ledge(RIGHT, 880, 410)
    rr = right.catch_rect()
    assert rr.left == 880 and rr.width == config.LEDGE_CATCH_W      # right of corner


def test_hang_and_getup_positions_and_facing():
    size = (40, 60)
    left = Ledge(LEFT, 80, 410)
    assert left.facing_right() is True                       # face the stage (right)
    assert left.hang_topleft(size) == (80 - 40, 410)         # body off the left lip
    assert left.getup_topleft(size) == (80, 410 - 60)        # standing on the lip
    right = Ledge(RIGHT, 880, 410)
    assert right.facing_right() is False
    assert right.hang_topleft(size) == (880, 410)
    assert right.getup_topleft(size) == (880 - 40, 410 - 60)


def test_away_held_is_off_stage_direction():
    assert Ledge(LEFT, 80, 410).away_held(left_held=True, right_held=False) is True
    assert Ledge(LEFT, 80, 410).away_held(left_held=False, right_held=True) is False
    assert Ledge(RIGHT, 880, 410).away_held(left_held=False, right_held=True) is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest tests/test_ledge_hang.py -q`
Expected: FAIL — `ModuleNotFoundError: pycats.entities.ledge`.

- [ ] **Step 4: Create `pycats/entities/ledge.py`:**

```python
"""Grabbable stage edges (#14). A Ledge is a solid platform's top corner plus a
catch region and the hang/getup geometry. occupied_by enforces the one-occupant
lockout (PM edge-hog without trump; trump is a deferred follow-up)."""
from __future__ import annotations

import pygame  # type: ignore

from .. import config

LEFT = "left"
RIGHT = "right"


class Ledge:
    def __init__(self, side: str, ax: int, ay: int):
        self.side = side
        self.ax = ax          # corner anchor x (stage edge)
        self.ay = ay          # corner anchor y (lip / platform top)
        self.occupied_by = None

    def catch_rect(self) -> pygame.Rect:
        w, h = config.LEDGE_CATCH_W, config.LEDGE_CATCH_H
        left = self.ax - w if self.side == LEFT else self.ax
        return pygame.Rect(left, self.ay, w, h)

    def hang_topleft(self, size):
        w, _h = size
        x = self.ax - w if self.side == LEFT else self.ax
        return (x, self.ay)

    def getup_topleft(self, size):
        w, h = size
        x = self.ax if self.side == LEFT else self.ax - w
        return (x, self.ay - h)

    def facing_right(self) -> bool:
        return self.side == LEFT          # face toward the stage

    def away_held(self, left_held: bool, right_held: bool) -> bool:
        return left_held if self.side == LEFT else right_held


def ledges_from_platforms(platforms):
    ledges = []
    for p in platforms:
        if getattr(p, "thin", False):
            continue
        r = p.rect
        ledges.append(Ledge(LEFT, r.left, r.top))
        ledges.append(Ledge(RIGHT, r.right, r.top))
    return ledges
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest tests/test_ledge_hang.py -q`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add pycats/entities/ledge.py pycats/config.py tests/test_ledge_hang.py
git commit -m "feat(entities): Ledge value + grabbable-edge geometry (#14)"
```

---

### Task 2: Fighter fields + `ledge_hang` statechart leaf + LABELS

**Files:**
- Modify: `pycats/entities/fighter.py` (init block ~line 124-135)
- Modify: `pycats/charts/fighter_chart.py` (add leaf + hoist event)
- Modify: `pycats/systems/state_engine_sc.py:9-11` (LABELS)
- Test: `tests/test_ledge_hang.py`

**Interfaces:**
- Produces: `Fighter.grabbed_ledge` (default `None`), `Fighter.ledge_hang_timer: int` (0), `Fighter.ledge_regrab_lockout_timer: int` (0). New flat state label `"ledge_hang"`. Engine event `force_ledge_grab` (via `engine.force("ledge_grab")`).
- Consumes: existing `engine.force(label)` seam, `fighter.invulnerable`, `fighter.on_ground`.

- [ ] **Step 1: Add the shared test scaffolding** at the top of `tests/test_ledge_hang.py` (verified verbatim against `tests/test_prone.py` — `Player` ctor is `(x, y, controls: dict, color, eye_color, char_name, facing_right=True, fighter_data=None)`; `InputFrame` is `pycats.core.input.InputFrame(held, pressed, released)`):

```python
from pycats.entities import Player
from pycats.core.input import InputFrame

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _player():
    return Player(200, 200, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def _frame(*keys):
    ks = {_CONTROLS[k] for k in keys}
    return InputFrame(held=set(ks), pressed=set(ks), released=set())


def _empty_frame():
    return _frame()                       # nothing held


def _frame_up(p):    return _frame("up")
def _frame_down(p):  return _frame("down")
def _frame_left(p):  return _frame("left")


def p_attack_group():
    return pygame.sprite.Group()
```

- [ ] **Step 2: Write the failing tests** (append):

```python
def test_force_ledge_grab_enters_hang_and_exits():
    p = _player()
    p.fighter.grabbed_ledge = object()      # stand-in: "is hanging"
    p.fighter.on_ground = False
    p.engine.force("ledge_grab")
    assert p.state == "ledge_hang"
    # release while airborne -> fall
    p.fighter.grabbed_ledge = None
    p.engine.tick(None)
    assert p.state == "fall"


def test_ledge_hang_release_on_ground_goes_idle():
    p = _player()
    p.fighter.grabbed_ledge = object()
    p.fighter.on_ground = False
    p.engine.force("ledge_grab")
    assert p.state == "ledge_hang"
    p.fighter.grabbed_ledge = None
    p.fighter.on_ground = True
    p.engine.tick(None)
    assert p.state == "idle"


def test_fighter_ledge_fields_default():
    p = _player()
    assert p.fighter.grabbed_ledge is None
    assert p.fighter.ledge_hang_timer == 0
    assert p.fighter.ledge_regrab_lockout_timer == 0
```

- [ ] **Step 3: Run to verify failure**

Run: `... -m pytest tests/test_ledge_hang.py::test_force_ledge_grab_enters_hang_and_exits -q`
Expected: FAIL — state never becomes `"ledge_hang"` (label missing / leaf absent).

- [ ] **Step 4a: Add fields** in `pycats/entities/fighter.py` after `self.landing_lag_timer = 0` (line ~130):

```python
        self.grabbed_ledge = None  # the Ledge being held, or None (#14); the
        # presence of this is the authoritative "am I hanging" signal.
        self.ledge_hang_timer = 0  # hang timeout + intangibility window (#14)
        self.ledge_regrab_lockout_timer = 0  # post-release regrab suppression (#14)
```

- [ ] **Step 4b: Add `"ledge_hang"` to LABELS** in `pycats/systems/state_engine_sc.py`:

```python
LABELS = ("idle", "run", "crouch", "jump", "fall", "shield", "dodge", "ko",
          "hurt", "stun", "prone", "getup_roll", "getup_attack", "helpless",
          "landing_lag", "ledge_hang")
```

- [ ] **Step 4c: Add the leaf + hoist the event** in `pycats/charts/fighter_chart.py`. After the `landing_lag` leaf definition (~line 289) add:

```python
    # Ledge-hang (#14): force-entry via force_ledge_grab (player.update detects the
    # grab and sends it, mirroring force_prone). The hang holds while grabbed_ledge
    # is set; player.update releases it (getup repositions onto the stage -> idle;
    # drop/timeout -> airborne -> fall). Intangibility reuses `invulnerable`, so the
    # defensive_status region flips to intangible for free.
    ledge_hang = state(
        {"id": "ledge_hang"},
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and p.fighter.on_ground, "idle"),
        _tick(lambda e, d: p.fighter.grabbed_ledge is None and not p.fighter.on_ground, "fall"),
    )
```

Add `on("force_ledge_grab", "ledge_hang")` to the `action` compound (beside `on("force_prone", "prone")`), and add `ledge_hang` to `action`'s child list (after `landing_lag`):

```python
    action = state(
        {"id": "action", "initial": "idle"},
        on("force_ko", "ko"),
        on("force_idle", "idle"),
        on("force_prone", "prone"),
        on("force_ledge_grab", "ledge_hang"),
        actionable,
        attacking,
        dodging,
        hitstun,
        ko,
        prone,
        getup_roll,
        getup_attack,
        helpless,
        landing_lag,
        ledge_hang,
    )
```

- [ ] **Step 5: Run tests to verify pass**

Run: `... -m pytest tests/test_ledge_hang.py -q`
Expected: PASS (all Task 1 + Task 2 tests).

- [ ] **Step 6: Commit**

```bash
git add pycats/entities/fighter.py pycats/charts/fighter_chart.py pycats/systems/state_engine_sc.py tests/test_ledge_hang.py
git commit -m "feat(entities): ledge_hang fighter fields + statechart leaf (#14)"
```

---

### Task 3: Automatic grab detection in `Player.update`

**Files:**
- Modify: `pycats/entities/player.py` (signature line 189; insert after `step_physics` line 284)
- Test: `tests/test_ledge_hang.py`

**Interfaces:**
- Consumes: `Ledge`, `ledges_from_platforms`, `config.LEDGE_HANG_FRAMES`. `Player.update(..., ledges=())`.
- Produces: a grabbed fighter has `grabbed_ledge` set, `ledge_hang_timer == LEDGE_HANG_FRAMES`, `invulnerable == True`, position == `ledge.hang_topleft`, `vel == (0,0)`, `state == "ledge_hang"`, `ledge.occupied_by is p`.

- [ ] **Step 1: Write the failing test** (append; reuses the Task-2 scaffolding — `_player`, `_frame*`, `p_attack_group` — plus `ledges_from_platforms`/`Platform` already imported in Task 1):

```python
def _stage():
    return [Platform(pygame.Rect(80, 410, 800, 80), thin=False)]


def test_descending_into_left_catch_region_grabs():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    # place the body just left of the left lip, descending
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.x, p.fighter.vel.y = 0, 5
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state == "ledge_hang"
    assert p.fighter.invulnerable is True
    assert p.fighter.ledge_hang_timer == config.LEDGE_HANG_FRAMES
    assert (p.rect.left, p.rect.top) == (40, 410)         # snapped to hang_topleft
    assert ledges[0].occupied_by is p or ledges[1].occupied_by is p


def test_rising_does_not_grab():
    plats = _stage()
    ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420)
    p.fighter.vel.y = -5            # rising
    p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p.state != "ledge_hang"
    assert p.fighter.grabbed_ledge is None
```

- [ ] **Step 2: Run to verify failure**

Run: `... -m pytest tests/test_ledge_hang.py::test_descending_into_left_catch_region_grabs -q`
Expected: FAIL — `update()` takes no `ledges` arg / no grab happens.

- [ ] **Step 3a: Change the signature** (`player.py:189`):

```python
    def update(self, input_frame, platforms, attack_group, ledges=()):
```

- [ ] **Step 3b: Add an imports line** near the other entity imports at the top of `player.py`:

```python
from .ledge import Ledge  # noqa: F401  (type ref only; detection uses passed ledges)
from ..config import (LEDGE_HANG_FRAMES, LEDGE_REGRAB_LOCKOUT_FRAMES)
```

(Append these names to the existing config import if one already exists — do not duplicate the import statement.)

- [ ] **Step 3c: Insert grab detection** right after `step_physics(self, platforms, held)` (line 284):

```python
        # ---------- ledge grab (#14): automatic, PM-faithful ----------
        # After physics so on_ground/vel/pos are final. Grab when airborne +
        # descending + body overlaps a free edge's catch box + not locked out.
        if (self.fighter.grabbed_ledge is None
                and self.fighter.ledge_regrab_lockout_timer == 0
                and not self.fighter.on_ground
                and self.fighter.vel.y >= 0):
            for ledge in ledges:
                if ledge.occupied_by is not None:
                    continue                       # one-occupant lockout
                if self.rect.colliderect(ledge.catch_rect()):
                    self.rect.topleft = ledge.hang_topleft(self.rect.size)
                    self.fighter.vel.x = 0
                    self.fighter.vel.y = 0
                    self.fighter.ledge_hang_timer = LEDGE_HANG_FRAMES
                    self.fighter.invulnerable = True
                    self.fighter.facing_right = ledge.facing_right()
                    self.fighter.grabbed_ledge = ledge
                    ledge.occupied_by = self
                    self.engine.force("ledge_grab")
                    break
```

- [ ] **Step 4: Run tests to verify pass**

Run: `... -m pytest tests/test_ledge_hang.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pycats/entities/player.py tests/test_ledge_hang.py
git commit -m "feat(entities): automatic ledge grab detection in Player.update (#14)"
```

---

### Task 4: Hang driving — getup / drop / timeout + lockout + pin

**Files:**
- Modify: `pycats/entities/player.py` (action gate ~line 261-263; insert hang handling before `step_physics`; lockout decrement near the other timer ticks)
- Test: `tests/test_ledge_hang.py`

**Interfaces:**
- Consumes: `Fighter.grabbed_ledge`, `ledge_hang_timer`, `ledge_regrab_lockout_timer`, `config.LEDGE_REGRAB_LOCKOUT_FRAMES`.
- Produces: getup → on stage + `idle`; drop/timeout → airborne + `fall` + `ledge_regrab_lockout_timer == LEDGE_REGRAB_LOCKOUT_FRAMES`; edge freed (`occupied_by is None`) on every release.

- [ ] **Step 1: Write the failing tests** (append; uses the Task-2 `_frame_up`/`_frame_down`/`_frame_left` helpers):

```python
def test_getup_climbs_onto_stage_and_idles():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420); p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)   # grab
    assert p.state == "ledge_hang"
    p.update(_frame_up(p), plats, p_attack_group(), ledges)     # press up -> getup
    assert p.fighter.grabbed_ledge is None
    assert ledges[0].occupied_by is None and ledges[1].occupied_by is None
    assert p.fighter.invulnerable is False
    assert p.state == "idle"


def test_drop_releases_into_fall_with_lockout():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420); p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)   # grab on LEFT
    p.update(_frame_down(p), plats, p_attack_group(), ledges)   # press down -> drop
    assert p.fighter.grabbed_ledge is None
    assert p.fighter.ledge_regrab_lockout_timer == config.LEDGE_REGRAB_LOCKOUT_FRAMES
    assert p.state == "fall"


def test_timeout_auto_releases():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420); p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    p.fighter.ledge_hang_timer = 1                              # force imminent timeout
    p.update(_empty_frame(), plats, p_attack_group(), ledges)   # tick to 0 -> release
    assert p.fighter.grabbed_ledge is None
    assert p.state == "fall"


def test_regrab_lockout_blocks_immediate_regrab():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p = _player()
    p.rect.topleft = (80 - 40, 420); p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)
    p.update(_frame_down(p), plats, p_attack_group(), ledges)   # drop -> lockout armed
    p.rect.topleft = (80 - 40, 420); p.fighter.vel.y = 5; p.fighter.on_ground = False
    p.update(_empty_frame(), plats, p_attack_group(), ledges)   # in region again
    assert p.fighter.grabbed_ledge is None                      # blocked by lockout
```

- [ ] **Step 2: Run to verify failure**

Run: `... -m pytest tests/test_ledge_hang.py::test_getup_climbs_onto_stage_and_idles -q`
Expected: FAIL — no getup handling yet (stays `ledge_hang`).

- [ ] **Step 3a: Exclude `ledge_hang` from the action/move gate.** In `player.py` ~line 262, add `"ledge_hang"` to the excluded-state tuple:

```python
                and self.state not in ("dodge", "hurt", "stun", "prone",
                                       "getup_roll", "getup_attack", "ledge_hang")):
```

- [ ] **Step 3b: Pin + drive the hang.** Insert immediately BEFORE `step_physics(self, platforms, held)` (line 284):

```python
        # ---------- ledge-hang driving (#14) ----------
        # While hanging: pin position (skip gravity), tick the hang timer, and read
        # the two options. Up = neutral getup (climb on). Down or away = drop. The
        # timer reaching 0 auto-releases like a drop. Release frees the edge.
        if self.fighter.grabbed_ledge is not None:
            ledge = self.fighter.grabbed_ledge
            self.fighter.vel.x = 0
            self.fighter.vel.y = 0
            if self.fighter.ledge_hang_timer > 0:
                self.fighter.ledge_hang_timer -= 1
            up = self._pressed(held, "up")
            down = self._pressed(held, "down")
            away = ledge.away_held(self._pressed(held, "left"),
                                   self._pressed(held, "right"))
            if up:                                   # neutral getup
                self.rect.topleft = ledge.getup_topleft(self.rect.size)
                self.fighter.invulnerable = False
                ledge.occupied_by = None
                self.fighter.grabbed_ledge = None
            elif down or away or self.fighter.ledge_hang_timer == 0:   # drop / timeout
                self.fighter.invulnerable = False
                self.fighter.ledge_regrab_lockout_timer = LEDGE_REGRAB_LOCKOUT_FRAMES
                ledge.occupied_by = None
                self.fighter.grabbed_ledge = None
                self.fighter.vel.y = 1               # nudge so next frame is airborne
```

(`self._pressed(set, name)` is the existing input helper used elsewhere in `player.py`; confirm its signature there and match it.)

- [ ] **Step 3c: Skip physics while still hanging.** Change the `step_physics` call to:

```python
        if self.fighter.grabbed_ledge is None:
            step_physics(self, platforms, held)
```

(If still hanging after the block above, position stays pinned; if released this frame, physics runs and resolves on_ground/fall.)

- [ ] **Step 3d: Decrement the regrab lockout.** Add beside the other timer ticks (after the `landing_lag_timer` tick ~line 322):

```python
        if self.fighter.ledge_regrab_lockout_timer > 0:
            self.fighter.ledge_regrab_lockout_timer -= 1
```

- [ ] **Step 4: Run tests to verify pass**

Run: `... -m pytest tests/test_ledge_hang.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pycats/entities/player.py tests/test_ledge_hang.py
git commit -m "feat(entities): ledge-hang getup/drop/timeout + regrab lockout (#14)"
```

---

### Task 5: One-occupant lockout across two fighters

**Files:**
- Test: `tests/test_ledge_hang.py` (behavior already implemented in Tasks 3-4 via `occupied_by`; this task proves the cross-fighter case)

**Interfaces:**
- Consumes: Task 3 grab + Task 4 release.

- [ ] **Step 1: Write the failing test** (append):

```python
def test_occupied_edge_blocks_second_grabber():
    plats = _stage(); ledges = ledges_from_platforms(plats)
    p1 = _player(); p2 = _player()
    # p1 grabs the LEFT edge
    p1.rect.topleft = (80 - 40, 420); p1.fighter.vel.y = 5; p1.fighter.on_ground = False
    p1.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p1.state == "ledge_hang"
    # p2 enters the SAME left catch region while p1 holds it
    p2.rect.topleft = (80 - 40, 420); p2.fighter.vel.y = 5; p2.fighter.on_ground = False
    p2.update(_empty_frame(), plats, p_attack_group(), ledges)
    assert p2.fighter.grabbed_ledge is None     # blocked: one occupant per edge
    assert p2.state != "ledge_hang"
```

- [ ] **Step 2: Run to verify it passes immediately** (logic from Task 3's `occupied_by` check)

Run: `... -m pytest tests/test_ledge_hang.py::test_occupied_edge_blocks_second_grabber -q`
Expected: PASS. If it FAILS, the `occupied_by is not None: continue` guard in Task 3 is wrong — fix there.

- [ ] **Step 3: Commit**

```bash
git add tests/test_ledge_hang.py
git commit -m "test(entities): one-occupant ledge lockout across two fighters (#14)"
```

---

### Task 6: Wire the live game (battle_screen) to build + pass ledges

**Files:**
- Modify: `pycats/battle_screen.py` (build ledges once from platforms; pass at `:87`)
- Test: manual run (Task 8) — no golden change here (sim wiring is Task 7)

**Interfaces:**
- Consumes: `ledges_from_platforms`.

- [ ] **Step 1: Build ledges where platforms are owned** in `battle_screen.py` (near where `platforms` is set up). Add:

```python
from .entities.ledge import ledges_from_platforms
...
        self.ledges = ledges_from_platforms(platforms)   # solid-edge ledges (#14)
```

- [ ] **Step 2: Pass them in the update call** (`battle_screen.py:87`):

```python
            p.update(frame_input, platforms, self.attacks, self.ledges)
```

- [ ] **Step 3: Run the full suite** (no behavior change to existing tests expected)

Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest -q`
Expected: PASS (goldens unaffected — sim/runner not yet wired).

- [ ] **Step 4: Commit**

```bash
git add pycats/battle_screen.py
git commit -m "feat(screens): build + pass solid-edge ledges in battle_screen (#14)"
```

---

### Task 7: Sim/golden decision (measure, then choose)

**Files:**
- Modify (conditionally): `pycats/sim/runner.py:134`
- Modify (if regen): `tests/golden/*.json`, `tests/golden/*.summary.json`

**Interfaces:** none new.

- [ ] **Step 1: Temporarily wire ledges into the sim to MEASURE impact.** In `sim/runner.py`, build `ledges = ledges_from_platforms(platforms)` and pass to `p.update(fi, platforms, attacks, ledges)`.

- [ ] **Step 2: Run the golden suite and read the SEMANTIC diff first:**

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest tests/test_golden.py tests/test_golden_summary.py -q
git diff tests/golden/*.summary.json   # if it regenerated locally; else inspect failures
```

- [ ] **Step 3: Decide (record the choice in the commit message):**
  - **If goldens are UNCHANGED** → keep the sim wiring (faithful + free). Done.
  - **If goldens change** → follow `tests/golden/REGEN_PROTOCOL.md`: confirm every changed `summary.json` field is a genuine ledge-grab consequence (a fighter that previously fell to a KO now hangs/recovers). If the diff is a small, fully-explained semantic change, regen with `PYCATS_UPDATE_GOLDENS=1 …` and explain it in the commit. **If the diff is a large cascading trajectory change that cannot be cleanly justified** → REVERT the sim wiring (leave `sim/runner.py` passing no ledges, `ledges=()` default), so the golden scenarios stay byte-identical; the feature stays fully covered by `tests/test_ledge_hang.py`, and "exercise ledges in the golden sims" becomes a deferred follow-up. Document this divergence in the commit + the close comment.

- [ ] **Step 4: Run the full suite**

Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit** (message states the decision + evidence)

```bash
git add -A
git commit -m "test(sim): wire ledges into sim + golden decision (#14) — <unchanged | semantic regen | reverted, divergence documented>"
```

---

### Task 8: Manual verify, file deferred follow-ups, close

- [ ] **Step 1: Manual smoke-run** the live game and grab a ledge:

```
REPO=/home/avi/Documents/Study/Python/pycats
PY="$REPO/.venv/bin/python"
"$PY" -m pycats.game
```

- [ ] **Step 2: Revert-the-fix check** on one regression test (prove able-to-fail): temporarily neutralize the grab block (comment the `self.engine.force("ledge_grab")` line), confirm `test_descending_into_left_catch_region_grabs` FAILS, then restore.

- [ ] **Step 3: File deferred follow-up tickets** (`enhancement, area:entities`, referencing #14): ledge roll, ledge attack, ledge jump (the 3 remaining getups); intangibility decay-on-regrab; ledge-trump (flips the one-occupant lockout); the "2-frame"; teching; up-B sweetspot; hold-away-to-decline + frame-accurate getup window; and (if Task 7 reverted) "exercise ledges in the golden sims".

- [ ] **Step 4: Final commit + close** (squash already per-task; ensure a commit body carries `Closes #14`, then `pmtools close 14`). Post the closing comment from the main checkout.

---

## Self-Review

**Spec coverage:** Ledge model + solid-edges-only (Task 1); fighter fields + intangibility-reuse + statechart leaf + LABELS (Task 2); automatic descending grab + golden-risk handling (Tasks 3, 7); hang pin + getup + drop + timeout + regrab lockout (Task 4); one-occupant lockout (Tasks 3+5); input lock while hanging (Task 4 step 3a); ⚠-playtest constants (Task 1); full TDD test list (Tasks 1-5); golden REGEN handling (Task 7); deferred follow-ups (Task 8). All spec sections map to a task.

**Placeholder scan:** Two intentional "match the existing helper verbatim" notes (Player construction, `_pressed`/`InputFrame`/attack-group, control-key frame helpers) point the implementer at `tests/test_prone.py` rather than guessing — these are real, existing patterns, not unspecified work.

**Type consistency:** `grabbed_ledge`/`ledge_hang_timer`/`ledge_regrab_lockout_timer`, `engine.force("ledge_grab")` → `force_ledge_grab` event → `"ledge_hang"` label, and `Ledge.catch_rect/hang_topleft/getup_topleft/facing_right/away_held` names are used identically across Tasks 1-5.
