# Statecharts Battle Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the real pycats battle with either the hand-rolled FSM or statecharts-py behind a swappable `StateEngine` seam, prove byte-identical parity, and benchmark the per-frame cost — plus watch/video playback of the same deterministic replay.

**Architecture:** Introduce a `StateEngine` protocol with `LegacyEngine` (wraps the existing `FSM`) and `StatechartEngine` (wraps a `statecharts.Session`). `Player` reads `self.engine.state` instead of `self.fsm.state`. A headless deterministic runner drives the real per-frame loop from a scripted input timeline; pytest asserts both backends produce identical frame-by-frame snapshots; a benchmark times each. A pluggable presenter adds live/video playback via an extracted `render_battle()`.

**Tech Stack:** Python 3.10+, pygame-ce (headless via `SDL_VIDEODRIVER=dummy`), statecharts-py (sibling repo `../statecharts-py`), pytest, optional `imageio-ffmpeg` for video.

## Global Constraints

- **No new battle mechanics.** The statechart only re-expresses existing transitions; preserve all existing behavior including quirks (e.g. `"stun"` is currently unreachable — keep it unreachable).
- **Strict parity.** Legacy and statechart backends, given identical scripted input, must produce byte-identical per-frame snapshots.
- **Scope:** both fighters' action-state FSMs + match/stage state. Exclude the menu/char-select/pause screen system (`screen_manager.py` has its own separate `FSM` — do not touch it).
- **Default backend is `legacy`.** The shipping game must behave exactly as before.
- **Determinism:** no RNG anywhere; rely on deterministic float math. Snapshot equality is exact (a rounding hook is allowed only as a fallback if real float noise ever appears).
- **Statechart fidelity rules:** flat chart; atomic states named exactly the existing labels; all transitions fire on the explicit `"tick"` event; **no eventless transitions** (guarantees exactly one hop per `send("tick")`, matching the legacy `break`-after-first); guards close over the live `Player`; datamodel stays empty.
- Spec: `docs/superpowers/specs/2026-06-21-statecharts-benchmark-design.md`.

## File Structure

```
pycats/systems/state_engine.py      # NEW: StateEngine protocol, LegacyEngine, StatechartEngine, make_state_engine
pycats/systems/match_engine.py      # NEW: LegacyMatchEngine, StatechartMatchEngine, make_match_engine
pycats/statecharts/__init__.py      # NEW: package marker
pycats/statecharts/fighter_chart.py # NEW: build_fighter_chart(player) -> statecharts chart
pycats/sim/__init__.py              # NEW: package marker
pycats/sim/input_script.py          # NEW: input-timeline DSL -> per-frame InputFrame
pycats/sim/runner.py                # NEW: build_stage/build_players/run_battle + snapshot + presenters
pycats/sim/presenters.py            # NEW: HeadlessPresenter, LivePresenter, VideoPresenter
pycats/render_battle.py             # NEW: extracted draw helpers + render_battle()
bench.py                            # NEW: CLI benchmark table
watch.py                            # NEW: CLI live/video playback
conftest.py                         # NEW: pytest headless setup
tests/test_state_engine.py          # NEW
tests/test_input_script.py          # NEW
tests/test_fighter_chart.py         # NEW
tests/test_runner.py                # NEW
tests/test_parity.py                # NEW
tests/test_benchmark.py             # NEW
tests/test_render_battle.py         # NEW
--- MODIFIED ---
pycats/entities/player.py           # self.fsm -> self.engine; Player.state property; force/tick calls
pycats/core/physics.py              # resolve_player_push: a.fsm.state -> a.state
pycats/entities/tail.py             # self.player.fsm.state -> self.player.state
pycats/game.py                      # p.fsm.state -> p.state; reset force; use render_battle()
README.md                           # dependency + usage notes
```

---

## Task 1: Test harness + dependency wiring

**Files:**
- Create: `conftest.py`
- Create: `tests/test_smoke.py`
- Modify: `README.md`

**Interfaces:**
- Produces: a headless pytest environment where `import pygame` and `import statecharts` both work without a display.

- [ ] **Step 1: Install dependencies**

Run:
```bash
cd /home/avi/Documents/Study/Python/pycats
python -m pip install pytest pygame-ce
python -m pip install -e ../statecharts-py
```
Expected: all three install successfully; `statecharts` installs in editable mode.

- [ ] **Step 2: Write `conftest.py` (headless SDL before any pygame import)**

```python
# conftest.py — pytest session setup: force pygame headless so tests need no display.
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

pygame.init()
```

- [ ] **Step 3: Write the smoke test**

```python
# tests/test_smoke.py
def test_imports_headless():
    import pygame
    import statecharts
    surf = pygame.Surface((10, 10))
    assert surf.get_size() == (10, 10)
    assert hasattr(statecharts, "Session")
```

- [ ] **Step 4: Run the smoke test**

Run: `python -m pytest tests/test_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Note deps in README**

Add under a "Development / benchmarking" heading in `README.md`:
```markdown
## Development / benchmarking

Headless tests and the battle benchmark need:

    python -m pip install pytest pygame-ce
    python -m pip install -e ../statecharts-py   # sibling repo

Run tests:        python -m pytest
Run benchmark:    python bench.py
Watch a replay:   python watch.py --backend statechart
```

- [ ] **Step 6: Commit**

```bash
git add conftest.py tests/test_smoke.py README.md
git commit -m "test: headless pytest harness + statecharts-py dependency"
```

---

## Task 2: StateEngine protocol + LegacyEngine

**Files:**
- Create: `pycats/systems/state_engine.py`
- Test: `tests/test_state_engine.py`

**Interfaces:**
- Produces:
  - `class StateEngine(Protocol)` with `state: str`, `tick(self, ctx) -> None`, `force(self, label: str) -> None`.
  - `class LegacyEngine` wrapping a `pycats.systems.fsm.FSM`: constructor `LegacyEngine(fsm)`; `state` returns `fsm.state`; `tick(ctx)` calls `fsm.update(ctx)`; `force(label)` sets `fsm.state = label`.
  - `make_state_engine(player, backend="legacy") -> StateEngine` (StatechartEngine branch added in Task 5).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_state_engine.py
from pycats.systems.fsm import FSM, Transition
from pycats.systems.state_engine import LegacyEngine


def _toggle_fsm():
    return FSM(
        state="a",
        table={
            "a": [Transition("b", lambda f, ctx: ctx.get("go", False))],
            "b": [Transition("a", lambda f, ctx: ctx.get("back", False))],
        },
    )


def test_legacy_engine_delegates_state():
    eng = LegacyEngine(_toggle_fsm())
    assert eng.state == "a"


def test_legacy_engine_tick_uses_guards():
    eng = LegacyEngine(_toggle_fsm())
    eng.tick({"go": True})
    assert eng.state == "b"


def test_legacy_engine_tick_single_hop():
    # a->b fires; b->a must NOT also fire in the same tick (one hop per tick)
    eng = LegacyEngine(_toggle_fsm())
    eng.tick({"go": True, "back": True})
    assert eng.state == "b"


def test_legacy_engine_force():
    eng = LegacyEngine(_toggle_fsm())
    eng.force("b")
    assert eng.state == "b"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_state_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: pycats.systems.state_engine`.

