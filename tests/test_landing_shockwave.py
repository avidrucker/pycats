"""Landing-triggered projectile spawn (#974, B-cluster of #566 Final Cutter).

Engine capability split out of #969 and ratified under #1066 (phase model C): a
recovery/special move can declare a `LandingSpawn`, and the engine spawns that
projectile on the TOUCHDOWN EVENT — the frame the fighter goes airborne->ground
(`Player._step_physics` detects it, `Player._spawn_landing_shockwave` emits it) —
not on a move-clock frame. This is the mechanism behind Final Cutter's ground
shockwave beam. The event trigger (not a fixed frame count) is canon-required:
the descent-to-floor distance varies (off a ledge, taller stage), so a frame
count would desync the beam (#1066 Q2). By touchdown the move has usually ended
(routed to `helpless`), so the spawn keys off a descriptor stashed at move start,
not off the move clock.

These tests drive a GENERIC test fighter carrying a synthetic recovery `up_b`
with a landing shockwave — NO per-cat data is wired here (#974 out-of-scope:
Birky's real beam speed/lifetime/lag land on a follow-up DATA ticket once the
capability exists). The custom FighterData is injected via the Player
`fighter_data=` seam, so the shared default cat is never mutated.
"""

import dataclasses
import json

import pygame as pg

from pycats.combat.data import (
    Circle,
    Hitbox,
    LandingSpawn,
    MoveData,
    _move_from_json,
    _move_to_json,
    load_fighter_data,
)
from pycats.config import P1_COLOR, WHITE
from pycats.core.input import InputFrame
from pycats.entities.attack import Projectile
from pycats.entities.platform import Platform
from pycats.entities.player import Player

_TESTCAT = load_fighter_data("testcat")

CONTROLS = {
    "left": pg.K_a,
    "right": pg.K_d,
    "up": pg.K_w,
    "down": pg.K_s,
    "shield": pg.K_q,
    "attack": pg.K_e,
    "special": pg.K_c,
}
UP, SPECIAL = pg.K_w, pg.K_c

RISE_VY = -8.0  # a modest start burst so the short move ends well before touchdown
BEAM_SPEED = 8.0  # px/frame outward — distinct from any physics value
BEAM_LIFETIME = 20
BEAM_LANDING_LAG = 35  # datamined Final Cutter lag (SpecialAirHi4); a FOUND value
_BEAM_HITBOX = Hitbox(circle=Circle(0, 0, 12), damage=5, angle=30, base_knockback=20, knockback_growth=50)


def _beam(both_directions=False):
    return LandingSpawn(
        hitboxes=(_BEAM_HITBOX,),
        speed=BEAM_SPEED,
        lifetime=BEAM_LIFETIME,
        landing_lag=BEAM_LANDING_LAG,
        both_directions=both_directions,
    )


def _shockwave_fd(both_directions=False):
    up_b = MoveData(
        name="TestFinalCutter",
        in_air=True,
        startup=2,
        active=2,
        recovery=2,  # total = 6; the move ends airborne (routes to helpless) before landing
        hitboxes=(),
        grants_recovery=True,
        recovery_vy=RISE_VY,
        landing_spawn=_beam(both_directions),
    )
    return dataclasses.replace(_TESTCAT, moves={**_TESTCAT.moves, "up_b": up_b})


def _frame(held, pressed):
    return InputFrame(held=set(held), pressed=set(pressed), released=set())


def _airborne(facing_right=True, both_directions=False):
    """Spawn a fighter above a reachable floor, drop a few frames so it's airborne."""
    plats = pg.sprite.Group()
    plats.add(Platform(pg.Rect(0, 500, 960, 40), thin=False))  # floor ~400px below spawn
    p = Player(
        x=300,
        y=100,
        controls=CONTROLS,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name="ShockCat",
        facing_right=facing_right,
        fighter_data=_shockwave_fd(both_directions),
    )
    ag = pg.sprite.Group()
    for _ in range(3):
        p.update(_frame(set(), set()), plats, ag)
    assert not p.fighter.on_ground, "fixture precondition: airborne"
    return p, plats, ag


def _up_b(p, plats, ag):
    p.update(_frame({UP, SPECIAL}, {UP, SPECIAL}), plats, ag)


def _run_until_land(p, plats, ag, max_frames=600):
    for _ in range(max_frames):
        p.update(_frame(set(), set()), plats, ag)
        if p.fighter.on_ground:
            return True
    return False


def _beams(ag):
    return [s for s in ag if isinstance(s, Projectile)]


