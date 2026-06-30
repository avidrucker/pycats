# watch.py
"""Watch or record a deterministic battle replay.
  python watch.py                                      # scripted replay, live window
  python watch.py --video out.mp4                      # ...write video instead
  python watch.py --match                               # full battle to defeat (chase bot)
  python watch.py --match --video full_battle.mp4      # ...recorded to video
  python watch.py --vs chase                            # P1 vs an NPC: idle|chase|idler|follower (#61)
  python watch.py --vs chase --seed 42                  # ...reproducible: same seed + backend → same battle (#166)
                                                        #   (omit --seed → clocktime seed, so the battle varies each run)
"""
from __future__ import annotations

import argparse
import random

from pycats.config import FPS
from pycats.sim.runner import run_battle
from pycats.sim.presenters import LivePresenter, VideoPresenter
from pycats.sim.controllers import (
    AttackerController, IdlerController, FollowerController,
)
from pycats.characters.roster import ARCHETYPE_ROSTER

# P2 controller per `--vs` archetype (P1 is always an attacker).
VS_CONTROLLERS = {
    "chase": AttackerController,
    "idler": IdlerController,
    "follower": FollowerController,
}

VS_FRAMES = 30 * FPS   # #61: a --vs demo runs up to 30s (1800 @ 60 FPS)...
MATCH_FRAMES = 6000    # ...a full --match plays to defeat...
REPLAY_FRAMES = 300    # ...the scripted replay default (~5s).

# Characters selectable per player (#244) — sourced from the single roster source of
# truth (#272) so it can't drift as #117 archetypes land. None = the default cat.
# (load_fighter_data falls through to the default for any other key.)
CHARACTERS = list(ARCHETYPE_ROSTER)


def cpu_controllers(p1_level, p2_level, rng):
    """Leveled `AttackerController`s for a per-player CPU-difficulty battle (#244).
    A `None` level leaves that player uncontrolled (idle). Returns `(c1, c2)`."""
    c1 = AttackerController(attacker_num=1, level=p1_level, rng=rng) if p1_level is not None else None
    c2 = AttackerController(attacker_num=2, level=p2_level, rng=rng) if p2_level is not None else None
    return (c1, c2)


def resolve_battle_plan(vs, match, frames):
    """Map the CLI mode flags to ``(frames, stop_on_match_over)`` (#61).

    A ``--vs`` archetype battle runs up to 30s (``VS_FRAMES``) and stops the
    frame a player is fully KO'd out (3 stocks gone), whichever comes first.
    ``--match`` is a full battle to defeat (``MATCH_FRAMES``, unchanged); the
    scripted replay runs ``REPLAY_FRAMES`` to completion. ``frames`` (the
    ``--frames`` flag, ``None`` when unset) overrides the cap for ``--vs`` and the
    scripted replay; ``--match`` keeps its fixed cap. ``--vs`` takes precedence
    over ``--match`` (mirroring the controller selection in ``main``).
    """
    if vs in VS_CONTROLLERS:
        return (frames if frames is not None else VS_FRAMES), True
    if match:
        return MATCH_FRAMES, True
    return (frames if frames is not None else REPLAY_FRAMES), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=None,
                    help="frame-cap override; defaults per mode (scripted 300, "
                         "--vs 1800 ≈ 30s, --match 6000). --match ignores this.")
    ap.add_argument("--video", default=None, help="output path; omit for live window")
    ap.add_argument("--match", action="store_true",
                    help="play a full match to defeat (P1 chase bot vs idle P2) "
                         "instead of the fixed scripted replay")
    ap.add_argument("--vs", choices=["idle", "chase", "idler", "follower"], default="idle",
                    help="who controls P2 in a 2-NPC battle (P1 is always an "
                         "attacker): idle (default, no P2 controller), chase "
                         "(attacker), idler (baseline), or follower (shadow).")
    ap.add_argument("--uncapped", action="store_true",
                    help="run the live window uncapped so the FPS readout shows "
                         "the true achievable rate (default paces to 60)")
    ap.add_argument("--no-overlay", dest="overlay", action="store_false",
                    help="hide the live FPS / stocks / damage overlay")
    ap.add_argument("--seed", type=int, default=None,
                    help="PRNG seed for the NPC controllers (#166): pass an int "
                         "for a reproducible run; omit for a clocktime seed so a "
                         "live match varies run-to-run.")
    ap.add_argument("--p1-char", choices=CHARACTERS, default=None,
                    help="P1 character/archetype (e.g. nalio); default cat if omitted. (#244)")
    ap.add_argument("--p2-char", choices=CHARACTERS, default=None,
                    help="P2 character/archetype.")
    ap.add_argument("--p1-level", type=int, choices=range(1, 10), default=None,
                    help="P1 CPU difficulty 1-9 (#231/#148); makes P1 a leveled bot.")
    ap.add_argument("--p2-level", type=int, choices=range(1, 10), default=None,
                    help="P2 CPU difficulty 1-9; makes P2 a leveled bot.")
    args = ap.parse_args()

    presenter = (VideoPresenter(args.video) if args.video
                 else LivePresenter(cap_fps=not args.uncapped, overlay=args.overlay))
    # Seed home is this CLI edge (#166): an explicit --seed is reproducible; absent
    # is clocktime (live variation). Injected into the controllers so the seed is
    # caller-controlled — controllers never import-and-call a module-level random.
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    # `--vs <archetype>` drives BOTH players (controllers=): P1 is always an
    # attacker, P2 is the chosen archetype. Otherwise the classic single-bot
    # `--match` (P1 attacker vs idle P2) or the scripted replay.
    controller = None
    controllers = None
    leveled = args.p1_level is not None or args.p2_level is not None
    if leveled:
        # #244: per-player CPU-difficulty battle (overrides --vs). Runs like a --vs
        # demo (≤30s or KO, or --frames). Pair with --p1-char/--p2-char to pick who.
        controllers = cpu_controllers(args.p1_level, args.p2_level, rng)
        frames = args.frames if args.frames is not None else VS_FRAMES
        stop_on_match_over = True
    elif args.vs in VS_CONTROLLERS:
        controllers = (AttackerController(attacker_num=1, rng=rng),
                       VS_CONTROLLERS[args.vs](attacker_num=2, rng=rng))
        frames, stop_on_match_over = resolve_battle_plan(args.vs, args.match, args.frames)
    else:
        if args.match:
            controller = AttackerController(attacker_num=1, rng=rng)
        frames, stop_on_match_over = resolve_battle_plan(args.vs, args.match, args.frames)
    try:
        run_battle(frames=frames, presenter=presenter,
                   controller=controller, controllers=controllers,
                   stop_on_match_over=stop_on_match_over,
                   p1_char=args.p1_char, p2_char=args.p2_char)
    except KeyboardInterrupt:
        presenter.close()
    if args.video:
        print(f"wrote {args.video}")


if __name__ == "__main__":
    main()