- [ ] **Step 3: Implement `state_engine.py`**

```python
# pycats/systems/state_engine.py
"""Swappable state-machine engines behind a common interface.

LegacyEngine wraps the hand-rolled FSM. StatechartEngine (added later) wraps a
statecharts-py Session. Both expose the same tiny surface so Player can use
either interchangeably.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateEngine(Protocol):
    state: str

    def tick(self, ctx: Any) -> None: ...

    def force(self, label: str) -> None: ...


class LegacyEngine:
    """Wraps the existing pycats.systems.fsm.FSM verbatim."""

    def __init__(self, fsm) -> None:
        self._fsm = fsm

    @property
    def state(self) -> str:
        return self._fsm.state

    def tick(self, ctx: Any = None) -> None:
        self._fsm.update(ctx)

    def force(self, label: str) -> None:
        self._fsm.state = label


def make_state_engine(player, backend: str = "legacy") -> StateEngine:
    """Build the state engine for a Player. backend in {"legacy","statechart"}."""
    if backend == "statechart":
        from statecharts import Session
        from ..statecharts.fighter_chart import build_fighter_chart
        from .state_engine_sc import StatechartEngine

        return StatechartEngine(Session(build_fighter_chart(player)))
    return LegacyEngine(player._build_fsm())
```

Note: the `statechart` branch imports `StatechartEngine` and `build_fighter_chart`, which do not exist until Task 5. That is fine — the import is inside the function and only runs when `backend="statechart"`. `make_state_engine(player, "legacy")` works now.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_state_engine.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add pycats/systems/state_engine.py tests/test_state_engine.py
git commit -m "feat: StateEngine protocol + LegacyEngine"
```

---

## Task 3: Wire Player to the engine seam (behavior-preserving sweep)

**Files:**
- Modify: `pycats/entities/player.py`
- Modify: `pycats/core/physics.py`
- Modify: `pycats/entities/tail.py`
- Modify: `pycats/game.py`
- Test: `tests/test_player_seam.py`

**Interfaces:**
- Consumes: `make_state_engine` from Task 2.
- Produces: `Player.state` property (read-only label); `Player.__init__(..., state_backend="legacy")`; all engine state changes go through `self.engine`.

- [ ] **Step 1: Write the failing test (behavior baseline through the new seam)**

```python
# tests/test_player_seam.py
import pygame
from pycats.entities.player import Player
from pycats.config import P1_KEYS if False else None  # placeholder import guard

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def test_player_exposes_state_property():
    p = _mk_player()
    assert p.state == "idle"


def test_player_force_ko_sets_label():
    p = _mk_player()
    p.engine.force("ko")
    assert p.state == "ko"


def test_player_default_backend_is_legacy():
    from pycats.systems.state_engine import LegacyEngine
    p = _mk_player()
    assert isinstance(p.engine, LegacyEngine)
```

Delete the bogus `from pycats.config import P1_KEYS if False else None` line before saving — it is shown only to flag that `P1` is defined inline here. Final file starts at `import pygame` then the `P1 = dict(...)` block.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_player_seam.py -v`
Expected: FAIL (`Player` has no attribute `state` / no `engine`).

- [ ] **Step 3: Edit `player.py` — imports and constructor**

In `pycats/entities/player.py`, add to the imports near line 61 (`from ..systems.fsm import FSM, Transition`):
```python
from ..systems.fsm import FSM, Transition
from ..systems.state_engine import make_state_engine
```

Change the constructor signature (line 89-91) from:
```python
    def __init__(
        self, x, y, controls: dict, color, eye_color, char_name, facing_right=True
    ):
```
to:
```python
    def __init__(
        self, x, y, controls: dict, color, eye_color, char_name, facing_right=True,
        state_backend: str = "legacy",
    ):
```

Replace line 157 (`self.fsm = self._build_fsm()`) with:
```python
        self.engine = make_state_engine(self, state_backend)
```

Add the `state` property immediately after the constructor (after line 168, before `receive_hit`):
```python
    @property
    def state(self) -> str:
        """Current action-state label, via the active state engine."""
        return self.engine.state
```

- [ ] **Step 4: Edit `player.py` — engine calls for tick and force**

Replace line 388 (`self.fsm.update()`) with:
```python
        self.engine.tick(None)
```

Replace line 559 (`self.fsm.state = "ko"`) with:
```python
        self.engine.force("ko")
```

- [ ] **Step 5: Edit `player.py` — replace remaining reads**

Every remaining occurrence of `self.fsm.state` in `player.py` is a *read*. Replace all `self.fsm.state` with `self.state`. (Lines 220, 236, 246, 259, 297, 320, 323, 328-comment, 340, 358, 362, 366, 381, 405, 422, 436, 439, 445, 447, 508, 518, 524.) After this step, `grep -n "self.fsm" pycats/entities/player.py` must return nothing.

- [ ] **Step 6: Edit `physics.py` — resolve_player_push**

In `pycats/core/physics.py` line 112, replace:
```python
            if a.fsm.state == "dodge" or b.fsm.state == "dodge":
```
with:
```python
            if a.state == "dodge" or b.state == "dodge":
```

- [ ] **Step 7: Edit `tail.py`**

In `pycats/entities/tail.py`, replace every `self.player.fsm.state` (lines 220, 223, 228, 234) with `self.player.state`.

- [ ] **Step 8: Edit `game.py` — reads and reset force**

In `pycats/game.py`:
- Line 325: `fsm = f"FSM: {p.fsm.state.capitalize()}"` → `fsm = f"FSM: {p.state.capitalize()}"`
- Line 419: `player1.fsm.state = "idle"` → `player1.engine.force("idle")`
- Line 449: `player2.fsm.state = "idle"` → `player2.engine.force("idle")`
- Line 739: `if p.fsm.state == "shield":` → `if p.state == "shield":`
- Line 843: `if p.fsm.state == "shield":` → `if p.state == "shield":`

Leave `screen_manager.py` untouched (its `self.fsm` is the separate screen-level FSM).

- [ ] **Step 9: Run the seam test and full suite**

Run: `python -m pytest tests/test_player_seam.py tests/test_smoke.py tests/test_state_engine.py -v`
Expected: PASS. Then verify no stray references:
Run: `grep -rn "\.fsm\.state" pycats/entities pycats/core pycats/game.py`
Expected: no output.

