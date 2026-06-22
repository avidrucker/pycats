# tests/test_fighter_chart.py
import pygame
from pycats.entities.player import Player
from pycats.systems.state_engine import LegacyEngine
from pycats.systems.state_engine_sc import StatechartEngine
from pycats.statecharts.fighter_chart import build_fighter_chart
from statecharts import Session

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player(backend):
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True, state_backend=backend)


def test_initial_state_idle():
    p = _mk_player("statechart")
    assert isinstance(p.engine, StatechartEngine)
    assert p.state == "idle"


def test_idle_to_run_on_velocity():
    # idle -> run requires vel.x != 0 and on_ground
    p = _mk_player("statechart")
    p.vel.x = 5
    p.on_ground = True
    p.engine.tick(None)
    assert p.state == "run"


def test_single_hop_per_tick():
    # From idle with attack_timer set, first tick -> attack (not multi-hop onward)
    p = _mk_player("statechart")
    p.attack_timer = 5
    p.engine.tick(None)
    assert p.state == "attack"


def test_force_ko_and_recover():
    p = _mk_player("statechart")
    p.engine.force("ko")
    assert p.state == "ko"
    # ko -> idle requires is_alive on next tick
    p.is_alive = True
    p.engine.tick(None)
    assert p.state == "idle"


def test_matches_legacy_across_scenarios():
    # Drive identical attribute snapshots through both engines, compare labels.
    scenarios = [
        dict(vel=(5, 0), on_ground=True),                 # -> run
        dict(vel=(0, -5), on_ground=False),               # -> jump
        dict(vel=(0, 5), on_ground=False),                # -> fall
        dict(shield_attempting=True, on_ground=True),     # -> shield
        dict(hurt_timer=5),                               # -> hurt
        dict(attack_timer=5),                             # -> attack
    ]
    for sc in scenarios:
        legacy = _mk_player("legacy")
        sch = _mk_player("statechart")
        for p in (legacy, sch):
            vx, vy = sc.get("vel", (0, 0))
            p.vel.x, p.vel.y = vx, vy
            p.on_ground = sc.get("on_ground", False)
            p.shield_attempting = sc.get("shield_attempting", False)
            p.hurt_timer = sc.get("hurt_timer", 0)
            p.attack_timer = sc.get("attack_timer", 0)
            p.engine.tick(None)
        assert legacy.state == sch.state, (sc, legacy.state, sch.state)
