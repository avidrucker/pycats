"""Per-move hurtbox override resolution (#835, R2 of the #792 editor).

`MoveData.hurtbox` (added inert in #831) is now READ at the two sites that
resolve a fighter's active hurtbox:
  - the sim hit-resolution — `systems/combat.py` `process_hits`;
  - the debug overlay      — `render_battle._active_hurtbox`.

When the DEFENDER is executing a move that carries a `hurtbox` override, that
override REPLACES the posture (stand / crouch / prone) hurtbox; with no active
move or no override, resolution is exactly as before.

No shipped move sets `hurtbox`, so every golden is byte-identical — these tests
drive a synthetic override to pin the new behavior. Able-to-fail: with the
resolvers ignoring `move.hurtbox`, the override never takes effect and the
posture-based assertions below flip.
"""

import pygame

from pycats.combat.data import Circle, Hurtbox, MoveData
from pycats.core.input import InputFrame
from pycats.entities import Player
from pycats.entities.platform import Platform
from pycats.systems import combat

_CONTROLS = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)


def _mk():
    return Player(100, 100, _CONTROLS, (255, 160, 64), eye_color=(0, 0, 0), char_name="P1", facing_right=True)


def _ground():
    return [Platform(pygame.Rect(0, 100, 600, 40), thin=False)]


def _settle(p, plats):
    grp = pygame.sprite.Group()
    for _ in range(3):
        p.update(InputFrame(held=set(), pressed=set(), released=set()), plats, grp)


def _override_move(hurtbox):
    """A minimal move (no hitboxes) carrying a per-move hurtbox override."""
    return MoveData(name="ovr", in_air=False, startup=1, active=1, recovery=1, hitboxes=(), hurtbox=hurtbox)


def _high_attack(owner, cx, cy, r=8):
    from types import SimpleNamespace

    return SimpleNamespace(
        active=True,
        owner=owner,
        hit_cx=cx,
        hit_cy=cy,
        hit_r=r,
        disappear_on_hit=False,
        damage=10.0,
        base_knockback=0.0,
        knockback_growth=0.0,
        angle=0,
    )


# --- sim: the override REPLACES the posture box -------------------------------


def test_move_override_replaces_posture_hurtbox_in_sim():
    """A body-centre hit that connects on the posture box WHIFFS when the
    defender's active move carries an override placed elsewhere (below the feet)."""
    plats = _ground()
    attacker = _mk()
    d = _mk()
    _settle(d, plats)
    body_cx, body_cy = d.rect.centerx, d.rect.top + 5  # inside the posture box

    # Override sits below the feet — it does NOT cover the body-centre point.
    override = Hurtbox(circles=(Circle(dx=d.rect.width // 2, dy=d.rect.height + 20, r=8),))
    d._clock.start(_override_move(override))
    assert d.current_move is not None and d.current_move.hurtbox is override

    combat.process_hits([d], [_high_attack(attacker, body_cx, body_cy)])
    assert d.fighter.percent == 0.0, "body hit must whiff — the override replaced the posture box"


def test_move_override_region_connects_in_sim():
    """A hit on the override region (which the posture box does NOT cover)
    connects while the defender executes the override move."""
    plats = _ground()
    attacker = _mk()
    d = _mk()
    _settle(d, plats)

    ox = d.rect.x + d.rect.width // 2
    oy = d.rect.y + d.rect.height + 20  # below the feet
    override = Hurtbox(circles=(Circle(dx=d.rect.width // 2, dy=d.rect.height + 20, r=10),))
    d._clock.start(_override_move(override))

    combat.process_hits([d], [_high_attack(attacker, ox, oy, r=8)])
    assert d.fighter.percent > 0.0, "a hit on the override region should connect"


def test_sim_no_override_uses_posture_box_unchanged():
    """Golden-safety sentinel: with no active move (current_move is None) the
    posture box is used exactly as today — a body hit connects."""
    plats = _ground()
    attacker = _mk()
    d = _mk()
    _settle(d, plats)
    assert d.current_move is None
    combat.process_hits([d], [_high_attack(attacker, d.rect.centerx, d.rect.top + 5)])
    assert d.fighter.percent == 10.0, "no-override path must resolve the posture box as before"


# --- overlay: _active_hurtbox mirrors the sim resolver ------------------------


def test_active_hurtbox_prefers_move_override():
    """The overlay resolver returns the active move's override when present,
    else the posture hurtbox — keeping the overlay in lockstep with the sim."""
    from pycats.render_battle import _active_hurtbox

    plats = _ground()
    p = _mk()
    _settle(p, plats)
    assert _active_hurtbox(p) is p.fighter_data.hurtbox  # no move -> posture

    override = Hurtbox(circles=(Circle(dx=20, dy=10, r=16),))
    p._clock.start(_override_move(override))
    assert _active_hurtbox(p) is override  # move -> override
