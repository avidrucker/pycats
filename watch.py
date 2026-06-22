# watch.py
"""Watch or record a deterministic battle replay.
  python watch.py --backend statechart            # live window
  python watch.py --backend legacy --video out.mp4 # write video
"""
from __future__ import annotations

import argparse

from pycats.sim.runner import run_battle
from pycats.sim.presenters import LivePresenter, VideoPresenter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["legacy", "statechart"], default="legacy")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--video", default=None, help="output path; omit for live window")
    args = ap.parse_args()

    presenter = VideoPresenter(args.video) if args.video else LivePresenter()
    try:
        run_battle(backend=args.backend, frames=args.frames, presenter=presenter)
    except KeyboardInterrupt:
        presenter.close()
    if args.video:
        print(f"wrote {args.video}")


if __name__ == "__main__":
    main()
