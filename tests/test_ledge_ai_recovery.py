"""CPU ledge recovery (#291): skilled bots (level >= 5) press `up` to getup off a
ledge-hang instead of hanging to a KO; low levels and the default (level=None) are
unchanged (no getup → golden-safe). The engine getup itself is #14 (press up while
hanging → onto the stage); this only adds the AI that presses it.
"""
from pycats.sim import runner
from pycats.sim.controllers import AttackerController


def _hanging_attacker_vs_dead_target():
    # Real players; a is ledge-hanging, t is dead so normal decide() returns empty
    # (a clean contrast: any `up` for a hanging bot must come from the getup branch).
    a, t, _ = runner.build_players(p1_char="nalio", p2_char="nalio")
    a.fighter.grabbed_ledge = object()   # non-None => ledge-hanging
    t.fighter.is_alive = False
    return a, t


def test_high_level_bot_getups_from_ledge_hang():
    a, t = _hanging_attacker_vs_dead_target()
    held = AttackerController(attacker_num=1, level=9).decide(a, t, 0)
    assert a.controls["up"] in held      # presses up -> neutral getup (recovers)


def test_low_level_and_default_bots_do_not_getup():
    a, t = _hanging_attacker_vs_dead_target()
    for lvl in (None, 3):                # default (golden-safe) + a low level
        held = AttackerController(attacker_num=1, level=lvl).decide(a, t, 0)
        assert a.controls["up"] not in held   # hang/drop "dumbly"; baseline unchanged
