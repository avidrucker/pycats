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

KEY FINDING pinned below: tap-jump is always on (`up` == jump), and the jump branch
reads the FRESH-press set and returns before the attack branch. So a *simultaneous*
Up + A (both pressed the same frame) registers the up-press as a JUMP and never
reaches the up-tilt — the up-tilt only comes out when Up is ALREADY HELD (no longer a
fresh press) as A is pressed. Whether the simultaneous case *should* favour the tilt
is a design fork (tap-jump behaviour) left to a downstream ARCHITECT ticket, not
"fixed" here. These tests lock the current behaviour so any change is a red diff.
"""

import pygame as pg

from pycats.combat.data import load_fighter_data
from pycats.core.input import InputFrame
from pycats.entities.player import Player

P1 = dict(left=pg.K_a, right=pg.K_d, up=pg.K_w, down=pg.K_s, attack=pg.K_v, special=pg.K_c, shield=pg.K_x, smash=pg.K_b)

_NALIO = load_fighter_data("nalio")


def _frame(held=(), pressed=(), released=()):
    return InputFrame(held={P1[k] for k in held}, pressed={P1[k] for k in pressed}, released={P1[k] for k in released})


def _grounded_nalio():
    pg.init()
    p = Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0), char_name="nalio", facing_right=True)
    p.fighter.on_ground = True
    return p


def _current_key(p):
    """The move key currently on the clock, or None."""
    cm = p.current_move
    if cm is None:
        return None
    return next((k for k, v in _NALIO.moves.items() if v is cm), "<unknown>")


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


# ---- the gotcha: simultaneous Up + A jumps instead --------------------------


def test_up_and_a_same_frame_jumps_instead_of_up_tilt():
    """The reported gotcha: pressing Up and A on the SAME frame (both fresh) with a
    jump available fires a JUMP, not the up-tilt — the jump branch consumes the
    fresh up-press and returns before move-select. Able-to-fail: if the seam is
    ever changed so simultaneous up+A tilts on the ground, this flips."""
    p = _grounded_nalio()
    jumps_before = p.fighter.jumps_remaining
    p.handle_actions(_frame(held=("up", "attack"), pressed=("up", "attack")), pg.sprite.Group())
    assert _current_key(p) is None  # no attack started
    assert p.fighter.jumps_remaining == jumps_before - 1  # spent a jump
    assert p.fighter.vel.y < 0.0  # launched upward


def test_up_and_a_same_frame_tilts_when_no_jump_is_left():
    """Corner of the same gotcha: with 0 jumps remaining the jump branch's
    `jumps_remaining` guard fails, so a simultaneous up+A falls through to the
    attack branch and DOES fire the up-tilt. Documents that the block is jump vs
    tilt, decided by jump availability, not by the input itself."""
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
