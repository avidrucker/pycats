# tests/test_archetypes.py
"""Controller scaffolding (#53, child B of #47).

`BaseController` owns the per-frame bookkeeping (a/t resolve, edge detection,
`emitted` capture, InputFrame build); archetypes implement `decide()`. The chase
policy becomes `AttackerController`; `ChaseController` stays as a back-compat
alias. This is a pure refactor — the existing chase-bot golden + full_match suite
are the byte-identical proof; the tests here pin structure + the attack policy.
"""
from pycats.sim.controllers import (
    BaseController, AttackerController, ChaseController, IdlerController,
    FollowerController,
)
from pycats.sim.runner import run_battle, P1_KEYS, P2_KEYS


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


# --- Child C (#55): IdlerController, the deterministic baseline opponent ---

def test_idler_subclasses_base():
    assert issubclass(IdlerController, BaseController)


def test_idler_default_is_a_true_noop_baseline():
    """A default idler emits nothing, so attacker-vs-idler is byte-identical to
    attacker-vs-idle (today's `controller=` path)."""
    idler = IdlerController(attacker_num=2)
    run_battle("legacy", frames=300, controllers=(AttackerController(1), idler))
    assert all(not (f.held or f.pressed or f.released) for f in idler.emitted), (
        "default IdlerController must emit no input"
    )

    dual = run_battle("legacy", frames=300,
                      controllers=(AttackerController(1), IdlerController(2)))
    single = run_battle("legacy", frames=300, controller=AttackerController(1))
    assert dual == single, "default idler is not a transparent baseline"


def test_idler_periodic_shield_is_deterministic_and_disjoint():
    """With shield_period/shield_hold set, the idler holds ONLY its own shield key
    on frames where `_f % period < hold`, and nothing otherwise."""
    period, hold = 10, 3
    idler = IdlerController(attacker_num=2, shield_period=period, shield_hold=hold)
    run_battle("legacy", frames=50, controllers=(None, idler))

    shield = P2_KEYS["shield"]
    for i, f in enumerate(idler.emitted):
        expected = {shield} if (i % period) < hold else set()
        assert f.held == expected, f"frame {i}: held={f.held} expected={expected}"
    # never leaks a P1 keycode
    emitted = set().union(*(f.held for f in idler.emitted)) if idler.emitted else set()
    assert emitted.isdisjoint(set(P1_KEYS.values()))


# --- Child D (#57): FollowerController, the shadow/spacing archetype ---

def test_follower_subclasses_base():
    assert issubclass(FollowerController, BaseController)


def test_follower_never_attacks_and_emits_no_p1_keys():
    """Pressure without committing: a follower emits no attack key, ever — and
    only its own (P2) keycodes."""
    foll = FollowerController(attacker_num=2)
    run_battle("legacy", frames=600, controllers=(None, foll))
    emitted = set().union(
        *(f.held | f.pressed | f.released for f in foll.emitted)
    ) if foll.emitted else set()
    assert P2_KEYS["attack"] not in emitted, "follower committed to an attack"
    assert emitted.isdisjoint(set(P1_KEYS.values())), "follower leaked P1 keycodes"
    assert emitted, "follower never moved at all"


def test_follower_settles_at_standoff_distance():
    """Vs an idle target the follower closes the initial gap but holds a standoff
    rather than piling on — the shadow/spacing behavior. Gap measured on rect.x
    (equal-width players ⇒ rect.x gap == centerx gap)."""
    standoff = 120
    foll = FollowerController(attacker_num=2, standoff=standoff)
    snaps = run_battle("legacy", frames=1500, controllers=(None, foll))

    def gap(s):
        p1x = next(p for p in s[0] if p[0] == "P1")[2]
        p2x = next(p for p in s[0] if p[0] == "P2")[2]
        return abs(p1x - p2x)

    start_gap = gap(snaps[0])
    final_gap = gap(snaps[-1])
    assert start_gap > 300, f"expected a wide initial gap, got {start_gap}"
    assert abs(final_gap - standoff) <= 20, (
        f"follower did not settle at standoff {standoff}: final gap {final_gap}"
    )
