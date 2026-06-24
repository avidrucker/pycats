# Phase 1 Foundation — Knockback + Hitstun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder linear knockback with the authentic Brawl/PM knockback formula and derive hitstun from knockback, behind a pure, unit-tested module.

**Architecture:** A pure `pycats/combat/knockback.py` (no pygame) holds the formula; `Player.receive_hit` calls it. Per-hitbox `base_knockback`/`knockback_growth` and a fighter `weight` feed the formula; a `KNOCKBACK_VELOCITY_SCALE` maps the Smash-scale knockback magnitude onto pycats' pixel/frame velocity. Hitstun = `floor(KB · multiplier)` with a floor.

**Tech Stack:** Python 3.12, pygame-ce, pytest. Tests via the main-repo venv: `/home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-06-24-phase1-combat-core-design.md` (#39). Umbrella #38, this ticket #40.
- **Run tests from the worktree using the main-repo interpreter:** `PY=/home/avi/Documents/Study/Python/pycats/.venv/bin/python`. Worktrees have no `.venv`.
- **Every change is TDD:** failing test first, confirm red, implement, confirm green, commit. Per RULES.md → "Fixing bugs", any test guarding a behavior must be shown able to fail.
- **Preserve #8:** the moving defender combines horizontal momentum with knockback (`vel.x +=`), vertical is an override (`vel.y =`). `tests/test_combat.py`/respawn tests must stay green.
- **Determinism / integer frames:** hitstun is whole frames; no RNG.
- **Formula (authentic, weight 100 = neutral):**
  `KB = (((((p/10) + (p·d/20)) · (200/(w+100)) · 1.4) + 18) · (KBG/100)) + BKB`, `p` = post-hit percent.
- Commits in this plan are local to the branch; the ticket is landed once via `pmtools close 40` at the end (never `git push` to main).

---

### Task 1: Pure knockback/hitstun module + config constants

**Files:**
- Create: `pycats/combat/knockback.py`
- Modify: `pycats/config.py` (add hitstun + velocity-scale constants)
- Test: `tests/test_knockback.py`

**Interfaces:**
- Consumes: nothing (pure).
- Produces:
  - `knockback(percent: float, damage: float, weight: int, base_knockback: float, knockback_growth: float) -> float`
  - `hitstun_frames(kb: float) -> int`
  - `config.HITSTUN_MULTIPLIER: float`, `config.HITSTUN_FLOOR: int`, `config.KNOCKBACK_VELOCITY_SCALE: float`

- [ ] **Step 1: Add config constants**

In `pycats/config.py`, replace the `# ---------------- knockback ----------------` block (currently `KNOCKBACK_SCALE = 0.5`, `KNOCKBACK_BASE = 5`) with:

```python
# ---------------- knockback / hitstun ----------------
# Authentic Brawl/PM knockback feeds these. The formula lives in
# pycats/combat/knockback.py; per-hitbox BKB/KBG and fighter weight are the
# per-move/character inputs.
HITSTUN_MULTIPLIER = 0.4   # hitstun_frames = floor(KB * this). ⚠ verify (Brawl/PM ~0.4).
HITSTUN_FLOOR = 1          # minimum hitstun frames for any clean hit. ⚠ tuning, not sourced.
# Authentic KB is on the Smash magnitude scale (tens-to-hundreds); this maps it
# onto pycats pixel/frame launch velocity. ⚠ tuning — playtest and adjust.
KNOCKBACK_VELOCITY_SCALE = 0.4
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_knockback.py`:

```python
"""Unit tests for the authentic Brawl/PM knockback + hitstun formula (#40)."""
import math

import pytest

from pycats.combat.knockback import knockback, hitstun_frames
from pycats.config import HITSTUN_FLOOR


def test_knockback_zero_percent_neutral_weight():
    # p=0, d=10, w=100 -> inner 0; (0*1.4)+18=18; *KBG/100(=1)=18; +BKB(30)=48
    assert knockback(0.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0) == pytest.approx(48.0)


def test_knockback_high_percent_neutral_weight():
    # p=100, d=10, w=100 -> (10+50)=60; *1.0*1.4=84; +18=102; *1=102; +30=132
    assert knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0) == pytest.approx(132.0)


def test_heavier_target_takes_less_knockback():
    light = knockback(100.0, 10.0, 50, base_knockback=30.0, knockback_growth=100.0)
    neutral = knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=100.0)
    heavy = knockback(100.0, 10.0, 200, base_knockback=30.0, knockback_growth=100.0)
    assert light > neutral > heavy
    assert heavy == pytest.approx(104.0)   # 200/300=.6667; 60*.6667*1.4=56; +18=74; +30=104


def test_knockback_growth_scales_the_percent_term():
    # KBG=0 -> growth term vanishes, leaving just BKB
    assert knockback(100.0, 10.0, 100, base_knockback=30.0, knockback_growth=0.0) == pytest.approx(30.0)


def test_hitstun_is_floored_product():
    assert hitstun_frames(132.0) == 52      # floor(52.8)
    assert hitstun_frames(48.0) == 19       # floor(19.2)


def test_hitstun_never_below_floor():
    assert hitstun_frames(0.0) == HITSTUN_FLOOR
    assert hitstun_frames(0.5) == HITSTUN_FLOOR


def test_hitstun_monotonic_in_knockback():
    assert hitstun_frames(50.0) <= hitstun_frames(100.0) <= hitstun_frames(200.0)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `$PY -m pytest tests/test_knockback.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pycats.combat.knockback'`.

- [ ] **Step 4: Implement the module**

Create `pycats/combat/knockback.py`:

```python
"""Authentic Brawl/Project-M knockback + hitstun (pure; no pygame).

KB = (((((p/10) + (p*d/20)) * (200/(w+100)) * 1.4) + 18) * (KBG/100)) + BKB
where p = target percent AFTER the hit, d = damage, w = weight, BKB/KBG per hitbox.
Source: https://www.ssbwiki.com/Knockback  (see spec #39 §2).
"""
import math

from ..config import HITSTUN_MULTIPLIER, HITSTUN_FLOOR


def knockback(percent: float, damage: float, weight: int,
              base_knockback: float, knockback_growth: float) -> float:
    """Knockback magnitude (Smash units). `percent` is the post-hit percent."""
    growth = ((percent / 10.0) + (percent * damage / 20.0)) * (200.0 / (weight + 100.0))
    growth = (growth * 1.4) + 18.0
    return (growth * (knockback_growth / 100.0)) + base_knockback


def hitstun_frames(kb: float) -> int:
    """Whole frames of hitstun for a knockback magnitude (floored, min HITSTUN_FLOOR)."""
    return max(HITSTUN_FLOOR, math.floor(kb * HITSTUN_MULTIPLIER))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `$PY -m pytest tests/test_knockback.py -q`
Expected: PASS (7 passed).

- [ ] **Step 6: Can-fail check (per #35)**

Temporarily change `+ 18.0` to `+ 19.0` in `knockback`, run the tests, confirm the two neutral-weight tests go RED, then restore and confirm green again.

Run: `$PY -m pytest tests/test_knockback.py -q`

- [ ] **Step 7: Commit**

```bash
git add pycats/combat/knockback.py pycats/config.py tests/test_knockback.py
git commit -m "feat(combat): authentic knockback + hitstun formula module (#40)"
```

---

### Task 2: Hitbox/Attack knockback data fields

**Files:**
- Modify: `pycats/combat/data.py` (Hitbox dataclass)
- Modify: `pycats/characters/default_cat.py` (the `_ATTACK_HITBOX`)
- Modify: `pycats/entities/attack.py` (carry fields through)
- Test: `tests/test_combat_data.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Hitbox.base_knockback: float`, `Hitbox.knockback_growth: float`; `Attack.base_knockback`, `Attack.knockback_growth` (absent on legacy fallback → defaults).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_combat_data.py` (create if absent, with the existing import style):

```python
from pycats.combat.data import Hitbox, Circle


def test_hitbox_carries_knockback_fields():
    hb = Hitbox(circle=Circle(dx=1, dy=2, r=3), damage=10.0, angle=0,
                base_knockback=30.0, knockback_growth=100.0)
    assert hb.base_knockback == 30.0
    assert hb.knockback_growth == 100.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `$PY -m pytest tests/test_combat_data.py::test_hitbox_carries_knockback_fields -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'base_knockback'`.

- [ ] **Step 3: Add the fields to Hitbox**

In `pycats/combat/data.py`, the `Hitbox` dataclass — replace its fields/docstring tail:

```python
@dataclass(frozen=True)
class Hitbox:
    """One active hitbox for a move.

    Fields:
        circle           — position and size (facing-right coords)
        damage           — percentage damage dealt on hit
        angle            — launch angle in degrees (0 = right, 90 = up)
        base_knockback   — BKB: knockback at 0% (Phase 1)
        knockback_growth — KBG: how knockback scales with percent (Phase 1)
    """
    circle: Circle
    damage: float
    angle: int
    base_knockback: float = 0.0
    knockback_growth: float = 0.0
```

(Defaults keep any other Hitbox construction valid; the real move sets them.)

- [ ] **Step 4: Populate the default cat's jab**

In `pycats/characters/default_cat.py`, replace `_ATTACK_HITBOX`:

```python
_ATTACK_HITBOX = Hitbox(
    circle=Circle(dx=27, dy=30, r=12),
    damage=10.0,
    angle=0,
    base_knockback=30.0,    # ⚠ initial tuning — a light jab; playtest with KNOCKBACK_VELOCITY_SCALE
    knockback_growth=100.0,
)
```

- [ ] **Step 5: Carry the fields through Attack**

In `pycats/entities/attack.py`, in the `if hitbox is not None:` branch (after `self.angle = hitbox.angle`), add:

```python
            self.base_knockback = hitbox.base_knockback
            self.knockback_growth = hitbox.knockback_growth
```

In the `else:` fallback branch (after `self.angle = angle`), add:

```python
            self.base_knockback = 0.0
            self.knockback_growth = 0.0
```

Remove the now-unused `base_kb=KNOCKBACK_BASE, kb_scale=KNOCKBACK_SCALE` constructor params and the `self.base_kb = base_kb` / `self.kb_scale = kb_scale` lines, and drop the `KNOCKBACK_BASE, KNOCKBACK_SCALE` names from the `from ..config import ...` at the top of `attack.py`.

- [ ] **Step 6: Run to verify pass + no breakage**

Run: `$PY -m pytest tests/test_combat_data.py tests/test_render_battle.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pycats/combat/data.py pycats/characters/default_cat.py pycats/entities/attack.py tests/test_combat_data.py
git commit -m "feat(combat): per-hitbox base_knockback/knockback_growth + cat jab values (#40)"
```

---

### Task 3: Wire into Player (weight + receive_hit + computed hitstun)

**Files:**
- Modify: `pycats/entities/player.py` (`__init__`, `receive_hit`, `_start_hurt`)
- Test: `tests/test_combat.py`

**Interfaces:**
- Consumes: `knockback(...)`, `hitstun_frames(...)` (Task 1); `Attack.base_knockback`/`knockback_growth` (Task 2); `config.KNOCKBACK_VELOCITY_SCALE`.
- Produces: `Player.weight: int` (default 100); `receive_hit` sets `hurt_timer` from computed hitstun.

- [ ] **Step 1: Write the failing integration test**

Add to `tests/test_combat.py` (match its existing Player/Attack construction helpers; sketch):

```python
def test_receive_hit_applies_computed_hitstun_and_combines_momentum():
    import pygame
    from pycats.entities.player import Player
    from pycats.entities.attack import Attack
    from pycats.combat.knockback import knockback, hitstun_frames
    from pycats.config import KNOCKBACK_VELOCITY_SCALE
    P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
              attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)
    attacker = Player(100, 100, P1, (1, 1, 1), eye_color=(0, 0, 0), char_name="A",
                      facing_right=True, state_backend="legacy")
    defender = Player(160, 100, P1, (1, 1, 1), eye_color=(0, 0, 0), char_name="D",
                      facing_right=False, state_backend="legacy")
    defender.vel.x = -3.0                      # moving left (the #8 case)
    atk = Attack(owner=attacker, damage=10.0, angle=0)
    atk.base_knockback, atk.knockback_growth = 30.0, 100.0
    defender.receive_hit(atk)
    kb = knockback(defender.percent, 10.0, defender.weight, 30.0, 100.0)
    assert defender.hurt_timer == hitstun_frames(kb)        # computed, not fixed 12
    # momentum combined (started at -3), not overwritten:
    assert defender.vel.x == pytest.approx(-3.0 + kb * KNOCKBACK_VELOCITY_SCALE)
