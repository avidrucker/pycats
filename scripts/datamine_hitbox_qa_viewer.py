#!/usr/bin/env python3
"""Interactive QA viewer: authored hitboxes vs datamine ground truth, per frame (#1278).

One pygame window superimposes, in the SAME pycats-px space, two layers for one move:

    - DATAMINE (ground truth): every box the datamine says is live THIS frame, drawn
      at its own per-frame world position (it MOVES across the window).
    - AUTHORED (cat data): the static Circle(s) whose [active_start, active_end] window
      covers this frame — what the shipped fighter actually spawns.

You step frame-by-frame and eyeball whether the authored circles LOCATE and COVER every
datamine box. Where #1217 reduced a moving datamined box to one representative circle and
compared three reduction rules, this shows all the datamine frames directly and sidesteps
the reduction question — the eyeball answers "does the authored data cover every frame's
box", not "which single frame best represents the sweep".

Frame mapping (resolve + document, don't fudge). The datamine dump is 0-based animation-
frame indices; a pycats Hitbox window is in 1-based MoveClock frames. Empirically, across
nalio usmash/fair/dsmash the authored active_start is exactly the datamine first-active
index + 1 (and jab's implicit window agrees), and both describe the same move starting at
the same instant. So the correspondence is a clean 1:1 index shift:

    MoveClock frame  =  datamine frame index + 1

anchored at a shared move-start (datamine frame 0 <-> MoveClock frame 1). There is no extra
startup offset; the "+1" is purely 0-based vs 1-based. The HUD prints both numbers.

Coordinate anchor (why the two layers actually line up). The pycats Circle offset (dx, dy)
is measured from the fighter's RECT TOP-LEFT (entities/attack.py: hitboxes resolve "using
the owner's rect top-left as origin"), and the rect is placed by its MIDBOTTOM at the feet
(entities/fighter.py `with_midbottom`). Brawl's datamine world origin, by contrast, is the
character ROOT — the feet-centre on the ground (world y is positive-UP from there). So the
two spaces share a SCALE (both go through units.u(); datamine radii equal authored radii to
the pixel) but NOT an origin: a raw `_circle_from_world` box lands ~a body-height too high
(a down-smash converts to ABOVE the head). This viewer therefore ANCHORS the datamine layer
by the fighter's feet-centre in Circle coords — the rect midbottom `(w/2, h)` from
`stand_size or config.PLAYER_SIZE` (nalio: (20, 60)). That is a PRINCIPLED frame alignment
(feet-centre -> feet-centre), derived from the fighter, not a hand-tuned nudge. Press `o`
to toggle it off and see the raw propose()-space offset for yourself.

    The raw offset is a property of `_circle_from_world` / `propose()` — it hands the editor
    candidates that need this same feet-centre anchor (plus a residual forward position-scale
    over-projection). Confirming/quantifying that gap and deciding where the anchor belongs is
    tracked as RESEARCH #1294 (related: #120/#195/#782); this viewer only visualises it and
    applies the anchor for display.

This is QA TOOLING, not game code: it reads existing cat data + a committed datamine fixture
and draws them. It never writes cat data and never touches the datamine schema. Eyeball-
gated (a human runs it); there is no numeric pass/fail.

Usage:
    scripts/datamine_hitbox_qa_viewer.py \
        pycats/characters/data/nalio.json \
        tests/fixtures/datamine/mario_attackhi4_hitboxes.json \
        usmash

Keys:  <- / -> step (pauses) · space play/pause · d datamine · a authored · b body ·
       o toggle feet-centre anchor · esc quit.

Dependencies: pygame-ce (declared runtime). No new dependency.
"""

# NOTE: deliberately NO `from __future__ import annotations`. Under PEP 563 the
# dataclass fields below become string annotations, and dataclass resolves them via
# `sys.modules[cls.__module__]` at class-creation — which is absent when this script
# is imported unregistered (as tests/test_scripts_import.py does), reddening that
# guard. Real (non-string) annotations sidestep that path; this script has no forward
# references that would need PEP 563.

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# pycats package import when run from a checkout without install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycats import config  # noqa: E402
from pycats.combat.data import _fighter_from_json  # noqa: E402
from pycats.combat.datamine_hitboxes import load_hitbox_table  # noqa: E402
from pycats.combat.datamine_proposer import _circle_from_world  # noqa: E402