# ---------------------------------------------------------------------------
# Engine: the touchdown-triggered spawn (able-to-fail)
# ---------------------------------------------------------------------------


def test_shockwave_spawns_on_touchdown():
    """The beam spawns the frame the fighter lands — the substance of #974. The
    move's hitboxes are empty (no mid-move spawn), so the ONLY projectile that can
    enter the group is the landing beam. Reverting the touchdown hook leaves the
    group empty and this fails."""
    p, plats, ag = _airborne()
    _up_b(p, plats, ag)
    assert _beams(ag) == [], "no projectile while airborne"
    assert _run_until_land(p, plats, ag), "fixture: fighter must reach the floor"
    beams = _beams(ag)
    assert len(beams) == 1, f"one landing shockwave expected, got {len(beams)}"
    assert beams[0].velocity == (BEAM_SPEED, 0.0), beams[0].velocity
    assert beams[0].frames_left == BEAM_LIFETIME


def test_shockwave_not_spawned_before_touchdown():
    """The spawn is armed at move start but must NOT fire until the fighter is
    grounded: while airborne the descriptor stays pending and nothing is emitted."""
    p, plats, ag = _airborne()
    _up_b(p, plats, ag)
    for _ in range(4):  # a few airborne frames — still rising/falling, not landed
        p.update(_frame(set(), set()), plats, ag)
        assert not p.fighter.on_ground, "fixture: still airborne"
    assert p._pending_landing_spawn is not None, "beam stays armed until touchdown"
    assert _beams(ag) == [], "no beam before the fighter lands"


def test_shockwave_travels_outward_by_facing():
    """The beam travels outward along the fighter's facing direction (Final
    Cutter's beam goes forward)."""
    pr, plats, ag = _airborne(facing_right=True)
    _up_b(pr, plats, ag)
    assert _run_until_land(pr, plats, ag)
    assert _beams(ag)[0].velocity[0] > 0, "right-facing beam travels +x"

    pl, plats2, ag2 = _airborne(facing_right=False)
    _up_b(pl, plats2, ag2)
    assert _run_until_land(pl, plats2, ag2)
    assert _beams(ag2)[0].velocity[0] < 0, "left-facing beam travels -x"


def test_shockwave_routes_through_landing_lag():
    """On touchdown the descriptor's `landing_lag` is applied, so the fighter
    routes helpless -> landing_lag (the #202 grounded action-lock) rather than
    straight to idle. Without the landing-lag set, the state would not be
    landing_lag."""
    p, plats, ag = _airborne()
    _up_b(p, plats, ag)
    assert _run_until_land(p, plats, ag)
    assert p.fighter.landing_lag_timer > 0, "landing lag armed on touchdown"
    assert p.state == "landing_lag", f"expected landing_lag, got {p.state}"


def test_shockwave_pending_cleared_after_spawn():
    """The stash is consumed on the landing frame so the beam fires exactly once —
    a later, unrelated landing must not re-emit it."""
    p, plats, ag = _airborne()
    _up_b(p, plats, ag)
    assert _run_until_land(p, plats, ag)
    assert p._pending_landing_spawn is None
    assert p._landing_spawn_now is None


def test_shockwave_both_directions_spawns_mirrored_pair():
    """`both_directions` emits a symmetric pair — two projectiles with opposite
    horizontal velocity."""
    p, plats, ag = _airborne(both_directions=True)
    _up_b(p, plats, ag)
    assert _run_until_land(p, plats, ag)
    beams = _beams(ag)
    assert len(beams) == 2, f"symmetric shockwave = 2 beams, got {len(beams)}"
    signs = sorted(1 if b.velocity[0] > 0 else -1 for b in beams)
    assert signs == [-1, 1], "one beam each direction"


# ---------------------------------------------------------------------------
# Data: serialization round-trip (omit-when-absent; inline when present)
# ---------------------------------------------------------------------------


def test_landing_spawn_omitted_when_absent():
    """A move with no landing spawn (the default) must not emit the key —
    golden-safe 'omit == default'."""
    plain = MoveData(name="plain", in_air=False, startup=2, active=2, recovery=4, hitboxes=())
    assert "landing_spawn" not in _move_to_json(plain)


def test_landing_spawn_roundtrip_through_json():
    """A move carrying a landing spawn survives serialize -> JSON text -> hydrate
    byte-equal, including the nested hitbox circle."""
    move = _shockwave_fd().moves["up_b"]
    rebuilt = _move_from_json(json.loads(json.dumps(_move_to_json(move))))
    assert rebuilt == move
    assert rebuilt.landing_spawn == _beam()
