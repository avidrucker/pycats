"""
tests/test_geometry.py

Tests for pycats/combat/geometry.py — pure circle-geometry helpers.

Functions under test:
  circle_overlap(ax, ay, ar, bx, by, br) -> bool
  resolve_circle(circle, origin_x, origin_y, facing_right) -> (cx, cy, r)
  circles_overlap(ax, ay, ar, circle_list_abs) -> bool
"""

import pytest
from pycats.combat.geometry import circle_overlap, resolve_circle, circles_overlap
from pycats.combat.data import Circle


# ---------------------------------------------------------------------------
# circle_overlap — two absolute circles
# ---------------------------------------------------------------------------

class TestCircleOverlap:
    def test_clearly_overlapping_circles_return_true(self):
        # Two circles with centers 3 apart, radii 5 and 5 → dist(3) < sum(10)
        assert circle_overlap(0, 0, 5, 3, 0, 5) is True

    def test_clearly_separate_circles_return_false(self):
        # Centers 20 apart, radii 3 and 3 → dist(20) > sum(6)
        assert circle_overlap(0, 0, 3, 20, 0, 3) is False

    def test_exactly_touching_circles_return_true(self):
        # Centers 10 apart, radii 5 and 5 → dist == sum → touching counts as overlap
        assert circle_overlap(0, 0, 5, 10, 0, 5) is True

    def test_one_circle_fully_inside_another_returns_true(self):
        # Small circle entirely inside large circle
        assert circle_overlap(0, 0, 20, 1, 1, 3) is True

    def test_same_center_circles_return_true(self):
        assert circle_overlap(5, 5, 4, 5, 5, 4) is True

    def test_diagonal_overlap_returns_true(self):
        # Centers at (0,0) and (3,4), dist=5; radii 3 and 3 → dist(5) < sum(6)
        assert circle_overlap(0, 0, 3, 3, 4, 3) is True

    def test_diagonal_no_overlap_returns_false(self):
        # Centers at (0,0) and (3,4), dist=5; radii 1 and 1 → dist(5) > sum(2)
        assert circle_overlap(0, 0, 1, 3, 4, 1) is False


# ---------------------------------------------------------------------------
# resolve_circle — facing-relative Circle → absolute (cx, cy, r)
# ---------------------------------------------------------------------------

WIDTH = 40  # the player body width (the facing-left mirror axis is its centre)


class TestResolveCircle:
    def test_facing_right_adds_dx_to_origin_x(self):
        c = Circle(dx=10, dy=20, r=5)
        cx, cy, r = resolve_circle(c, 100, 200, facing_right=True, width=WIDTH)
        assert cx == 110  # 100 + 10  (facing right is unaffected by width)

    def test_facing_right_preserves_dy(self):
        c = Circle(dx=10, dy=20, r=5)
        cx, cy, r = resolve_circle(c, 100, 200, facing_right=True, width=WIDTH)
        assert cy == 220  # 200 + 20

    def test_facing_left_mirrors_dx_around_body_center(self):
        # Facing left, cx = origin_x + width - dx (mirror around the body centre,
        # not the left-edge origin). dx=10 of a 40-wide body → 100 + 40 - 10 = 130.
        c = Circle(dx=10, dy=20, r=5)
        cx, cy, r = resolve_circle(c, 100, 200, facing_right=False, width=WIDTH)
        assert cx == 130

    def test_facing_left_dy_unaffected(self):
        c = Circle(dx=10, dy=20, r=5)
        cx, cy, r = resolve_circle(c, 100, 200, facing_right=False, width=WIDTH)
        assert cy == 220  # dy unchanged regardless of facing

    def test_radius_preserved_facing_right(self):
        c = Circle(dx=10, dy=20, r=7)
        cx, cy, r = resolve_circle(c, 0, 0, facing_right=True, width=WIDTH)
        assert r == 7

    def test_radius_preserved_facing_left(self):
        c = Circle(dx=10, dy=20, r=7)
        cx, cy, r = resolve_circle(c, 0, 0, facing_right=False, width=WIDTH)
        assert r == 7

    def test_body_center_dx_is_facing_invariant(self):
        # dx == width/2 is the body centre → same absolute centre for both facings
        # (a fighter's body part does not move when it turns around).
        c = Circle(dx=WIDTH // 2, dy=15, r=5)
        right = resolve_circle(c, 50, 100, facing_right=True, width=WIDTH)
        left = resolve_circle(c, 50, 100, facing_right=False, width=WIDTH)
        assert right[0] == left[0] == 50 + WIDTH // 2

    def test_default_cat_hurtbox_upper_facing_right(self):
        # Real data: upper hurtbox circle dx=20 (=body centre), origin (0,0).
        c = Circle(dx=20, dy=15, r=14)
        cx, cy, r = resolve_circle(c, 0, 0, facing_right=True, width=WIDTH)
        assert (cx, cy, r) == (20, 15, 14)

    def test_default_cat_hurtbox_upper_facing_left_is_invariant(self):
        # The body-centre hurtbox is facing-invariant: 0 + 40 - 20 = 20 (same).
        c = Circle(dx=20, dy=15, r=14)
        cx, cy, r = resolve_circle(c, 0, 0, facing_right=False, width=WIDTH)
        assert (cx, cy, r) == (20, 15, 14)


# ---------------------------------------------------------------------------
# circles_overlap — one circle vs list of absolute circles
# ---------------------------------------------------------------------------

class TestCirclesOverlap:
    def test_empty_list_returns_false(self):
        assert circles_overlap(0, 0, 5, []) is False

    def test_single_overlapping_circle_returns_true(self):
        # Subject at (0,0,5); target at (3,0,5) → overlapping
        assert circles_overlap(0, 0, 5, [(3, 0, 5)]) is True

    def test_single_non_overlapping_circle_returns_false(self):
        # Subject at (0,0,3); target at (20,0,3) → separate
        assert circles_overlap(0, 0, 3, [(20, 0, 3)]) is False

    def test_multiple_circles_any_overlapping_returns_true(self):
        # Two targets: one far away, one overlapping
        targets = [(100, 0, 3), (3, 0, 5)]
        assert circles_overlap(0, 0, 5, targets) is True

    def test_multiple_circles_none_overlapping_returns_false(self):
        targets = [(50, 0, 3), (100, 0, 3), (150, 0, 3)]
        assert circles_overlap(0, 0, 5, targets) is False

    def test_touching_circle_in_list_returns_true(self):
        # Exactly touching → counts as overlap
        targets = [(10, 0, 5)]
        assert circles_overlap(0, 0, 5, targets) is True

    def test_only_first_circle_overlaps(self):
        targets = [(3, 0, 5), (100, 0, 3)]
        assert circles_overlap(0, 0, 5, targets) is True

    def test_only_last_circle_overlaps(self):
        targets = [(100, 0, 3), (3, 0, 5)]
        assert circles_overlap(0, 0, 5, targets) is True
