"""S1 / #273 — `Fighter` owns its stateless per-frame timer decrements.

These five timers were ticked inline in `Player.update()` (N2: the adapter ticking
domain timers). `Fighter.tick_timers()` now owns the decrement; this guards the
contract — each ticks down by 1 per call and floors at 0 (never negative).
Able-to-fail: drop the `> 0` floor guard and `test_tick_timers_floors_at_zero`
goes red (0 → -1).
"""


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


# --- S4/#289: cleanly-movable coupled timers (prone + dodge). getup_roll/
# getup_attack stay inline (set-and-decremented same frame in the prone block).
ACTION_TIMERS = ("prone_timer", "dodge_timer")


def test_tick_action_timers_decrements_and_reports_no_expiry_above_zero():
    f = _fighter()
    for name in ACTION_TIMERS:
        setattr(f, name, 3)
    expired = f.tick_action_timers()
    for name in ACTION_TIMERS:
        assert getattr(f, name) == 2, name
    assert expired == set(), "nothing hit 0 this frame"


def test_tick_action_timers_reports_only_this_frames_expiries():
    f = _fighter()
    f.prone_timer = 1   # hits 0
    f.dodge_timer = 5   # decrements but stays > 0
    expired = f.tick_action_timers()
    assert expired == {"prone_timer"}
    assert f.prone_timer == 0 and f.dodge_timer == 4


def test_tick_action_timers_leaves_getup_timers_untouched():
    # getup_roll/getup_attack are NOT owned here — they keep their inline,
    # same-frame decrement in Player.update(). Able-to-fail: add them to the
    # method's loop and this reds.
    f = _fighter()
    f.getup_roll_timer = 7
    f.getup_attack_timer = 9
    f.tick_action_timers()
    assert f.getup_roll_timer == 7 and f.getup_attack_timer == 9


def test_tick_action_timers_already_zero_never_re_expires():
    # prone's once-on-expiry semantics depend on this: a timer already at 0 must
    # NOT appear in the expiry set (and must not go negative).
    f = _fighter()
    for name in ACTION_TIMERS:
        setattr(f, name, 0)
    expired = f.tick_action_timers()
    assert expired == set()
    for name in ACTION_TIMERS:
        assert getattr(f, name) == 0, name


# --- S4b/#293: the two out-of-block timers (respawn unfloored, ledge_hang floored)
def test_tick_respawn_decrements_unfloored():
    f = _fighter()
    f.respawn_timer = 2
    f.tick_respawn()
    assert f.respawn_timer == 1
    # Unfloored: keeps counting past 0 (a lives==0 fighter waits forever) — matches
    # the old inline `respawn_timer -= 1`. Able-to-fail: flooring it reds this.
    f.respawn_timer = 0
    f.tick_respawn()
    assert f.respawn_timer == -1

# (test_tick_ledge_hang_decrements_and_floors removed — the ledge-hang timeout and
#  its tick_ledge_hang() are gone in #475: PM has no hang timer.)
