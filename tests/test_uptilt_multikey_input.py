"""Up + A multi-key input registration at the fighter_input seam (#845, research).

Surfaced from #841 (Gnok's tilts, u-tilt bound to grounded up-A). The move-select
seam is already unit-tested (up + A -> "utilt"); what these tests pin is the layer
BELOW it — `entities/fighter_input.py :: handle_actions`, which turns a held/pressed
key set into an action. That layer decides jump-vs-attack BEFORE it ever reaches
move-select, so "up + A resolves to utilt" does not by itself prove "up + A fires
the up-tilt in the live loop".

Character-independent seam: driven here through nalio (which owns a `utilt` on the
base branch) so the test does not depend on #841's Gnok tilts being merged. The
finding is the same for any fighter whose up-A maps to a utilt.

Findings doc: docs/research/2026-07-21-uptilt-multikey-input-findings.md.

#878 (implementing the #865 Option-D ruling) resolved the design fork this file first
characterised: a fresh **Up + A** now resolves the ATTACK, not the jump. The jump
branch carries a guard (`attack_wins_over_jump`) that yields the frame to the
Attack/Special seam when a fresh attack accompanies the up-press, so simultaneous
Up + A fires the up-tilt (grounded) / up-air (airborne). A **bare Up** (no A) still
jumps / double-jumps, and jumping out of shield with A held is preserved (the attack
seam does not fire in shield, so the jump is not yielded there). The tests below pin
that post-#878 behaviour; the pre-#878 "simultaneous up+A jumps" assertions were
inverted here in the same commit as the fix (red on `main`, green with the guard).
"""

import pygame as pg

from pycats.core.input import InputFrame
from pycats.entities.player import Player

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s, attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held}, pressed={P1[k] for k in pressed}, released={P1[k] for k in released})


def _grounded_nalio():
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    p.fighter.on_ground = True
    return p


def _current_key(p):
    """The move key currently on the clock, or None.

    Resolve against the Player's OWN `fighter_data` (the same object its clock
    pulled the move from), not a separate module-level `load_fighter_data("nalio")`.
    Since the #792 JSON flip, `load_fighter_data` hydrates a FRESH instance per
    call, so two loads compare `==` but not `is` — an identity check against a
    separate load resolves to "<unknown>" (#870). Identity holds within one Player."""
    cm = p.current_move
    if cm is None:
        return None
    return next((k for k, v in p.fighter_data.moves.items() if v is cm), "<unknown>")


# ---- the working path: Up already held, then A ------------------------------


def test_up_held_then_a_fires_the_up_tilt():
    """The path that DOES produce an up-tilt: Up is held from a prior frame (so it
    is not a fresh press this frame), and A is pressed. The jump branch reads the
    fresh set, sees no fresh up, and falls through to the attack branch, which
    reads `held` -> direction "up" -> utilt. Able-to-fail: if the seam stops
    routing held-up + A to the up-tilt, `move` is no longer "utilt"."""
    p = _grounded_nalio()
    jumps_before = p.fighter.jumps_remaining
    p.handle_actions(_frame(held=("up", "attack"), pressed=("attack",)), pg.sprite.Group())
    assert _current_key(p) == "utilt"
    assert p.fighter.jumps_remaining == jumps_before  # did not jump
    assert p.fighter.vel.y == 0.0


# ---- post-#878: simultaneous Up + A resolves the attack ---------------------


def test_up_and_a_same_frame_grounded_fires_up_tilt():
    """#878: pressing Up and A on the SAME frame (both fresh) grounded fires the
    up-tilt, NOT a jump — the `attack_wins_over_jump` guard yields the frame to the
    attack seam. Able-to-fail: reverting the guard makes this jump (move None,
    a jump spent), which is exactly the pre-#878 behaviour on `main`."""
    p = _grounded_nalio()
    jumps_before = p.fighter.jumps_remaining
    p.handle_actions(_frame(held=("up", "attack"), pressed=("up", "attack")), pg.sprite.Group())
    assert _current_key(p) == "utilt"  # attack won over the jump branch
    assert p.fighter.jumps_remaining == jumps_before  # did not jump
    assert p.fighter.vel.y == 0.0


def test_up_and_a_same_frame_airborne_fires_up_air():
    """#878, airborne half: with a double-jump banked, simultaneous Up + A in the
    air fires the up-air, NOT a double-jump. The jump branch is not `on_ground`-gated,
    so the same guard fixes both cases. Able-to-fail: reverting the guard spends the
    double-jump (jumps 2->1, move None), the pre-#878 airborne bug #864 found."""
    p = _grounded_nalio()
    p.fighter.on_ground = False
    jumps_before = p.fighter.jumps_remaining
    assert jumps_before > 0  # a jump is banked, so the pre-fix path WOULD double-jump
    p.handle_actions(_frame(held=("up", "attack"), pressed=("up", "attack")), pg.sprite.Group())
    assert _current_key(p) == "uair"  # attack won over the double-jump
    assert p.fighter.jumps_remaining == jumps_before  # did not spend a jump
    assert p.fighter.vel.y == 0.0  # no upward launch


# ---- bare Up (no A) still jumps / double-jumps ------------------------------


def test_bare_up_grounded_still_jumps():
    """#878 must not touch bare Up: a fresh Up with no attack still jumps on the
    ground. Able-to-fail: an over-broad guard that also swallowed bare Up would
    leave jumps unspent here."""
    p = _grounded_nalio()
    jumps_before = p.fighter.jumps_remaining
    p.handle_actions(_frame(held=("up",), pressed=("up",)), pg.sprite.Group())
    assert _current_key(p) is None  # no attack
    assert p.fighter.jumps_remaining == jumps_before - 1  # spent a jump
    assert p.fighter.vel.y < 0.0  # launched upward


def test_bare_up_airborne_still_double_jumps():
    """#878 must not touch bare Up in the air either: with a jump banked, a fresh Up
    (no attack) double-jumps. Able-to-fail: an over-broad guard would drop this."""
    p = _grounded_nalio()
    p.fighter.on_ground = False
    jumps_before = p.fighter.jumps_remaining
    p.handle_actions(_frame(held=("up",), pressed=("up",)), pg.sprite.Group())
    assert _current_key(p) is None  # no attack
    assert p.fighter.jumps_remaining == jumps_before - 1  # spent the double-jump
    assert p.fighter.vel.y < 0.0  # launched upward


def test_up_and_a_same_frame_tilts_when_no_jump_is_left():
    """Redundant-but-explicit: even with 0 jumps remaining, simultaneous up+A fires
    the up-tilt. Post-#878 the `attack_wins_over_jump` guard already yields the frame;
    the `jumps_remaining` guard failing is a second, independent reason it falls
    through to the attack seam."""
    p = _grounded_nalio()
    p.fighter.jumps_remaining = 0
    p.handle_actions(_frame(held=("up", "attack"), pressed=("up", "attack")), pg.sprite.Group())
    assert _current_key(p) == "utilt"


# ---- baselines: the seam is not just always-utilt / always-jump -------------


def test_neutral_a_still_fires_the_jab():
    """A alone (no direction) resolves to the jab — proves the harness actually
    drives move-select and the up cases above are about the up-press, not a
    broken fixture."""
    p = _grounded_nalio()
    p.handle_actions(_frame(held=("attack",), pressed=("attack",)), pg.sprite.Group())
    assert _current_key(p) == "jab"
