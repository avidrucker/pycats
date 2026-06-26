"""#102 — a fighter must not stay red (HURT tint) after being hit while moving or
attacking.

The red flash is render-time (`render_battle.body_tint`, #75): RED while
`fighter.hurt_timer > 0`, and the per-frame decrement in `Player.update` is
*unconditional* (not gated by state or held input). So the tint must clear within
the hitstun window regardless of a held movement direction or an in-progress
attack. The original symptom (a state-flag red that stuck when hit mid-action,
`player.py:19`) predates the #75 render-time refactor and does NOT reproduce on
current `main` — these are the regression guards that keep it that way.

Revert-the-fix check: gate the decrement at `Player.update` on
`not in_hitstun`/`self.state != "attack"` and the timer never reaches 0 → both
tests go red.
"""
import pygame as pg

from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.entities.attack import Attack
from pycats.combat.data import Hitbox, Circle
from pycats.core.input import InputFrame
from pycats.render_battle import body_tint
from pycats.config import P1_COLOR, P2_COLOR, WHITE, RED

CONTROLS = {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w,
            "down": pg.K_s, "shield": pg.K_q, "attack": pg.K_e}


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held=set(held), pressed=set(pressed), released=set(released))


def _floor():
    g = pg.sprite.Group()
    g.add(Platform(pg.Rect(0, 400, 1200, 20), thin=False))
    return g


def _mk(x, name, color):
    return Player(x=x, y=400, controls=CONTROLS, color=color, eye_color=WHITE,
                  char_name=name, facing_right=True)


def _hit(victim, attacker):
    # Real knockback so computed hitstun (#40) exceeds 1 frame — else a single
    # update() would consume it before we can observe the countdown.
    hb = Hitbox(circle=Circle(dx=27, dy=30, r=12), damage=10, angle=0,
                base_knockback=30.0, knockback_growth=100.0)
    victim.fighter.receive_hit(Attack(owner=attacker, hitbox=hb, lifetime=1))


def _assert_tint_clears(victim_input):
    """Drive a victim that is continuously fed `victim_input()` (moving or
    attacking), hit it mid-action, and assert the red HURT tint clears within a
    bounded window. Returns the frame the timer hit 0."""
    plats, empty = _floor(), pg.sprite.Group()
    attacker, victim = _mk(360, "A", P1_COLOR), _mk(420, "V", P2_COLOR)

    # Settle the victim into the moving/attacking action before the hit lands.
    for _ in range(2):
        attacker.update(_frame(), plats, empty)
        victim.update(victim_input(), plats, empty)

    _hit(victim, attacker)
    assert victim.fighter.hurt_timer > 0, "setup: victim is not actually hurt"
    assert tuple(body_tint(victim)) == tuple(RED), "setup: victim should be red right after the hit"

    cleared_at = None
    for f in range(60):  # well past any reasonable hitstun
        victim.update(victim_input(), plats, empty)
        if victim.fighter.hurt_timer == 0:
            cleared_at = f
            break

    assert cleared_at is not None, "hurt_timer never returned to 0 — fighter stuck red"
    assert tuple(body_tint(victim)) == tuple(victim.char_color), \
        "tint did not return to the character colour after hitstun"
    return cleared_at


def test_hurt_tint_clears_when_hit_while_moving():
    _assert_tint_clears(lambda: _frame(held={CONTROLS["right"]}))


def test_hurt_tint_clears_when_hit_while_attacking():
    _assert_tint_clears(
        lambda: _frame(held={CONTROLS["attack"]}, pressed={CONTROLS["attack"]})
    )