# --- palette -----------------------------------------------------------------
BG_COLOR = (24, 26, 32)
ORIGIN_COLOR = (120, 120, 128)  # fighter body origin (rect top-left, dx=dy=0)
BODY_COLOR = (90, 92, 100)  # faint body rect + hurtbox context
DATAMINE_COLOR = (250, 235, 120)  # ground truth (moves per frame)
AUTHORED_COLOR = (120, 190, 255)  # shipped cat data (static window circles)
TEXT_COLOR = (225, 225, 230)
DIM_TEXT_COLOR = (150, 150, 158)
WIDTH, HEIGHT = 900, 700
MARGIN = 60
TOP = 132  # HUD text band height; the plot fits below this


@dataclass(frozen=True)
class Dot:
    """One circle to plot in pycats px: centre (dx, dy) and radius r, plus its label."""

    dx: float
    dy: float
    r: float
    label: str


def datamine_layer(table):
    """{datamine frame index -> [Dot, ...]} — every box live that frame, RAW px.

    Raw = straight `_circle_from_world` (the exact seam `propose()` uses), so dy = -u(y)
    with no origin translation. `run()` applies the feet-centre anchor at draw time; the
    dots here are in propose()-space so the anchor can be toggled off to show it.
    Frames with no live box map to [].
    """
    out = {}
    for frame in table.frames:
        out[frame.index] = [
            Dot(c.dx, c.dy, c.r, f"id{box.hitbox_id}")
            for box in frame.boxes
            for c in (_circle_from_world(box.pos[2], box.pos[1], box.size),)
        ]
    return out


@dataclass(frozen=True)
class AuthoredBox:
    """One authored hitbox: its static Circle as a Dot + its resolved MoveClock window."""

    dot: Dot
    start: int  # inclusive MoveClock start frame
    end: int  # inclusive MoveClock end frame


def authored_boxes(move):
    """The move's hitboxes as static Dots with resolved [start, end] MoveClock windows.

    A hitbox with an explicit `[active_start, active_end]` (#204) uses it verbatim. A
    hitbox that leaves the window unset is live for the move's default active span,
    which in MoveClock coordinates is `[startup + 1, startup + active]` (frame 1 is the
    first startup frame; the active window opens right after startup).
    """
    default_start = move.startup + 1
    default_end = move.startup + move.active
    out = []
    for i, hb in enumerate(move.hitboxes):
        start = hb.active_start if hb.active_start is not None else default_start
        end = hb.active_end if hb.active_end is not None else default_end
        out.append(AuthoredBox(Dot(hb.circle.dx, hb.circle.dy, hb.circle.r, f"hb{i}"), start, end))
    return out


def feet_centre_anchor(fd):
    """The fighter's feet-centre in Circle (rect-top-left) coords: `(w/2, h)`.

    Circle offsets are measured from the rect top-left and the rect is placed by its
    midbottom at the feet, so the feet-centre — which is Brawl's datamine world origin —
    sits at the rect midbottom `(w/2, h)`. `w, h` come from the fighter's own
    `stand_size`, or `config.PLAYER_SIZE` when it has none (nalio: (40, 60) -> (20, 60)).
    """
    w, h = fd.stand_size or config.PLAYER_SIZE
    return (w / 2.0, float(h))


def body_dots(fd):
    """The standing hurtbox circles as grey context Dots (unlabelled)."""
    return [Dot(c.dx, c.dy, c.r, "") for c in fd.hurtbox.circles]


def compute_bounds(anchored_dm, auth, body, rect_wh):
    """(min_x, min_y, max_x, max_y) enclosing the ANCHORED datamine + authored + body.

    Fit to the anchored (correct-frame) view + the body rect so the default overlay is
    tight; toggling the anchor OFF may push the raw datamine above the top — that is the
    instructive "raw floats high" state, not a clip bug. Includes each circle's radius and
    the rect corners so nothing central is cut.
    """
    w, h = rect_wh
    xs = [0.0, w]
    ys = [0.0, h]
    dots = list(anchored_dm) + [b.dot for b in auth] + list(body)
    for d in dots:
        xs += [d.dx - d.r, d.dx + d.r]
        ys += [d.dy - d.r, d.dy + d.r]
    return min(xs), min(ys), max(xs), max(ys)


