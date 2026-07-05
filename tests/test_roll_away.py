"""#338: reactive roll-away — an evasive alternative to the #254 reactive shield.

Re-scoped per #343 (Smash CPUs reposition with rolls, not walk-retreat). On a
detected threat, a level-gated bot may ROLL AWAY instead of shielding — emitted as
a `shield` + away-direction combo (a ground roll, resolved by fighter_input to
`_start_dodge`). Evade is rolled BEFORE the shield and is mutually exclusive with it.
`evade_chance` defaults 0.0 → level-less/low levels never roll (golden-safe).
"""
import random
import types

import pygame as pg

from pycats.sim.controllers import AttackerController, level_params

pg.init()

_CTRL = {"left": 1, "right": 2, "up": 3, "down": 4, "attack": 5, "special": 6, "shield": 7}


def _move(startup=4, active=3, recovery=20):
    return types.SimpleNamespace(startup=startup, active=active, recovery=recovery)


def _stub(cx, cy, alive=True, on_ground=True, current_move=None, move_frame=0,
          state="idle", hurt_timer=0, stun_timer=0):
    s = types.SimpleNamespace()
    s.rect = pg.Rect(0, 0, 40, 60)
    s.rect.center = (cx, cy)
    s.fighter = types.SimpleNamespace(is_alive=alive, on_ground=on_ground,
                                      hurt_timer=hurt_timer, stun_timer=stun_timer)
    s.controls = _CTRL
    s.current_move = current_move
    s.move_frame = move_frame
    s.state = state  # #338: evade only rolls from a dodge-able state
    return s


def _evader(evade_chance=1.0, **kw):
    base = dict(attacker_num=1, evade_chance=evade_chance, reactive_shield=True,
                shield_chance=0.0, reaction_delay=0, whiff_punish=False,
                reactive_spacing=False, follow_through_p=1.0, rng=random.Random(0))
    base.update(kw)
    return AttackerController(**base)


def _threat(cx=480, cy=300):
    # opponent winding up (move_frame 5 <= startup4+active3=7 → a THREAT) within the band.
    return _stub(cx, cy, current_move=_move(4, 3, 20), move_frame=5)


# ---- level wiring ----

def test_level_params_evade_chance_graded():
    # evade is a higher-skill option: off at/below Lv5, graded up at 7/9.
    assert level_params(1).evade_chance == 0.0
    assert level_params(3).evade_chance == 0.0
    assert level_params(5).evade_chance == 0.0          # keeps Lv5 tests byte-identical
    assert level_params(9).evade_chance > level_params(7).evade_chance > 0.0


def test_controller_pulls_evade_chance_from_level():
    assert AttackerController(level=9).evade_chance > 0.0
    assert AttackerController(level=5).evade_chance == 0.0
    assert AttackerController().evade_chance == 0.0  # default golden-safe


# ---- roll-away behaviour ----
# a at cx=400, opponent to the right (dx>0) → away = left.

def test_rolls_away_on_a_detected_threat():
    a = _stub(400, 300)
    held = _evader(evade_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"], _CTRL["left"]}, (
        f"an evade should emit a roll = shield + away(left) combo, got {held}"
    )


