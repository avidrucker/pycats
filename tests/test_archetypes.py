# tests/test_archetypes.py
"""Controller scaffolding (#53, child B of #47).

`BaseController` owns the per-frame bookkeeping (a/t resolve, edge detection,
`emitted` capture, InputFrame build); archetypes implement `decide()`. The chase
policy becomes `AttackerController`; `ChaseController` stays as a back-compat
alias. This is a pure refactor — the existing chase-bot golden + full_match suite
are the byte-identical proof; the tests here pin structure + the attack policy.
"""
from pycats.sim.controllers import BaseController, AttackerController, ChaseController
from pycats.sim.runner import run_battle


def test_attacker_subclasses_base_and_chase_is_alias():
    assert issubclass(AttackerController, BaseController)
    assert ChaseController is AttackerController, (
        "ChaseController must remain a back-compat alias of AttackerController"
    )


def test_base_controller_requires_decide():
    """BaseController is abstract scaffolding — using it directly must error,
    forcing archetypes to supply a decide() policy."""
    import pytest
    base = BaseController(attacker_num=1)
    with pytest.raises(NotImplementedError):
        base.decide(None, None, 0)


def test_attacker_drives_the_ko_arc():
    """The extracted attacker still fights: hurt+ko states and a P2 stock loss.
    Fails if decide() dropped the close/standoff/attack policy."""
    ctrl = AttackerController(attacker_num=1)
    snaps = run_battle("legacy", frames=6000, controller=ctrl, stop_on_match_over=True)
    states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in states and "ko" in states, sorted(states)
    p2_lives = [next(p for p in s[0] if p[0] == "P2")[9] for s in snaps]
    assert min(p2_lives) < p2_lives[0], "attacker scored no KO — policy broken"


def test_attacker_and_chase_alias_emit_identically():
    """AttackerController and the ChaseController alias produce the same stream."""
    a = AttackerController(attacker_num=1)
    b = ChaseController(attacker_num=1)
    run_battle("legacy", frames=400, controller=a)
    run_battle("legacy", frames=400, controller=b)
    assert [(f.held, f.pressed, f.released) for f in a.emitted] == \
           [(f.held, f.pressed, f.released) for f in b.emitted]
