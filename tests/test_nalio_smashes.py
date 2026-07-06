"""Nalio's uncharged smashes — fsmash/usmash/dsmash (#327 slice 2).

Authored from PM3.6 Mario rukaidata (AttackS4S / AttackHi4 / AttackLw4), same
convention as the tilts/aerials: raw damage/angle/BKB/KBG/frames, radii = u(size).
These are the UNCHARGED release swings, reachable through the #331 smash-input
seam; the charge scaling is slice 3.

Golden-safety is structural: the sim path loads the default cat, which has no
smash move, so these never touch a golden. A test pins that.
"""
from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key
from pycats.combat.units import u

_NALIO = load_fighter_data("nalio")
# The minimal one-move test fixture, loaded by name (#591).
_TESTCAT = load_fighter_data("testcat")


def test_fsmash_frames_and_hitboxes():
    m = _NALIO.moves["fsmash"]
    assert m.in_air is False
    assert (m.startup, m.active, m.recovery) == (7, 5, 26)   # AttackS4S 8-12, IASA 38
    dmgs = [h.damage for h in m.hitboxes]
    assert dmgs == [14.0, 19.0, 10.0]                        # id0 fist / id1 sweetspot / id2 inner
    assert all(h.angle == 361 for h in m.hitboxes)           # Sakurai sentinel (#203)
    sweet = m.hitboxes[1]
    assert (sweet.base_knockback, sweet.knockback_growth) == (30.0, 97.0)
    assert sweet.circle.r == u(3.94)                         # radius = round(size × PX_PER_UNIT)


def test_usmash_two_windows():
    m = _NALIO.moves["usmash"]
    assert m.in_air is False
    assert (m.startup, m.active, m.recovery) == (2, 4, 33)   # AttackHi4 3-6; FAF 39 (⚠ playtest)
    # Up-hit window [3,4] (angle 83) then late window [5,6] (angle 259).
    up = [h for h in m.hitboxes if h.angle == 83]
    late = [h for h in m.hitboxes if h.angle == 259]
    assert len(up) == 2 and len(late) == 2
    assert all((h.active_start, h.active_end) == (3, 4) for h in up)
    assert all((h.active_start, h.active_end) == (5, 6) for h in late)
    assert up[0].damage == 15.0 and late[0].damage == 16.0


def test_dsmash_front_then_back():
    m = _NALIO.moves["dsmash"]
    assert m.in_air is False
    assert (m.startup, m.active, m.recovery) == (2, 11, 23)  # AttackLw4 3-4 + 12-13; total 36
    front = [h for h in m.hitboxes if h.active_start == 3]
    back = [h for h in m.hitboxes if h.active_start == 12]
    assert len(front) == 2 and len(back) == 2
    # Front hits ahead (+dx), back hits behind (-dx); back is weaker.
    assert all(h.circle.dx > 0 for h in front)
    assert all(h.circle.dx < 0 for h in back)
    assert [h.damage for h in front] == [16.0, 16.0]
    assert [h.damage for h in back] == [12.0, 10.0]
    assert all(h.angle == 361 for h in m.hitboxes)


def test_smashes_reachable_through_the_331_seam():
    """A smash input resolves to Nalio's real smash move (not the tilt fallback)."""
    keys = set(_NALIO.moves)
    assert resolve_move_key(keys, "forward", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "up", True, False, is_smash=True) == "usmash"
    assert resolve_move_key(keys, "down", True, False, is_smash=True) == "dsmash"


def test_default_cat_has_no_smash_golden_safety():
    """The sim/golden path loads the default cat — it must stay smash-free so no
    golden is touched by Nalio's new smash data."""
    for k in ("fsmash", "usmash", "dsmash"):
        assert k not in _TESTCAT.moves
