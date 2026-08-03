"""CPU ledge recovery (#291 + #902 C1): a hanging bot only escapes by pressing `up`
(the neutral getup, #14) — the engine imposes no timeout (#475). Skilled bots
(level >= 5) getup immediately; lower leveled bots (1-4) hang "dumbly" for a bounded
spell but ALWAYS escape once LEDGE_ESCAPE_MAX_FRAMES is reached, so no leveled CPU
hangs to a KO (#902). The default (level=None) is the golden baseline and never
auto-getups. The engine getup itself is #14 (press up while hanging → onto the stage);
this only adds the AI that presses it.
"""

from pycats.sim import runner
from pycats.sim.controllers import LEDGE_ESCAPE_MAX_FRAMES, AttackerController


def _hanging_attacker_vs_dead_target():
    # Real players; a is ledge-hanging, t is dead so normal decide() returns empty
    # (a clean contrast: any `up` for a hanging bot must come from the getup branch).
    a, t, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    a.fighter.grabbed_ledge = object()  # non-None => ledge-hanging
    t.fighter.is_alive = False
    return a, t


def test_high_level_bot_getups_from_ledge_hang():
    a, t = _hanging_attacker_vs_dead_target()
    held = AttackerController(attacker_num=1, level=9).decide(a, t, 0)
    assert a.controls["up"] in held  # presses up -> neutral getup (recovers)


def test_default_bot_never_getups():
    # level=None is the deterministic golden baseline: no auto-getup, EVER — even
    # held on the ledge far past the low-level escape cap. Keeps live-sim goldens
    # stable while the leveled (real in-game) CPUs are fixed.
    a, t = _hanging_attacker_vs_dead_target()
    c = AttackerController(attacker_num=1, level=None)
    for _ in range(LEDGE_ESCAPE_MAX_FRAMES + 5):
        held = c.decide(a, t, 0)
        assert a.controls["up"] not in held


def test_low_level_bot_hangs_early_then_getups():
    # #902 C1: a low-level bot (1-4) does NOT getup on the first hang frames (its
    # dumb-hang behaviour is preserved) but MUST escape once the bounded cap is
    # reached — it can never hang to a KO.
    a, t = _hanging_attacker_vs_dead_target()
    c = AttackerController(attacker_num=1, level=3)

    early = c.decide(a, t, 0)
    assert a.controls["up"] not in early  # frame 1: still hanging dumbly

    got_up = False
    for _ in range(LEDGE_ESCAPE_MAX_FRAMES + 5):
        held = c.decide(a, t, 0)
        if a.controls["up"] in held:
            got_up = True
            break
    assert got_up, "a level-3 bot must eventually press up to escape the ledge (#902)"