- [ ] **Step 10: Commit**

```bash
git add pycats/entities/player.py pycats/core/physics.py pycats/entities/tail.py pycats/game.py tests/test_player_seam.py
git commit -m "refactor: route player state through StateEngine seam (legacy default)"
```

---

## Task 4: Scripted input timeline

**Files:**
- Create: `pycats/sim/__init__.py`
- Create: `pycats/sim/input_script.py`
- Test: `tests/test_input_script.py`

**Interfaces:**
- Produces:
  - `@dataclass class InputSpan: start: int; end: int; player: int; action: str` (`player` is 1 or 2; `action` in `{"left","right","up","down","attack","shield"}`; active for frames `start <= f < end`).
  - `compile_timeline(spans, keymaps) -> list[InputFrame]` where `keymaps = [p1_controls, p2_controls]`; returns one `InputFrame` per frame from 0..max(end). Each frame has correct `held`/`pressed`/`released` edges relative to the previous frame.
  - `DEFAULT_SCRIPT: list[InputSpan]` exercising walk, jump, double-jump, attack, shield, dodge variants.
  - `default_timeline(keymaps) -> list[InputFrame]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_input_script.py
import pygame
from pycats.core.input import InputFrame
from pycats.sim.input_script import InputSpan, compile_timeline

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2 = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP, down=pygame.K_DOWN,
          attack=pygame.K_SLASH, special=pygame.K_PERIOD, shield=pygame.K_COMMA)


def test_compile_length_covers_last_frame():
    frames = compile_timeline([InputSpan(0, 3, 1, "right")], [P1, P2])
    assert len(frames) == 3
    assert all(isinstance(f, InputFrame) for f in frames)


def test_held_pressed_released_edges():
    frames = compile_timeline([InputSpan(1, 3, 1, "right")], [P1, P2])
    # frame 0: nothing
    assert P1["right"] not in frames[0].held
    # frame 1: freshly pressed + held
    assert P1["right"] in frames[1].pressed
    assert P1["right"] in frames[1].held
    # frame 2: still held, not freshly pressed
    assert P1["right"] in frames[2].held
    assert P1["right"] not in frames[2].pressed


def test_release_edge_after_span_end():
    # span active frames 0..1; ensure a release edge is recorded the frame it ends
    frames = compile_timeline([InputSpan(0, 1, 1, "right")], [P1, P2])
    assert P1["right"] in frames[0].held
    # only one frame long -> no extra frame to observe release; extend:
    frames = compile_timeline([InputSpan(0, 1, 1, "right"), InputSpan(2, 3, 1, "left")], [P1, P2])
    assert P1["right"] in frames[1].released
    assert P1["right"] not in frames[1].held
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_input_script.py -v`
Expected: FAIL (`ModuleNotFoundError: pycats.sim.input_script`).

- [ ] **Step 3: Create the package marker and module**

`pycats/sim/__init__.py`:
```python
```
(empty file)

`pycats/sim/input_script.py`:
```python
"""Deterministic scripted input for headless battle replays.

A timeline is a list of InputSpans; compile_timeline turns it into one
InputFrame per frame with correct held/pressed/released edges, so the headless
runner can drive Player.update without pygame events.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..core.input import InputFrame

ACTIONS = ("left", "right", "up", "down", "attack", "shield")


@dataclass(frozen=True)
class InputSpan:
    start: int            # first frame the action is held (inclusive)
    end: int              # first frame the action is NOT held (exclusive)
    player: int           # 1 or 2
    action: str           # one of ACTIONS


def compile_timeline(spans, keymaps):
    """spans -> list[InputFrame]. keymaps = [p1_controls, p2_controls]."""
    if not spans:
        return []
    total = max(s.end for s in spans)
    # held_keys[f] = set of keycodes held on frame f
    held_per_frame = [set() for _ in range(total)]
    for s in spans:
        keymap = keymaps[s.player - 1]
        key = keymap[s.action]
        for f in range(s.start, s.end):
            held_per_frame[f].add(key)

    frames = []
    prev = set()
    for f in range(total):
        held = held_per_frame[f]
        pressed = held - prev
        released = prev - held
        frames.append(InputFrame(held=set(held), pressed=set(pressed),
                                 released=set(released)))
        prev = held
    return frames


# A scripted battle that visits every action-state. Frame numbers chosen so each
# move resolves before the next begins (timers in config.py: DODGE_TIME=14,
# HURT_TIME=12, PLAYER_ATTACK_DURATION=12).
DEFAULT_SCRIPT = [
    InputSpan(10, 40, 1, "right"),    # P1 walk/run
    InputSpan(50, 51, 1, "up"),       # P1 jump
    InputSpan(60, 61, 1, "up"),       # P1 double jump
    InputSpan(90, 91, 1, "attack"),   # P1 attack
    InputSpan(110, 140, 1, "shield"), # P1 shield
    InputSpan(120, 121, 1, "left"),   # P1 roll dodge (shield held + dir)
    InputSpan(30, 60, 2, "left"),     # P2 walk toward P1
    InputSpan(95, 96, 2, "attack"),   # P2 attack (may hit P1)
    InputSpan(150, 151, 2, "up"),     # P2 jump
]


def default_timeline(keymaps):
    return compile_timeline(DEFAULT_SCRIPT, keymaps)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_input_script.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add pycats/sim/__init__.py pycats/sim/input_script.py tests/test_input_script.py
git commit -m "feat: scripted input timeline for headless replays"
```

---

## Task 5: Fighter statechart + StatechartEngine

**Files:**
- Create: `pycats/statecharts/__init__.py`
- Create: `pycats/statecharts/fighter_chart.py`
- Create: `pycats/systems/state_engine_sc.py`
- Test: `tests/test_fighter_chart.py`

**Interfaces:**
- Consumes: `statecharts.statechart`, `statecharts.state`, `statecharts.transition`, `statecharts.on`, `statecharts.Session`.
- Produces:
  - `build_fighter_chart(player) -> StateNode` — flat chart mirroring `Player._build_fsm()` exactly, all transitions on event `"tick"`, plus `on("force_ko","ko")` and `on("force_idle","idle")` on every state; guards close over `player`.
  - `class StatechartEngine` (`state_engine_sc.py`): `StatechartEngine(session)`; `state` scans labels via `session.in_state`; `tick(ctx)` → `session.send("tick")`; `force(label)` → `session.send("force_" + label)`.
  - `LABELS = ("idle","run","jump","fall","shield","dodge","ko","hurt","stun","attack")`.

- [ ] **Step 1: Write the failing test (statechart matches legacy on crafted scenarios)**

