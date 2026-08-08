"""Button-neutral charge trigger (#1189): a chargeable SPECIAL charges on the
special button, not the smash button.

The charge mechanism (#327) was button-neutral downstream (the spawn-time scaling
gates on `mv.chargeable`) but its TRIGGER was hard-bound to the smash button: a
chargeable special press fired immediately, uncharged, and the release watched
`smash`. #1189 generalizes the trigger — the start-gate begins a charge for a
chargeable move pressed via smash OR special, `charge_button` records which, and
the release reads that same button. So a B-button move (Shield Breaker) charges on
special and never reads the smash button; smashes still charge on smash.

These tests are able to fail: without the #1189 slice a chargeable special routes
to the immediate-fire `else`, so `test_special_press_enters_charge_not_fire`
(state == "charge", no move started) is RED. The existing smash-charge suite
(tests/test_smash_charge.py) proves the smash path is byte-identical.
"""

from dataclasses import replace

import pygame as pg
from helpers import P1
from helpers import ground as _ground

from pycats.combat.data import Circle, Hitbox, MoveData, load_fighter_data
from pycats.config import SMASH_CHARGE_FRAMES, SMASH_CHARGE_SCALE
from pycats.core.input import InputFrame
from pycats.entities.player import Player

# A chargeable neutral-B grafted onto the minimal fixture cat (#591). testcat has
# no chargeable move of its own (golden-safety), so the chargeable special lives
# only in this injected fighter_data — the sim/golden cat is untouched.
_CHARGE_NB = MoveData(
    name="test_charge_nb",
    in_air=False,
    startup=2,
    active=3,
    recovery=2,
    hitboxes=(Hitbox(circle=Circle(20, 0, 8), damage=10.0, angle=361, base_knockback=25.0, knockback_growth=90.0),),
    chargeable=True,
)
_BASE = load_fighter_data("testcat")
_FD_CHARGE_SPECIAL = replace(_BASE, moves={**_BASE.moves, "neutral_b": _CHARGE_NB})


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held}, pressed={P1[k] for k in pressed}, released={P1[k] for k in released})


def _mk(fighter_data):
    pg.init()
    p = Player(
        100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True, fighter_data=fighter_data
    )
    plats = _ground()
    grp = pg.sprite.Group()
    for _ in range(3):  # settle onto the ground
        p.update(_frame(), plats, grp)
    return p, plats


def _step(p, plats, **kw):
    p.update(_frame(**kw), plats, pg.sprite.Group())


# ---- a chargeable special charges on the special button ---------------------


def test_special_press_enters_charge_not_fire():
    # RED without #1189: a chargeable special fired immediately (else branch), so
    # state would be "attack"/current_move set, not "charge".
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    _step(p, plats, held=("special",), pressed=("special",))
    assert p.state == "charge"
    assert p.current_move is None  # the swing has NOT started — it is charging
    assert p.fighter.charge_button == "special"  # release will read the B button


def test_special_hold_accumulates_the_timer():
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    _step(p, plats, held=("special",), pressed=("special",))
    _step(p, plats, held=("special",))  # keep holding B
    assert p.fighter.charge_timer > 0
    assert p.current_move is None  # still charging


def test_special_release_fires_the_pending_special_and_clears_charge():
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    _step(p, plats, held=("special",), pressed=("special",))
    _step(p, plats, held=("special",))  # charge a bit
    _step(p, plats, released=("special",))  # let go of B
    assert p.current_move is p.fighter_data.moves["neutral_b"]
    assert p.fighter.charge_fraction > 0.0  # a real charge was captured for output scaling
    assert p.fighter.charge_timer == 0
    assert p.fighter.pending_charge_key is None


def test_special_reaching_max_autofires_without_release():
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    _step(p, plats, held=("special",), pressed=("special",))
    for _ in range(SMASH_CHARGE_FRAMES + 5):
        _step(p, plats, held=("special",))  # never release
    assert p.current_move is p.fighter_data.moves["neutral_b"]  # fired at the cap


# ---- the smash button plays no part in a special charge ---------------------


def test_special_charge_ignores_the_smash_button():
    # Charging on special: holding smash does not fire it, and RELEASING special
    # fires even while smash stays held — the release reads `special`, not `smash`.
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    _step(p, plats, held=("special",), pressed=("special",))
    _step(p, plats, held=("special", "smash"), pressed=("smash",))  # mash smash — no effect
    assert p.current_move is None  # smash press did NOT fire the special charge
    assert p.state == "charge"
    _step(p, plats, held=("smash",), released=("special",))  # drop B, keep smash held
    assert p.current_move is p.fighter_data.moves["neutral_b"]  # fired on the B release


def test_nonchargeable_special_still_fires_on_press():
    # A special without `chargeable` fires immediately — #1189 only routes CHARGEABLE
    # specials into the charge state, so plain B moves are unchanged.
    plain_nb = replace(_CHARGE_NB, chargeable=False)
    fd = replace(_BASE, moves={**_BASE.moves, "neutral_b": plain_nb})
    p, plats = _mk(fd)
    _step(p, plats, held=("special",), pressed=("special",))
    assert p.state != "charge"
    assert p.current_move is p.fighter_data.moves["neutral_b"]


# ---- end-to-end: a charged special spawns a damage-scaled hitbox ------------


def test_full_charge_special_scales_the_spawned_hitbox():
    p, plats = _mk(_FD_CHARGE_SPECIAL)
    grp = pg.sprite.Group()
    p.update(_frame(held=("special",), pressed=("special",)), plats, grp)
    atk = None
    for _ in range(SMASH_CHARGE_FRAMES + 15):  # hold B to max (auto-fire), let the window open
        p.update(_frame(held=("special",)), plats, grp)
        if len(grp):
            atk = next(iter(grp))
            break
    assert atk is not None, "no Attack spawned from the charged special"
    authored = _CHARGE_NB.hitboxes[0].damage  # 10.0
    assert atk.hitboxes[0].damage == authored * SMASH_CHARGE_SCALE


# ---- the smash path is unchanged: a chargeable smash charges on smash --------


def test_smash_still_charges_on_the_smash_button():
    # Regression guard for the button-neutral field on the smash branch: a chargeable
    # smash (Nalio's fsmash) records charge_button == "smash" and charges as before.
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    plats = _ground()
    for _ in range(3):
        p.update(_frame(), plats, pg.sprite.Group())
    _step(p, plats, held=("smash", "right"), pressed=("smash", "right"))
    assert p.state == "charge"
    assert p.fighter.charge_button == "smash"
    _step(p, plats, released=("smash",))
    assert p.current_move is p.fighter_data.moves["fsmash"]
