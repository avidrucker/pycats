"""Issue #1 / #1020 — PM-faithful ground jostle (ADR-0012).

`resolve_player_push` is a literal port of meleelight's grounded push
(schmooblidon/meleelight @ 27af171, src/physics/physics.js): a gradual,
**position-only** nudge apart along X, firing only when BOTH fighters are grounded
on the *same* platform and their centres are within `JOSTLE_TRIGGER_PX`. It never
touches velocity and never resolves Y.

These are the able-to-fail regression anchors for the ADR-0012 rewrite — the old
resolver resolved the whole overlap in one frame AND rewrote `vel.x`, so the
gradual-nudge (a) and velocity-untouched (b) assertions red against it. The
grounded gate (c) also supersedes the #68 flyover-ratchet fix: an airborne fighter
neither pushes nor is pushed, so two airborne fighters pass through each other.

Repro/proof of the original #1 defect: repros/repro_issue_1.py.
"""

import pygame
from helpers import P1, P2  # noqa: F401  (kept for parity with the sibling push tests)

from pycats.config import PLAYER_SIZE
from pycats.core.physics import (
    JOSTLE_PUSH_PX,
    JOSTLE_TRIGGER_PX,
    resolve_player_push,
)
from pycats.entities.platform import Platform

PW = PLAYER_SIZE[0]  # player width (40)
FLOOR_TOP = 410


def _floor():
    # A wide thick (solid) platform; top at y=FLOOR_TOP.
    return [Platform(pygame.Rect(0, FLOOR_TOP, 960, 80), thin=False)]


class _FakeFighter:
    """Minimal stand-in — resolve_player_push reads only `.state`, `.rect`,
    `.fighter.on_ground`, and `.fighter.vel`. A fake gives exact control over the
    grounded flag and position (Player.state/on_ground are derived properties that
    need a full input sequence to force)."""

    def __init__(self, midbottom, *, state="idle", on_ground=True):
        self.rect = pygame.Rect(0, 0, *PLAYER_SIZE)
        self.rect.midbottom = midbottom
        self.vel = pygame.Vector2(0, 0)
        self.state = state
        self.on_ground = on_ground
        self.fighter = self  # resolver reads a.fighter.on_ground / a.fighter.vel


def test_wide_overlap_separates_gradually_and_settles_overlapping():
    # (a) A wide overlap is NOT resolved in one frame: each fighter steps
    # JOSTLE_PUSH_PX apart per frame and is still overlapping afterwards. The pair
    # settles when centres reach the trigger — slightly overlapping (canon), not
    # fully apart (the old resolver snapped them to a >= body-width gap in one frame).
    floor = _floor()
    a = _FakeFighter((480, FLOOR_TOP))
    b = _FakeFighter((490, FLOOR_TOP))  # centres 10px apart → overlapping, within trigger
    ax0, bx0 = a.rect.x, b.rect.x

    resolve_player_push([a, b], floor)

    assert a.rect.x == ax0 - JOSTLE_PUSH_PX and b.rect.x == bx0 + JOSTLE_PUSH_PX, "not a gradual per-frame nudge"
    assert abs(a.rect.centerx - b.rect.centerx) == 10 + 2 * JOSTLE_PUSH_PX, "each fighter must move exactly one step"
    assert a.rect.colliderect(b.rect), "a single frame fully separated the pair (should be gradual)"

    for _ in range(20):  # run to rest
        resolve_player_push([a, b], floor)
    gap = abs(a.rect.centerx - b.rect.centerx)
    assert JOSTLE_TRIGGER_PX <= gap < JOSTLE_TRIGGER_PX + 2 * JOSTLE_PUSH_PX, (
        f"did not settle at the trigger (gap={gap})"
    )
    assert a.rect.colliderect(b.rect), (
        "fighters should settle slightly overlapping (centre-dist < body width), not apart"
    )


