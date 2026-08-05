"""tests/test_temporal_windows_c005.py

Fresh red-green pinning of **PYC-C-005-GRAPE** (#999, successor to the closed #872
verification pass, which showed non-vacuity only by an ephemeral mutation). Restated
2026-08-01 for Design B (#951): same-start / different-end boxes now spawn plural
Attacks via `extra_spawns` (the old "one start frame ⇒ one window" v1 constraint is
lifted).

Claim ID: PYC-C-005-GRAPE
Statement: In pycats one move can open its hitboxes across DIFFERENT frame windows
(#204). Each box may carry its own `active_start`/`active_end`;
`combat/move_clock.py:_compute_windows` groups boxes by their `(start, end)` window, and
`MoveClock.tick()` opens each DISTINCT window on its own start frame — spawning a
SEPARATE Attack per window (player.py turns each spawn group into one Attack). Boxes
sharing an IDENTICAL window spawn together in one Attack. Design B (#951): two windows
sharing a start frame but differing in end each open as their own Attack on that frame,
carried by `MoveTick.extra_spawns` (first group rides `spawn`/`lifetime`, the rest ride
`extra_spawns`). A move with no per-box timing keeps one default window
`[startup+1, startup+active]`, unchanged.

The claim covers the SPAWNING mechanism, which is what these tests execute (N windows →
N spawn groups → N Attacks). The multi-hit OUTCOME (a target taking N hits) is the
composition with PYC-C-003 and is pinned separately by #852's
`test_two_windows_deal_two_hits_to_a_stationary_target`.

Each test below is proven able-to-fail by a NAMED source mutation (revert-check), then
reverted to green. The three mutations isolate cleanly — each reds only its own test:

  M1 — collapse every window onto the default START frame. In `_compute_windows`, key
       every group under the default window's start instead of its own:
       `windows.setdefault(start, [])` → `windows.setdefault(default_window[0], [])`.
       Distinct-start windows then all open on the first active frame instead of their
       own start frames. Reds only
       test_c005_distinct_windows_spawn_on_their_own_start_frames (the late window no
       longer opens on frame 13). Same-start (Test 2) and no-timing (Test 3) already
       key at the default start, so they are unaffected. THE claim-negating mutation for
       the headline "opens each distinct window on its own start frame".

  M2 — drop `extra_spawns`. In `tick()`, replace `extra_spawns = tuple(rest)` with
       `extra_spawns = ()`, so only the first group on a frame spawns and any other
       same-start window is dropped. Reds only
       test_c005_same_start_different_end_spawns_two_attacks_on_one_frame (2 groups → 1).
       Distinct-start frames each hold exactly one group (rest is already empty), so
       Test 1 and Test 3 are unaffected. THE claim-negating mutation for Design B.

  M3 — off-by-one the default window start. In `_compute_windows`, change
       `default_window = (move.startup + 1, ...)` to `(move.startup + 2, ...)`, so a
       no-timing move opens one frame late. Reds only
       test_c005_no_per_box_timing_keeps_one_default_window. Tests 1 and 2 use fully
       TIMED boxes (never touch `default_window`), so they are unaffected. Proves the
       no-timing contrast non-vacuous — the default-window guarantee is a real,
       breakable property.
"""

from __future__ import annotations

from pycats.combat.data import Circle, Hitbox, MoveData
from pycats.combat.move_clock import MoveClock


def _box(damage=10.0, **kw):
    """A hitbox at the origin; per-box timing passed via kwargs. Geometry is
    irrelevant here — these tests drive the CLOCK (spawn scheduling), not overlap."""
    return Hitbox(circle=Circle(0, 0, 10), damage=damage, angle=0, **kw)


def _drive(move, frames):
    """Tick a fresh clock `frames` times; return [(frame, MoveTick), ...] for the ticks
    that spawned something. Mirrors the harness in test_temporal_windows.py."""
    clk = MoveClock()
    clk.start(move)
    out = []
    for _ in range(frames):
        t = clk.tick()
        if t.spawn is not None:
            out.append((clk.frame, t))
    return out


