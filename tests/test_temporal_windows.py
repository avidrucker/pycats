"""Per-hitbox temporal windows (#204, a #142 gate / the #67 schema gap).

A move's hitboxes can declare *different* active sub-windows, so sequential
multi-hit moves (jab1→jab2, n-air clean+late, a multi-hit d-air) become
authorable — while every move that omits the feature stays byte-identical.

A `Hitbox` may carry `active_start`/`active_end` (inclusive frame offsets in the
MoveClock 1-indexed frame coordinate). `None` = "use the move's window"
(`[startup+1, startup+active]`, exactly today's behavior). `MoveClock` fires
each window on its own start frame.

Design B (#951, ruling on #945): boxes sharing a start frame may hold DIFFERENT
windows, each spawning its own `Attack`. `MoveTick` conveys every group opening
on a frame — `spawn`/`lifetime` for the first, `extra_spawns` for the rest — so
a single-group frame stays byte-identical (`extra_spawns == ()`), and `player.py`
loops over the groups.
"""

import types

import pygame
import pytest

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
from pycats.combat.move_clock import MoveClock
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.systems.combat import process_hits

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


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
    box_a = _box(damage=10.0, active_start=4, active_end=5)  # window len 2
    box_b = _box(damage=20.0, active_start=13, active_end=17)  # window len 5
    move = MoveData(
        name="two-hit",
        in_air=False,
        startup=3,
        active=14,
        recovery=3,  # total 20, env [4,17]
        hitboxes=(box_a, box_b),
    )

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
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P", facing_right=True)
    plats = [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(3):  # settle on the ground
        p.update(neutral, plats, group)

    box_a = _box(damage=10.0, active_start=4, active_end=5)
    box_b = _box(damage=20.0, active_start=13, active_end=17)
    move = MoveData(name="two-hit", in_air=False, startup=3, active=14, recovery=3, hitboxes=(box_a, box_b))
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
        MoveData(
            name="bad", in_air=False, startup=2, active=4, recovery=2, hitboxes=(_box(active_start=1, active_end=99),)
        )  # 99 > total 8


# ------------------------------------ Cycle 5: Design B — divergent same-start


def test_same_start_different_end_builds_and_spawns_both_windows():
    """Design B (#951): two boxes sharing a start frame with DIFFERENT ends now
    BUILD (no ValueError — the v1 rejection is lifted) and the clock opens BOTH
    groups on that shared start frame, each carrying its own box + lifetime. The
    first group rides `spawn`/`lifetime`; the rest ride `extra_spawns`."""
    a = _box(damage=10.0, active_start=4, active_end=5)  # window len 2
    b = _box(damage=20.0, active_start=4, active_end=9)  # same start, window len 6
    move = MoveData(name="clash", in_air=False, startup=3, active=7, recovery=2, hitboxes=(a, b))  # total 12, [4,9]

    clk = MoveClock()
    clk.start(move)
    frame4 = None
    for _ in range(12):
        t = clk.tick()
        if clk.frame == 4:
            frame4 = t

    assert frame4 is not None and frame4.spawn is not None
    groups = [(frame4.spawn, frame4.lifetime), *frame4.extra_spawns]
    assert len(groups) == 2, "both same-start windows open on frame 4"
    # Each group carries exactly its own box; lifetimes are the two distinct lengths.
    by_damage = {boxes[0].damage: (len(boxes), lifetime) for boxes, lifetime in groups}
    assert by_damage == {10.0: (1, 2), 20.0: (1, 6)}


def test_same_start_windows_become_two_attacks_on_one_frame():
    """The acceptance criterion for Design B end-to-end: two same-start boxes with
    different ends spawn two SEPARATE Attacks on the SAME frame via Player.update,
    each with its own frames_left and only its own box."""
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P", facing_right=True)
    plats = [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(3):  # settle on the ground
        p.update(neutral, plats, group)

    box_a = _box(damage=10.0, active_start=4, active_end=5)  # len 2
    box_b = _box(damage=20.0, active_start=4, active_end=9)  # same start, len 6
    move = MoveData(name="clash", in_air=False, startup=3, active=7, recovery=2, hitboxes=(box_a, box_b))
    p._clock.start(move)

    seen: set[int] = set()
    appeared: list[tuple[int, float, int]] = []  # (frame, box damage, frames_left)
    for frame in range(1, 13):
        p.update(neutral, plats, group)
        for atk in group:
            if id(atk) not in seen:
                seen.add(id(atk))
                appeared.append((frame, atk.hitboxes[0].damage, atk.frames_left))

    assert sorted(appeared) == [(4, 10.0, 2), (4, 20.0, 6)]


# ------------------------ Cycle 6: the multi-hit OUTCOME through process_hits (#852)


def _hit_counting_defender(rect):
    """A minimal duck-typed defender for `process_hits` — a big hurtbox that
    overlaps the attacker's hitbox and counts the hits it takes. Mirrors the stub
    in test_rehit_rate; only the hit tally matters here."""
    d = types.SimpleNamespace(
        rect=rect,
        facing_right=True,
        intangible=False,
        is_alive=True,
        fighter_data=FighterData(hurtbox=Hurtbox(circles=(Circle(dx=0, dy=0, r=80),)), moves={}),
        hits_received=0,
        percent=0.0,
    )

    def receive_hit(atk, is_crouching=False):
        d.hits_received += 1
        d.percent += atk.damage

    d.receive_hit = receive_hit
    d.record_hit_landed = lambda: None
    d.fighter = d
    return d


def test_two_windows_deal_two_hits_to_a_stationary_target():
    """The PYC-C-005 evidence gap (#852): a 2-window move doesn't just spawn two
    Attacks — a stationary target overlapping both windows actually TAKES two hits.
    Drives the real Player.update (spawns the windows) + process_hits + group.update
    against one overlapping defender across the move, and asserts it is struck
    exactly twice — 10 on window A's frame, 20 on window B's — for 30% total.

    Able-to-fail: with only one window opening (or a shared per-target hit-ID
    collapsing the two into one), hits_received would be 1 and percent 10.0."""
    p = Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P", facing_right=True)
    plats = [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]
    group = pygame.sprite.Group()
    neutral = InputFrame(held=set(), pressed=set(), released=set())
    for _ in range(3):  # settle on the ground
        p.update(neutral, plats, group)

    # A stationary defender parked on the attacker's hitbox origin (r=80 hurtbox
    # guarantees overlap with the r=10 hitbox both windows spawn there).
    defender = _hit_counting_defender(p.rect.copy())

    box_a = _box(damage=10.0, active_start=4, active_end=5)  # window A: frame 4, len 2
    box_b = _box(damage=20.0, active_start=13, active_end=17)  # window B: frame 13, len 5
    move = MoveData(name="two-hit", in_air=False, startup=3, active=14, recovery=3, hitboxes=(box_a, box_b))
    p._clock.start(move)

    for _frame in range(1, 21):
        p.update(neutral, plats, group)  # ticks the clock; spawns each window's Attack
        process_hits([defender], list(group))  # attacker isn't in the list — never a self-hit
        group.update()  # drain each Attack's lifetime

    assert defender.hits_received == 2, "target takes one hit per temporal window"
    assert defender.percent == 30.0, "10 from window A + 20 from window B"
