"""B-full hit resolution — set_id makes a two-window ground move hit once (#888, ruling #893).

Under the per-window model (#204) a move with two temporal windows (an early "clean" box and
a later "late" box) spawns a SEPARATE `Attack` per window, so a stationary target was hit
TWICE (#879/#890). Brawl resolves this with hitbox SETS: boxes sharing a `set_id` share a
per-target hit-list within one move-instance, so the set hits a given target once (a different
set re-hits). This models the ratified B-full fix, narrowed by #893 to Birky's ground
clean/late moves — `utilt`, `fsmash`, `usmash`, `dsmash`.

Two layers:
  - the data (`load_fighter_data("birky")`, i.e. the shipped JSON): each of the 4 moves is
    two-window and every box carries one shared, non-None `set_id`;
  - the engine (`process_hits` + `MoveClock`): driving the move frame-by-frame against a
    stationary target lands exactly ONE hit.

Able-to-fail: `test_engine_dedup_is_what_changed` drives the SAME synthetic two-window move
with `set_id=None` and asserts TWO hits (today's independent-window default, #852) and with a
shared `set_id` asserts ONE. If the engine ignored `set_id`, the one-hit half reddens; if the
dedup over-reached, the two-hit half reddens. Removing `set_id` from the birky data reddens
`test_stationary_target_takes_one_hit`.
"""

from __future__ import annotations

import types

import pygame
import pytest

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData, load_fighter_data
from pycats.combat.move_clock import MoveClock
from pycats.entities.attack import Attack
from pycats.systems.hit_resolution import process_hits

GROUND_MOVES = ["utilt", "fsmash", "usmash", "dsmash"]


# --------------------------------------------------------------------- data layer


@pytest.mark.parametrize("key", GROUND_MOVES)
def test_birky_ground_move_is_two_window_one_set(key):
    """Each in-scope ground move keeps its two temporal windows AND tags every box with a
    single, shared, non-None set_id — the authoring B-full needs to collapse it to one hit."""
    move = load_fighter_data("birky").moves[key]
    windows = {(hb.active_start, hb.active_end) for hb in move.hitboxes}
    assert len(windows) == 2, f"birky.{key} must stay two-window (got {sorted(windows)})"
    set_ids = {hb.set_id for hb in move.hitboxes}
    assert set_ids == {1}, f"birky.{key} every box must share set_id=1 (got {sorted(set_ids)})"


# ------------------------------------------------------------------- engine driver


def _attacker(registry):
    """Owner stub: never self-hit; carries the shared per-move-instance hit_registry that
    process_hits consults for set-dedup."""
    a = types.SimpleNamespace(
        rect=pygame.Rect(0, 0, 40, 60),
        facing_right=True,
        intangible=False,
        invincible_timer=0,
        is_alive=True,
        hit_registry=registry,
    )
    a.fighter = a
    a.record_hit_landed = lambda: None
    return a


def _defender_at(cx, cy, r=44):
    """Stationary target: one hurtbox circle at absolute (cx, cy) (rect top-left 0,0), counting
    the hits it receives. r is generous so both windows' boxes overlap it."""
    p = types.SimpleNamespace(
        rect=pygame.Rect(0, 0, 40, 60),
        facing_right=True,
        intangible=False,
        invincible_timer=0,
        is_alive=True,
        fighter_data=FighterData(
            walk=1.1, dash=1.5, run=1.5, hurtbox=Hurtbox(circles=(Circle(dx=int(cx), dy=int(cy), r=r),)), moves={}
        ),
        hits_received=0,
    )
    p.fighter = p
    p.receive_hit = lambda atk, is_crouching=False: setattr(p, "hits_received", p.hits_received + 1)
    p.record_hit_landed = lambda: None
    return p


def _drive_hits(move):
    """Run `move` through a MoveClock frame-by-frame: spawn one Attack per temporal window
    (as Player.update does), run process_hits each frame against a stationary target parked on
    the first spawn's primary box, and cull expired/deactivated Attacks. Returns the hit count."""
    pygame.init()
    clk = MoveClock()
    clk.start(move)
    attacker = _attacker(clk.hit_registry)  # registry is the clock's — reset per move-instance
    attacks: list[Attack] = []
    defender = None
    frames = move.startup + move.active + move.recovery + 2
    for _ in range(frames):
        tick = clk.tick()
        if tick.spawn is not None:
            atk = Attack(attacker, hitboxes=tick.spawn, in_air=move.in_air, lifetime=tick.lifetime)
            if defender is None:
                px, py, _r, _hb = atk.resolved[0]
                defender = _defender_at(px, py)
            attacks.append(atk)
        players = [attacker, defender] if defender is not None else [attacker]
        process_hits(players, attacks)
        for a in attacks:
            a.frames_left -= 1
        attacks = [a for a in attacks if a.active and a.frames_left > 0]
    return defender.hits_received if defender is not None else 0


@pytest.mark.parametrize("key", GROUND_MOVES)
def test_stationary_target_takes_one_hit(key):
    """The acceptance criterion: driven end-to-end, each ground move hits a stationary target
    exactly once — the two windows no longer double-hit."""
    move = load_fighter_data("birky").moves[key]
    assert _drive_hits(move) == 1


def _synthetic_two_window(set_id):
    """A minimal contiguous two-window move: early f4-5, late f6-10, boxes co-located so a
    single stationary target overlaps both windows."""
    box = dict(circle=Circle(0, 0, 12), damage=10.0, angle=0)
    return MoveData(
        name="synthetic",
        in_air=False,
        startup=3,
        active=7,
        recovery=4,  # total 14, windows within [4,10]
        hitboxes=(
            Hitbox(**box, base_knockback=40.0, active_start=4, active_end=5, set_id=set_id),
            Hitbox(**box, base_knockback=20.0, active_start=6, active_end=10, set_id=set_id),
        ),
    )


def test_engine_dedup_is_what_changed():
    """Same synthetic two-window move: with no set (today's independent-window default, #852)
    the target is hit TWICE; with a shared set_id it is hit ONCE. This isolates the set-dedup
    as the sole behavioral change and makes the one-hit guarantee able-to-fail."""
    assert _drive_hits(_synthetic_two_window(set_id=None)) == 2
    assert _drive_hits(_synthetic_two_window(set_id=1)) == 1
