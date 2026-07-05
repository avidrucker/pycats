"""Smash charge — hold-to-charge state machine (#327 slice 3a).

A chargeable smash (Nalio's fsmash/usmash/dsmash, #366) is HELD to charge and
RELEASED to fire. Pressing enters a `smash_charge` state and accumulates
`smash_charge_timer` (0..SMASH_CHARGE_FRAMES); releasing (or reaching the cap)
fires the pending smash on the move clock. This slice adds the state + timer
(which unblocks the #334 CHARGE bar); the damage/KB scaling is slice 3b, so the
smash still fires at its authored (uncharged) values here.

Golden-safety is structural: the sim path loads the default cat, which has no
chargeable move, and scripted controllers never press smash.
"""
import pygame as pg

from pycats.characters.default_cat import DEFAULT_FIGHTER_DATA
from pycats.combat.data import Circle, Hitbox, MoveData, load_fighter_data
from pycats.config import SMASH_CHARGE_FRAMES
from pycats.core.input import InputFrame
from pycats.entities.platform import Platform
from pycats.entities.player import Player

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s,
          attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held},
                      pressed={P1[k] for k in pressed},
                      released={P1[k] for k in released})


def _ground():
    return [Platform(pg.Rect(0, 100, 600, 40), thin=False)]


def _mk(char="nalio"):
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
               char_name=char, facing_right=True)
    plats = _ground()
    grp = pg.sprite.Group()
    for _ in range(3):                 # settle onto the ground
        p.update(_frame(), plats, grp)
    return p, plats


def _step(p, plats, **kw):
    p.update(_frame(**kw), plats, pg.sprite.Group())


# ---- schema -----------------------------------------------------------------

def test_chargeable_defaults_false_and_tilts_are_not_chargeable():
    m = MoveData(name="x", in_air=False, startup=1, active=1, recovery=1,
                 hitboxes=(Hitbox(circle=Circle(0, 0, 5), damage=1.0, angle=0),))
    assert m.chargeable is False
    assert load_fighter_data("nalio").moves["ftilt"].chargeable is False


def test_nalio_smashes_are_chargeable():
    nalio = load_fighter_data("nalio")
    assert all(nalio.moves[k].chargeable for k in ("fsmash", "usmash", "dsmash"))


# ---- charge state machine ---------------------------------------------------

def test_press_enters_charge_then_accumulates():
    p, plats = _mk()
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    assert p.state == "smash_charge"
    assert p.current_move is None          # the swing has NOT started yet
    _step(p, plats, held=("smash",))       # keep holding
    assert p.fighter.smash_charge_timer > 0  # accumulates while held
    assert p.current_move is None            # still charging


def test_holding_caps_the_timer_at_max():
    p, plats = _mk()
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    # Hold to just before the auto-fire cap; the timer never exceeds the max.
    for _ in range(SMASH_CHARGE_FRAMES - 2):
        _step(p, plats, held=("smash",))
    assert 0 < p.fighter.smash_charge_timer <= SMASH_CHARGE_FRAMES


def test_release_fires_the_pending_smash_and_clears_charge():
    p, plats = _mk()
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    _step(p, plats, held=("smash",))       # charge a bit
    _step(p, plats, released=("smash",))   # let go
    assert p.current_move is p.fighter_data.moves["fsmash"]
    assert p.fighter.smash_charge_timer == 0
    assert p.fighter.pending_smash_key is None


def test_reaching_max_autofires_without_release():
    p, plats = _mk()
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    for _ in range(SMASH_CHARGE_FRAMES + 5):
        _step(p, plats, held=("smash",))   # never release
    assert p.current_move is p.fighter_data.moves["fsmash"]  # fired at the cap


def test_hit_mid_charge_exits_and_clears():
    p, plats = _mk()
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    assert p.state == "smash_charge"
    # A hit sets hurt_timer AND cancels the charge (what the combat hit path does).
    p.fighter.hurt_timer = 20
    p.fighter.cancel_smash_charge()
    _step(p, plats, held=("smash",))       # input is gated during hitstun
    assert p.state == "hurt"
    assert p.fighter.pending_smash_key is None
    assert p.fighter.smash_charge_timer == 0


def test_down_and_up_directions_charge_their_smash():
    # Direction pre-HELD + smash freshly pressed (a fresh up-press would jump; a
    # held direction routes the smash by direction without triggering jump).
    dn, plats = _mk()
    _step(dn, plats, held=("smash", "down"), pressed=("smash",))
    _step(dn, plats, released=("smash",))
    assert dn.current_move is dn.fighter_data.moves["dsmash"]

    up, plats2 = _mk()
    _step(up, plats2, held=("smash", "up"), pressed=("smash",))
    _step(up, plats2, released=("smash",))
    assert up.current_move is up.fighter_data.moves["usmash"]


# ---- non-chargeable moves unaffected ----------------------------------------

def test_uncharged_move_fires_on_press_no_charge():
    # A tilt (attack input, not smash) fires immediately — no charge state.
    p, plats = _mk()
    _step(p, plats, held=("attack", "right"), pressed=("attack", "right"))
    assert p.state != "smash_charge"
    assert p.current_move is p.fighter_data.moves["ftilt"]


def test_default_cat_has_no_chargeable_move_golden_safety():
    assert not any(m.chargeable for m in DEFAULT_FIGHTER_DATA.moves.values())