```python
# tests/test_fighter_chart.py
import pygame
from pycats.entities.player import Player
from pycats.systems.state_engine import LegacyEngine
from pycats.systems.state_engine_sc import StatechartEngine
from pycats.statecharts.fighter_chart import build_fighter_chart
from statecharts import Session

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player(backend):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def test_initial_state_idle():
    p = _mk_player("statechart")
    assert isinstance(p.engine, StatechartEngine)
    assert p.state == "idle"


def test_idle_to_run_on_velocity():
    # idle -> run requires vel.x != 0 and on_ground
    p = _mk_player("statechart")
    p.vel.x = 5
    p.on_ground = True
    p.engine.tick(None)
    assert p.state == "run"


def test_single_hop_per_tick():
    # From idle with attack_timer set, first tick -> attack (not multi-hop onward)
    p = _mk_player("statechart")
    p.attack_timer = 5
    p.engine.tick(None)
    assert p.state == "attack"


def test_force_ko_and_recover():
    p = _mk_player("statechart")
    p.engine.force("ko")
    assert p.state == "ko"
    # ko -> idle requires is_alive on next tick
    p.is_alive = True
    p.engine.tick(None)
    assert p.state == "idle"


def test_matches_legacy_across_scenarios():
    # Drive identical attribute snapshots through both engines, compare labels.
    scenarios = [
        dict(vel=(5, 0), on_ground=True),                 # -> run
        dict(vel=(0, -5), on_ground=False),               # -> jump
        dict(vel=(0, 5), on_ground=False),                # -> fall
        dict(shield_attempting=True, on_ground=True),     # -> shield
        dict(hurt_timer=5),                               # -> hurt
        dict(attack_timer=5),                             # -> attack
    ]
    for sc in scenarios:
        legacy = _mk_player("legacy")
        sch = _mk_player("statechart")
        for p in (legacy, sch):
            vx, vy = sc.get("vel", (0, 0))
            p.vel.x, p.vel.y = vx, vy
            p.on_ground = sc.get("on_ground", False)
            p.shield_attempting = sc.get("shield_attempting", False)
            p.hurt_timer = sc.get("hurt_timer", 0)
            p.attack_timer = sc.get("attack_timer", 0)
            p.engine.tick(None)
        assert legacy.state == sch.state, (sc, legacy.state, sch.state)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_fighter_chart.py -v`
Expected: FAIL (`ModuleNotFoundError: pycats.statecharts.fighter_chart`).

- [ ] **Step 3: Create the statecharts package marker**

`pycats/statecharts/__init__.py`:
```python
```
(empty file)

- [ ] **Step 4: Implement `StatechartEngine`**

`pycats/systems/state_engine_sc.py`:
```python
"""StateEngine backed by a statecharts-py Session (the benchmark subject)."""
from __future__ import annotations

from typing import Any

LABELS = ("idle", "run", "jump", "fall", "shield", "dodge", "ko", "hurt",
          "stun", "attack")


class StatechartEngine:
    def __init__(self, session) -> None:
        self._session = session

    @property
    def state(self) -> str:
        for label in LABELS:
            if self._session.in_state(label):
                return label
        raise RuntimeError("statechart in no known fighter state")

    def tick(self, ctx: Any = None) -> None:
        self._session.send("tick")

    def force(self, label: str) -> None:
        self._session.send("force_" + label)
```

- [ ] **Step 5: Implement `build_fighter_chart`**

`pycats/statecharts/fighter_chart.py`:
```python
"""Flat statechart mirroring Player._build_fsm() exactly.

Every transition fires on the explicit "tick" event (no eventless transitions),
so one send("tick") performs at most one hop — matching the legacy FSM's
break-after-first behavior. Guards close over the live Player. Each state also
carries force_ko / force_idle transitions for imperative jumps (Player._ko and
reset_game).
"""
from __future__ import annotations

from statecharts import on, state, statechart, transition


def _tick(cond, target):
    return transition({"event": "tick", "cond": cond, "target": target})


def build_fighter_chart(p):
    """p is the owning Player; guards read its live attributes."""
    forces = (on("force_ko", "ko"), on("force_idle", "idle"))

    return statechart(
        {"initial": "idle"},
        state(
            {"id": "idle"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.x != 0 and p.on_ground, "run"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.on_ground and p.vel.y > 0, "fall"),
            _tick(lambda e, d: p.shield_attempting, "shield"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "run"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.x == 0, "idle"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.on_ground and p.vel.y > 0, "fall"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            _tick(lambda e, d: p.shield_attempting and p.on_ground, "shield"),
            *forces,
        ),
        state(
            {"id": "jump"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.vel.y >= 0, "fall"),
            _tick(lambda e, d: not p.is_alive, "ko"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "fall"},
            _tick(lambda e, d: p.attack_timer > 0, "attack"),
            _tick(lambda e, d: p.on_ground and p.vel.x == 0, "idle"),
            _tick(lambda e, d: p.on_ground and p.vel.x != 0, "run"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            _tick(lambda e, d: not p.is_alive, "ko"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.hurt_timer > 0, "hurt"),
            *forces,
        ),
        state(
            {"id": "shield"},
            _tick(lambda e, d: not p.shield_attempting, "idle"),
            _tick(lambda e, d: p.dodge_timer > 0, "dodge"),
            _tick(lambda e, d: p.vel.y < 0, "jump"),
            *forces,
        ),
        state(
            {"id": "ko"},
            _tick(lambda e, d: p.is_alive, "idle"),
            *forces,
        ),
        state(
            {"id": "dodge"},
            _tick(lambda e, d: p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground, "shield"),
            _tick(lambda e, d: not p.shield_attempting and p.dodge_timer <= 0
                  and p.on_ground and not p.spot_dodge_shield_held, "idle"),
            _tick(lambda e, d: p.dodge_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "hurt"},
            _tick(lambda e, d: p.hurt_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.hurt_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "stun"},
            _tick(lambda e, d: p.stun_timer <= 0 and p.on_ground, "idle"),
            _tick(lambda e, d: p.stun_timer <= 0 and not p.on_ground, "fall"),
            *forces,
        ),
        state(
            {"id": "attack"},
            _tick(lambda e, d: p.done_attacking and p.on_ground, "idle"),
            _tick(lambda e, d: p.done_attacking and not p.on_ground, "fall"),
            *forces,
        ),
    )
```

- [ ] **Step 6: Run to verify pass**

Run: `python -m pytest tests/test_fighter_chart.py -v`
Expected: PASS (5 tests). If `test_matches_legacy_across_scenarios` fails, the transition order or a guard in `fighter_chart.py` diverges from `player.py:_build_fsm`; fix the chart to match the FSM table exactly.

- [ ] **Step 7: Commit**

```bash
git add pycats/statecharts/__init__.py pycats/statecharts/fighter_chart.py pycats/systems/state_engine_sc.py tests/test_fighter_chart.py
git commit -m "feat: fighter statechart + StatechartEngine backend"
```

