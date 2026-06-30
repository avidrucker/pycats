"""#274: reactive whiff-punish — attack the opponent's move-recovery window.

Phase-aware reaction (#251 decision model): a move in startup/active is a *threat*
(shield, #254); a move in *recovery* is a *whiff-punish opportunity* (attack now,
bypassing the cadence gate). High levels punish reliably; low/default unchanged.
"""
import random
import types

import pygame as pg

from pycats.sim.controllers import AttackerController, level_params

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _move(startup=4, active=3, recovery=20):
    return types.SimpleNamespace(startup=startup, active=active, recovery=recovery)


def _stub(cx, cy, alive=True, on_ground=True, current_move=None, move_frame=0):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground)
    s.controls = _CTRL
    s.current_move = current_move
    s.move_frame = move_frame
    return s


def _punisher(**kw):
    base = dict(attacker_num=1, whiff_punish=True, reaction_delay=0, follow_through_p=1.0,
                shield_chance=1.0, reactive_shield=True, rng=random.Random(0))
    base.update(kw)
    return AttackerController(**base)


# ---- level wiring ----

def test_level_params_whiff_punish_flag():
    assert level_params(1).whiff_punish is False
    assert level_params(3).whiff_punish is False
    assert level_params(5).whiff_punish is True
    assert level_params(9).whiff_punish is True


def test_controller_pulls_whiff_punish_from_level():
    assert AttackerController(level=9).whiff_punish is True
    assert AttackerController(level=1).whiff_punish is False
    assert AttackerController().whiff_punish is False  # default golden-safe


# ---- whiff-punish behaviour ----

def _opp_in_phase(move_frame, cx=130):
    # opponent at cx (within attack_range ~45 of a bot at 100), executing a move.
    return _stub(cx, 300, current_move=_move(startup=4, active=3, recovery=20),
                 move_frame=move_frame)


def test_whiff_punish_attacks_during_recovery_bypassing_cadence():
    c = _punisher()
    c._last_attack = c._f  # cadence NOT ready (just attacked) → only a punish can fire
    a = _stub(100, 300)
    t = _opp_in_phase(move_frame=10)  # startup4+active3=7 → frame 10 is RECOVERY
    pressed = any(_CTRL["attack"] in c(a, t, frame=k).held for k in range(3))
    assert pressed, "whiff-punish should attack during the opponent's recovery even off-cadence"


def test_no_whiff_punish_during_startup_or_active():
    c = _punisher()
    c._last_attack = c._f  # cadence not ready
    a = _stub(100, 300)
    # frame 2 = startup, frame 6 = active (both <= startup+active=7) → NOT a punish window
    for mf in (2, 6):
        cc = _punisher()
        cc._last_attack = cc._f
        t = _stub(130, 300, current_move=_move(4, 3, 20), move_frame=mf)
        # during startup/active the move is a THREAT → the bot shields, does not punish-attack
        out = cc(a, t, frame=0).held
        assert _CTRL["attack"] not in out, f"must not whiff-punish during startup/active (mf={mf})"


def test_whiff_punish_requires_range():
    c = _punisher()
    c._last_attack = c._f
    a = _stub(100, 300)
    t = _stub(600, 300, current_move=_move(4, 3, 20), move_frame=10)  # in recovery but FAR
    pressed = any(_CTRL["attack"] in c(a, t, frame=k).held for k in range(3))
    assert not pressed, "no whiff-punish when the opponent is out of attack range"


def test_default_controller_never_whiff_punishes():
    c = AttackerController(attacker_num=1)  # default: whiff_punish False
    a = _stub(100, 300)
    t = _opp_in_phase(move_frame=10)  # a juicy recovery opening
    c._last_attack = c._f
    pressed = any(_CTRL["attack"] in c(a, t, frame=k).held for k in range(5))
    assert not pressed, "default controller must not whiff-punish (golden-safe)"


def test_threat_excludes_recovery_phase():
    # #254 refinement: a move in recovery is NOT a threat (so the bot punishes, not shields);
    # startup/active still ARE threats.
    c = _punisher()
    a = _stub(100, 300)
    danger = _stub(130, 300, current_move=_move(4, 3, 20), move_frame=5)   # active → threat
    whiffed = _stub(130, 300, current_move=_move(4, 3, 20), move_frame=10)  # recovery → not
    assert c._threat_incoming(a, danger, None) is True
    assert c._threat_incoming(a, whiffed, None) is False


def _off_cadence_recovery_attack(whiff_punish_on, frames=200):
    """Real battle loop. Returns True if the bot (p2) ever presses attack on a frame
    where (the opponent p1 is in its move RECOVERY phase) AND (p2's own cadence is
    NOT ready). A cadence-only bot structurally cannot attack off-cadence, so this
    cleanly discriminates whiff-punish from normal cadence attacking (the #248 gotcha:
    a "real battle" test must FAIL when the feature is off)."""
    import pygame
    from pycats.sim import runner
    from pycats.core.input import merge_frames
    from pycats.sim.controllers import BaseController
    from pycats.systems import combat

    class Swinger(BaseController):
        """Swings a melee move periodically so it cycles through recovery windows."""
        def decide(self, a, t, frame, attacks=None):
            return {a.controls["attack"]} if (self._f % 30 == 5) else set()

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    p1.rect.center = (440, 380)
    p2.rect.center = (480, 380)  # within attack range
    c1 = Swinger(attacker_num=1)
    c2 = AttackerController(attacker_num=2, level=9, rng=random.Random(2))  # whiff_punish ON via level
    if not whiff_punish_on:
        c2.whiff_punish = False  # the discriminating control
    attacks = pygame.sprite.Group()
    for f in range(frames):
        cadence_ready = (c2._f - c2._last_attack) >= c2.attack_period  # before c2 decides
        f1 = c1(p1, p2, f, attacks)
        f2 = c2(p1, p2, f, attacks)
        p1_in_recovery = (p1.current_move is not None
                          and p1.move_frame > p1.current_move.startup + p1.current_move.active)
        if (p2.controls["attack"] in f2.held) and p1_in_recovery and not cadence_ready:
            return True
        fi = merge_frames([f1, f2])
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update(plats)
        combat.process_hits(players, attacks)
    return False


def test_reactive_bot_punishes_whiff_in_real_battle():
    # #248 gotcha guard, made DISCRIMINATING: the punisher attacks off-cadence during
    # the opponent's recovery in a real loop; a cadence-only bot never does.
    assert _off_cadence_recovery_attack(whiff_punish_on=True) is True, \
        "whiff-punish bot should attack off-cadence during the opponent's recovery (real battle)"
    assert _off_cadence_recovery_attack(whiff_punish_on=False) is False, \
        "a cadence-only bot must NOT attack off-cadence (proves the test discriminates the feature)"
