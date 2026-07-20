# tests/test_fighter_chart.py
import pygame

from pycats.entities.player import Player
from pycats.systems.state_engine_sc import StatechartEngine

P1 = dict(left=pygame.K_a, right=pygame.K_d, up=pygame.K_w, down=pygame.K_s,
          attack=pygame.K_v, special=pygame.K_c, shield=pygame.K_x)


def _mk_player():
    return Player(100, 100, P1, (255, 160, 64), eye_color=(0, 0, 0),
                  char_name="P1", facing_right=True)


def test_initial_state_idle():
    p = _mk_player()
    assert isinstance(p.engine, StatechartEngine)
    assert p.state == "idle"


def test_idle_to_run_on_velocity():
    # idle -> run requires vel.x != 0 and on_ground
    p = _mk_player()
    p.fighter.vel.x = 5
    p.fighter.on_ground = True
    p.engine.tick(None)
    assert p.state == "walk"


def test_single_hop_per_tick():
    # From idle mid-attack (move clock live -> attack_timer > 0), first tick ->
    # attack (not multi-hop onward).
    p = _mk_player()
    p._clock.start(p.fighter_data.moves["attack"])
    assert p.attack_timer > 0
    p.engine.tick(None)
    assert p.state == "attack"


def test_force_ko_and_recover():
    p = _mk_player()
    p.engine.force("ko")
    assert p.state == "ko"
    # ko -> idle requires is_alive on next tick
    p.fighter.is_alive = True
    p.engine.tick(None)
    assert p.state == "idle"


def test_in_state_nested_and_container_ids():
    # in_state is True for the active leaf AND its compound/parallel ancestors.
    p = _mk_player()
    sess = p.engine._session
    for sid in ("root", "action", "actionable", "grounded", "idle"):
        assert sess.in_state(sid), sid
    # Sibling containers that aren't on the active path are False.
    assert not sess.in_state("airborne")
    assert not sess.in_state("walk")


def test_both_regions_active_simultaneously():
    # The parallel root enters both regions: an action leaf + a defensive leaf.
    p = _mk_player()
    cfg = p.engine._session.configuration
    # action region leaf present
    assert "idle" in cfg
    # defensive_status region leaf present
    assert "vulnerable" in cfg
    assert p.engine._session.in_state("action")
    assert p.engine._session.in_state("defensive_status")


def test_defensive_status_tracks_intangible():
    p = _mk_player()
    assert p.engine.defensive_status == "vulnerable"
    assert p.defensive_status == "vulnerable"
    # vulnerable -> intangible when p.intangible, on tick.
    p.fighter.intangible = True
    p.engine.tick(None)
    assert p.engine.defensive_status == "intangible"
    assert p.engine._session.in_state("intangible")
    # action region unaffected by the defensive tick (orthogonal).
    assert p.state == "idle"
    # intangible -> vulnerable when no longer intangible.
    p.fighter.intangible = False
    p.engine.tick(None)
    assert p.engine.defensive_status == "vulnerable"


def test_player_defensive_status_is_direct_from_flag():
    # Player.defensive_status is computed from the flag (engine-agnostic),
    # without ticking.
    p = _mk_player()
    assert p.defensive_status == "vulnerable"
    p.fighter.intangible = True
    assert p.defensive_status == "intangible"


def test_reaches_expected_state_across_scenarios():
    # One tick from idle with the given attributes lands on the expected label.
    # (ADR-0002, #178: the cross-engine legacy oracle is gone; statechart ==
    # frozen golden is now anchored in test_golden.py.)
    scenarios = [
        (dict(vel=(5, 0), on_ground=True), "walk"),
        (dict(vel=(0, -5), on_ground=False), "jump"),
        (dict(vel=(0, 5), on_ground=False), "fall"),
        (dict(shield_attempting=True, on_ground=True), "shield"),
        (dict(hurt_timer=5), "hurt"),
        (dict(attack_timer=5), "attack"),
        (dict(dodge_timer=5), "dodge"),
    ]
    for sc, expected in scenarios:
        p = _mk_player()
        vx, vy = sc.get("vel", (0, 0))
        p.fighter.vel.x, p.fighter.vel.y = vx, vy
        p.fighter.on_ground = sc.get("on_ground", False)
        p.fighter.shield_attempting = sc.get("shield_attempting", False)
        p.fighter.hurt_timer = sc.get("hurt_timer", 0)
        # attack_timer is derived from the move clock (#71); a live move gives
        # attack_timer > 0, which is all the "-> attack" guard reads.
        if sc.get("attack_timer", 0):
            p._clock.start(p.fighter_data.moves["attack"])
        p.fighter.dodge_timer = sc.get("dodge_timer", 0)
        p.engine.tick(None)
        assert p.state == expected, (sc, p.state, expected)


def test_run_to_idle_and_ko():
    # Multi-step paths exercising leaf-specific (non-hoisted) transitions and
    # the hoisted force_ko on the action parent.
    p = _mk_player()
    p.fighter.vel.x, p.fighter.on_ground = 5, True
    p.engine.tick(None)
    assert p.state == "walk"
    p.fighter.vel.x = 0
    p.engine.tick(None)
    assert p.state == "idle"
    # force_ko (hoisted to action parent) then recover.
    p.engine.force("ko")
    assert p.state == "ko"
    p.fighter.is_alive = True
    p.engine.tick(None)
    assert p.state == "idle"
