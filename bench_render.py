# bench_render.py
"""Profile the battle RENDERER (the drawing), separately from game logic.

bench.py times the simulation with drawing off; this times the drawing itself:
the shared render_battle() plus its components (platforms, tails, cat bodies,
shield, attacks). It reports mean us/frame and the resulting render-only FPS
ceiling, then a cProfile function-level hotspot list.

Caveat: rendering here goes to an offscreen software Surface (SDL dummy), so it
measures the CPU cost of the draw calls (pygame.draw.*, transform.rotate, blits).
That is exactly where the procedural drawing and per-segment tail rotation live,
so it is a faithful proxy for the CPU rendering cost. It does NOT include any
GPU/display blit, nor the HUD/controls/FPS text (those live in game.py, not in
render_battle); it also does not include vsync, which the live game caps at 60.

Usage: python bench_render.py [--iters N]
"""
from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import statistics
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame  # noqa: E402

if not pygame.get_init():
    pygame.init()

from pycats.config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH  # noqa: E402
from pycats.core.input import InputFrame  # noqa: E402
from pycats.entities.attack import Attack  # noqa: E402
from pycats.render_battle import (  # noqa: E402
    _BODY_PAD_TOP,
    _BODY_PAD_X,
    _cat_body_surface,
    draw_cat_features,
    draw_eye,
    draw_player_name,
    draw_stripes,
    render_attacks,
    render_battle,
)
from pycats.sim.runner import build_players, build_stage  # noqa: E402

BUDGET_US = 1_000_000 / 60  # 16,667 us/frame at 60 FPS


def _build_scene():
    """A representative frame: tails in motion, one shielding cat, a live attack."""
    platforms = build_stage()
    p1, p2, players = build_players("statechart")
    attacks = pygame.sprite.Group()
    # Move a few frames so the tails have settled into a real curved pose.
    right = InputFrame(held={p1.controls["right"]}, pressed=set(), released=set())
    for f in range(40):
        for p in players:
            p.update(right if f < 20 else InputFrame(set(), set(), set()),
                     platforms, attacks)
    # Force one fighter to render its shield bubble, and add a live attack hitbox
    # (the fighter's jab move data — the single attack model).
    p2.shield_attempting = True
    p2.engine.force("shield")
    jab = p1.fighter_data.moves["attack"]
    attacks.add(Attack(p1, hitbox=jab.hitboxes[0], lifetime=jab.active))
    return platforms, players, attacks


def _time(fn, iters):
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1e6)
    return statistics.mean(samples), statistics.median(samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=3000)
    args = ap.parse_args()
    iters = args.iters

    platforms, players, attacks = _build_scene()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def full():
        surface.fill(BG_COLOR)
        render_battle(surface, players, platforms)
        render_attacks(surface, attacks)

    def only_platforms():
        for pl in platforms:
            surface.blit(pl.image, pl.rect)

    def only_tails():
        for p in players:
            p.tail.draw(surface)

    def only_bodies_cached():
        # What render_battle actually does now: one cached composite blit/cat.
        for p in players:
            body = _cat_body_surface(p)
            surface.blit(body, (p.rect.x - _BODY_PAD_X, p.rect.y - _BODY_PAD_TOP))

    def only_bodies_uncached():
        # Reference: the pre-cache per-frame draw (for the cache speedup ratio).
        for p in players:
            surface.blit(p.image, p.rect)
            draw_stripes(surface, p)
            draw_eye(surface, p)
            draw_eye(surface, p, eye=False)
            draw_cat_features(surface, p)
            draw_player_name(surface, p)

    def only_attacks():
        render_attacks(surface, attacks)

    only_bodies_cached()  # warm the body cache before timing

    buckets = [
        ("FULL render_battle+attacks", full),
        ("  platforms", only_platforms),
        ("  tails (2x30 segs, cached)", only_tails),
        ("  cat bodies (cached composite)", only_bodies_cached),
        ("  cat bodies (uncached ref)", only_bodies_uncached),
        ("  attacks", only_attacks),
    ]

    print(f"\nRenderer profile — {iters} iters, offscreen {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print("=" * 64)
    print(f"{'component':<40}{'mean us':>10}{'median us':>12}")
    print("-" * 64)
    full_mean = None
    for name, fn in buckets:
        mean, median = _time(fn, iters)
        if full_mean is None:
            full_mean = mean
        print(f"{name:<40}{mean:>10.2f}{median:>12.2f}")
    print("-" * 64)
    fps = 1e6 / full_mean if full_mean else 0.0
    print(f"render-only ceiling: {fps:,.0f} FPS  "
          f"({full_mean:.1f} us/frame = {full_mean / BUDGET_US * 100:.1f}% of the "
          f"16.67ms/60fps budget)")
    print("(CPU draw cost only; excludes GPU/display blit, vsync, and HUD/text.)")

    # cProfile hotspots over the full render.
    print(f"\nTop functions (cProfile, full render x{iters}):")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(iters):
        full()
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(12)
    # Trim pstats header noise; show the table lines.
    for line in s.getvalue().splitlines():
        if line.strip() and ("function)" in line or "{" in line or "/" in line
                             or "pycats" in line or "ncalls" in line):
            print("  " + line.strip())


if __name__ == "__main__":
    main()