```

- [ ] **Step 2: Run to verify it fails**

Run: `$PY -m pytest tests/test_combat.py::test_receive_hit_applies_computed_hitstun_and_combines_momentum -q`
Expected: FAIL (`Player` has no `weight`, or hitstun == 12 / velocity unscaled).

- [ ] **Step 3: Add `weight` to Player**

In `pycats/entities/player.py` `__init__` signature add `weight: int = 100,` (near `facing_right`), and after `self.facing_right = facing_right` add:

```python
        self.weight = weight
```

- [ ] **Step 4: Rewrite `receive_hit`'s knockback branch**

In `player.py`, add the import near the top: `from ..combat.knockback import knockback, hitstun_frames` and `from ..config import KNOCKBACK_VELOCITY_SCALE`. Replace the `else:` body of `receive_hit` (the `self._start_hurt()` / `self.percent += ...` / `kb = atk.base_kb + ...` block) with:

```python
        else:
            self.percent += atk.damage
            kb = knockback(self.percent, atk.damage, self.weight,
                           atk.base_knockback, atk.knockback_growth)
            self.hurt_timer = hitstun_frames(kb)
            self._start_hurt()                      # visual flash; timer set above
            direction = 1 if atk.owner.facing_right else -1
            radians = math.radians(atk.angle)
            launch = kb * KNOCKBACK_VELOCITY_SCALE
            # #8: combine horizontal momentum, override vertical (launch arc)
            self.vel.x += launch * math.cos(radians) * direction
            self.vel.y = launch * -math.sin(radians)
