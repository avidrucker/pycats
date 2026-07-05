"""Nalio neutral-B Fireball — minimal moving projectile (#223).

PM3.6 Mario neutral-B as a flat-travelling projectile: an `Attack` that MOVES
(velocity) rather than the static-at-spawn hitbox. Covers the Attack-velocity
primitive, Nalio's neutral_b move data, and the end-to-end spawn → travel →
despawn via Player.update.
"""
import types

import pygame as pg

from pycats.combat.data import Circle, Hitbox, load_fighter_data
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.attack import Attack
from pycats.entities.platform import Platform
from pycats.entities.player import Player


def _owner(x=100, y=100):
    return types.SimpleNamespace(
        rect=pg.Rect(x, y, 40, 60),
        fighter=types.SimpleNamespace(facing_right=True),
    )


def _hb():
    return Hitbox(circle=Circle(dx=20, dy=30, r=10), damage=5, angle=0)


# ---------------- Attack velocity primitive ----------------

def test_attack_with_velocity_advances_each_frame():
    a = Attack(_owner(), hitbox=_hb(), lifetime=5, velocity=(10, 0))
    cx0, cy0 = a.hit_cx, a.hit_cy
    a.update()
    assert a.hit_cx == cx0 + 10, f"hit_cx should advance, got {a.hit_cx}"
    assert a.resolved[0][0] == cx0 + 10, "resolved circle must advance (process_hits reads it)"
    assert a.hit_cy == cy0
    assert a.rect.centerx == int(cx0 + 10)


def test_attack_without_velocity_stays_static():
    a = Attack(_owner(), hitbox=_hb(), lifetime=5)
    cx0 = a.hit_cx
    a.update()
    assert a.hit_cx == cx0, "a velocity-less attack must remain static (default behaviour)"


# ---------------- Nalio neutral_b move data ----------------

def test_nalio_defines_fireball_neutral_b():
    fd = load_fighter_data("nalio")
    assert "neutral_b" in fd.moves, "Nalio must define neutral_b (fireball)"
    m = fd.moves["neutral_b"]
    assert m.projectile_speed is not None, "fireball move must carry a projectile_speed"
    assert m.projectile_lifetime == 73
    assert m.startup == 14
    hb = m.hitboxes[0]
    assert hb.damage == 7
    assert hb.angle == 361          # Sakurai sentinel (supported via #203/#206)
    assert hb.base_knockback == 22
    assert hb.knockback_growth == 20


def test_non_projectile_move_has_no_projectile_speed():
    m = load_fighter_data("nalio").moves["jab"]
    assert m.projectile_speed is None


# ---------------- end-to-end spawn → travel → despawn ----------------

CONTROLS = {
    "left": pg.K_a, "right": pg.K_d, "up": pg.K_w, "down": pg.K_s,
    "attack": pg.K_e, "special": pg.K_b, "shield": pg.K_q,
}


def _frame(pressed=()):
    return InputFrame(held=set(pressed), pressed=set(pressed), released=set())


def _nalio_on_floor():
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 400, 960, 40), thin=False))
    p = Player(x=300, y=400, controls=CONTROLS, color=P1_COLOR, eye_color=WHITE,
               char_name="Nalio", facing_right=True,
               fighter_data=load_fighter_data("nalio"))
    for _ in range(8):  # settle / land on the floor
        p.update(_frame(), plats, pg.sprite.Group())
    assert p.fighter.on_ground, "fixture: Nalio should be grounded"
    return p, plats


def _find_projectile(group):
    for a in group:
        if getattr(a, "velocity", None):
            return a
    return None


def test_neutral_b_spawns_a_moving_projectile_that_travels_then_despawns():
    p, plats = _nalio_on_floor()
    attacks = pg.sprite.Group()
    p.update(_frame({pg.K_b}), plats, attacks)        # press B → start fireball
    proj = None
    for _ in range(40):                                # past startup (14), spawn
        p.update(_frame(), plats, attacks)
        proj = _find_projectile(attacks)
        if proj is not None:
            break
    assert proj is not None, "neutral-B should spawn a moving projectile"
    x0 = proj.hit_cx
    attacks.update()                                   # the loop ticks the attack group (runner.py:126)
    assert proj.hit_cx > x0, "projectile should travel right (facing_right)"

    for _ in range(90):                                # outlive ~73f / fly off-stage
        attacks.update()
    assert _find_projectile(attacks) is None, "projectile must despawn (lifetime / off-stage)"
