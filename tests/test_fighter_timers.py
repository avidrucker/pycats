"""S1 / #273 — `Fighter` owns its stateless per-frame timer decrements.

These five timers were ticked inline in `Player.update()` (N2: the adapter ticking
domain timers). `Fighter.tick_timers()` now owns the decrement; this guards the
contract — each ticks down by 1 per call and floors at 0 (never negative).
Able-to-fail: drop the `> 0` floor guard and `test_tick_timers_floors_at_zero`
goes red (0 → -1).
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
from pycats.entities.player import Player  # noqa: E402

CONTROLS = {"left": pygame.K_a, "right": pygame.K_d, "up": pygame.K_w,
            "down": pygame.K_s, "shield": pygame.K_q, "attack": pygame.K_e}

PURE_TIMERS = ("hurt_timer", "stun_timer", "landing_lag_timer",
               "ledge_regrab_lockout_timer", "shieldstun_timer")


def _fighter():
    pygame.init()
    p = Player(x=100, y=100, controls=CONTROLS, color=(10, 200, 30),
               eye_color=(0, 0, 200), char_name="P1", facing_right=True)
    return p.fighter


def test_tick_timers_decrements_each_pure_timer_by_one():
    f = _fighter()
    for name in PURE_TIMERS:
        setattr(f, name, 5)
    f.tick_timers()
    for name in PURE_TIMERS:
        assert getattr(f, name) == 4, name


def test_tick_timers_floors_at_zero():
    f = _fighter()
    for name in PURE_TIMERS:
        setattr(f, name, 0)
    f.tick_timers()
    for name in PURE_TIMERS:
        assert getattr(f, name) == 0, name  # never negative