---

## Task 6: Match/stage engine (both backends)

**Files:**
- Create: `pycats/systems/match_engine.py`
- Test: `tests/test_match_engine.py`

**Interfaces:**
- Produces:
  - `class LegacyMatchEngine`: `LegacyMatchEngine(players)` where `players=[p1,p2]`; `phase` is `"in_play"` or `"match_over"`; `winner` is `1`, `2`, or `0`; `tick()` recomputes from lives (P1 lives<=0 -> winner 2; P2 lives<=0 -> winner 1; matches `game.check_win_condition`).
  - `class StatechartMatchEngine`: same interface, backed by a 2-state statechart firing `"tick"`.
  - `make_match_engine(players, backend="legacy")`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_match_engine.py
from pycats.systems.match_engine import make_match_engine


class _P:
    def __init__(self, lives):
        self.lives = lives


def _run(backend, p1_lives, p2_lives):
    players = [_P(p1_lives), _P(p2_lives)]
    eng = make_match_engine(players, backend)
    eng.tick()
    return eng.phase, eng.winner


def test_in_play_when_both_alive():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 3, 3) == ("in_play", 0)


def test_p1_out_means_p2_wins():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 0, 2) == ("match_over", 2)


def test_p2_out_means_p1_wins():
    for backend in ("legacy", "statechart"):
        assert _run(backend, 1, 0) == ("match_over", 1)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_match_engine.py -v`
Expected: FAIL (`ModuleNotFoundError: pycats.systems.match_engine`).

- [ ] **Step 3: Implement `match_engine.py`**

```python
# pycats/systems/match_engine.py
"""Match/stage state with swappable backends. Mirrors game.check_win_condition:
P1 out of lives -> winner 2; P2 out -> winner 1; else in_play."""
from __future__ import annotations

from statecharts import on, state, statechart, transition, Session


def _winner_from_lives(players) -> int:
    p1, p2 = players
    if p1.lives <= 0:
        return 2
    if p2.lives <= 0:
        return 1
    return 0


class LegacyMatchEngine:
    def __init__(self, players) -> None:
        self._players = players
        self.phase = "in_play"
        self.winner = 0

    def tick(self) -> None:
        w = _winner_from_lives(self._players)
        if w:
            self.phase = "match_over"
            self.winner = w


class StatechartMatchEngine:
    def __init__(self, players) -> None:
        self._players = players
        self.winner = 0
        chart = statechart(
            {"initial": "in_play"},
            state(
                {"id": "in_play"},
                transition({"event": "tick",
                            "cond": lambda e, d: _winner_from_lives(self._players) != 0,
                            "target": "match_over"}),
            ),
            state({"id": "match_over"}),
        )
        self._session = Session(chart)

    @property
    def phase(self) -> str:
        return "match_over" if self._session.in_state("match_over") else "in_play"

    def tick(self) -> None:
        if self.phase == "in_play":
            w = _winner_from_lives(self._players)
            self._session.send("tick")
            if self.phase == "match_over":
                self.winner = w


def make_match_engine(players, backend: str = "legacy"):
    if backend == "statechart":
        return StatechartMatchEngine(players)
    return LegacyMatchEngine(players)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_match_engine.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add pycats/systems/match_engine.py tests/test_match_engine.py
git commit -m "feat: match/stage engine with legacy + statechart backends"
```

---

## Task 7: Headless runner + snapshots

**Files:**
- Create: `pycats/sim/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `make_match_engine`, `default_timeline`, `Player`, `Platform`, `combat.process_hits`, `resolve_player_push`, config constants.
- Produces:
  - `build_stage() -> list[Platform]` (replicates `game.py:59-87` from config dicts).
  - `build_players(backend) -> (p1, p2, players_group)` (replicates `game.py` player creation with `P1_KEYS`/`P2_KEYS`, calico/tabby-ish colors, start positions).
  - `KEYMAPS = [P1_KEYS, P2_KEYS]` (defined here, copied from `game.py:89-106`).
  - `snapshot(players, attacks, match) -> tuple` — fully ordered, hashable per-frame snapshot.
  - `run_battle(backend="legacy", frames=None, frame_inputs=None, presenter=None) -> list[snapshot]` — runs the real loop sequence per frame; if `frame_inputs` is None uses `default_timeline(KEYMAPS)`; `frames` defaults to `len(frame_inputs)`; calls `presenter.show(...)` each frame if given.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
from pycats.sim.runner import run_battle


def test_runner_is_deterministic():
    a = run_battle(backend="legacy", frames=120)
    b = run_battle(backend="legacy", frames=120)
    assert a == b


def test_runner_produces_one_snapshot_per_frame():
    snaps = run_battle(backend="legacy", frames=80)
    assert len(snaps) == 80


def test_runner_runs_statechart_backend():
    snaps = run_battle(backend="statechart", frames=80)
    assert len(snaps) == 80
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_runner.py -v`
Expected: FAIL (`ModuleNotFoundError: pycats.sim.runner`).

- [ ] **Step 3: Implement `runner.py`**

```python
# pycats/sim/runner.py
"""Headless deterministic battle runner. Drives the exact real per-frame loop
(game.py:702-709) from a scripted input timeline, with a swappable state-engine
backend, producing per-frame snapshots for parity checks and benchmarking."""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

if not pygame.get_init():
    pygame.init()

from ..config import (  # noqa: E402
    THICK_PLAT_DICT, THIN_PLAT_DICT_L, THIN_PLAT_DICT_R,
    PLAYER1_START_X, PLAYER1_START_Y, PLAYER2_START_X, PLAYER2_START_Y,
    CAT_CHARACTERS,
)
from ..entities import Platform, Player  # noqa: E402
from ..systems import combat  # noqa: E402
from ..core.physics import resolve_player_push  # noqa: E402
from ..systems.match_engine import make_match_engine  # noqa: E402
from .input_script import default_timeline  # noqa: E402

P1_KEYS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
               attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
P2_KEYS = dict(left=pygame.K_LEFT, right=pygame.K_RIGHT, up=pygame.K_UP,
               down=pygame.K_DOWN, attack=pygame.K_SLASH, special=pygame.K_PERIOD,
               shield=pygame.K_COMMA)
KEYMAPS = [P1_KEYS, P2_KEYS]


def build_stage():
    return [
        Platform(pygame.Rect(THICK_PLAT_DICT["x"], THICK_PLAT_DICT["y"],
                             THICK_PLAT_DICT["w"], THICK_PLAT_DICT["h"]), thin=False),
        Platform(pygame.Rect(THIN_PLAT_DICT_L["x"], THIN_PLAT_DICT_L["y"],
                             THIN_PLAT_DICT_L["w"], THIN_PLAT_DICT_L["h"]), thin=True),
        Platform(pygame.Rect(THIN_PLAT_DICT_R["x"], THIN_PLAT_DICT_R["y"],
                             THIN_PLAT_DICT_R["w"], THIN_PLAT_DICT_R["h"]), thin=True),
    ]


