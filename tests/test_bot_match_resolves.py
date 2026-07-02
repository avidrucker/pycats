"""Regression for #292 — a level-5 CPU-vs-CPU match must be winnable by KO.

Root cause (research #287 + this ticket): a leveled `AttackerController` converges
to its `standoff` gap and attacks from *neutral* spacing, so the move-select seam
always resolves the neutral **jab**. Nalio's jab is a *set-knockback* move (WDSK 20)
whose launch is fixed (~3 px/frame) regardless of the victim's percent — so it can
never KO. The bot never inputs a directional tilt (its only percent-scaling moves),
so no bot-vs-bot match ever ends by KO: the losing fighter is juggled past 1400%
with all stocks intact and the match never resolves.

Fix: a leveled tilt-enabled bot holds "toward" when it commits a grounded attack,
so the seam resolves a percent-scaling **forward-tilt** instead of the jab.

Able-to-fail: without the fix no stock is ever lost — the loser is juggled to a
runaway percent (675% within this budget, 1404% at the 200 s cap) with all 3 stocks
intact. With the fix, KOs convert at sane percents and stocks fall. This is the exact
seed/matchup from the #292 report.

Scope note: the assertions below prove the *defect* is gone — the win-condition (a
KO) is reachable in bot play and no fighter is juggled to an absurd percent. They do
NOT assert a full 3-stock `match_over`: with #309's faithful Birky geometry the last
stock is slow to close out for this particular seed (a separate difficulty-tuning
concern), whereas KO *conversion* — the thing #292 was about — is immediate and
robust.
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.sim.runner import run_battle
from pycats.sim.controllers import AttackerController

# indices into snapshot player tuple (see sim/runner.snapshot)
_PERCENT, _LIVES = 7, 9

# ~100 s at 60 fps: comfortably past the first KO conversion (frame ~1428 with
# #309's Birky geometry), yet well inside the 12000-frame runaway of the bug (which
# never converts a single KO).
_FRAME_BUDGET = 6000
# A light/floaty fighter must be KO'd well before this; the bug juggled to 1404%.
_SANE_PERCENT_CEILING = 300.0


def _run_l5_nalio_vs_birky(frames):
    rng = random.Random(3)  # the #292 report's seed
    c1 = AttackerController(attacker_num=1, level=5, rng=rng)
    c2 = AttackerController(attacker_num=2, level=5, rng=rng)
    return run_battle(frames=frames, controllers=(c1, c2),
                      p1_char="nalio", p2_char="birky", stop_on_match_over=True)


def test_l5_bot_converts_a_ko():
    # The heart of #292: the KO win-condition must be REACHABLE in bot play. Without
    # the fix, birky is juggled forever and never loses a stock (lives stay 3/3);
    # with it, a clean scaling hit converts and a stock falls within the budget.
    snaps = _run_l5_nalio_vs_birky(_FRAME_BUDGET)
    p1_lo = min(s[0][0][_LIVES] for s in snaps)
    p2_lo = min(s[0][1][_LIVES] for s in snaps)
    assert min(p1_lo, p2_lo) < 3, (
        f"#292: no KO converted in {_FRAME_BUDGET} frames — a fighter juggled with "
        f"all stocks intact (min lives p1={p1_lo}, p2={p2_lo})"
    )


def test_no_fighter_is_juggled_past_a_sane_percent():
    # The bug's signature: birky survives 1404% with all stocks. A clean hit should
    # KO a floaty fighter long before that, so neither fighter should ever reach an
    # absurd percent across the whole match.
    snaps = _run_l5_nalio_vs_birky(_FRAME_BUDGET)
    worst = max(max(s[0][0][_PERCENT], s[0][1][_PERCENT]) for s in snaps)
    assert worst < _SANE_PERCENT_CEILING, (
        f"#292: a fighter was juggled to {worst:.0f}% without a KO "
        f"(ceiling {_SANE_PERCENT_CEILING:.0f}%)"
    )
