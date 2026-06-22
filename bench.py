# bench.py
"""Benchmark the two state-engine backends over the headless battle.

Reports per-frame timing and a per-bucket breakdown (state engine vs physics vs
combat) so we can see whether the state machine is a meaningful slice of the
frame budget. Usage: python bench.py [--frames N]
"""
from __future__ import annotations

import argparse
import statistics
import time

from pycats.sim.runner import (
    KEYMAPS, build_players, build_stage, run_battle,
)
from pycats.sim.input_script import default_timeline
from pycats.systems import combat
from pycats.core.physics import resolve_player_push
from pycats.systems.match_engine import make_match_engine

BUDGET_US = 1_000_000 / 60  # 16,667 us per frame at 60 FPS


def _percentile(xs, q):
    s = sorted(xs)
    if not s:
        return 0.0
    idx = min(len(s) - 1, int(q * len(s)))
    return s[idx]


def benchmark(backend, frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    per_frame = []
    platforms = build_stage()
    p1, p2, players = build_players(backend)
    import pygame
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2], backend)
    for f in range(frames):
        fi = inputs[f % n]
        t0 = time.perf_counter()
        for p in players:
            p.update(fi, platforms, attacks)
        resolve_player_push(list(players))
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        per_frame.append((time.perf_counter() - t0) * 1e6)
    total_s = sum(per_frame) / 1e6
    mean_us = statistics.mean(per_frame)
    return {
        "total_s": total_s,
        "mean_us": mean_us,
        "median_us": statistics.median(per_frame),
        "p95_us": _percentile(per_frame, 0.95),
        "p99_us": _percentile(per_frame, 0.99),
        "fps": 1e6 / mean_us if mean_us else 0.0,
    }


def bucketed(backend, frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    phys, push, comb = [], [], []
    platforms = build_stage()
    p1, p2, players = build_players(backend)
    import pygame
    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2], backend)
    plist = list(players)
    for f in range(frames):
        fi = inputs[f % n]
        # The state engine's tick() is fused inside Player.update, so it cannot
        # be timed separately post-hoc. We therefore bucket the frame as:
        #   physics_us = Player.update (physics + the engine tick, both backends)
        #   push_us    = resolve_player_push (identical across backends)
        #   combat_us  = attacks.update + process_hits + match.tick
        # The engine's true cost is isolated by the mean_us delta between
        # backends in benchmark(), where everything but the engine is identical.
        t0 = time.perf_counter()
        for p in players:
            p.update(fi, platforms, attacks)
        t1 = time.perf_counter()
        resolve_player_push(plist)
        t2 = time.perf_counter()
        attacks.update()
        combat.process_hits(players, attacks)
        match.tick()
        t3 = time.perf_counter()
        phys.append((t1 - t0) * 1e6)
        push.append((t2 - t1) * 1e6)
        comb.append((t3 - t2) * 1e6)
    import statistics as st
    return {
        "physics_us": st.mean(phys),
        "push_us": st.mean(push),
        "combat_us": st.mean(comb),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=20_000)
    args = ap.parse_args()

    rows = {b: benchmark(b, args.frames) for b in ("legacy", "statechart")}
    print(f"\nBattle benchmark — {args.frames} frames\n" + "=" * 56)
    hdr = f"{'metric':<14}{'legacy':>14}{'statechart':>16}"
    print(hdr)
    print("-" * 56)
    for k in ("mean_us", "median_us", "p95_us", "p99_us", "fps"):
        print(f"{k:<14}{rows['legacy'][k]:>14.2f}{rows['statechart'][k]:>16.2f}")
    delta = rows["statechart"]["mean_us"] - rows["legacy"]["mean_us"]
    print("-" * 56)
    print(f"statechart - legacy: {delta:+.2f} us/frame "
          f"({delta / BUDGET_US * 100:+.3f}% of 16.67ms budget)")
    print("\nper-bucket mean us/frame (statechart):")
    for k, v in bucketed("statechart", args.frames).items():
        print(f"  {k:<12}{v:>10.2f}")


if __name__ == "__main__":
    main()
