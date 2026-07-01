"""Battle event-log core — the executable contract (#302, child of #300).

Derives a chronological 'git-diff for the fight' by diffing consecutive snapshot()s.
Unit tests build SYNTHETIC snapshot tuples (no sim / no pygame) so the contract is
pinned fast and deterministically; one integration test drives a real seeded run.

snapshot() shapes (runner.snapshot): part = (0 name, 1 state, 2 x, 3 y, 4 vx, 5 vy,
6 on_ground, 7 percent, 8 shield_hp, 9 lives, 10 is_alive, 11 jumps_remaining, 12
dodge_timer, 13 hurt_timer, 14 stun_timer, 15 attack_timer, 16 invuln_timer, 17 facing,
18 invuln, 19 defensive_status, 20 move_frame); attack = (x, y, frames_left, owner,
active, hit_cx, hit_cy, hit_r); snap = (parts, attacks, phase, winner).
"""
from pycats.sim.battle_log import (
    events_from_snaps, render, BattleEvent, JUMP, ATTACK, HIT, KO, STATE, MATCH_END,
)


def _part(name, state="idle", percent=0.0, lives=3, jumps=2, on_ground=True):
    # 21-field part tuple; only the contract-relevant fields vary.
    return (name, state, 0, 0, 0.0, 0.0, on_ground, float(percent), 0.0, lives,
            lives > 0, jumps, 0, 0, 0, 0, 0, True, False, "none", 0)


def _atk(owner, active=True):
    return (0, 0, 5, owner, active, 0.0, 0.0, 0.0)


def _snap(parts, atk=(), phase="play", winner=None):
    return (tuple(parts), tuple(atk), phase, winner)


def _types(events):
    return [(e.actor, e.type) for e in events]


def test_jump_event_on_jumps_remaining_drop():
    snaps = [_snap([_part("P1", jumps=2)]),
             _snap([_part("P1", jumps=1)])]
    ev = events_from_snaps(snaps)
    assert ev == [BattleEvent(1, "P1", JUMP, {"remaining": 1})]


def test_hit_event_carries_damage_delta_and_attacker():
    # P2's percent rises while P1 owns an active attack -> HIT on P2, by P1.
    snaps = [_snap([_part("P1"), _part("P2", percent=0)]),
             _snap([_part("P1"), _part("P2", percent=14)], atk=[_atk("P1")])]
    ev = events_from_snaps(snaps)
    assert len(ev) == 2  # ATTACK P1 + HIT P2
    hit = [e for e in ev if e.type == HIT]
    assert hit == [BattleEvent(1, "P2", HIT,
                               {"damage": 14.0, "from": 0.0, "to": 14.0, "by": "P1"})]


def test_ko_event_on_stock_loss():
    snaps = [_snap([_part("P2", percent=142, lives=2)]),
             _snap([_part("P2", percent=0, lives=1)])]
    ev = events_from_snaps(snaps)
    assert ev == [BattleEvent(1, "P2", KO,
                              {"stock_from": 2, "stock_to": 1, "percent": 142.0})]


def test_attack_event_on_new_active_attack():
    snaps = [_snap([_part("P1")]),
             _snap([_part("P1")], atk=[_atk("P1")])]
    ev = events_from_snaps(snaps)
    assert ev == [BattleEvent(1, "P1", ATTACK, {})]


def test_state_event_only_on_notable_transition():
    # idle -> hurt is notable; idle -> run is not.
    notable = events_from_snaps([_snap([_part("P1", state="idle")]),
                                 _snap([_part("P1", state="hurt")])])
    assert notable == [BattleEvent(1, "P1", STATE, {"from": "idle", "to": "hurt"})]
    plain = events_from_snaps([_snap([_part("P1", state="idle")]),
                              _snap([_part("P1", state="run")])])
    assert plain == []


def test_match_end_event_on_winner_set():
    snaps = [_snap([_part("P1")], winner=None),
             _snap([_part("P1")], winner="P1")]
    ev = events_from_snaps(snaps)
    assert ev == [BattleEvent(1, "MATCH", MATCH_END, {"winner": "P1"})]


def test_no_events_when_frames_identical():
    s = _snap([_part("P1"), _part("P2")])
    assert events_from_snaps([s, s, s]) == []


def test_intra_frame_event_ordering():
    # One frame: P1 starts an attack, P2 jumps AND takes a hit.
    # Contract order: ATTACK, then per-fighter (index order) JUMP/HIT/KO/STATE.
    snaps = [_snap([_part("P1"), _part("P2", percent=0, jumps=2)]),
             _snap([_part("P1"), _part("P2", percent=14, jumps=1)], atk=[_atk("P1")])]
    ev = events_from_snaps(snaps)
    assert _types(ev) == [("P1", ATTACK), ("P2", JUMP), ("P2", HIT)]


def test_render_formats_readable_lines():
    events = [
        BattleEvent(43, "P2", JUMP, {"remaining": 5}),
        BattleEvent(811, "P2", HIT, {"damage": 14.0, "from": 128.0, "to": 142.0, "by": "P1"}),
        BattleEvent(840, "P2", KO, {"stock_from": 2, "stock_to": 1, "percent": 142.0}),
        BattleEvent(187, "P1", STATE, {"from": "idle", "to": "helpless"}),
        BattleEvent(1799, "MATCH", MATCH_END, {"winner": "P1"}),
    ]
    out = render(events).splitlines()
    assert out[0] == "    43  P2     JUMP      (5 left)"
    assert out[1] == "   811  P2     HIT       +14% (128->142) by P1"
    assert out[2] == "   840  P2     KO        stock 2->1 @142%"
    assert out[3] == "   187  P1     STATE     -> helpless"
    assert out[4] == "  1799  MATCH  MATCH_END winner=P1"


def test_events_from_real_seeded_run():
    # Integration: a real seeded run must derive plausible events — JUMP/ATTACK/HIT
    # and, since #292 is fixed, a KO once a fighter is finished. Before the fix this
    # exact matchup produced ZERO KO events (the loser juggled past 1400% with all
    # stocks); the leveled bot now lands percent-scaling f-tilts, so a KO converts.
    # Regression coverage for the win-condition itself lives in
    # tests/test_bot_match_resolves.py; here we only assert the log DERIVES the KO.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import random
    from pycats.sim.runner import run_battle
    from pycats.sim.controllers import AttackerController
    rng = random.Random(3)
    cs = (AttackerController(attacker_num=1, level=5, rng=rng),
          AttackerController(attacker_num=2, level=5, rng=rng))
    # 2000f window: #309 zone-anchored Birky's hitboxes, re-placing its move
    # geometry and perturbing this deterministic seed-3 trajectory (the first KO
    # now converts around frame ~1428). The window is sized past that so the log
    # has a KO event to derive.
    snaps = run_battle(frames=2000, controllers=cs, p1_char="nalio", p2_char="birky",
                       stop_on_match_over=True)
    ev = events_from_snaps(snaps)
    kinds = {e.type for e in ev}
    assert JUMP in kinds and ATTACK in kinds, kinds
    hits_on_p2 = [e for e in ev if e.type == HIT and e.actor == "P2"]
    kos = [e for e in ev if e.type == KO]
    assert hits_on_p2, "birky should take hits in this matchup"
    assert kos, "#292 fixed: a KO must now convert and be derivable from the log"