```

- [ ] **Step 5: Make `_start_hurt` not clobber the timer**

In `player.py` `_start_hurt`, remove `self.hurt_timer = HURT_TIME` (keep `self.image.fill(RED)`). If `HURT_TIME` is now unused anywhere (`grep -rn HURT_TIME pycats/`), remove it from `config.py` and the import; otherwise leave it.

- [ ] **Step 6: Run to verify pass + #8 guard intact**

Run: `$PY -m pytest tests/test_combat.py tests/test_respawn_timers.py -q`
Expected: PASS (the new test + the #8/#31 guards).

- [ ] **Step 7: Commit**

```bash
git add pycats/entities/player.py tests/test_combat.py pycats/config.py
git commit -m "feat(combat): receive_hit uses authentic knockback + computed hitstun; add weight (#40)"
```

---

### Task 4: Regenerate goldens (semantic verify) + full suite + docs

**Files:**
- Modify: `tests/golden/combat.json` (regenerated)
- Modify: `README.md` (one line if it documents knockback) — optional
- Test: full README suite

**Interfaces:**
- Consumes: all prior tasks.
- Produces: a green full suite with updated goldens.

- [ ] **Step 1: Regenerate the golden**

Run: `PYCATS_UPDATE_GOLDENS=1 $PY -m pytest tests/test_golden.py -q`
Expected: PASS (rewrites `tests/golden/combat.json`).

- [ ] **Step 2: Verify the golden diff semantically (per #31)**

Diff old vs new per-field (use the `combat_old.json` vs working-tree comparison pattern from the #31 session). Confirm only knockback-derived fields move and in the expected direction: `velx`/`vely` (larger launches), `hurt_timer` (computed hitstun, not 12), `percent`. No `state`/`x`/`y`-at-rest or unrelated field should change except as a downstream consequence of the new launch. Write the observed changed-field set into the commit message.

- [ ] **Step 3: Run the full README suite**

Run:
```bash
$PY -m pytest tests/test_smoke.py tests/test_state_engine.py tests/test_player_seam.py \
  tests/test_input_script.py tests/test_fighter_chart.py tests/test_match_engine.py \
  tests/test_runner.py tests/test_parity.py tests/test_full_match.py tests/test_render_battle.py \
  tests/test_render_cache.py tests/test_benchmark.py tests/test_combat_data.py tests/test_geometry.py \
  tests/test_player_move.py tests/test_combat.py tests/test_golden.py tests/test_knockback.py \
  tests/test_respawn_facing.py tests/test_respawn_timers.py -q
