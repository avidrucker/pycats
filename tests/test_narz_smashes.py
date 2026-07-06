"""Narz's tipper smashes — fsmash/usmash/dsmash (#327 slice 5 / #294).

Narz (Marth) smashes are his signature KO tools: 2-box disjoint TIPPERS (tip box
FIRST so priority = tuple order makes the far tip win), chargeable via the mechanic
in #371/#377. Values are PM3.6-Marth-shaped (⚠ playtest, like the rest of the kit).

Golden-safe: the sim path loads the default cat (no smash, not chargeable); Narz is
never the golden cat. A test pins that.
"""
from pycats.combat.data import load_fighter_data
from pycats.combat.move_select import resolve_move_key

_NARZ = load_fighter_data("narz")
# The minimal one-move test fixture, loaded by name (#591).
_TESTCAT = load_fighter_data("testcat")


def _forward_hurtbox_extent():
    # farthest forward reach of the (default) hurtbox: max(dx + r)
    return max(c.dx + c.r for c in _NARZ.hurtbox.circles)


def test_smashes_exist_chargeable_and_grounded():
    for k in ("fsmash", "usmash", "dsmash"):
        m = _NARZ.moves[k]
        assert m.in_air is False
        assert m.chargeable is True


def test_fsmash_is_a_disjoint_tipper():
    m = _NARZ.moves["fsmash"]
    tip, base = m.hitboxes[0], m.hitboxes[1]
    # tipper: the FIRST box (priority) is the far, strong tip
    assert tip.damage > base.damage
    assert tip.circle.dx > base.circle.dx           # tip reaches farther forward
    assert tip.base_knockback > base.base_knockback  # ...and hits harder
    # disjoint: the tip's near edge is beyond the hurtbox's forward extent
    assert tip.circle.dx - tip.circle.r > _forward_hurtbox_extent()
    assert (m.startup, m.active, m.recovery) == (10, 3, 31)


def test_usmash_tip_is_higher_and_stronger():
    m = _NARZ.moves["usmash"]
    tip, base = m.hitboxes[0], m.hitboxes[1]
    assert tip.damage > base.damage
    assert tip.circle.dy < base.circle.dy    # tip is higher (smaller dy = up)
    assert all(h.angle == 90 for h in m.hitboxes)  # launches up


def test_dsmash_front_then_back_each_a_tipper():
    m = _NARZ.moves["dsmash"]
    front = [h for h in m.hitboxes if h.active_start == 6]
    back = [h for h in m.hitboxes if h.active_start == 13]
    assert len(front) == 2 and len(back) == 2
    # front hits ahead (+dx), back hits behind (-dx)
    assert all(h.circle.dx > 0 for h in front)
    assert all(h.circle.dx < 0 for h in back)
    # each window is a tipper: box-0 (tip) stronger than box-1 (base)
    assert front[0].damage > front[1].damage
    assert back[0].damage > back[1].damage


def test_smashes_reachable_through_the_331_seam():
    keys = set(_NARZ.moves)
    assert resolve_move_key(keys, "forward", True, False, is_smash=True) == "fsmash"
    assert resolve_move_key(keys, "up", True, False, is_smash=True) == "usmash"
    assert resolve_move_key(keys, "down", True, False, is_smash=True) == "dsmash"


def test_default_cat_has_no_chargeable_smash_golden_safety():
    for k in ("fsmash", "usmash", "dsmash"):
        assert k not in _TESTCAT.moves
    assert not any(mv.chargeable for mv in _TESTCAT.moves.values())