def make_transform(bounds, width, height, top, margin):
    """px -> (screen_x, screen_y), isotropic + centred, fitting `bounds` below `top`.

    One scale for both axes (circles stay circular). pycats screen convention is kept:
    +dx is right, +dy is DOWN, so this is a pure positive scale + translate (no y flip).
    """
    min_x, min_y, max_x, max_y = bounds
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    avail_w = max(width - 2 * margin, 1)
    avail_h = max(height - top - margin, 1)
    scale = min(avail_w / span_x, avail_h / span_y)
    off_x = margin + (avail_w - span_x * scale) / 2.0
    off_y = top + (avail_h - span_y * scale) / 2.0

    def tx(dx, dy):
        return (int(round(off_x + (dx - min_x) * scale)), int(round(off_y + (dy - min_y) * scale)))

    return tx, scale


def _draw_circle(pygame, surf, color, tx, scale, d, font, width=2):
    cx, cy = tx(d.dx, d.dy)
    r = max(int(round(d.r * scale)), 1)
    pygame.draw.circle(surf, color, (cx, cy), r, width)
    pygame.draw.circle(surf, color, (cx, cy), 2)  # centre pip
    if d.label:
        surf.blit(font.render(d.label, True, color), (cx + r + 3, cy - 7))


def run(cat_path, datamine_path, move_key, fps):
    import pygame

    table = load_hitbox_table(datamine_path)
    fd = _fighter_from_json(json.loads(cat_path.read_text()))
    if move_key not in fd.moves:
        print(f"move {move_key!r} not in {cat_path.name}; available: {sorted(fd.moves)}", file=sys.stderr)
        return 2
    move = fd.moves[move_key]

    dm = datamine_layer(table)
    auth = authored_boxes(move)
    body = body_dots(fd)
    ax, ay = feet_centre_anchor(fd)
    rect_wh = fd.stand_size or config.PLAYER_SIZE
    total = move.startup + move.active + move.recovery
    frame_count = table.frame_count
    if not auth and not any(dm.values()):
        print(f"move {move_key!r} has no authored hitboxes and no datamine boxes — nothing to show", file=sys.stderr)
        return 2

    # Bounds fit the anchored view (every frame's datamine, feet-centre shifted) + body.
    anchored_all = [Dot(d.dx + ax, d.dy + ay, d.r, d.label) for dots in dm.values() for d in dots]
    bounds = compute_bounds(anchored_all, auth, body, rect_wh)
    tx, scale = make_transform(bounds, WIDTH, HEIGHT, TOP, MARGIN)

    pygame.init()
    pygame.display.set_caption(f"hitbox QA — {table.fighter} {table.subaction} / {move_key}")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    hud = pygame.font.SysFont("monospace", 15)
    small = pygame.font.SysFont("monospace", 13)

    frame_i = 0  # 0-based datamine index (the ground-truth timeline)
    playing = False
    show_dm = True
    show_auth = True
    show_body = True
    anchored = True  # feet-centre anchor ON = the correct overlay
    tick_accum = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_RIGHT:
                    playing = False
                    frame_i = (frame_i + 1) % frame_count
                elif event.key == pygame.K_LEFT:
                    playing = False
                    frame_i = (frame_i - 1) % frame_count
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                    tick_accum = 0.0
                elif event.key == pygame.K_d:
                    show_dm = not show_dm
                elif event.key == pygame.K_a:
                    show_auth = not show_auth
                elif event.key == pygame.K_b:
                    show_body = not show_body
                elif event.key == pygame.K_o:
                    anchored = not anchored

        if playing:
            tick_accum += dt
            step = 1.0 / max(fps, 1)
            while tick_accum >= step:
                tick_accum -= step
                frame_i = (frame_i + 1) % frame_count

        mc_frame = frame_i + 1  # MoveClock frame = datamine index + 1
        shift = (ax, ay) if anchored else (0.0, 0.0)
        dm_dots = [Dot(d.dx + shift[0], d.dy + shift[1], d.r, d.label) for d in dm.get(frame_i, [])]
        live_auth = [b for b in auth if b.start <= mc_frame <= b.end]

        screen.fill(BG_COLOR)

        # Body context: rect outline (feet at the bottom edge) + hurtbox circles + origin.
        if show_body:
            x0, y0 = tx(0.0, 0.0)
            x1, y1 = tx(rect_wh[0], rect_wh[1])
            pygame.draw.rect(screen, BODY_COLOR, pygame.Rect(x0, y0, x1 - x0, y1 - y0), 1)
            for d in body:
                _draw_circle(pygame, screen, BODY_COLOR, tx, scale, d, small, width=1)
            fx, fy = tx(ax, ay)  # feet-centre marker (where the datamine origin anchors)
            pygame.draw.line(screen, BODY_COLOR, (fx - 6, fy), (fx + 6, fy), 1)
        ox, oy = tx(0.0, 0.0)  # rect-top-left origin cross (dx=dy=0)
        pygame.draw.line(screen, ORIGIN_COLOR, (ox - 7, oy), (ox + 7, oy), 1)
        pygame.draw.line(screen, ORIGIN_COLOR, (ox, oy - 7), (ox, oy + 7), 1)

        if show_dm:
            for d in dm_dots:
                _draw_circle(pygame, screen, DATAMINE_COLOR, tx, scale, d, small)
        if show_auth:
            for b in live_auth:
                _draw_circle(pygame, screen, AUTHORED_COLOR, tx, scale, b.dot, small)

        # --- HUD ---------------------------------------------------------------
        state = "PLAY" if playing else "PAUSE"
        line1 = f"datamine frame {frame_i}/{frame_count - 1}   MoveClock frame {mc_frame}/{total}   [{state}]"
        line2 = "map: MoveClock = datamine idx + 1   (0-based dump -> 1-based clock; move-start shared)"
        if anchored:
            line3 = f"[o] anchor: feet-centre ON  (datamine shifted by rect midbottom {int(ax)},{int(ay)})"
        else:
            line3 = "[o] anchor: OFF — RAW propose() space (datamine floats ~a body-height high)"
        dm_state = "on" if show_dm else "OFF"
        au_state = "on" if show_auth else "OFF"
        bd_state = "on" if show_body else "OFF"
        dm_ids = ",".join(d.label for d in dm_dots) or "-"
        au_ids = ",".join(b.dot.label for b in live_auth) or "-"
        line5 = "<- / -> step   space play/pause   [d][a][b] layers   [o] anchor   esc quit"
        screen.blit(hud.render(line1, True, TEXT_COLOR), (12, 10))
        screen.blit(small.render(line2, True, DIM_TEXT_COLOR), (12, 34))
        screen.blit(small.render(line3, True, TEXT_COLOR), (12, 54))
        screen.blit(small.render("[d] datamine", True, DATAMINE_COLOR), (12, 76))
        screen.blit(small.render(f"({dm_state}): {dm_ids}", True, TEXT_COLOR), (120, 76))
        screen.blit(small.render("[a] authored", True, AUTHORED_COLOR), (12, 94))
        screen.blit(small.render(f"({au_state}): {au_ids}", True, TEXT_COLOR), (120, 94))
        screen.blit(small.render(f"[b] body ({bd_state})", True, BODY_COLOR), (12, 112))
        screen.blit(small.render(line5, True, DIM_TEXT_COLOR), (300, 112))

        pygame.display.flip()

    pygame.quit()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Interactive datamine-vs-authored hitbox QA viewer (#1278).")
    p.add_argument("cat_data", type=Path, help="path to a cat data JSON (e.g. pycats/characters/data/nalio.json)")
    p.add_argument("datamine", type=Path, help="path to a datamine hitbox fixture JSON")
    p.add_argument("move_key", help="move key to view (e.g. usmash, jab, fair, dsmash)")
    p.add_argument("--fps", type=int, default=6, help="playback speed when playing (default 6)")
    args = p.parse_args(argv)
    return run(args.cat_data, args.datamine, args.move_key, args.fps)


if __name__ == "__main__":
    raise SystemExit(main())
