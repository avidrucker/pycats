# tests/test_fighter_chart.py
import pygame
from pycats.entities.player import Player
from pycats.systems.state_engine import LegacyEngine
from pycats.systems.state_engine_sc import StatechartEngine
from pycats.charts.fighter_chart import build_fighter_chart
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
    # From idle mid-attack (move clock live -> attack_timer > 0), first tick ->
    # attack (not multi-hop onward).
    p = _mk_player("statechart")
    p._clock.start(p.fighter_data.moves["attack"])
    assert p.attack_timer > 0
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


def test_in_state_nested_and_container_ids():
    # in_state is True for the active leaf AND its compound/parallel ancestors.
    p = _mk_player("statechart")
    sess = p.engine._session
    for sid in ("root", "action", "actionable", "grounded", "idle"):
        assert sess.in_state(sid), sid
    # Sibling containers that aren't on the active path are False.
    assert not sess.in_state("airborne")
    assert not sess.in_state("run")


def test_both_regions_active_simultaneously():
    # The parallel root enters both regions: an action leaf + a defensive leaf.
    p = _mk_player("statechart")
    cfg = p.engine._session.configuration
    # action region leaf present
    assert "idle" in cfg
    # defensive_status region leaf present
    assert "vulnerable" in cfg
    assert p.engine._session.in_state("action")
    assert p.engine._session.in_state("defensive_status")


def test_defensive_status_tracks_invulnerable():
    p = _mk_player("statechart")
    assert p.engine.defensive_status == "vulnerable"
    assert p.defensive_status == "vulnerable"
    # vulnerable -> intangible when p.invulnerable, on tick.
    p.invulnerable = True
    p.engine.tick(None)
    assert p.engine.defensive_status == "intangible"
    assert p.engine._session.in_state("intangible")
    # action region unaffected by the defensive tick (orthogonal).
    assert p.state == "idle"
    # intangible -> vulnerable when no longer invulnerable.
    p.invulnerable = False
    p.engine.tick(None)
    assert p.engine.defensive_status == "vulnerable"


def test_player_defensive_status_is_direct_from_flag():
    # Player.defensive_status is computed from the flag (backend-agnostic),
    # for both backends, without ticking.
    for backend in ("legacy", "statechart"):
        p = _mk_player(backend)
        assert p.defensive_status == "vulnerable"
        p.invulnerable = True
        assert p.defensive_status == "intangible"


def test_matches_legacy_across_scenarios():
    # Drive identical attribute snapshots through both engines, compare labels.
    scenarios = [
        dict(vel=(5, 0), on_ground=True),                 # -> run
        dict(vel=(0, -5), on_ground=False),               # -> jump
        dict(vel=(0, 5), on_ground=False),                # -> fall
        dict(shield_attempting=True, on_ground=True),     # -> shield
        dict(hurt_timer=5),                               # -> hurt
        dict(attack_timer=5),                             # -> attack
        dict(dodge_timer=5),                              # -> dodge
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
            # attack_timer is derived from the move clock (#71); a live move
            # gives attack_timer > 0, which is all the "-> attack" guard reads.
            if sc.get("attack_timer", 0):
                p._clock.start(p.fighter_data.moves["attack"])
            p.dodge_timer = sc.get("dodge_timer", 0)
            p.engine.tick(None)
        assert legacy.state == sch.state, (sc, legacy.state, sch.state)


def test_matches_legacy_run_to_idle_and_ko():
    # Multi-step paths exercising leaf-specific (non-hoisted) transitions and
    # the hoisted force_ko on the action parent.
    for backend in ("legacy", "statechart"):
        p = _mk_player(backend)
        p.vel.x, p.on_ground = 5, True
        p.engine.tick(None)
        assert p.state == "run"
        p.vel.x = 0
        p.engine.tick(None)
        assert p.state == "idle"
        # force_ko (hoisted to action parent) then recover.
        p.engine.force("ko")
        assert p.state == "ko"
        p.is_alive = True
        p.engine.tick(None)
        assert p.state == "idle"
