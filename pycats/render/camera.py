# pycats/render/camera.py
"""THROWAWAY follow+zoom camera prototype (#1315) — do NOT productionize as-is.

Ratified experiment spec: docs/design/camera-prototype-experiment-spec.md (#1308).
This exists only so a human can play-test a moving camera and give a go/no-go on
#1304 Q1 (does pycats build a moving camera for v1, or stay fixed?). It is default
OFF; when off, nothing here runs and the battle renders byte-for-byte as today.

Mechanism (the spec's "cheap oversized-surface transform"): render the whole
extended world onto one oversized surface at a constant positive BASE offset
(so blast-zone room to the left/top maps to positive pixels), then crop the
camera's view sub-rectangle and scale it to the 960x540 window. No (scale, offset)
is threaded through the inner draw primitives — the world-draw entry points take a
single `offset`, default (0, 0) = identity.

The framer is the ratified IN scope: fighters' bounding box · flat margin ·
zoom-to-fit + zoom-in/out clamps · pan-to-center · per-frame lerp smoothing. The
per-count weight table and the magnifying-glass edge bubble are OUT (a launched cat
just shrinks off-frame until KO). Feel constants below are by-feel throwaway values
— the experiment answers go/no-go on the CONCEPT, not final numbers.
"""

import pygame

from ..config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH

# --- extended world bounds (throwaway) --------------------------------------
# Room for the camera to follow a launched fighter into, matching the on-branch
# world-bound hack in Fighter._outside_blast_zone (~848 side / 745 top / 486
# bottom). Padded a little beyond the KO lines so the surface never runs out.
_PAD_X = 900
_PAD_TOP = 800
_PAD_BOTTOM = 560
_BASE_X = _PAD_X  # world x=0 -> surface x=_BASE_X (so world x=-_PAD_X -> 0)
_BASE_Y = _PAD_TOP
_EXT_W = SCREEN_WIDTH + 2 * _PAD_X
_EXT_H = SCREEN_HEIGHT + _PAD_TOP + _PAD_BOTTOM
BASE_OFFSET = (_BASE_X, _BASE_Y)

# --- framer feel (throwaway, by-feel) ---------------------------------------
_MARGIN = 190  # world-px padding around the fighters' box before fitting
_SCALE_MAX = 1.8  # zoom-IN floor: never magnify past this (fighters very close)
_SCALE_MIN = 0.55  # zoom-OUT ceiling: never shrink past this (blast lines stay hidden)
# Per-frame ease toward the target (0..1; lower = slower + more perceived delay/lag,
# since an exponential ease-out lags its target). Zoom eases a touch slower than pan
# so the zoom trails the pan slightly (#1315 feedback: "slower, with a little delay").
_PAN_LERP = 0.07
_ZOOM_LERP = 0.05


class Camera:
    """Auto follow+zoom framer + oversized-surface transform. One per battle."""

    def __init__(self):
        # View center (world coords) + scale (screen px per world px). Start at the
        # base view so the first frame after toggle-on eases out from identity.
        self.cx = SCREEN_WIDTH / 2
        self.cy = SCREEN_HEIGHT / 2
        self.scale = 1.0
        self._world_surf = None  # allocated lazily on first render (needs pygame)

    def _target(self, players):
        """Desired (cx, cy, scale) framing the alive fighters' box + margin, with the
        zoom clamped to [_SCALE_MIN, _SCALE_MAX] and the center clamped so the view
        never reveals beyond the extended world bounds."""
        alive = [p for p in players if p.fighter.is_alive]
        if not alive:
            return self.cx, self.cy, self.scale  # nothing to frame — hold
        minx = min(p.rect.left for p in alive)
        maxx = max(p.rect.right for p in alive)
        miny = min(p.rect.top for p in alive)
        maxy = max(p.rect.bottom for p in alive)
        bw = (maxx - minx) + 2 * _MARGIN
        bh = (maxy - miny) + 2 * _MARGIN
        s = min(SCREEN_WIDTH / bw, SCREEN_HEIGHT / bh)
        s = max(_SCALE_MIN, min(_SCALE_MAX, s))
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        # Clamp center so the [cx±half] view stays inside [-_PAD, SCREEN+_PAD].
        half_w = SCREEN_WIDTH / (2 * s)
        half_h = SCREEN_HEIGHT / (2 * s)
        lo_x, hi_x = -_PAD_X + half_w, SCREEN_WIDTH + _PAD_X - half_w
        lo_y, hi_y = -_PAD_TOP + half_h, SCREEN_HEIGHT + _PAD_BOTTOM - half_h
        if lo_x <= hi_x:
            cx = max(lo_x, min(hi_x, cx))
        if lo_y <= hi_y:
            cy = max(lo_y, min(hi_y, cy))
        return cx, cy, s

    def update(self, players):
        """Ease the live (cx, cy, scale) toward the target framing (pan + zoom lerp)."""
        tcx, tcy, ts = self._target(players)
        self.cx += (tcx - self.cx) * _PAN_LERP
        self.cy += (tcy - self.cy) * _PAN_LERP
        self.scale += (ts - self.scale) * _ZOOM_LERP

    def render_world(self, surface, players, platforms, attacks):
        """Render the camera-transformed world (platforms + fighters + attacks) onto
        `surface` (the 960x540 window). HUD/overlays are the caller's job, drawn in
        screen space AFTER this so they are not warped by the camera."""
        # Import here (not at module load) to avoid a render<->camera import cycle.
        from .battle import render_attacks, render_battle

        if self._world_surf is None:
            self._world_surf = pygame.Surface((_EXT_W, _EXT_H))
        world = self._world_surf
        world.fill(BG_COLOR)
        render_battle(world, players, platforms, offset=BASE_OFFSET)
        render_attacks(world, attacks, offset=BASE_OFFSET)

        # The camera view rect in world coords -> surface (add BASE), clamped to the
        # oversized surface so subsurface() never raises at the bounds.
        half_w = SCREEN_WIDTH / (2 * self.scale)
        half_h = SCREEN_HEIGHT / (2 * self.scale)
        src_w = int(round(SCREEN_WIDTH / self.scale))
        src_h = int(round(SCREEN_HEIGHT / self.scale))
        src_x = int(round((self.cx - half_w) + _BASE_X))
        src_y = int(round((self.cy - half_h) + _BASE_Y))
        src_x = max(0, min(_EXT_W - src_w, src_x))
        src_y = max(0, min(_EXT_H - src_h, src_y))
        src_w = min(src_w, _EXT_W - src_x)
        src_h = min(src_h, _EXT_H - src_y)
        view = world.subsurface((src_x, src_y, src_w, src_h))
        pygame.transform.scale(view, (SCREEN_WIDTH, SCREEN_HEIGHT), surface)
