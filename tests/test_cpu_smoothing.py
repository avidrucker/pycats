"""#970 (child of #925): leveled-CPU smoothing — jump purpose-gate + spacing hysteresis.

Root-caused in #966 (`docs/research/cpu-jitter-jump-v2-findings.md`): leveled bots read as
"jumpy" (a reflexive jump-toward-any-slightly-elevated-foe policy) and "jittery" (a hard
±8px spacing deadband, re-decided every frame with no hysteresis). The fix is level-gated so
the level-less golden path stays byte-identical:
  * facet 1 — only jump-chase a foe genuinely higher (>= JUMP_PURPOSE_DY px), not one barely
    overhead (>= FOE_ABOVE_DY), plus a takeoff cooldown;
  * facet 2 — hysteresis: a wide settle band (± SPACING_STOP of standoff) plus a wider
    re-trigger band (± SPACING_START), so the bot coasts through the margin between them
    instead of flapping across one line.

These tests SYNTHESIZE static frames (call decide() without stepping physics), the same way
`test_reactive_spacing` does. Each leveled assertion is able-to-fail: RED on the pre-#970
code (the FOE_ABOVE_DY gate / the flat ±8 deadband) and GREEN after. The level-less
assertions are byte-identity guards (unchanged on both).

Fixtures are kept OUT of attack range (adx below `standoff - IN_RANGE_NEAR_MARGIN`, or gap
beyond melee range) so decide() never reaches the smash/attack path — no fuller fighter stub
is needed.
"""

import random
import types

import pygame as pg

from pycats.core.geometry import FrozenRect
from pycats.sim.controllers import (
    FOE_ABOVE_DY,
    JUMP_PURPOSE_DY,
    SPACING_START,
    AttackerController,
)

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _stub(cx, cy, on_ground=True):
    s = types.SimpleNamespace()
    s.rect = FrozenRect(0, 0, 40, 60)
    s.rect = s.rect.with_center((cx, cy))
    s.fighter = types.SimpleNamespace(is_alive=True, on_ground=on_ground)
    s.controls = _CTRL
    s.current_move = None  # not recovering -> engage path, press_in stays off
    s.move_frame = 0
    return s


# ---- facet 1: jump purpose gate -------------------------------------------------
# A foe 40px above straddles the two thresholds: above FOE_ABOVE_DY (30, the old gate)
# but below JUMP_PURPOSE_DY (60, the leveled gate). adx=10 keeps both bots out of attack
# range (in_range_low = standoff - 18 is >= 12), so decide() never reaches the attack path.


def _barely_elevated_pair(adx=10, dy_px=-40):
    a = _stub(400, 360)
    t = _stub(400 + adx, 360 + dy_px)  # dy_px < 0 -> target above
    return a, t


def test_leveled_bot_does_not_hop_at_a_barely_elevated_foe():
    assert FOE_ABOVE_DY < 40 < JUMP_PURPOSE_DY  # fixture straddles the two gates
    a, t = _barely_elevated_pair()
    held = AttackerController(attacker_num=1, level=7, rng=random.Random(0))(a, t, frame=0).held
    assert _CTRL["up"] not in held, (
        "leveled bot must NOT reflexively hop at a foe only 40px up (pre-#970 it pressed up "
        f"via the FOE_ABOVE_DY gate); held={sorted(held)}"
    )


def test_level_less_default_still_jumps_at_a_barely_elevated_foe():
    # byte-identity guard: the level-less path keeps the FOE_ABOVE_DY (30) gate unchanged.
    a, t = _barely_elevated_pair()
    held = AttackerController(attacker_num=1)(a, t, frame=0).held
    assert _CTRL["up"] in held, "level-less default must still jump at a 40px-elevated foe (unchanged golden path)"


# ---- facet 2: spacing hysteresis coast ------------------------------------------
# Lv1 standoff=45. A gap of standoff+12 (=57) sits in the coast margin: past the settle
# band (standoff + SPACING_STOP = 53) but inside the re-trigger band (standoff +
# SPACING_START = 61). Gap 57 > melee range (45) -> out of attack range, no smash path.


def test_leveled_bot_coasts_within_the_hysteresis_margin():
    c = AttackerController(attacker_num=1, level=1, rng=random.Random(0))
    assert c.standoff == 45  # fixture anchor
    gap = c.standoff + 12  # 57: in [standoff+SPACING_STOP, standoff+SPACING_START] = [53, 61]
    a = _stub(400, 360)
    t = _stub(400 + gap, 360)  # target to the right -> toward = right
    held = c(a, t, frame=0).held
    assert _CTRL["right"] not in held, (
        f"leveled bot must COAST (no toward-move) at gap standoff+12={gap} inside the "
        f"hysteresis margin; pre-#970 the flat +8 deadband stepped in. held={sorted(held)}"
    )


def test_leveled_bot_still_closes_when_clearly_outside_the_band():
    # not-frozen guard: a gap beyond the re-trigger band still closes.
    c = AttackerController(attacker_num=1, level=1, rng=random.Random(0))
    gap = c.standoff + SPACING_START + 20  # well outside -> must move toward
    a = _stub(400, 360)
    t = _stub(400 + gap, 360)
    held = c(a, t, frame=0).held
    assert _CTRL["right"] in held, "leveled bot must still approach a clearly-too-far foe"


# ---- facing: a grounded leveled bot faces its target ----------------------------
# The "back-to-back, attacking away" bug: facing is otherwise set only by a movement
# press, so a bot that backed off (faced away) then coasts kept facing away and attacked
# the wrong direction. A gap of standoff+5 (=50) coasts (band [37,53]) and is beyond melee
# range (45), so no attack path — the only thing that can set facing is the #970 direct set.


def test_leveled_bot_faces_its_target_when_coasting():
    c = AttackerController(attacker_num=1, level=1, rng=random.Random(0))
    gap = c.standoff + 5  # 50: coasting, out of attack range
    a = _stub(400, 360)
    a.fighter.facing_right = False  # currently facing LEFT (as if it just backed off)
    t = _stub(400 + gap, 360)  # target to the RIGHT
    c(a, t, frame=0)  # controller only; step_horizontal not run, so facing is the bot's own
    assert a.fighter.facing_right is True, (
        "a grounded leveled bot must face its target (foe on the right) even while coasting; "
        "pre-#970 it kept its stale movement-facing and would attack away"
    )


def test_level_less_default_does_not_force_facing():
    # byte-identity guard: the level-less path must NOT touch facing directly (it is set
    # only by movement in step_horizontal, which this controller-only call never runs) —
    # so a level-less bot's facing is unchanged by decide(). Gap 60 is out of attack range.
    c = AttackerController(attacker_num=1)  # level=None
    a = _stub(400, 360)
    a.fighter.facing_right = False
    t = _stub(460, 360)  # 60px away -> out of melee range, no attack path
    c(a, t, frame=0)
    assert a.fighter.facing_right is False, "level-less default must not force-face (unchanged)"
