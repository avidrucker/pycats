"""Repro for issue #5 — players can jump into the SIDE faces of thick platforms.

Drives the *real* per-frame loop (Player.update + core.physics + the real stage)
exactly like pycats.sim.runner, but seeds one player next to the thick
platform's left side face and gives it a jump-arc into that face. Side faces are
supposed to be solid (PM-style); the bug is that solve_vertical only resolves
top-landing and head-bonk, never the left/right faces, so the player passes
straight through the solid platform body.

Prints a per-frame trajectory + a PENETRATION verdict, and can either record a
video or open a live window so the bug is viewable.

────────────────────────────────────────────────────────────────────────────
HOW TO RUN / VIEW  (PYTHONPATH must point at the worktree root so `pycats`
resolves; PY = the main checkout's venv, which has pygame-ce + imageio)
────────────────────────────────────────────────────────────────────────────
  WT=/home/avi/Documents/Study/Python/pycats/.claude/worktrees/banana-issue-5
  PY=/home/avi/Documents/Study/Python/pycats/.venv/bin/python

  # headless proof (prints trajectory + verdict; exits 0 only if bug present)
  cd "$WT" && PYTHONPATH="$WT" "$PY" tools/repro_issue_5.py

  # LIVE window — loops the scenario; close the window or press Esc to stop
  cd "$WT" && PYTHONPATH="$WT" "$PY" tools/repro_issue_5.py --live

  # record an mp4 (slowed to 20 fps for viewability)
  cd "$WT" && PYTHONPATH="$WT" "$PY" tools/repro_issue_5.py --video media/issue_5_side.mp4

  # then play the recording / stills with your default viewer:
  xdg-open "$WT"/media/issue_5_side.mp4
  xdg-open "$WT"/media/issue_5_frame06.png   # cat embedded inside the platform
  xdg-open "$WT"/media/issue_5_frame20.png   # cat popped out on top
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import argparse
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

if not pygame.get_init():
    pygame.init()

from pycats.config import THICK_PLAT_DICT, CAT_CHARACTERS  # noqa: E402
from pycats.core.input import InputFrame  # noqa: E402
from pycats.sim.runner import build_stage, P1_KEYS  # noqa: E402
from pycats.entities import Player  # noqa: E402


def make_frame(*keys):
    held = set(keys)
    return InputFrame(held=held, pressed=set(held), released=set())


def overlaps_thick(rect, thick):
    return rect.colliderect(thick)


def _seed(p):
    """Place the player just LEFT of the left side face, vertically inside the
    platform body, launched up-and-into the face (a "jump into the side")."""
    p.rect.midbottom = (50, 489)      # rect spans x[30,70], y[429,489]; face at x=80
    p.vel = pygame.Vector2(0, -9)     # jumping upward beside the face
    p.on_ground = False


def run(video_path=None, live=False):
    platforms = build_stage()
    thick = platforms[0].rect  # x[80,880] y[410,490]
    print(f"thick platform: left_face_x={thick.left} right_face_x={thick.right} "
          f"top={thick.top} bottom={thick.bottom}")

    c = CAT_CHARACTERS["calico"]
    p = Player(0, 0, P1_KEYS, c["color"], eye_color=c["eye_color"],
               char_name="P1", facing_right=True, state_backend="statechart")
    _seed(p)

    attacks = pygame.sprite.Group()
    group = pygame.sprite.Group(p)

    if live:
        return _run_live(platforms, thick, p, group, attacks)

    presenter = None
    if video_path:
        os.makedirs(os.path.dirname(video_path) or ".", exist_ok=True)
        from pycats.sim.presenters import VideoPresenter
        presenter = VideoPresenter(video_path, fps=20)  # slow for viewability

    # Timeline: a few frames holding RIGHT (drive into the side face), then coast.
    HOLD_RIGHT = 22
    TOTAL = 48
    penetrated_frame = None
    crossed_face = False

    print(f"{'f':>3} {'x.left':>7} {'x.right':>8} {'y.top':>6} {'y.bot':>6} "
          f"{'vx':>6} {'vy':>6} {'grnd':>4} {'inside?':>7}")
    for f in range(TOTAL):
        fi = make_frame(P1_KEYS["right"]) if f < HOLD_RIGHT else InputFrame(set(), set(), set())
        for pl in group:
            pl.update(fi, platforms, attacks)
        inside = overlaps_thick(p.rect, thick)
        # "inside" specifically means the player has entered past the left face
        # while spanning the platform's vertical band (not merely resting on top).
        deep = inside and p.rect.bottom > thick.top + 2 and p.rect.right > thick.left
        if deep and penetrated_frame is None:
            penetrated_frame = f
        if p.rect.right > thick.left:
            crossed_face = True
        if f % 2 == 0 or deep:
            print(f"{f:>3} {p.rect.left:>7} {p.rect.right:>8} {p.rect.top:>6} "
                  f"{p.rect.bottom:>6} {p.vel.x:>6.2f} {p.vel.y:>6.2f} "
                  f"{str(p.on_ground):>4} {str(deep):>7}")
        if presenter is not None:
            presenter.show(platforms, group, attacks, f)
    if presenter is not None:
        presenter.close()

    print("\n--- VERDICT ---")
    print(f"player crossed the left side face (x>{thick.left}): {crossed_face}")
    if penetrated_frame is not None:
        print(f"BUG REPRODUCED: player penetrated the solid thick platform body "
              f"at frame {penetrated_frame} (side face is not solid).")
    else:
        print("No penetration observed (side face behaved as solid).")
    if video_path:
        print(f"wrote {video_path}")
    return penetrated_frame is not None


def _run_live(platforms, thick, p, group, attacks):
    """Open a real window and loop the jump-into-side scenario until you close
    it (or press Esc). Paced slow (~15 fps) so the penetration is easy to see."""
    import time
    from pycats.sim.presenters import LivePresenter

    presenter = LivePresenter(caption="issue #5 repro — jump into thick platform side",
                              cap_fps=True, overlay=True)
    HOLD_RIGHT = 22
    CYCLE = 60          # frames per loop (scenario + a beat to hold the result)
    print("LIVE: watch the cat pass through the LEFT side face of the thick "
          "platform and pop out on top. Close the window (or Esc) to stop.")
    try:
        f = 0
        while True:
            phase = f % CYCLE
            if phase == 0:
                _seed(p)            # restart the scenario each cycle
            fi = make_frame(P1_KEYS["right"]) if phase < HOLD_RIGHT else InputFrame(set(), set(), set())
            for pl in group:
                pl.update(fi, platforms, attacks)
            for ev in pygame.event.get(pygame.KEYDOWN):
                if ev.key == pygame.K_ESCAPE:
                    raise KeyboardInterrupt
            presenter.show(platforms, group, attacks, f)
            time.sleep(0.05)        # extra slowdown on top of the 60fps cap
            f += 1
    except KeyboardInterrupt:
        pass
    finally:
        presenter.close()
    print("live window closed.")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=None, help="record an mp4 to this path")
    ap.add_argument("--live", action="store_true",
                    help="open a real window and loop the scenario to watch")
    args = ap.parse_args()
    ok = run(args.video, live=args.live)
    raise SystemExit(0 if ok else 1)
