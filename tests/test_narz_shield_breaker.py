"""Narz neutral-B Shield Breaker — chargeable-special DATA (#1204, ruled #1184).

The charge ENGINE ships already (#1189: a chargeable move charges on its own
button and fires on release / at the cap; button-neutral output scaling gates on
`mv.chargeable`). This ticket authored the *data*: a real `neutral_b` on Narz with
`chargeable: true` + datamined timing/hitbox (Marth SpecialNEnd, PM 3.6). So these
tests drive the REAL narz fighter (not a synthetic graft) — they prove the shipped
JSON dispatches + charges through the engine, which the synthetic #1189 suite
(tests/test_charge_special.py) cannot.

Able-to-fail:
- Without `chargeable: true` on narz `neutral_b`, a special press routes to the
  immediate-fire `else`, so `test_neutral_b_press_enters_charge` (state == "charge",
  no move started) is RED.
- Without the authored move at all, `resolve_move_key` returns None for neutral-B
  and nothing fires — the release/autofire/spawn tests are RED.
- If the datamined damage regressed off 7.0, `test_authored_damage_is_datamined_seven`
  and the scaling tests are RED.
"""

import pygame as pg
from helpers import P1
from helpers import ground as _ground

from pycats.combat.charge import charge_factor
from pycats.combat.data import Status, load_fighter_data
from pycats.config import SMASH_CHARGE_FRAMES, SMASH_CHARGE_SCALE
from pycats.core.input import InputFrame
from pycats.entities.player import Player

_NARZ = load_fighter_data("narz")


def _frame(held=(), pressed=(), released=()):
    return InputFrame(
        held={P1[k] for k in held},
        pressed={P1[k] for k in pressed},
        released={P1[k] for k in released},
    )


def _mk():
    pg.init()
    p = Player(100, 100, P1, (48, 48, 96), eye_color=(0, 0, 0), char_name="narz", facing_right=True)
    plats = _ground()
    for _ in range(3):  # settle onto the ground
        p.update(_frame(), plats, pg.sprite.Group())
    return p, plats


def _step(p, plats, **kw):
    p.update(_frame(**kw), plats, pg.sprite.Group())


def _fire_and_get_attack(p, plats, hold_frames):
    """Press neutral-B, hold `hold_frames` frames (auto-fires at the cap), keep
    stepping until the swing spawns an Attack; return it."""
    grp = pg.sprite.Group()
    p.update(_frame(held=("special",), pressed=("special",)), plats, grp)
    for _ in range(hold_frames + 20):
        p.update(_frame(held=("special",)), plats, grp)
        if len(grp):
            return next(iter(grp))
    return None


# ---- the shipped narz neutral-B is a chargeable special ---------------------


def test_neutral_b_press_enters_charge():
    # RED without `chargeable: true`: the special would fire immediately (else
    # branch), so current_move would be set and state would not be "charge".
    p, plats = _mk()
    _step(p, plats, held=("special",), pressed=("special",))
    assert p.state == "charge"
    assert p.current_move is None  # the swing has NOT started — it is charging
    assert p.fighter.charge_button == "special"  # release reads the B button
    assert p.fighter.pending_charge_key == "neutral_b"


def test_neutral_b_release_fires_shield_breaker():
    p, plats = _mk()
    _step(p, plats, held=("special",), pressed=("special",))
    _step(p, plats, held=("special",))  # charge a bit
    _step(p, plats, released=("special",))  # let go of B
    assert p.current_move is p.fighter_data.moves["neutral_b"]
    assert p.current_move.name == "shield breaker"
    assert p.fighter.charge_timer == 0
    assert p.fighter.pending_charge_key is None


def test_neutral_b_reaching_max_autofires_without_release():
    p, plats = _mk()
    _step(p, plats, held=("special",), pressed=("special",))
    for _ in range(SMASH_CHARGE_FRAMES + 5):
        _step(p, plats, held=("special",))  # never release
    assert p.current_move is p.fighter_data.moves["neutral_b"]  # fired at the cap


# ---- output scaling: the datamined base scales like a smash -----------------


def test_full_charge_scales_spawned_hitbox_by_smash_scale():
    # Max charge (auto-fired at the cap) → spawned hitbox damage == authored 7.0
    # x SMASH_CHARGE_SCALE (reuses the smash output half, ruled #1184).
    p, plats = _mk()
    atk = _fire_and_get_attack(p, plats, SMASH_CHARGE_FRAMES)
    assert atk is not None, "no Attack spawned from the max-charged Shield Breaker"
    authored = _NARZ.moves["neutral_b"].hitboxes[0].damage  # 7.0
    assert atk.hitboxes[0].damage == authored * SMASH_CHARGE_SCALE


def test_min_charge_spawn_stays_within_the_authored_to_max_span():
    # A near-instant tap accrues a minimal fraction, so its spawned damage sits in
    # [authored, authored x SMASH_CHARGE_SCALE): at c=0 the factor is 1.0 (unscaled
    # == authored), and it never exceeds the full-charge value.
    p, plats = _mk()
    grp = pg.sprite.Group()
    p.update(_frame(held=("special",), pressed=("special",)), plats, grp)
    p.update(_frame(released=("special",)), plats, grp)  # release ASAP
    atk = None
    for _ in range(40):
        p.update(_frame(), plats, grp)
        if len(grp):
            atk = next(iter(grp))
            break
    assert atk is not None, "no Attack spawned from the tapped Shield Breaker"
    authored = _NARZ.moves["neutral_b"].hitboxes[0].damage  # 7.0
    assert charge_factor(0.0) == 1.0  # c=0 is exactly the authored value
    assert authored <= atk.hitboxes[0].damage < authored * SMASH_CHARGE_SCALE


# ---- the datamined value is registered FOUND (source: datamine) -------------


def test_authored_damage_is_datamined_seven():
    mv = _NARZ.moves["neutral_b"]
    hb = mv.hitboxes[0]
    assert hb.damage == 7.0  # Marth SpecialNEnd uncharged
    st = hb.status["damage"]
    assert st.status is Status.FOUND
    assert "datamine" in st.source
    # timing datamined FOUND too
    assert mv.status["startup"].status is Status.FOUND
    assert (mv.startup, mv.active, mv.recovery) == (4, 6, 23)
