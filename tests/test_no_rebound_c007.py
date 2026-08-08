"""tests/test_no_rebound_c007.py — fresh able-to-fail guard for PYC-C-007-GRAPE (#1001).

PYC-C-007-GRAPE — a clank only ENDS the losing/tied hitbox:
    When pycats resolves a clank (`systems/hit_resolution.py:_resolve_clanks`),
    the only effect on the losing/tied hitbox is that it ends — `_negate` either
    `kill()`s the Attack or sets `active = False`. The clank path sets NOTHING on
    either fighter: no rebound/recoil, no clank freeze / hitlag, no bounce-back.
    The implemented behavior is cancellation, not bouncing — so #807's "attacks
    bouncing off each other" describes behavior pycats does not implement. (The
    only real "bounce" in pycats is a projectile off a platform, `Projectile.update`
    #266 — a different mechanic, the likely source of the conflation.)

This is a NEGATIVE / UNIVERSAL claim: its evidence is that the clank path adds no
rebound, so the guards below are written to FAIL THE MOMENT A REBOUND PATH IS
ADDED — the negative can't rot unnoticed. NOTE: the C-007 ledger cited the
pre-rename `systems/combat.py`; the module is `systems/hit_resolution.py` as of
commit 481edcf.

Two complementary guards, each able-to-fail via a NAMED source mutation:

  M1 — add a rebound to the clank path, e.g. in `_negate`:
       `atk.owner.fighter.hitlag_timer = 8` (a clank-freeze), or `.vx = -5`
       (a recoil). Reds T1 (runtime) — the fighter write is recorded / a field
       moves.
  M2 — add a rebound *identifier* to `_resolve_clanks`/`_negate` (any of
       rebound/recoil/freeze/hitlag/bounce as code). Reds T2 (source scan) even
       if that code would not fire in the two-attack scenario T1 exercises.

Geometry mirrors the clank tests: attacker A rect (0,0) facing right + box dx=120
and attacker B rect (200,100) facing left + box dx=120 both resolve to abs
(120,130), so the pair overlaps and clanks (equal damage → mutual clank).
"""

from __future__ import annotations

import ast
import inspect

import pygame

from pycats.combat.data import Circle, Hitbox
from pycats.entities.attack import Attack
from pycats.systems import hit_resolution
from pycats.systems.hit_resolution import _negate, _resolve_clanks

# The rebound/recoil/clank-freeze/bounce vocabulary the claim says the clank path
# must never touch. Substring match (so `hitlag_timer`, `rebound_state`, etc. are
# all caught).
_REBOUND_TOKENS = ("rebound", "recoil", "freeze", "hitlag", "bounce")


class _SpyFighter:
    """A minimal owner/fighter that records every attribute WRITE made after
    construction. `_resolve_clanks` reads the owner but must never write to it —
    a recorded write means a rebound/recoil/freeze was applied to the fighter."""

    def __init__(self, rect, *, facing_right):
        self.rect = rect
        self.facing_right = facing_right
        self.intangible = False
        self.is_alive = True
        # realistic per-fighter state a rebound/recoil/freeze would plausibly move:
        self.vx = 0.0
        self.vy = 0.0
        self.state = "attack"
        self.hitlag_timer = 0
        self.fighter = self  # Attack + hit_resolution read owner.fighter.*
        self.writes = []  # set LAST so the assignments above are not recorded

    def __setattr__(self, name, value):
        if name != "writes" and "writes" in self.__dict__:
            self.__dict__["writes"].append((name, value))
        object.__setattr__(self, name, value)


def _atk(owner, damage):
    """A single-box ground attack resolving to abs (120,130) for both owners."""
    hb = Hitbox(
        circle=Circle(dx=120, dy=130 if owner.facing_right else 30, r=20),
        damage=damage,
        angle=0,
        base_knockback=30.0,
        knockback_growth=80.0,
    )
    return Attack(owner, hitbox=hb, lifetime=4, in_air=False)


def _identifiers(fn):
    """Every Name/Attribute identifier used in fn's body (lower-cased). Parsed via
    ast, so a docstring mention (e.g. `_negate`'s "no rebound state/freeze yet")
    is NOT included — only actual code identifiers are."""
    tree = ast.parse(inspect.getsource(fn))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
    return names


def test_c007_clank_path_writes_nothing_to_either_fighter():
    """Runtime guard: resolving a mutual clank ends both hitboxes and touches
    NEITHER fighter — no write recorded, and vx/vy/state/hitlag_timer unmoved.
    Able-to-fail: M1."""
    pygame.init()
    a_owner = _SpyFighter(pygame.Rect(0, 0, 40, 60), facing_right=True)
    b_owner = _SpyFighter(pygame.Rect(200, 100, 40, 60), facing_right=False)
    a = _atk(a_owner, 10.0)
    b = _atk(b_owner, 10.0)
    a_owner.writes.clear()  # ignore any incidental construction-time writes
    b_owner.writes.clear()

    _resolve_clanks([a, b])

    # the one allowed effect: both hitboxes end (mutual clank)
    assert a.active is False and b.active is False, "the pair should mutually clank"
    # the claim: the clank path sets NOTHING on either fighter
    assert a_owner.writes == [], f"clank wrote to attacker A's fighter: {a_owner.writes}"
    assert b_owner.writes == [], f"clank wrote to attacker B's fighter: {b_owner.writes}"
    for who, f in (("A", a_owner), ("B", b_owner)):
        assert f.vx == 0.0 and f.vy == 0.0, f"clank pushed fighter {who} (recoil/bounce-back)"
        assert f.state == "attack", f"clank changed fighter {who}'s state (rebound state)"
        assert f.hitlag_timer == 0, f"clank froze fighter {who} (clank hitlag/freeze)"


def test_c007_clank_functions_reference_no_rebound_identifier():
    """Source guard (the query pin, made durable): neither `_resolve_clanks` nor
    `_negate` uses any rebound/recoil/freeze/hitlag/bounce identifier in its code.
    Catches an added rebound path even when it would not fire at runtime.
    Able-to-fail: M2."""
    for fn in (_resolve_clanks, _negate):
        names = _identifiers(fn)
        offenders = {n for n in names for tok in _REBOUND_TOKENS if tok in n}
        assert not offenders, f"{fn.__name__} references a rebound-family identifier: {sorted(offenders)}"


def test_c007_negate_only_ends_the_hitbox():
    """The whole of `_negate`'s effect is to end the hitbox: its code identifiers
    are a subset of {kill, active, disappear_on_hit, atk} — no fighter/owner write.
    Able-to-fail if `_negate` grows any side effect beyond ending the box."""
    names = _identifiers(_negate)
    allowed = {"kill", "active", "disappear_on_hit", "atk"}
    extra = names - allowed
    assert not extra, f"_negate does more than end the hitbox; unexpected identifiers: {sorted(extra)}"


def test_c007_no_bounce_in_clank_module_outside_the_negate_docstring():
    """Whole-module scan: the only rebound/bounce vocabulary in
    `systems/hit_resolution.py` is the single `_negate` docstring line. A new
    occurrence (a rebound code path or comment) reds this. Durable form of the
    ledger `grep -c 'rebound'` query pin."""
    src = inspect.getsource(hit_resolution)
    lines_with_rebound = [ln for ln in src.splitlines() if "rebound" in ln.lower()]
    assert len(lines_with_rebound) == 1, f"expected only the _negate docstring, got: {lines_with_rebound}"
    assert "no rebound state/freeze yet" in lines_with_rebound[0], "the one rebound mention is not the known docstring"
