"""Body-relative vertical zone anchoring for hitbox dy (#309).

`zone_dy` maps a named vertical zone (head / center / feet / below_feet) plus a
fighter's standing body height to an absolute dy (px from the body top-left, which
grows downward: 0 = head, H = feet). Body-relative, so a move placed "at the feet"
lands at the feet on ANY body size — the #309 fix for Birky's move dy offsets, which
were authored for the old 60-tall body and sit too low (into the floor) on the 44.
"""
import pytest

from pycats.characters.body_zones import BODY_ZONES, zone_dy


def test_zones_are_ordered_head_to_below_feet():
    assert (BODY_ZONES["head"] < BODY_ZONES["center"]
            < BODY_ZONES["feet"] < BODY_ZONES["below_feet"])


def test_head_is_near_the_top_center_is_mid_feet_is_low():
    H = 44
    assert zone_dy("head", H) < H * 0.3            # up near the head
    assert abs(zone_dy("center", H) - H / 2) <= 1  # mid-body
    assert H * 0.7 < zone_dy("feet", H) <= H       # low, but still ON the body
    assert zone_dy("below_feet", H) > H            # past the feet (bounded spike)


def test_feet_stays_on_body_across_sizes():
    for H in (44, 60, 80):
        assert zone_dy("feet", H) <= H             # never resolves below the feet
        assert zone_dy("head", H) < zone_dy("center", H) < zone_dy("feet", H)


def test_nudge_shifts_within_the_zone():
    H = 44
    base = zone_dy("center", H)
    assert zone_dy("center", H, nudge=3) == base + 3
    assert zone_dy("center", H, nudge=-2) == base - 2


def test_unknown_zone_raises():
    with pytest.raises(KeyError):
        zone_dy("shoulder", 44)