def build_players(backend):
    c1 = CAT_CHARACTERS["calico"]
    c2 = CAT_CHARACTERS["tabby"]
    p1 = Player(PLAYER1_START_X, PLAYER1_START_Y, P1_KEYS, c1["color"],
                eye_color=c1["eye_color"], char_name="P1", facing_right=True,
                state_backend=backend)
    p2 = Player(PLAYER2_START_X, PLAYER2_START_Y, P2_KEYS, c2["color"],
                eye_color=c2["eye_color"], char_name="P2", facing_right=False,
                state_backend=backend)
    p1.stripe_color = c1["stripe_color"]
    p2.stripe_color = c2["stripe_color"]
    return p1, p2, pygame.sprite.Group(p1, p2)


def snapshot(players, attacks, match):
    parts = []
    for p in players:
        parts.append((
            p.char_name, p.state, p.rect.x, p.rect.y,
            round(p.vel.x, 6), round(p.vel.y, 6), p.on_ground,
            round(p.percent, 6), round(p.shield_hp, 6), p.lives, p.is_alive,
            p.jumps_remaining, p.dodge_timer, p.hurt_timer, p.stun_timer,
            p.attack_timer, p.invulnerable_timer, p.facing_right, p.invulnerable,
        ))
    atk = tuple(sorted(
        (a.rect.x, a.rect.y, a.frames_left, a.owner.char_name, a.active)
        for a in attacks
    ))
    return (tuple(parts), atk, match.phase, match.winner)


def run_battle(backend="legacy", frames=None, frame_inputs=None, presenter=None):
    if frame_inputs is None:
        frame_inputs = default_timeline(KEYMAPS)
    if frames is None:
        frames = len(frame_inputs)

    platforms = build_stage()
    p1, p2, players = build_players(backend)
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2], backend)

    snaps = []
    for f in range(frames):
        fi = frame_inputs[f] if f < len(frame_inputs) else _empty_frame()
        for p in players:
            p.update(fi, platforms, attacks)
        resolve_player_push(list(players))
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        snaps.append(snapshot(players, attacks, match))
        if presenter is not None:
            presenter.show(platforms, players, attacks, f)
    if presenter is not None:
        presenter.close()
    return snaps


def _empty_frame():
    from ..core.input import InputFrame
    return InputFrame(held=set(), pressed=set(), released=set())
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_runner.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add pycats/sim/runner.py tests/test_runner.py
git commit -m "feat: headless deterministic battle runner + snapshots"
```

---

## Task 8: Parity cross-check

**Files:**
- Test: `tests/test_parity.py`

**Interfaces:**
- Consumes: `run_battle` from Task 7.

- [ ] **Step 1: Write the parity test**

```python
# tests/test_parity.py
from pycats.sim.runner import run_battle

FRAMES = 200


def test_backends_are_byte_identical():
    legacy = run_battle(backend="legacy", frames=FRAMES)
    statechart = run_battle(backend="statechart", frames=FRAMES)
    assert len(legacy) == len(statechart) == FRAMES
    for f, (a, b) in enumerate(zip(legacy, statechart)):
        assert a == b, f"divergence at frame {f}:\n legacy={a}\n  state={b}"
```

- [ ] **Step 2: Run the parity test**

Run: `python -m pytest tests/test_parity.py -v`
Expected: PASS. If it fails, the printed frame index and the two snapshots localize the first divergence. Compare the divergent player's label against `player.py:_build_fsm` for that state; the cause is almost always a transition-order or guard mismatch in `fighter_chart.py`. Fix the chart (not the legacy FSM) and re-run.

- [ ] **Step 3: Commit**

```bash
git add tests/test_parity.py
git commit -m "test: byte-identical parity between legacy and statechart backends"
```

---

## Task 9: Benchmark + bucketed timing

**Files:**
- Create: `bench.py`
- Test: `tests/test_benchmark.py`

**Interfaces:**
- Consumes: `run_battle`, `build_stage`, `build_players`, `default_timeline`, `KEYMAPS`.
- Produces:
  - `benchmark(backend, frames) -> dict` with keys `total_s, mean_us, median_us, p95_us, p99_us, fps`.
  - `bucketed(backend, frames) -> dict` with keys `engine_us, physics_us, combat_us` (mean per-frame µs per bucket).
  - `main()` prints a comparison table for both backends + the delta vs the 16.67 ms budget.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_benchmark.py
import pytest
from bench import benchmark, bucketed


@pytest.mark.slow
def test_benchmark_keys():
    r = benchmark("legacy", frames=300)
    for k in ("total_s", "mean_us", "median_us", "p95_us", "p99_us", "fps"):
        assert k in r
    assert r["mean_us"] > 0


@pytest.mark.slow
def test_bucketed_keys():
    r = bucketed("statechart", frames=300)
    for k in ("engine_us", "physics_us", "combat_us"):
        assert k in r
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_benchmark.py -v -m slow`
Expected: FAIL (`ModuleNotFoundError: bench`).

- [ ] **Step 3: Implement `bench.py`**

