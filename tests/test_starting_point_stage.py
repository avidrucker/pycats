"""Spec test for the v1 "Starting Point" stage — pycats' flat Final Destination (#660).

Asserts the built layout against the PM FD measurements researched in #659
(docs/research/2026-07-06-pm-final-destination-measurements.md): one flat main platform,
no side platforms, sized to the Melee FD ground half-width scaled by PX_PER_UNIT, with
grabbable ledges at both edges.

Able-to-fail: the width assertion pins the concrete 924 px AND re-evaluates the #659
derivation, so a drift in either the platform width or the scale/unit it derives from
reds this test (see the revert-check note in the commit).
"""

from pycats.config import (
    FD_EDGE_GROUND_UNITS,
    GLOBAL_Y_OFF,
    PX_PER_UNIT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STARTING_POINT_WIDTH,
    THICK_PLAT_Y_OFF,
)
from pycats.entities.ledge import LEFT, RIGHT, ledges_from_platforms
from pycats.entities.stages import DEFAULT_PLAYER_STAGE, STAGES, STARTING_POINT


def test_starting_point_is_the_default_player_stage():
    assert DEFAULT_PLAYER_STAGE is STARTING_POINT
    assert STARTING_POINT.name == "Starting Point"
    assert "Starting Point" in STAGES


def test_starting_point_is_a_single_flat_platform_no_side_platforms():
    plats = STARTING_POINT.build()
    # Final Destination is flat: exactly one platform, and it is solid (not thin/pass-through).
    assert len(plats) == 1
    assert plats[0].thin is False


def test_starting_point_width_matches_659_spec():
    # Concrete literal (able-to-fail if the layout drifts) cross-checked against the
    # #659 derivation: Melee FD ground half-width x 2 x pycats' fighter scale.
    assert STARTING_POINT_WIDTH == 924
    assert STARTING_POINT_WIDTH == round(2 * FD_EDGE_GROUND_UNITS * PX_PER_UNIT)


def test_starting_point_platform_is_centered_and_at_floor_height():
    rect = STARTING_POINT.build()[0].rect
    assert rect.width == 924
    assert rect.centerx == SCREEN_WIDTH // 2  # centered -> ledges at x=18 / x=942
    # Reuses the thick-platform surface-y convention so live-game spawns land at today's floor.
    assert rect.top == SCREEN_HEIGHT - THICK_PLAT_Y_OFF - GLOBAL_Y_OFF


def test_starting_point_ledges_are_grabbable_at_both_edges():
    plats = STARTING_POINT.build()
    ledges = ledges_from_platforms(plats)
    # One grabbable LEFT + one RIGHT ledge, anchored to the flat platform's top corners.
    assert len(ledges) == 2
    rect = plats[0].rect
    by_side = {le.side: le for le in ledges}
    assert by_side[LEFT].ax == rect.left
    assert by_side[RIGHT].ax == rect.right
    assert by_side[LEFT].ay == rect.top
    assert by_side[RIGHT].ay == rect.top
