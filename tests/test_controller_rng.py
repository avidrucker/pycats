"""#166 — seeded-RNG seam for AI NPC controllers.

A controller takes an injected PRNG. The default (rng=None) is a FIXED seed, so
sims/goldens/parity stay reproducible; callers (watch.py) inject a clocktime/
`--seed` Random for live variation. The RNG lives only at the controller edge —
it influences the chosen InputFrame and never reaches the FSM backends.

First consumer: IdlerController's `shield_chance` (an rng roll per frame),
so a seed change visibly changes shield timing while a fixed seed repeats.

Revert-the-fix check: if IdlerController.decide() ignores self.rng (no jitter
wired), the two-distinct-seeds-diverge test goes red (both streams identical).
"""
import random
from types import SimpleNamespace

from pycats.sim.controllers import AttackerController, BaseController, IdlerController

CONTROLS = {"left": "L", "right": "R", "up": "U", "down": "D",
            "shield": "S", "attack": "A"}


def _idle_player():
    # IdlerController.decide only reads a.controls["shield"]; position-independent.
    return SimpleNamespace(controls=CONTROLS,
                           fighter=SimpleNamespace(is_alive=True, on_ground=True),
                           rect=SimpleNamespace(centerx=400, centery=400))


def _run_idler(seed, *, chance=0.5, n=80, rng="seed"):
    """Drive an rng-jittered IdlerController n frames; return the held-key stream."""
    kw = {} if rng == "default" else {"rng": random.Random(seed)}
    c = IdlerController(attacker_num=1, shield_chance=chance, **kw)
    p = _idle_player()
    for f in range(n):
        c(p, p, f)
    return [frozenset(fi.held) for fi in c.emitted]


# --- the seam: injected, seeded, repeatable -----------------------------------

def test_same_seed_same_inputs_give_identical_emitted_stream():
    assert _run_idler(7) == _run_idler(7)


def test_two_distinct_seeds_diverge():
    # The able-to-fail guard: if the jitter didn't actually read self.rng, both
    # streams would be identical and this would fail.
    assert _run_idler(7) != _run_idler(8)


def test_default_rng_is_fixed_seed_deterministic():
    # rng=None must default to a FIXED seed (not clocktime), so a controller built
    # with no rng is reproducible run-to-run — this is what keeps goldens green.
    assert _run_idler(None, rng="default") == _run_idler(None, rng="default")


def test_default_idler_without_jitter_is_still_a_noop():
    # shield_chance defaults to 0 -> the rng is never drawn, behaviour unchanged.
    c = IdlerController(attacker_num=1)
    p = _idle_player()
    for f in range(30):
        c(p, p, f)
    assert all(not fi.held for fi in c.emitted)


# --- RNG stays at the edge: a non-consuming archetype is seed-invariant --------

def _attacker_player(cx):
    return SimpleNamespace(
        controls=CONTROLS,
        fighter=SimpleNamespace(is_alive=True, on_ground=True),
        rect=SimpleNamespace(centerx=cx, centery=400),
    )


def _run_attacker(seed, n=60):
    c = AttackerController(attacker_num=1, rng=random.Random(seed))
    a, t = _attacker_player(300), _attacker_player(360)
    for f in range(n):
        c(a, t, f)
    return [frozenset(fi.held) for fi in c.emitted]


def test_attacker_ignores_rng_so_goldens_are_seed_invariant():
    # AttackerController.decide() never draws rng -> two seeds emit identically.
    # This is why the live goldens (chase / two-npc) cannot churn from the seam.
    assert _run_attacker(7) == _run_attacker(8)


def test_base_controller_accepts_rng_kwarg():
    assert isinstance(BaseController(attacker_num=1, rng=random.Random(1)).rng,
                      random.Random)
