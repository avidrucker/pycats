"""The fighter outline is one continuous edge BEHIND body + ears + tail — it must
not seam at the body↔tail junction (#585).

Before #585 the tail was drawn first, then the body composite (with its own ring
baked in) on top, so the body's ring overpainted the tail body at the join — a
visible ring-coloured line between the body and the tail. The fix draws the ring
behind the tail (ring -> tail -> body pixels), so the tail covers the body ring
at the overlap and no ring segment is left on the join.

Detector: any pixel the *tail body* occupies that the *full render* shows in the
ring colour is the body ring painted over the tail = a seam. There must be none.
Able-to-fail: revert render_battle to `tail then merged body composite` and the
body ring lands back over the tail (~40 px) -> the count is non-zero.
"""


import pygame
import pytest

from pycats import render_battle as rb
from pycats.config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.core.input import InputFrame
from pycats.sim.runner import build_players, build_stage

pytestmark = pytest.mark.usefixtures("render_isolation")


def _settle():
    """Run a few sim frames so each Verlet tail droops to its resting pose, where
    its base overlaps the body's lower edge (the join that used to seam)."""
    platforms = build_stage()
    p1, p2, players = build_players()
    empty = InputFrame(set(), set(), set())
    for _ in range(30):
        for p in players:
            p.update(empty, platforms, pygame.sprite.Group())
    return p1, p2, players, platforms


def _seam_pixels(p, players, platforms):
    """Count pixels where the tail body sits but the full render shows the ring
    colour — i.e. the body ring painted over the tail (a junction seam)."""
    ring = tuple(rb.slot_accent_color(p))
    tail_col = tuple(rb.tinted(p.char_color, p))

    tail_only = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    tail_only.fill(BG_COLOR)
    rb.render_tail(tail_only, p.tail, rb.tinted(p.char_color, p), rb.slot_accent_color(p))

    full = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    full.fill(BG_COLOR)
    rb.render_battle(full, players, platforms)

    bounds = tail_only.get_bounding_rect()  # scan only where the tail is
    count = 0
    for x in range(bounds.left, bounds.right):
        for y in range(bounds.top, bounds.bottom):
            if tuple(tail_only.get_at((x, y))[:3]) == tail_col and tuple(full.get_at((x, y))[:3]) == ring:
                count += 1
    return count


def test_body_ring_never_paints_over_the_tail():
    p1, p2, players, platforms = _settle()
    assert _seam_pixels(p1, players, platforms) == 0
    assert _seam_pixels(p2, players, platforms) == 0


def test_outline_still_rings_the_body_outer_edge():
    # Regression guard: the fix must not drop the ring entirely — the body's outer
    # silhouette still carries slot-accent pixels above the head (clear of the tail).
    p1, _, players, platforms = _settle()
    ring = tuple(rb.slot_accent_color(p1))
    full = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    full.fill(BG_COLOR)
    rb.render_battle(full, players, platforms)
    # Band just above the head top, where only the body ring can be.
    top = p1.rect.top
    found = any(
        tuple(full.get_at((x, y))[:3]) == ring
        for x in range(p1.rect.left, p1.rect.right)
        for y in range(top - rb.FIGHTER_OUTLINE_WIDTH - 1, top + 1)
    )
    assert found, "body outer ring vanished — expected slot-accent pixels at the head edge"