```python
# bench.py
"""Benchmark the two state-engine backends over the headless battle.

Reports per-frame timing and a per-bucket breakdown (state engine vs physics vs
combat) so we can see whether the state machine is a meaningful slice of the
frame budget. Usage: python bench.py [--frames N]
"""
from __future__ import annotations

import argparse
import statistics
import time

from pycats.sim.runner import (
    KEYMAPS, build_players, build_stage, run_battle,
)
from pycats.sim.input_script import default_timeline
from pycats.systems import combat
from pycats.core.physics import resolve_player_push
from pycats.systems.match_engine import make_match_engine

BUDGET_US = 1_000_000 / 60  # 16,667 us per frame at 60 FPS


def _percentile(xs, q):
    s = sorted(xs)
    if not s:
        return 0.0
    idx = min(len(s) - 1, int(q * len(s)))
    return s[idx]


def benchmark(backend, frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    per_frame = []
    platforms = build_stage()
    p1, p2, players = build_players(backend)
    import pygame
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2], backend)
    for f in range(frames):
        fi = inputs[f % n]
        t0 = time.perf_counter()
        for p in players:
            p.update(fi, platforms, attacks)
        resolve_player_push(list(players))
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        per_frame.append((time.perf_counter() - t0) * 1e6)
    total_s = sum(per_frame) / 1e6
    mean_us = statistics.mean(per_frame)
    return {
        "total_s": total_s,
        "mean_us": mean_us,
        "median_us": statistics.median(per_frame),
        "p95_us": _percentile(per_frame, 0.95),
        "p99_us": _percentile(per_frame, 0.99),
        "fps": 1e6 / mean_us if mean_us else 0.0,
    }


def bucketed(backend, frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    eng, phys, comb = [], [], []
    platforms = build_stage()
    p1, p2, players = build_players(backend)
    import pygame
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2], backend)
    plist = list(players)
    for f in range(frames):
        fi = inputs[f % n]
        # physics + engine are fused inside Player.update; time the whole update
        # as "physics", then time the engine tick separately is not possible
        # post-hoc, so we time update() (physics+engine) and the standalone
        # systems below.
        t0 = time.perf_counter()
        for p in players:
            p.update(fi, platforms, attacks)
        t1 = time.perf_counter()
        resolve_player_push(plist)
        t2 = time.perf_counter()
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        t3 = time.perf_counter()
        phys.append((t1 - t0) * 1e6)
        eng.append((t2 - t1) * 1e6)   # player-push bucket (shared)
        comb.append((t3 - t2) * 1e6)
    import statistics as st
    return {
        "physics_us": st.mean(phys),
        "engine_us": st.mean(eng),
        "combat_us": st.mean(comb),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=20_000)
    args = ap.parse_args()

    rows = {b: benchmark(b, args.frames) for b in ("legacy", "statechart")}
    print(f"\nBattle benchmark — {args.frames} frames\n" + "=" * 56)
    hdr = f"{'metric':<14}{'legacy':>14}{'statechart':>16}"
    print(hdr)
    print("-" * 56)
    for k in ("mean_us", "median_us", "p95_us", "p99_us", "fps"):
        print(f"{k:<14}{rows['legacy'][k]:>14.2f}{rows['statechart'][k]:>16.2f}")
    delta = rows["statechart"]["mean_us"] - rows["legacy"]["mean_us"]
    print("-" * 56)
    print(f"statechart - legacy: {delta:+.2f} us/frame "
          f"({delta / BUDGET_US * 100:+.3f}% of 16.67ms budget)")
    print("\nper-bucket mean us/frame (statechart):")
    for k, v in bucketed("statechart", args.frames).items():
        print(f"  {k:<12}{v:>10.2f}")


if __name__ == "__main__":
    main()
```

Note on buckets: `Player.update()` fuses physics and the engine `tick()` (the engine tick happens last inside `update`), so they cannot be separated post-hoc without instrumenting `Player`. The `physics_us` bucket therefore includes the engine tick; the `engine_us` bucket measures the shared player-push step; `combat_us` covers attack lifetime + hit resolution. This is enough to show whether per-frame cost is dominated by `update` vs the shared systems, and the `mean_us` delta between backends isolates the engine's contribution (everything else is identical). If finer attribution is wanted later, add optional timing hooks inside `Player.update` around `self.engine.tick`.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_benchmark.py -v -m slow`
Expected: PASS (2 tests). Also sanity-run the CLI:
Run: `python bench.py --frames 2000`
Expected: a printed table with both backends and the delta line.

- [ ] **Step 5: Register the `slow` marker**

Create `pytest.ini`:
```ini
[pytest]
markers =
    slow: long-running benchmark tests (deselect with -m "not slow")
```

- [ ] **Step 6: Commit**

```bash
git add bench.py tests/test_benchmark.py pytest.ini
git commit -m "feat: battle benchmark CLI + bucketed timing"
```

---

## Task 10: Render extraction + live/video presenters

**Files:**
- Create: `pycats/render_battle.py`
- Create: `pycats/sim/presenters.py`
- Create: `watch.py`
- Modify: `pycats/game.py`
- Test: `tests/test_render_battle.py`

**Interfaces:**
- Produces:
  - `render_battle(surface, players, platforms)` — draws platforms + alive players (body, tail, stripes, eyes, cat features, name, shield bubble) + attacks, replicating `game.py:714-753`'s draw block (no HUD/controls/FPS text).
  - The draw helpers `draw_eye`, `draw_cat_features`, `draw_stripes`, `draw_player_name` move from `game.py` into `render_battle.py`.
  - `class HeadlessPresenter` (no-op `show`/`close`), `class LivePresenter` (real window, 60 FPS), `class VideoPresenter` (writes frames to mp4/gif via `imageio`, graceful skip if missing).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render_battle.py
import pygame
from pycats.sim.runner import build_stage, build_players
from pycats.render_battle import render_battle


def test_render_battle_draws_without_error():
    surface = pygame.Surface((960, 540))
    platforms = build_stage()
    p1, p2, players = build_players("legacy")
    # advance one frame so players have valid rects/tails
    from pycats.core.input import InputFrame
    empty = InputFrame(held=set(), pressed=set(), released=set())
    for p in players:
        p.update(empty, platforms, pygame.sprite.Group())
    render_battle(surface, players, platforms)  # must not raise
    assert surface.get_at((0, 0)) is not None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_render_battle.py -v`
Expected: FAIL (`ModuleNotFoundError: pycats.render_battle`).

- [ ] **Step 3: Create `render_battle.py` by moving the draw helpers**

Move the four functions `draw_eye` (game.py:182-199), `draw_cat_features` (201-273), `draw_stripes` (275-321), and `draw_player_name` (393-403) **verbatim** from `game.py` into a new `pycats/render_battle.py`. Add the module's imports at the top of the new file:

```python
# pycats/render_battle.py
"""Shared battle renderer: draws the stage, fighters, and attacks onto a surface.
Extracted from game.py so the live game, pause screen, and sim presenters all
use one renderer."""
import math
import pygame

from .config import (
    EYE_OFFSET_X, EYE_OFFSET_Y, EYE_RADIUS, GLINT_OFFSET_X, GLINT_OFFSET_Y,
    GLINT_RADIUS, EAR_WIDTH, EAR_HEIGHT, EAR_SPACING, EAR_PADDING,
    WHISKER_LENGTH, WHISKER_THICKNESS, WHISKER_COUNT, WHISKER_ANGLE,
    WHISKER_OFFSET_Y, WHISKER_OFFSET_X, STRIPE_COUNT, STRIPE_WIDTH,
    STRIPE_HEIGHT, STRIPE_SPACING, SHIELD_COLOR, SHIELD_MAX_HP,
    MAX_SHIELD_RADIUS, MIN_SHIELD_RADIUS, BLACK, WHITE,
)
from . import text_utils

# (moved verbatim from game.py): draw_eye, draw_cat_features, draw_stripes,
# draw_player_name  ... paste the four function bodies here unchanged ...


