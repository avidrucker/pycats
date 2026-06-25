# tests/test_move_clock.py
"""Unit tests for MoveClock — the unified move-progress source (#71 / D1 slice 2).

These pin the exact frame semantics the old triple-tracked Player clock had, so
the extraction stays behaviour-preserving (parity + goldens are the integration
net; these are the direct unit net)."""
from pycats.combat.data import Circle, Hitbox, MoveData
from pycats.combat.move_clock import MoveClock, MoveTick


def _move(startup=3, active=3, recovery=6):
    hb = Hitbox(circle=Circle(dx=10, dy=10, r=5), damage=1.0, angle=0)
    return MoveData(name="t", in_air=False, startup=startup, active=active,
                    recovery=recovery, hitboxes=(hb,))


def test_idle_clock_is_inactive_and_zero():
    c = MoveClock()
    assert not c.is_active
    assert c.remaining == 0
    assert c.frame == 0
    assert c.move is None
    assert c.tick() == MoveTick(None, 0)  # no-op tick on an idle clock


def test_start_sets_remaining_to_total_at_frame_zero():
    c = MoveClock()
    m = _move()  # total = 12
    c.start(m)
    assert c.is_active and c.move is m
    assert c.frame == 0
    assert c.remaining == 12


def test_tick_advances_frame_and_decrements_remaining():
    c = MoveClock()
    c.start(_move())
    c.tick()
    assert c.frame == 1 and c.remaining == 11


def test_hitbox_spawns_exactly_once_on_first_active_frame():
    c = MoveClock()
    c.start(_move(startup=3, active=3, recovery=6))
    spawns = []
    for _ in range(12):
        t = c.tick()
        if t.spawn is not None:
            spawns.append((c.frame, t.lifetime))
    # active window startup<frame<=startup+active => frames 4,5,6; spawn once @4
    assert len(spawns) == 1
    assert spawns[0] == (4, 3)  # first active frame; lifetime == active


def test_completes_at_total_then_ticks_are_noops():
    c = MoveClock()
    c.start(_move())  # total = 12
    for _ in range(12):
        c.tick()
    assert not c.is_active and c.remaining == 0
    frame_at_completion = c.frame
    assert c.tick() == MoveTick(None, 0)  # no-op
    assert c.frame == frame_at_completion and c.remaining == 0


def test_remaining_never_goes_negative_past_completion():
    c = MoveClock()
    c.start(_move())
    for _ in range(50):
        c.tick()
    assert c.remaining == 0


def test_reset_clears_to_idle():
    c = MoveClock()
    c.start(_move())
    c.tick()
    c.tick()
    c.reset()
    assert not c.is_active and c.remaining == 0 and c.frame == 0 and c.move is None


def test_attack_timer_equals_total_minus_move_frame_invariant():
    """The golden snapshots record attack_timer AND move_frame; legacy keeps
    attack_timer == total - move_frame every frame. MoveClock must too."""
    c = MoveClock()
    c.start(_move())  # total = 12
    total = 12
    for _ in range(total):
        c.tick()
        assert c.remaining == total - c.frame


def test_recovery_zero_spawns_and_completes_same_frame():
    # edge case: active window's last frame == total (recovery=0)
    c = MoveClock()
    c.start(_move(startup=1, active=1, recovery=0))  # total = 2
    c.tick()  # frame 1: startup boundary, not yet active (1 < 1 is False)
    assert c.is_active
    t = c.tick()  # frame 2: active window (1 < 2 <= 2) AND completion
    assert t.spawn is not None and t.lifetime == 1
    assert not c.is_active and c.remaining == 0
