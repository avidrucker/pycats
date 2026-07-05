"""Per-hitbox temporal windows (#204, a #142 gate / the #67 schema gap).

A move's hitboxes can declare *different* active sub-windows, so sequential
multi-hit moves (jab1→jab2, n-air clean+late, a multi-hit d-air) become
authorable — while every move that omits the feature stays byte-identical.

A `Hitbox` may carry `active_start`/`active_end` (inclusive frame offsets in the
MoveClock 1-indexed frame coordinate). `None` = "use the move's window"
(`[startup+1, startup+active]`, exactly today's behavior). `MoveClock` fires
each window on its own start frame; `MoveTick`'s shape is unchanged (≤1 window
starts per frame), so `player.py`/`attack.py` are untouched.
"""
import pygame
import pytest

from pycats.combat.data import Circle, Hitbox, MoveData
from pycats.combat.move_clock import MoveClock
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.platform import Platform

_CONTROLS = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w,
                 down=pygame.K_s, attack=pygame.K_v, special=pygame.K_c,
                 shield=pygame.K_x)


def _box(damage=10.0, **kw):
    return Hitbox(circle=Circle(0, 0, 10), damage=damage, angle=0, **kw)


def _drive(move, frames):
    """Tick a fresh clock `frames` times; return [(frame, MoveTick), ...] for the
    ticks that spawned something."""
    clk = MoveClock()
    clk.start(move)
    out = []
    for _ in range(frames):
        t = clk.tick()
        if t.spawn is not None:
            out.append((clk.frame, t))
    return out


# --------------------------------------------------------------- Cycle 1: schema

def test_hitbox_timing_defaults_to_none():
    """A hitbox with no per-box timing leaves both window fields None."""
    hb = _box()
    assert hb.active_start is None
    assert hb.active_end is None


def test_hitbox_accepts_explicit_window():
    """A hitbox can carry an explicit [active_start, active_end] window."""
    hb = _box(active_start=4, active_end=5)
    assert hb.active_start == 4
    assert hb.active_end == 5


# ------------------------------------------------- Cycle 2: MoveClock per-window

def test_two_windows_spawn_on_their_own_start_frames():
    """A move with two timed boxes fires each on its window's start frame, with
    that window's length as the spawn lifetime — and only its own box."""
    box_a = _box(damage=10.0, active_start=4, active_end=5)    # window len 2
    box_b = _box(damage=20.0, active_start=13, active_end=17)  # window len 5
    move = MoveData(name="two-hit", in_air=False,
                    startup=3, active=14, recovery=3,           # total 20, env [4,17]
                    hitboxes=(box_a, box_b))

    spawns = _drive(move, frames=20)

    assert len(spawns) == 2, "exactly two spawn events, one per window"
    (fa, ta), (fb, tb) = spawns
    # Box A: spawns on frame 4, lifetime 2, carries only box A.
    assert fa == 4
    assert ta.lifetime == 2
    assert tuple(h.damage for h in ta.spawn) == (10.0,)
    # Box B: spawns on frame 13, lifetime 5, carries only box B.
    assert fb == 13
    assert tb.lifetime == 5
    assert tuple(h.damage for h in tb.spawn) == (20.0,)


# ----------------------------------- Cycle 3: end-to-end through Player.update

def test_two_windows_become_two_separate_attacks_via_player_update():
    """The acceptance criterion: driving a 2-window move through the real
    Player.update spawns two SEPARATE Attacks on their distinct start frames,
    each with the right frames_left and only its own box."""
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0),
               char_name="P", facing_right=True)
    plats = [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(3):  # settle on the ground
        p.update(neutral, plats, group)

    box_a = _box(damage=10.0, active_start=4, active_end=5)
    box_b = _box(damage=20.0, active_start=13, active_end=17)
    move = MoveData(name="two-hit", in_air=False,
                    startup=3, active=14, recovery=3, hitboxes=(box_a, box_b))
    p._clock.start(move)

    seen: set[int] = set()
    appeared: list[tuple[int, float, int]] = []  # (frame, box damage, frames_left)
    for frame in range(1, 21):
        p.update(neutral, plats, group)  # ticks the clock; adds Attacks, no group.update
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].damage, atk.frames_left))

    assert appeared == [(4, 10.0, 2), (13, 20.0, 5)]


# ------------------------------------------------- Cycle 4: validation guards


def test_half_specified_window_is_rejected():
    """Setting active_start without active_end (or vice versa) is an error."""
    with pytest.raises(ValueError):
        _box(active_start=4)
    with pytest.raises(ValueError):
        _box(active_end=5)


def test_inverted_window_is_rejected():
    """A window whose start is after its end is an error."""
    with pytest.raises(ValueError):
        _box(active_start=6, active_end=4)


def test_window_outside_the_move_is_rejected():
    """A window that starts before frame 1 or ends after the move is an error."""
    with pytest.raises(ValueError):
        MoveData(name="bad", in_air=False, startup=2, active=4, recovery=2,
                 hitboxes=(_box(active_start=1, active_end=99),))  # 99 > total 8


def test_same_start_different_end_is_rejected():
    """Two boxes that begin on the same frame must share the same window (v1
    constraint — one window => one Attack)."""
    a = _box(damage=10.0, active_start=4, active_end=5)
    b = _box(damage=20.0, active_start=4, active_end=9)  # same start, different end
    with pytest.raises(ValueError):
        MoveData(name="clash", in_air=False, startup=3, active=10, recovery=2,
                 hitboxes=(a, b))
