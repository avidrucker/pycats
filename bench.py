# bench.py
"""Benchmark the state engine over the headless battle.

Reports per-frame timing and a per-bucket breakdown (state engine vs physics vs
combat) so we can see whether the state machine is a meaningful slice of the
frame budget. Usage: python bench.py [--frames N]
"""

from __future__ import annotations

import argparse
import statistics
import time

from pycats.core.physics import resolve_player_push
from pycats.sim.input_script import default_timeline
from pycats.sim.runner import (
    KEYMAPS,
    build_players,
    build_stage,
)
from pycats.systems import combat
from pycats.systems.match_engine import make_match_engine

BUDGET_US = 1_000_000 / 60  # 16,667 us per frame at 60 FPS


def _percentile(xs, q):
    s = sorted(xs)
    if not s:
        return 0.0
    idx = min(len(s) - 1, int(q * len(s)))
    return s[idx]


def benchmark(frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    per_frame = []
    platforms = build_stage()
    p1, p2, players = build_players()
    import pygame

    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2])
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


def bucketed(frames=10_000):
    inputs = default_timeline(KEYMAPS)
    n = len(inputs)
    phys, push, comb = [], [], []
    platforms = build_stage()
    p1, p2, players = build_players()
    import pygame

    attacks = pygame.sprite.Group()
    match = make_match_engine([p1, p2])
    plist = list(players)
    for f in range(frames):
        fi = inputs[f % n]
        # The state engine's tick() is fused inside Player.update, so it cannot
        # be timed separately post-hoc. We therefore bucket the frame as:
        #   physics_us = Player.update (physics + the engine tick)
        #   push_us    = resolve_player_push
        #   combat_us  = attacks.update + process_hits + match.tick
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


def collect(frames):
    """Run the benchmark and return a single results dict (also what --json writes)."""
    row = benchmark(frames)
    return {
        "frames": frames,
        "budget_us_per_frame": BUDGET_US,
        "engine": row,
        "overhead_pct_of_budget": row["mean_us"] / BUDGET_US * 100,
        "buckets_us": bucketed(frames),
    }


def print_report(results):
    frames = results["frames"]
    row = results["engine"]
    print(f"\nBattle benchmark — {frames} frames\n" + "=" * 40)
    print(f"{'metric':<14}{'statechart':>16}")
    print("-" * 40)
    for k in ("mean_us", "median_us", "p95_us", "p99_us", "fps"):
        print(f"{k:<14}{row[k]:>16.2f}")
    print("-" * 40)
    print(f"mean {row['mean_us']:.2f} us/frame ({results['overhead_pct_of_budget']:.3f}% of 16.67ms budget)")
    print("\nper-bucket mean us/frame:")
    for k, v in results["buckets_us"].items():
        print(f"  {k:<12}{v:>10.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=20_000)
    ap.add_argument("--json", default=None, help="write results to this JSON path (timestamped) and print")
    args = ap.parse_args()

    results = collect(args.frames)
    print_report(results)

    if args.json:
        import datetime
        import json
        import platform

        results = dict(results)  # shallow copy + add run metadata
        results["meta"] = {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        }
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