def test_no_roll_when_evade_chance_zero():
    a = _stub(400, 300)
    # evade off but shield on → the bot shields, never rolls.
    held = _evader(evade_chance=0.0, shield_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"]}, f"evade off → bare shield, no away-move, got {held}"


def test_evade_wins_over_shield_precedence():
    # both evade and shield certain → evade fires first and is mutually exclusive.
    a = _stub(400, 300)
    held = _evader(evade_chance=1.0, shield_chance=1.0)(a, _threat(), frame=0).held
    assert _CTRL["left"] in held and _CTRL["shield"] in held, "evade should win (roll combo)"
    assert held == {_CTRL["shield"], _CTRL["left"]}, f"evade beats shield, got a roll only: {held}"


def test_no_roll_from_a_non_dodgeable_state():
    # mid-walk/attack the bot cannot start a roll (fighter_input gates it), so the
    # controller must not emit a wasted roll — it falls through to shield instead.
    a = _stub(400, 300, state="walk")
    held = _evader(evade_chance=1.0, shield_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"]}, f"no roll from a non-dodge-able state; shield instead, got {held}"


def test_no_roll_without_a_threat():
    a = _stub(400, 300)
    # opponent idle (no current_move) → not a threat → no evade, no roll.
    idle = _stub(480, 300)
    held = _evader(evade_chance=1.0)(a, idle, frame=0).held
    assert _CTRL["left"] not in held, f"no roll when there is no threat, got {held}"


def test_default_controller_never_rolls():
    a = _stub(400, 300)
    # default: reactive_shield False, evade_chance 0 → never rolls even on a threat.
    # (a roll requires `shield`; the default may still move toward as normal approach —
    # that is not a roll, so assert on the absence of the shield combo.)
    held = AttackerController(attacker_num=1)(a, _threat(), frame=0).held
    assert _CTRL["shield"] not in held, \
        f"default controller must never roll (no shield combo, golden-safe), got {held}"


def test_roll_direction_is_away_from_opponent():
    # opponent to the LEFT (dx<0) → away = right.
    a = _stub(400, 300)
    left_opponent = _stub(320, 300, current_move=_move(4, 3, 20), move_frame=5)
    held = _evader(evade_chance=1.0)(a, left_opponent, frame=0).held
    assert held == {_CTRL["shield"], _CTRL["right"]}, f"roll away from a left opponent = right, got {held}"


# ---- discriminating real battle ----

def _roll_emissions(evade_on, frames=400):
    """Real loop: a Swinger opponent threatens the bot; count frames where the bot
    EMITS a roll (a `shield`+direction combo) from a dodge-able state. The evade-enabled
    bot rolls; a shield-only control never emits a directional shield combo.

    We assert on the controller's OUTPUT (its contract), not the resulting dodge STATE:
    whether a roll converts to an in-game dodge additionally depends on fighter_input
    (a fighter in `hurt`/`walk`/`attack` cannot dodge, and air/edge constraints apply),
    so live conversion is rare — matching #343's finding that evasion is a minor CPU
    behaviour. Returns (total rolls, rolls emitted while in hitstun). #379/#370: the
    FSM `state` label lags hurt_timer, so a dodge-able label alone does NOT prove a
    valid roll — the timer gate is what makes emissions non-wasted."""
    import pygame

    from pycats.core.input import merge_frames
    from pycats.sim import runner
    from pycats.sim.controllers import BaseController
    from pycats.systems import combat

    class Swinger(BaseController):
        def decide(self, a, t, frame, attacks=None, ledges=None):  # ledges: protocol (#404)
            return {a.controls["attack"]} if (self._f % 12 < 8) else set()

    plats = runner.build_stage()
    p1, p2, players = runner.build_players(p1_char="nalio", p2_char="nalio")
    p1.rect.center = (440, 380)
    p2.rect.center = (500, 380)  # inside the threat band
    c1 = Swinger(attacker_num=1)
    c2 = AttackerController(attacker_num=2, level=9, rng=random.Random(2), whiff_punish=False)
    if not evade_on:
        c2.evade_chance = 0.0  # discriminating control (shield stays on)
    attacks = pygame.sprite.Group()
    rolls = 0
    wasted = 0   # rolls emitted while the bot is in hitstun (dropped by Player.update)
    for f in range(frames):
        f1 = c1(p1, p2, f, attacks)
        f2 = c2(p1, p2, f, attacks)
        held = f2.held
        if p2.controls["shield"] in held and (
                p2.controls["left"] in held or p2.controls["right"] in held):
            rolls += 1
            if p2.fighter.hurt_timer > 0 or p2.fighter.stun_timer > 0:
                wasted += 1
        fi = merge_frames([f1, f2])
        for p in players:
            p.update(fi, plats, attacks)
        attacks.update(plats)
        combat.process_hits(players, attacks)
    return rolls, wasted


def test_no_wasted_rolls_during_hitstun_in_a_real_juggle():
    # #379/#370: in a jab-lock juggle the label lags hurt_timer, so the pre-fix bot
    # emitted 12-16 rolls WHILE in hitstun — all dropped by Player.update. The timer
    # gate drives that to 0. (Every roll this scenario produced was such a wasted emit,
    # so total rolls also fall to 0 here — legit evasion is rare, #343.)
    _rolls, wasted = _roll_emissions(evade_on=True)
    assert wasted == 0, f"evade bot emitted {wasted} rolls while in hitstun (#379 wants 0)"
    # the shield-only control never emits a directional roll at all (discrimination)
    ctrl_rolls, _ = _roll_emissions(evade_on=False)
    assert ctrl_rolls == 0, f"a shield-only control must never emit a roll (got {ctrl_rolls})"


# ---- #379: gate the evade on the real actionability timers, not the lagging label ----

def test_no_roll_during_hitstun():
    # A bot in hitstun (hurt_timer > 0) can't dodge, but its FSM `state` label lags the
    # timer by a frame (#8/#370), so a dodge-able label is not enough. The controller must
    # not emit a wasted roll — it falls through to shield like the non-dodge-able case.
    a = _stub(400, 300, hurt_timer=5)          # dodge-able label 'idle', but in hitstun
    held = _evader(evade_chance=1.0, shield_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"]}, f"no roll while in hitstun (#379); shield instead, got {held}"


def test_no_roll_during_stun():
    a = _stub(400, 300, stun_timer=8)          # shield-break dizzy
    held = _evader(evade_chance=1.0, shield_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"]}, f"no roll while stunned (#379), got {held}"


def test_rolls_once_the_timers_clear():
    # Same dodge-able state under the same threat, but actionable (timers 0) -> rolls.
    a = _stub(400, 300, hurt_timer=0, stun_timer=0)
    held = _evader(evade_chance=1.0)(a, _threat(), frame=0).held
    assert held == {_CTRL["shield"], _CTRL["left"]}, f"must roll when actionable + threatened, got {held}"
