"""FrozenRect parity with pygame.Rect (#975/#833 §6).

FrozenRect (pycats/core/geometry.py) replaces pygame.Rect in the entity sim state.
It must reproduce pygame.Rect's *exact* integer arithmetic — truncate-toward-zero
on assignment, floor-division centres, edge/empty-rect colliderect semantics — or
the golden sims move. These tests pin that parity against the real pygame.Rect
across a grid of sizes and positions, so any drift in FrozenRect (or a pygame
upgrade that changes semantics) fails here rather than in a golden.

Able-to-fail: change any with_*/accessor to a non-pygame rule (e.g. round instead
of truncate, or w/2 instead of w//2) and the matching assertion reds.
"""

import pygame  # type: ignore
import pytest

from pycats.core.geometry import FrozenRect

# A grid that exercises even/odd widths+heights, positive and negative positions —
# the cases where floor-div vs round and trunc vs floor diverge.
GRID = [
    (0, 0, 60, 80),
    (10, 20, 61, 81),
    (10, 20, 59, 79),
    (10, 20, 63, 77),
    (-11, -13, 5, 5),
    (480, 300, 40, 60),
    (-1000, -1000, 40, 60),
]

TARGETS = [0, 1, 2, 100, 100.9, -0.9, -5.9, 200.5, 200.9, 481, -1000, 33.3]


def _rect(spec):
    return pygame.Rect(*spec), FrozenRect(*spec)


@pytest.mark.parametrize("spec", GRID)
def test_construction_truncates_like_pygame(spec):
    # Float coords truncate toward zero at construction, exactly as a pygame.Rect.
    f = FrozenRect(spec[0] + 0.9, spec[1] - 0.9, spec[2] + 0.5, spec[3] + 0.1)
    p = pygame.Rect(spec[0] + 0.9, spec[1] - 0.9, spec[2] + 0.5, spec[3] + 0.1)
    assert (f.x, f.y, f.w, f.h) == (p.x, p.y, p.w, p.h)


@pytest.mark.parametrize("spec", GRID)
def test_read_accessors_match_pygame(spec):
    p, f = _rect(spec)
    for name in ("x", "y", "w", "h", "width", "height", "left", "right", "top", "bottom", "centerx", "centery"):
        assert getattr(f, name) == getattr(p, name), name
    for name in ("center", "midbottom", "midtop", "topleft", "size"):
        assert getattr(f, name) == tuple(getattr(p, name)), name


@pytest.mark.parametrize("spec", GRID)
@pytest.mark.parametrize("v", TARGETS)
def test_scalar_setters_match_pygame(spec, v):
    for attr, meth in (
        ("x", "with_x"),
        ("y", "with_y"),
        ("left", "with_left"),
        ("top", "with_top"),
        ("right", "with_right"),
        ("bottom", "with_bottom"),
        ("centerx", "with_centerx"),
        ("centery", "with_centery"),
    ):
        p = pygame.Rect(*spec)
        setattr(p, attr, v)
        f = getattr(FrozenRect(*spec), meth)(v)
        assert (f.x, f.y, f.w, f.h) == (p.x, p.y, p.w, p.h), f"{meth}({v}) on {spec}"


@pytest.mark.parametrize("spec", GRID)
@pytest.mark.parametrize("pos", [(100, 200), (100.9, 200.9), (-1000, -1000), (33.3, -5.9)])
def test_pair_setters_match_pygame(spec, pos):
    for attr, meth in (("center", "with_center"), ("midbottom", "with_midbottom"), ("topleft", "with_topleft")):
        p = pygame.Rect(*spec)
        setattr(p, attr, pos)
        f = getattr(FrozenRect(*spec), meth)(pos)
        assert (f.x, f.y, f.w, f.h) == (p.x, p.y, p.w, p.h), f"{meth}({pos}) on {spec}"


@pytest.mark.parametrize("spec", GRID)
@pytest.mark.parametrize("size", [(40, 60), (61, 81), (1, 1)])
def test_with_size_matches_pygame(spec, size):
    p = pygame.Rect(*spec)
    p.size = size
    f = FrozenRect(*spec).with_size(size)
    assert (f.x, f.y, f.w, f.h) == (p.x, p.y, p.w, p.h)


@pytest.mark.parametrize("spec", GRID)
@pytest.mark.parametrize("dx,dy", [(0, 0), (5, 5), (5.9, 1.7), (-5.9, -1.7), (0, 1.7), (10, -3.9)])
def test_moved_matches_pygame_assignment(spec, dx, dy):
    # move_rect does `rect.x += round(vel.x); rect.y += vel.y`; FrozenRect.moved
    # replicates a raw `rect.x += dx; rect.y += dy` (truncate each coord).
    p = pygame.Rect(*spec)
    p.x += dx
    p.y += dy
    f = FrozenRect(*spec).moved(dx, dy)
    assert (f.x, f.y) == (p.x, p.y), f"moved({dx},{dy}) on {spec}"


def test_colliderect_matches_pygame_including_edges_and_empty():
    a_specs = [(0, 0, 10, 10), (480, 300, 40, 60)]
    b_specs = [
        (10, 0, 10, 10),  # touching right edge -> no collide
        (9, 0, 10, 10),  # 1px overlap
        (5, 5, 0, 0),  # empty inside -> no collide
        (2, 2, 3, 3),  # fully contained
        (-100, -100, 5, 5),  # far away
        (0, 10, 10, 10),  # touching bottom edge -> no collide
    ]
    for aspec in a_specs:
        for bspec in b_specs:
            pa, fa = _rect(aspec)
            pb, fb = _rect(bspec)
            assert fa.colliderect(fb) == bool(pa.colliderect(pb)), (aspec, bspec)


def test_colliderect_accepts_pygame_rect_operand():
    # Physics compares a FrozenRect actor against a platform whose rect may still be
    # a pygame.Rect (test fixtures) — colliderect must read x/y/w/h off either.
    f = FrozenRect(0, 0, 10, 10)
    assert f.colliderect(pygame.Rect(9, 0, 10, 10)) is True
    assert f.colliderect(pygame.Rect(10, 0, 10, 10)) is False


def test_with_methods_do_not_mutate_original():
    r = FrozenRect(0, 0, 60, 80)
    r.with_left(500)
    r.with_midbottom((100, 200))
    r.moved(10, 10)
    assert (r.x, r.y, r.w, r.h) == (0, 0, 60, 80)


def test_is_frozen():
    r = FrozenRect(0, 0, 60, 80)
    with pytest.raises(Exception):
        r.x = 5  # frozen dataclass -> no in-place mutation
