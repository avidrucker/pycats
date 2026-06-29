# watch.py
"""Watch or record a deterministic battle replay.
  python watch.py                                      # scripted replay, live window
  python watch.py --video out.mp4                      # ...write video instead
  python watch.py --match                               # full battle to defeat (chase bot)
  python watch.py --match --video full_battle.mp4      # ...recorded to video
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

# P2 controller per `--vs` archetype (P1 is always an attacker).
VS_CONTROLLERS = {
    "chase": AttackerController,
    "idler": IdlerController,
    "follower": FollowerController,
}

VS_FRAMES = 30 * FPS   # #61: a --vs demo runs up to 30s (1800 @ 60 FPS)...
MATCH_FRAMES = 6000    # ...a full --match plays to defeat...
REPLAY_FRAMES = 300    # ...the scripted replay default (~5s).


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
    if args.vs in VS_CONTROLLERS:
        controllers = (AttackerController(attacker_num=1, rng=rng),
                       VS_CONTROLLERS[args.vs](attacker_num=2, rng=rng))
    elif args.match:
        controller = AttackerController(attacker_num=1, rng=rng)
    # A --vs demo runs up to 30s or until a 3-stock KO-out, whichever first (#61).
    frames, stop_on_match_over = resolve_battle_plan(args.vs, args.match, args.frames)
    try:
        run_battle(frames=frames, presenter=presenter,
                   controller=controller, controllers=controllers,
                   stop_on_match_over=stop_on_match_over)
    except KeyboardInterrupt:
        presenter.close()
    if args.video:
        print(f"wrote {args.video}")


if __name__ == "__main__":
    main()