def test_push_never_touches_velocity():
    # (b) The resolver mutates position only — neither vel.x (the old
    # zero/half/average rewrite) nor vel.y (the old vertical branch) is changed.
    floor = _floor()
    a = _FakeFighter((480, FLOOR_TOP))
    b = _FakeFighter((490, FLOOR_TOP))
    a.vel = pygame.Vector2(5.0, 7.0)
    b.vel = pygame.Vector2(-3.0, -2.0)

    resolve_player_push([a, b], floor)

    assert (a.vel.x, a.vel.y) == (5.0, 7.0), "push modified a fighter's velocity"
    assert (b.vel.x, b.vel.y) == (-3.0, -2.0), "push modified a fighter's velocity"


def test_no_push_when_either_fighter_airborne():
    # (c) The grounded gate: if either fighter is airborne, no push fires — so two
    # airborne fighters pass through / overlap each other, and a fighter flying over
    # a grounded one never shoves it (supersedes the #68 vertical-overlap gate).
    floor = _floor()
    for a_ground, b_ground in [(False, True), (True, False), (False, False)]:
        a = _FakeFighter((480, FLOOR_TOP), on_ground=a_ground)
        b = _FakeFighter((490, FLOOR_TOP), on_ground=b_ground)
        before = (a.rect.x, b.rect.x)

        resolve_player_push([a, b], floor)

        assert (a.rect.x, b.rect.x) == before, f"airborne pair pushed (grounded={a_ground},{b_ground})"


def test_no_push_across_different_platforms():
    # (d) Same-platform gate: grounded fighters on different platforms are not
    # jostled even when their centres are within the trigger.
    floor = Platform(pygame.Rect(0, FLOOR_TOP, 960, 80), thin=False)  # top 410
    upper = Platform(pygame.Rect(400, 300, 200, 20), thin=False)  # top 300
    a = _FakeFighter((480, FLOOR_TOP))  # rests on floor
    b = _FakeFighter((490, 300))  # rests on upper; centre 10px from a
    before = (a.rect.x, b.rect.x)

    resolve_player_push([a, b], [floor, upper])

    assert (a.rect.x, b.rect.x) == before, "fighters on different platforms were jostled"


def test_flush_adjacent_not_pushed():
    # Bodies exactly touching sit PW (40px) apart centre-to-centre, beyond the 35px
    # trigger, so resting side-by-side fighters are not jostled.
    assert PW >= JOSTLE_TRIGGER_PX  # guard: the scenario is only meaningful if flush > trigger
    floor = _floor()
    a = _FakeFighter((480, FLOOR_TOP))
    b = _FakeFighter((480 + PW, FLOOR_TOP))  # flush: centres PW apart
    before = (a.rect.x, b.rect.x)

    resolve_player_push([a, b], floor)

    assert (a.rect.x, b.rect.x) == before, "flush-adjacent fighters (centre-dist == body width) were jostled"


def test_dodge_player_skips_push():
    # A fighter in the "dodge" state is intangible to the push (preserved guard).
    floor = _floor()
    a = _FakeFighter((480, FLOOR_TOP), state="dodge")
    b = _FakeFighter((490, FLOOR_TOP))
    before = (a.rect.x, b.rect.x)

    resolve_player_push([a, b], floor)

    assert (a.rect.x, b.rect.x) == before, "dodging fighter was pushed"


def test_perfectly_stacked_separates_deterministically():
    # Identical centerx (worst case): the tie-break moves them apart on X the same
    # way every time — no jitter, deterministic, and they do separate.
    floor = _floor()

    def push_once():
        a = _FakeFighter((480, FLOOR_TOP))
        b = _FakeFighter((480, FLOOR_TOP))  # exactly stacked
        resolve_player_push([a, b], floor)
        return a.rect.centerx, b.rect.centerx

    r1 = push_once()
    r2 = push_once()
    assert r1 == r2, "tie-break is non-deterministic"
    assert r1[0] != r1[1], "perfectly-stacked fighters did not separate on X"