def render_battle(surface, players, platforms):
    """Draw platforms, alive fighters, and their attacks onto `surface`.
    Mirrors game.py's playing-branch draw block (no HUD/controls/FPS text)."""
    for pl in platforms:
        surface.blit(pl.image, pl.rect)
    for p in players:
        if not p.is_alive:
            continue
        p.tail.draw(surface)
        surface.blit(p.image, p.rect)
        draw_stripes(surface, p)
        draw_eye(surface, p)
        draw_eye(surface, p, eye=False)
        draw_cat_features(surface, p)
        draw_stripes(surface, p)
        draw_player_name(surface, p)
        if p.state == "shield":
            ratio = p.shield_hp / SHIELD_MAX_HP
            shield_radius = int(MAX_SHIELD_RADIUS * ratio)
            r = max(MIN_SHIELD_RADIUS, shield_radius)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*SHIELD_COLOR, 100), (r, r), r)
            surface.blit(s, (p.rect.centerx - r, p.rect.centery - r))


def render_attacks(surface, attacks):
    for a in attacks:
        surface.blit(a.image, a.rect)
```

Adjust the imports in the moved functions if any referenced a name not in the import block above (the moved functions only use config constants already imported here, `pygame`, `math`, and `text_utils`).

- [ ] **Step 4: Update `game.py` to import the moved helpers**

In `game.py`:
- Delete the four moved function definitions (`draw_eye`, `draw_cat_features`, `draw_stripes`, `draw_player_name`).
- Add an import near line 53: `from .render_battle import draw_eye, draw_cat_features, draw_stripes, draw_player_name, render_battle, render_attacks`.
- In the `playing` branch (game.py:716-753), replace the platform + player + attacks draw block with:
```python
        render_battle(render_surface, players, platforms)
        render_attacks(render_surface, attacks)
```
  (Keep the `render_surface.fill(BG_COLOR)` line before it and the HUD/controls/FPS text after it.)
- In the `pause` branch (game.py:824-852), replace the duplicated platform + player + attacks draw block with:
```python
        render_battle(background_surface, players, platforms)
        render_attacks(background_surface, attacks)
```

- [ ] **Step 5: Implement presenters**

```python
# pycats/sim/presenters.py
"""Presenters let the deterministic runner replay headless, live, or to video."""
from __future__ import annotations

import pygame

from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, FPS
from ..render_battle import render_battle, render_attacks


class HeadlessPresenter:
    def show(self, platforms, players, attacks, frame): ...
    def close(self): ...


class LivePresenter:
    """Opens a real window and renders the replay at 60 FPS."""

    def __init__(self, caption="PyCats replay"):
        import os
        os.environ.pop("SDL_VIDEODRIVER", None)
        pygame.display.quit()
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

    def show(self, platforms, players, attacks, frame):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                raise KeyboardInterrupt
        self.screen.fill(BG_COLOR)
        render_battle(self.screen, players, platforms)
        render_attacks(self.screen, attacks)
        pygame.display.flip()
        self.clock.tick(FPS)

    def close(self):
        pygame.display.quit()


class VideoPresenter:
    """Writes each frame to a video file. Requires imageio (+ imageio-ffmpeg)."""

    def __init__(self, path="battle.mp4", fps=FPS):
        try:
            import imageio.v2 as imageio
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError(
                "video mode needs imageio: pip install imageio imageio-ffmpeg"
            ) from exc
        self._imageio = imageio
        self._writer = imageio.get_writer(path, fps=fps)
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def show(self, platforms, players, attacks, frame):
        self._surface.fill(BG_COLOR)
        render_battle(self._surface, players, platforms)
        render_attacks(self._surface, attacks)
        arr = pygame.surfarray.array3d(self._surface).transpose(1, 0, 2)
        self._writer.append_data(arr)

    def close(self):
        self._writer.close()
```

- [ ] **Step 6: Implement `watch.py`**

```python
# watch.py
"""Watch or record a deterministic battle replay.
  python watch.py --backend statechart            # live window
  python watch.py --backend legacy --video out.mp4 # write video
"""
from __future__ import annotations

import argparse

from pycats.sim.runner import run_battle
from pycats.sim.presenters import LivePresenter, VideoPresenter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["legacy", "statechart"], default="legacy")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--video", default=None, help="output path; omit for live window")
    args = ap.parse_args()

    presenter = VideoPresenter(args.video) if args.video else LivePresenter()
    try:
        run_battle(backend=args.backend, frames=args.frames, presenter=presenter)
    except KeyboardInterrupt:
        presenter.close()
    if args.video:
        print(f"wrote {args.video}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Run the render test + full suite (excluding slow)**

Run: `python -m pytest -m "not slow" -v`
Expected: PASS across all test files. Then confirm the game still imports its renderer cleanly:
Run: `python -c "import ast; ast.parse(open('pycats/game.py').read()); print('game.py parses')"`
Expected: `game.py parses`.

- [ ] **Step 8: Commit**

```bash
git add pycats/render_battle.py pycats/sim/presenters.py watch.py pycats/game.py tests/test_render_battle.py
git commit -m "feat: extract render_battle + live/video replay presenters"
```

---

## Self-Review

**Spec coverage:**
- §3 StateEngine seam → Tasks 2, 3. ✓
- §4 flat all-`"tick"` statechart → Task 5. ✓
- §5 match/stage engine → Task 6. ✓
- §6 headless runner + scripted input → Tasks 4, 7. ✓
- §7 parity cross-check → Task 8. ✓
- §8 benchmark + bucketed timing → Task 9. ✓
- §9 presentation modes + render_battle extraction (de-dups pause branch) → Task 10. ✓
- §10 dependency wiring + config flag (`state_backend` arg; `PYCATS_STATE_BACKEND` noted) → Tasks 1, 3.
  - Gap closed: the live game reading `PYCATS_STATE_BACKEND` is optional and not required for the benchmark; if wanted, `game.py:create_players_from_selection` can pass `state_backend=os.environ.get("PYCATS_STATE_BACKEND","legacy")`. Left out of the critical path deliberately (YAGNI for the benchmark goal).

**Placeholder scan:** The only intentional "paste verbatim" is moving four existing draw functions in Task 10 Step 3 (a pure move, exact source line ranges given) — not a placeholder. The bogus import line in Task 3 Step 1 is explicitly flagged for deletion. No TBD/TODO/"add error handling" steps remain.

**Type consistency:** `state_backend` param name consistent (Player, make_state_engine, build_players). `StateEngine` surface (`state`/`tick(ctx)`/`force(label)`) consistent across LegacyEngine, StatechartEngine. `snapshot()` tuple ordering fixed and used only by `run_battle`. Match engine `phase`/`winner`/`tick()` consistent across both backends and the runner. `render_battle(surface, players, platforms)` signature consistent across game.py and presenters.

**Known risk to watch during execution:** Task 8 (parity) is where any `fighter_chart.py` divergence surfaces. Fix the chart to match `_build_fsm`, never the legacy FSM.
