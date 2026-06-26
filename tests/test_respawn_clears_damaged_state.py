"""Issue #9 — a respawn (new life / new round) must reset the fighter to normal,
not leave it in the hurt/stun "damaged" state.

A player KO'd while hurt or stunned kept its hurt_timer/stun_timer through death
(the _ko early-return freezes them) and _respawn() reset the image colour but NOT
those timers — so the respawned fighter re-entered the hurt/stun FSM state and was
frozen (in_hitstun) for several frames at the start of its new life. reset_game()
already zeroes these timers; _respawn() must match it.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.entities.attack import Attack
from pycats.combat.data import Hitbox, Circle
from pycats.core.input import InputFrame
from pycats.render_battle import body_tint
from pycats.config import P1_COLOR, P2_COLOR, WHITE, RESPAWN_DELAY_FRAMES

CONTROLS = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
            "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _empty():
    return InputFrame(held=set(), pressed=set(), released=set())


def _ko_while_damaged_then_respawn(kind):
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(200, 400, 600, 20), thin=False))
    attacker = Player(x=360, y=400, controls=CONTROLS, color=P1_COLOR,
                      eye_color=WHITE, char_name="A", facing_right=True)
    victim = Player(x=420, y=400, controls=CONTROLS, color=P2_COLOR,
                    eye_color=WHITE, char_name="V", facing_right=True)
    empty = pg.sprite.Group()
    for _ in range(2):
        attacker.update(_empty(), plats, empty)
        victim.update(_empty(), plats, empty)

    if kind == "hurt":
        # Give the hit real knockback so computed hitstun (#40) exceeds 1 frame;
        # zero BKB/KBG would leave only the HITSTUN_FLOOR, which one update()
        # would consume before the assertion below.
        hb = Hitbox(circle=Circle(dx=27, dy=30, r=12), damage=10,
                    angle=0, base_knockback=30.0, knockback_growth=100.0)
        victim.fighter.receive_hit(Attack(owner=attacker, hitbox=hb, lifetime=1))
    else:  # stun
        victim.fighter._start_stun()
    victim.update(_empty(), plats, empty)
    assert victim.fighter.hurt_timer > 0 or victim.fighter.stun_timer > 0  # genuinely damaged

    victim.rect.center = (5000, 400)          # outside the blast zone -> KO
    victim.update(_empty(), plats, empty)
    assert not victim.fighter.is_alive

    for _ in range(RESPAWN_DELAY_FRAMES + 2):  # wait out respawn + settle
        victim.update(_empty(), plats, empty)
    return victim


def test_respawn_clears_hurt_state():
    v = _ko_while_damaged_then_respawn("hurt")
    assert v.fighter.is_alive
    assert v.fighter.hurt_timer == 0
    assert v.state not in ("hurt", "stun", "ko")
    assert body_tint(v) == v.char_color  # rendered normal (#75: tint is render-time)


def test_respawn_clears_stun_state():
    v = _ko_while_damaged_then_respawn("stun")
    assert v.fighter.is_alive
    assert v.fighter.stun_timer == 0
    assert v.state not in ("hurt", "stun", "ko")
    assert body_tint(v) == v.char_color  # rendered normal (#75: tint is render-time)
