#!/usr/bin/env python3
"""Two-panel comparison of the three datamine representative-frame strategies (#1217).

For one datamined move this renders a side-by-side animated GIF:

    [ reference GIF ]  |  [ exact pycats-px plot ]
      brawllib render  |    box arc + FIRST_ACTIVE / MID_WINDOW / WINDOW_AVERAGE

The LEFT panel is the brawllib reference animation (gif_generator_fixed, #1157) — it
shows the limb and, in brawllib's own render, the hitbox sweeping. The RIGHT panel is
an EXACT plot in pycats px of every active frame's box (the arc) plus the three static
circles `propose()` would pick (`pycats.combat.datamine_proposer.RepresentativeFrame`).

Why two panels instead of one overlay (#1217 build decision): the reference GIF is a
per-subaction camera render with no fixed world->px POSITION scale (#120/#195/#1153),
so compositing pycats-px circles onto it would require a hand-tuned align. The three
strategies all live in ONE pycats-px space, so the right panel's positions are exact
and need no alignment — the approximation is avoided by NOT compositing the two spaces.
The GIF frame count equals the datamine frame count 1:1, so the right panel highlights
the box active on the same frame the left panel is showing.

This is comparison TOOLING, not game code: it reads the datamine + the reference GIF
and writes an artifact a human eyeballs to pick `propose()`'s default. It never writes
cat data. Outputs land under repros/ (gitignored).

Dependencies: pygame-ce (declared runtime) draws the plot; imageio (declared dev dep)
reads the reference GIF frames and writes the combined GIF; numpy rides along with
imageio. No new dependency.

Usage:
    scripts/compare_representative_frames.py \
        --gif  repros/rep-frame-compare/gifs/output_Mario_AttackHi4.gif \
        --datamine pycats/combat/datamine_data/mario_attackhi4_hitboxes.json \
        --move "u-smash (AttackHi4)" \
        --out  repros/rep-frame-compare/compare_AttackHi4.gif
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Offscreen SDL before pygame import (headless render).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

# pycats package import when run from a checkout without install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycats.combat.datamine_hitboxes import HitboxTable, load_hitbox_table  # noqa: E402
from pycats.combat.datamine_proposer import (  # noqa: E402
    RepresentativeFrame,
    _active_boxes,
    _circle_from_world,
    propose,
)

# The three strategies get one stable colour each, used across every hitbox id.
STRATEGY_COLOR = {
    RepresentativeFrame.FIRST_ACTIVE: (240, 90, 90),  # red
    RepresentativeFrame.MID_WINDOW: (90, 210, 110),  # green
    RepresentativeFrame.WINDOW_AVERAGE: (100, 160, 255),  # blue
}
ARC_COLOR = (120, 120, 128)  # faint per-frame boxes (the sweep)
HIGHLIGHT_COLOR = (250, 235, 120)  # the box active on the currently-shown frame
ORIGIN_COLOR = (220, 220, 220)  # fighter body origin (dx=dy=0)
BG_COLOR = (24, 26, 32)
TEXT_COLOR = (225, 225, 230)


@dataclass(frozen=True)
class _Dot:
    """One plotted circle in pycats px: centre (dx, dy) and radius r."""

    dx: float
    dy: float
    r: float


def collect_geometry(table: HitboxTable) -> dict[int, dict]:
    """Per hitbox id: the per-frame arc dots and the three strategy dots.

    Returns {hid: {"arc": {frame_index: _Dot, ...},
                   "strat": {RepresentativeFrame: _Dot, ...}}}.
    Pure — reuses propose()/_active_boxes/_circle_from_world, so it agrees exactly
    with what the editor would receive from propose().
    """
    strat_by_id = {s: {c.hitbox_id: c.circle for c in propose(table, s)} for s in RepresentativeFrame}
    out: dict[int, dict] = {}
    for hid in table.distinct_ids():
        arc = {
            idx: _Dot(c.dx, c.dy, c.r)
            for (idx, box) in _active_boxes(table, hid)
            for c in (_circle_from_world(box.pos[2], box.pos[1], box.size),)
        }
        strat = {
            s: _Dot(strat_by_id[s][hid].dx, strat_by_id[s][hid].dy, strat_by_id[s][hid].r) for s in RepresentativeFrame
        }
        out[hid] = {"arc": arc, "strat": strat}
    return out


def geometry_bounds(geometry: dict[int, dict]) -> tuple[float, float, float, float]:
    """(min_x, min_y, max_x, max_y) enclosing every dot's full extent + the origin.

    Includes each dot's radius so no circle is clipped, and always includes the
    body origin (0, 0) so the fighter reference point is on-canvas.
    """
    xs = [0.0]
    ys = [0.0]
    for gid in geometry.values():
        dots = list(gid["arc"].values()) + list(gid["strat"].values())
        for d in dots:
            xs += [d.dx - d.r, d.dx + d.r]
            ys += [d.dy - d.r, d.dy + d.r]
    return min(xs), min(ys), max(xs), max(ys)


def make_transform(bounds, width: int, height: int, margin: int = 14):
    """Return a px->(canvas_x, canvas_y) mapping that fits `bounds` in the canvas.

    Isotropic (one scale for both axes, so circles stay circular), centred, with a
    uniform pixel margin. pycats screen convention is preserved: +dx is right and
    +dy is DOWN, so the mapping is a pure positive scale + translate (no y flip).
    """
    min_x, min_y, max_x, max_y = bounds
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    avail_w = max(width - 2 * margin, 1)
    avail_h = max(height - 2 * margin, 1)
    scale = min(avail_w / span_x, avail_h / span_y)
    # Centre the scaled content in the available area.
    off_x = margin + (avail_w - span_x * scale) / 2.0
    off_y = margin + (avail_h - span_y * scale) / 2.0

    def tx(dx: float, dy: float) -> tuple[int, int]:
        return (
            int(round(off_x + (dx - min_x) * scale)),
            int(round(off_y + (dy - min_y) * scale)),
        )

    return tx, scale


def _draw_column(pygame, size, geometry, tx, scale, highlight_frame, strategy, font, small):
    """One strategy's column: every id's faint arc + only THIS strategy's circles.

    Separating the three strategies into three columns (rather than overlaying all
    three colours in one plot) is what makes the comparison legible — each column
    shows the single static circles you'd get if you picked that strategy, laid over
    the faint full sweep, so the eyeball compares columns instead of untangling
    overlapping circles.
    """
    surf = pygame.Surface(size)
    surf.fill(BG_COLOR)
    color = STRATEGY_COLOR[strategy]

    # Column header (the strategy name, in its colour).
    surf.blit(font.render(strategy.name, True, color), (8, 6))

    # Body origin (dx=dy=0) as a small cross — the fighter reference point.
    ox, oy = tx(0.0, 0.0)
    pygame.draw.line(surf, ORIGIN_COLOR, (ox - 6, oy), (ox + 6, oy), 1)
    pygame.draw.line(surf, ORIGIN_COLOR, (ox, oy - 6), (ox, oy + 6), 1)

    for hid, g in sorted(geometry.items()):
        # Faint full sweep (all active frames), path-linked; the box active on the
        # currently-shown reference frame is brightened so both panels move together.
        prev = None
        for idx, d in sorted(g["arc"].items()):
            cx, cy = tx(d.dx, d.dy)
            r = max(int(round(d.r * scale)), 1)
            bright = idx == highlight_frame
            pygame.draw.circle(surf, HIGHLIGHT_COLOR if bright else ARC_COLOR, (cx, cy), r, 2 if bright else 1)
            if prev is not None:
                pygame.draw.line(surf, ARC_COLOR, prev, (cx, cy), 1)
            prev = (cx, cy)

        # This strategy's single representative circle for the id.
        d = g["strat"][strategy]
        cx, cy = tx(d.dx, d.dy)
        r = max(int(round(d.r * scale)), 1)
        pygame.draw.circle(surf, color, (cx, cy), r, 2)
        pygame.draw.circle(surf, color, (cx, cy), 2)
        surf.blit(small.render(f"id{hid}", True, TEXT_COLOR), (cx + r + 2, cy - 6))

    surf.blit(small.render("pycats px (5.4 px/unit)", True, TEXT_COLOR), (8, size[1] - 16))
    return surf


def _surf_to_rgb(pygame, surf):
    """pygame Surface -> (H, W, 3) uint8 array for imageio."""
    import numpy as np

    arr = pygame.surfarray.array3d(surf)  # (W, H, 3)
    return np.transpose(arr, (1, 0, 2))


def build_frames(gif_path: Path, table: HitboxTable, move: str, plot_width: int | None):
    """Compose the side-by-side frames: [reference gif frame | synced plot]."""
    import imageio.v3 as iio
    import numpy as np
    import pygame

    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont(None, 20)
    small = pygame.font.SysFont(None, 16)

    gif = iio.imread(gif_path, index=None)  # (N, H, W, 3|4)
    gif = np.asarray(gif)
    if gif.ndim == 3:  # single frame -> add frame axis
        gif = gif[None, ...]
    n_frames, gh = gif.shape[0], gif.shape[1]
    gif = gif[..., :3]  # drop alpha if present

    geometry = collect_geometry(table)
    cw = plot_width or 240
    # One shared transform across all three columns so they are directly comparable.
    tx, scale = make_transform(geometry_bounds(geometry), cw, gh)
    sep = np.full((gh, 4, 3), (60, 60, 68), dtype=np.uint8)

    frames = []
    for i in range(n_frames):
        cols = [gif[i]]
        for s in RepresentativeFrame:
            col = _surf_to_rgb(pygame, _draw_column(pygame, (cw, gh), geometry, tx, scale, i, s, font, small))
            cols += [sep, col]
        row = np.concatenate(cols, axis=1)
        frames.append(_add_header(pygame, np, row, move, small))
    pygame.quit()
    return frames


def _add_header(pygame, np, row, move, small):
    """Stack a labelled header band (move name) atop the combined row."""
    w = row.shape[1]
    band = pygame.Surface((w, 22))
    band.fill(BG_COLOR)
    caption = f"{move}   —   reference (brawllib capsules + hitboxes) | representative-frame strategies"
    band.blit(small.render(caption, True, TEXT_COLOR), (8, 4))
    header = np.transpose(pygame.surfarray.array3d(band), (1, 0, 2))
    return np.concatenate([header, row], axis=0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gif", required=True, type=Path, help="reference GIF (left panel)")
    ap.add_argument("--datamine", required=True, type=Path, help="hitbox JSON for the move")
    ap.add_argument("--move", required=True, help="human label, e.g. 'u-smash (AttackHi4)'")
    ap.add_argument("--out", required=True, type=Path, help="output combined GIF")
    ap.add_argument("--fps", type=int, default=12, help="output frame rate (default 12)")
    ap.add_argument("--plot-width", type=int, default=None, help="plot panel width px")
    args = ap.parse_args(argv)

    import imageio.v3 as iio

    table = load_hitbox_table(args.datamine)
    frames = build_frames(args.gif, table, args.move, args.plot_width)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(args.out, frames, duration=1000 / max(args.fps, 1), loop=0)
    print(f"wrote {args.out}  ({len(frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