def test_c005_distinct_windows_spawn_on_their_own_start_frames():
    """Headline conjunct (N distinct windows → N separate spawns, each on its OWN start
    frame): a move with two timed boxes in DIFFERENT windows fires each on its window's
    start frame, carrying only that window's box with that window's length as the
    lifetime — so player.py creates two SEPARATE Attacks. Able-to-fail via M1 (collapse
    every window onto the default start frame → the late window opens on frame 4 instead
    of 13). Claim: PYC-C-005-GRAPE."""
    box_a = _box(damage=10.0, active_start=4, active_end=5)  # window len 2
    box_b = _box(damage=20.0, active_start=13, active_end=17)  # window len 5
    move = MoveData(
        name="two-window", in_air=False, startup=3, active=14, recovery=3, hitboxes=(box_a, box_b)
    )  # total 20, env [4,17]

    spawns = _drive(move, frames=20)

    assert len(spawns) == 2, "two distinct windows spawn as two separate events"
    (fa, ta), (fb, tb) = spawns
    # Each window opens on its OWN start frame, with only its own box + its own lifetime.
    assert (fa, ta.lifetime, tuple(h.damage for h in ta.spawn), ta.extra_spawns) == (4, 2, (10.0,), ())
    assert (fb, tb.lifetime, tuple(h.damage for h in tb.spawn), tb.extra_spawns) == (13, 5, (20.0,), ())


def test_c005_same_start_different_end_spawns_two_attacks_on_one_frame():
    """Design B conjunct (#951): two boxes sharing a start frame but DIFFERENT ends open
    as two SEPARATE groups on that one frame — the first rides `spawn`/`lifetime`, the
    rest ride `extra_spawns` — each carrying only its own box + its own lifetime, so
    player.py spawns two Attacks on the same frame. Able-to-fail via M2 (drop
    `extra_spawns` → only the first same-start window opens). Claim: PYC-C-005-GRAPE."""
    box_a = _box(damage=10.0, active_start=4, active_end=5)  # same start, len 2
    box_b = _box(damage=20.0, active_start=4, active_end=9)  # same start, len 6
    move = MoveData(
        name="same-start", in_air=False, startup=3, active=7, recovery=2, hitboxes=(box_a, box_b)
    )  # total 12, env [4,9]

    spawns = _drive(move, frames=12)

    assert len(spawns) == 1, "both same-start windows open on the one shared start frame"
    frame, tick = spawns[0]
    assert frame == 4
    # Two groups open on frame 4: the first via spawn/lifetime, the second via extra_spawns.
    groups = [(tick.spawn, tick.lifetime), *tick.extra_spawns]
    assert len(groups) == 2, "same-start / different-end ⇒ two separate Attacks on one frame (Design B #951)"
    by_damage = {boxes[0].damage: (len(boxes), lifetime) for boxes, lifetime in groups}
    assert by_damage == {10.0: (1, 2), 20.0: (1, 6)}, "each group carries only its own box + its own lifetime"


def test_c005_no_per_box_timing_keeps_one_default_window():
    """Contrast conjunct (byte-identical for untimed moves): a move whose boxes carry NO
    per-box timing keeps ONE default window `[startup+1, startup+active]` — a single
    spawn on the first active frame carrying ALL boxes, lifetime == move.active, and no
    extra_spawns. Able-to-fail via M3 (off-by-one the default window start → it opens on
    frame 5, not 4). Proves the distinct-window behavior above is attributable to per-box
    timing, not to the clock always splitting boxes. Claim: PYC-C-005-GRAPE."""
    box_a = _box(damage=10.0)  # no active_start/active_end
    box_b = _box(damage=20.0)  # no active_start/active_end
    move = MoveData(
        name="untimed", in_air=False, startup=3, active=5, recovery=2, hitboxes=(box_a, box_b)
    )  # total 10, default window [4, 8]

    spawns = _drive(move, frames=10)

    assert len(spawns) == 1, "an untimed move opens exactly one default window"
    frame, tick = spawns[0]
    assert frame == 4, "the default window opens on the first active frame (startup + 1)"
    assert tick.lifetime == move.active, "the default window's lifetime is the move's active length"
    assert tuple(h.damage for h in tick.spawn) == (10.0, 20.0), "the one window carries ALL boxes together"
    assert tick.extra_spawns == (), "a single-window frame carries no extra_spawns"
