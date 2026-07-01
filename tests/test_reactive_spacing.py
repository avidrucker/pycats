"""#277: reactive spacing — press the advantage on a vulnerable opponent.

Model A (re-spec per #343: Smash CPUs approach committally and don't do footsies).
When `reactive_spacing` is on and the opponent is in move RECOVERY (vulnerable, no
incoming threat) and the bot is within melee range, the bot must NOT back off — it
holds/presses instead of drifting back to `standoff`. It never targets a gap wider
than its range (no retreat-to-space). Level-less default is unchanged (golden-safe).
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


def _spacer(reactive_spacing, **kw):
    # isolate spacing: no shield, no whiff-punish, always-commit, react instantly.
    base = dict(attacker_num=1, reactive_spacing=reactive_spacing, reactive_shield=False,
                whiff_punish=False, standoff=35, reaction_delay=0, follow_through_p=1.0,
                shield_chance=0.0, rng=random.Random(0))
    base.update(kw)
    return AttackerController(**base)


# ---- level wiring ----

def test_level_params_reactive_spacing_flag():
    assert level_params(1).reactive_spacing is False
    assert level_params(3).reactive_spacing is False
    assert level_params(5).reactive_spacing is True
    assert level_params(7).reactive_spacing is True
    assert level_params(9).reactive_spacing is True


def test_controller_pulls_reactive_spacing_from_level():
    assert AttackerController(level=9).reactive_spacing is True
    assert AttackerController(level=1).reactive_spacing is False
    assert AttackerController().reactive_spacing is False  # default golden-safe


# ---- press-in behaviour ----
# a at cx=400 (inside safe_x so the away-move isn't clamped), opponent 20 px to the
# right → toward=right, away=left. adx=20 < standoff-8 (27) and within melee range.

def _close_recovering_opponent(cx=420, move_frame=10):
    # move_frame 10 > startup4+active3=7 → RECOVERY (vulnerable, not a threat)
    return _stub(cx, 300, current_move=_move(4, 3, 20), move_frame=move_frame)


def test_reactive_spacing_suppresses_backoff_on_recovering_opponent():
    a = _stub(400, 300)
    t = _close_recovering_opponent()  # adx=20, opponent recovering, in range
    away = _CTRL["left"]
    for reactive, expect_backoff in ((True, False), (False, True)):
        held = _spacer(reactive)(a, t, frame=0).held
        assert (away in held) is expect_backoff, (
            f"reactive_spacing={reactive}: away-move present should be {expect_backoff} "
            f"(held={held})"
        )


def test_reactive_spacing_still_backs_off_from_a_winding_up_threat():
    # opponent in ACTIVE (a threat, not recovery) → press-in must NOT trigger; the bot
    # backs off as usual. Proves the suppression is gated on vulnerability, not blanket.
    a = _stub(400, 300)
    t = _stub(420, 300, current_move=_move(4, 3, 20), move_frame=5)  # active → threat
    away = _CTRL["left"]
    held = _spacer(True)(a, t, frame=0).held
    assert away in held, "a reactive_spacing bot must still back off from a winding-up threat"


def test_reactive_spacing_never_widens_the_gap():
    # no footsies: even when pressing in, the bot never targets a gap wider than its
    # range — it only suppresses the back-off; it never emits an away-move to *space*.
    a = _stub(400, 300)
    t = _close_recovering_opponent()
    held = _spacer(True)(a, t, frame=0).held
    # away here is 'left' (opponent is to the right). Pressing in may hold or move
    # toward (right); it must never emit the away-move to open the gap.
    assert _CTRL["left"] not in held, "pressing in must never emit an away-move (no spacing)"


def test_default_controller_backs_off_regardless_of_opponent_state():
    # golden-safe: the level-less default always backs off when too close, even from a
    # recovering opponent (it is opponent-state-blind).
    a = _stub(400, 300)
    t = _close_recovering_opponent()
    held = AttackerController(attacker_num=1, standoff=35)(a, t, frame=0).held
    assert _CTRL["left"] in held, "default controller backs off (unchanged behaviour)"


# ---- discriminating real battle ----

def test_reactive_spacing_changes_a_real_battle_trajectory():
    # end-to-end: flipping reactive_spacing on the leveled bots changes a real
    # deterministic battle — proof the knob reaches sim behaviour, not just a getter.
    # reactive_spacing never consumes self.rng (it reads position + opponent move-phase
    # only), so the two runs share the same rng draws until a press-in decision genuinely
    # suppresses a back-off — any divergence here IS the feature biting. The natural
    # press-in window (opponent recovering while the bot is too close) is rare, matching
    # #343's finding that reactive spacing is a minor tweak for a Smash-faithful CPU, so
    # this uses a seed/length (seed 1 / 3000f) where it does occur.
    from pycats.sim.runner import run_battle

    def run(reactive_spacing):
        rng = random.Random(1)
        c1 = AttackerController(attacker_num=1, level=5, rng=rng)
        c2 = AttackerController(attacker_num=2, level=5, rng=rng)
        c1.reactive_spacing = c2.reactive_spacing = reactive_spacing
        return run_battle(frames=3000, controllers=(c1, c2),
                          p1_char="nalio", p2_char="birky", stop_on_match_over=True)

    assert run(True) != run(False), "reactive_spacing must change the sim trajectory"
