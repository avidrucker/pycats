"""CPU difficulty scaffold — deterministic core (#232, #231 / #148 step 1).

A `level` (1-9) sets the deterministic AI knobs (reaction_delay / attack_period /
standoff) from the #148 Q5 table; a level-less controller is unchanged (golden-safe).
RNG knobs (follow-through / shield) are a later child. Numbers per #148 (tuning
starting points).
"""
import types

import pygame as pg

from pycats.sim.controllers import AttackerController, level_params


def _knobs(p):
    return (p.reaction_delay, p.attack_period, p.standoff)


def test_level_params_anchor_values():
    assert _knobs(level_params(1)) == (30, 48, 45)
    assert _knobs(level_params(3)) == (20, 36, 40)
    assert _knobs(level_params(5)) == (12, 24, 35)
    assert _knobs(level_params(7)) == (6, 16, 32)
    assert _knobs(level_params(9)) == (1, 10, 30)


def test_intermediate_level_uses_nearest_anchor():
    # even levels are equidistant between odd anchors → tie resolves to the higher.
    assert level_params(2) == level_params(3)
    assert level_params(4) == level_params(5)
    assert level_params(8) == level_params(9)


def test_attacker_controller_pulls_knobs_from_level():
    c9 = AttackerController(level=9)
    assert (c9.attack_period, c9.standoff, c9.reaction_delay) == (10, 30, 1)
    c1 = AttackerController(level=1)
    assert (c1.attack_period, c1.standoff, c1.reaction_delay) == (48, 45, 30)


def test_default_controller_has_zero_reaction_delay():
    # level-less default must be unchanged (golden-safe): no reaction latency.
    assert AttackerController().reaction_delay == 0


# ---- reaction_delay actually gates the first attack ----

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _stub(cx, cy, alive=True, on_ground=True):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground)
    s.controls = _CTRL
    return s


def _first_attack_frame(level):
    c = AttackerController(attacker_num=1, level=level)
    a, t = _stub(100, 300), _stub(140, 300)  # adx=40, dy=0 → in range for Lv1 and Lv9
    for k in range(60):
        fi = c(a, t, frame=k)
        if _CTRL["attack"] in fi.pressed:
            return k
    return None


def test_reaction_delay_gates_first_attack_higher_level_attacks_sooner():
    lv9, lv1 = _first_attack_frame(9), _first_attack_frame(1)
    assert lv9 is not None and lv1 is not None, f"both should attack; lv9={lv9} lv1={lv1}"
    assert lv9 < lv1, f"Lv9 (delay 1) must attack before Lv1 (delay 30): lv9={lv9} lv1={lv1}"