```
Expected: PASS (all).

- [ ] **Step 4: If `test_parity` fails**

Knockback lives in `receive_hit` (shared by both backends), so parity should hold. If it diverges, that is the roadmap §6 parity-flip beginning — note it; the golden self-regression is the oracle. Do not force-match legacy.

- [ ] **Step 5: Commit the goldens**

```bash
git add tests/golden/combat.json
git commit -m "test(combat): regenerate goldens for authentic knockback (#40)

Verified semantically: changed fields = {velx, vely, hurt_timer, percent}, all
downstream of the new launch magnitudes."
```

- [ ] **Step 6: Tick the umbrella + close**

Add `Closes #40` to the final commit body (or amend), then from the worktree:
```bash
pmtools close 40
```
Then update #38: check the "Implement foundation" box. Post a close comment summarizing the changed-field set and the playtest note on `KNOCKBACK_VELOCITY_SCALE`.

---

## Self-Review

**Spec coverage:** §2 formula → Task 1; §2.2 hitstun + constants → Task 1; §3 pure module + receive_hit → Tasks 1, 3; §4 data (Hitbox fields, Attack carry-through, weight, retire old constants, computed hitstun) → Tasks 2, 3; §5 testing (unit + can-fail + integration + golden semantic) → Tasks 1, 3, 4; §6 deferred items → untouched (good). The one spec assumption refined: §2.1 "feeds velocity the same way" is implemented via `KNOCKBACK_VELOCITY_SCALE` (authentic KB units → pycats velocity) — surfaced to the human before execution.

**Placeholder scan:** no TBD/TODO; the only `⚠` markers are deliberate tuning/verify flags from the spec, each with a concrete chosen value.

**Type consistency:** `knockback(percent, damage, weight, base_knockback, knockback_growth)` and `hitstun_frames(kb)` used identically in Tasks 1, 3, and the tests; `Hitbox.base_knockback`/`knockback_growth` and `Attack.base_knockback`/`knockback_growth` names match across Tasks 2–3.
