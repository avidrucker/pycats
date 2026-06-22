# watch.py
"""Watch or record a deterministic battle replay.
  python watch.py --backend statechart                 # scripted replay, live window
  python watch.py --backend legacy --video out.mp4     # write video
  python watch.py --match                               # full battle to defeat (chase bot)
  python watch.py --match --video full_battle.mp4      # ...recorded to video
"""
from __future__ import annotations

import argparse

from pycats.sim.runner import run_battle
from pycats.sim.presenters import LivePresenter, VideoPresenter
from pycats.sim.controllers import ChaseController


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["legacy", "statechart"], default="statechart")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--video", default=None, help="output path; omit for live window")
    ap.add_argument("--match", action="store_true",
                    help="play a full match to defeat (P1 chase bot vs idle P2) "
                         "instead of the fixed scripted replay")
    ap.add_argument("--uncapped", action="store_true",
                    help="run the live window uncapped so the FPS readout shows "
                         "the true achievable rate (default paces to 60)")
    ap.add_argument("--no-overlay", dest="overlay", action="store_false",
                    help="hide the live FPS / stocks / damage overlay")
    args = ap.parse_args()

    presenter = (VideoPresenter(args.video) if args.video
                 else LivePresenter(cap_fps=not args.uncapped, overlay=args.overlay))
    controller = ChaseController(attacker_num=1) if args.match else None
    frames = 6000 if args.match else args.frames
    try:
        run_battle(backend=args.backend, frames=frames, presenter=presenter,
                   controller=controller, stop_on_match_over=args.match)
    except KeyboardInterrupt:
        presenter.close()
    if args.video:
        print(f"wrote {args.video}")


if __name__ == "__main__":
    main()
