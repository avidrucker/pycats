"""Birky owns Kirby-low crouch/prone geometry (#589, ratified in #565).

Birky's 44-tall stand made the inherited default crouch (40,40) drop only 4px —
"not really crouching". The owner ratified Kirby-low crouch (40,24) / prone (40,14),
which also needs Birky-own posture hurtboxes: combat tests the hurtbox *circles*
(systems/combat.py), and the inherited default circles reach below the shorter boxes.
"""
from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA as BIRKY
from pycats.combat.data import load_fighter_data

# The minimal one-move test fixture, loaded by name (#591).
_TESTCAT = load_fighter_data("testcat")


def test_birky_crouch_and_prone_sizes_are_kirby_low():
    assert BIRKY.crouch_size == (40, 24)
    assert BIRKY.prone_size == (40, 14)


def test_birky_crouch_drop_is_a_meaningful_fraction_of_stand():
    # Able-to-fail: the inherited (40,40) drops only 4px of a 44 stand (9%) and fails
    # this; Kirby-low (24) drops 20px (45%).
    stand_h = BIRKY.stand_size[1]
    crouch_h = BIRKY.crouch_size[1]
    assert stand_h - crouch_h >= 0.35 * stand_h


def _circles_fit(hurtbox, box_w, box_h):
    """Every circle lies fully within a box_w × box_h posture box."""
    for c in hurtbox.circles:
        if not (c.dy - c.r >= 0 and c.dy + c.r <= box_h):
            return False
        if not (c.dx - c.r >= 0 and c.dx + c.r <= box_w):
            return False
    return True


def test_birky_posture_hurtboxes_fit_inside_the_new_boxes():
    # Able-to-fail: the inherited default crouch circle (dy=32,r=12) reaches y=44,
    # far below a 24-tall box; the default prone reaches y=23 below a 14-tall box.
    assert _circles_fit(BIRKY.crouch_hurtbox, *BIRKY.crouch_size)
    assert _circles_fit(BIRKY.prone_hurtbox, *BIRKY.prone_size)


def test_birky_no_longer_shares_the_default_posture_hurtboxes():
    # Re-authored, not inherited — combat reads these per defender, so they must be
    # Birky's own values, not the default objects sized for the 40/22 boxes.
    assert BIRKY.crouch_hurtbox is not _TESTCAT.crouch_hurtbox
    assert BIRKY.prone_hurtbox is not _TESTCAT.prone_hurtbox
