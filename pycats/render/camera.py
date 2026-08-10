# pycats/render/camera.py
"""Auto follow+zoom battle camera (ADR-0023, #1304) — ported from the felt-approved
#1315 prototype by #1339.

Presentation-only: the camera never perturbs the sim, KO, or determinism (ADR-0023
Q5). It is default OFF; when off, nothing here runs and the battle renders
byte-for-byte as today (the world-draw seam is called with offset (0, 0) = identity).
`App` flips `BattleScreen.camera_on` on the `K` key.

Mechanism (the #1308 spec's "cheap oversized-surface transform"): render the whole
extended world onto one oversized surface at a constant positive BASE offset (so
blast-zone room to the left/top maps to positive pixels), then crop the camera's view
sub-rectangle and scale it to the 960x540 window. No (scale, offset) is threaded
through the inner draw primitives — the shared world-draw seam (`render.battle.
render_world`) takes a single `offset`, default (0, 0) = identity, so the camera and
the fixed view share one draw path (no camera-specific fork).

The framer is the ratified IN scope: fighters' bounding box · flat margin · zoom-to-fit
+ zoom-in/out clamps · pan-to-center · per-frame lerp smoothing. The per-count weight
table and the off-screen magnifying-glass edge bubble are OUT (D8/#734; a launched cat
just shrinks off-frame until KO).

Zone model (sourced, #790 datamine of PM 3.6 FD): two per-stage boxes. **CamLimit**
(inner) is the camera's pan-limit — the camera clamps to it, so the stage stays framed
and the blast lines never show (this is what makes "stage always visible" fall out for
free, PM-faithful). **Dead** (outer) is the KO boundary (== the interim wide-blast
scaffold in `entities.fighter.EXPERIMENTAL_WIDE_BLAST`). Between them is the off-screen
/ magnifying-glass band. The `--dev` overlay draws both boxes as outline-only rects on
the background AND relaxes the camera clamp from CamLimit to Dead, so all three zones
are visible for eyeballing.

Scope not yet landed (downstream of #1339, tracked by EPIC #1340): the CamLimit/Dead
boxes live here as module constants, not yet per-`Stage` (D6, #790/#661); the feel
constants below are literals, not yet registered in `provenance.py`/`config` (D7,
#1331); the KO decouple to world coords replaces the wide-blast scaffold (D5, #789).
"""

import pygame

from ..config import BG_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH

# --- sourced zone boxes (#790, PM 3.6 FD at PX_PER_UNIT 5.4) -----------------
# (left, top, right, bottom) screen/world-px rects centered on the 960x540 resting
# view. Beyond each screen edge: CamLimit +438 / +346 top / +162 bottom; Dead
# +848 / +745 top / +486 bottom (Dead == the fighter.EXPERIMENTAL_WIDE_BLAST scaffold).
# Both derived from #790's CamLimit (±170, +114/-80) and Dead (±246, +188/-140)
# units × 5.4 px/unit, mapped onto the screen.
_CAMLIMIT_BOX = (-438, -346, SCREEN_WIDTH + 438, SCREEN_HEIGHT + 162)  # 1836 x 1048
_DEAD_BOX = (-848, -745, SCREEN_WIDTH + 848, SCREEN_HEIGHT + 486)  # 2656 x 1771
_CAMLIMIT_COLOR = (255, 220, 80)  # yellow — camera pan-limit / on-screen line
_DEAD_COLOR = (255, 60, 60)  # red — KO / blast line
_ZONE_OUTLINE_W = 3  # outline-only rect stroke width (px, world space)

# --- oversized-surface bounds -----------------------------------------------
# Cover the Dead box + a little headroom (outline stroke + max dev zoom-out slack)
# so the overlay and the widest view never run off the surface.
_PAD_X = 980
_PAD_TOP = 820
_PAD_BOTTOM = 620
_BASE_X = _PAD_X  # world x=0 -> surface x=_BASE_X (so world x=-_PAD_X -> 0)
_BASE_Y = _PAD_TOP
_EXT_W = SCREEN_WIDTH + 2 * _PAD_X
_EXT_H = SCREEN_HEIGHT + _PAD_TOP + _PAD_BOTTOM
BASE_OFFSET = (_BASE_X, _BASE_Y)

# --- framer feel (CUSTOM / non-sourced, ratified #1331) ---------------------
# These are by-feel values from the #1315 play-test, ratified as the v1 camera feel at
# #1331: zoom-in cap 1.8×, pan lerp 0.07, zoom lerp 0.05, zoom-trailing-pan on. PM feel
# has no primary source (#1279), so they are TUNED-custom, NOT FOUND — revisit if/when
# accurate values are sourced. The zoom-OUT ceiling is the exception: it is DERIVED from
# the clamp box (_fit_scale), not guessed. Formal FOUND/TUNED registration in
# provenance.py + config is D7 (#1331), downstream of this port — see the module docstring.
_MARGIN = 190  # world-px padding around the fighters' box before fitting
_SCALE_MAX = 1.8  # zoom-IN floor: never magnify past this (fighters very close)
# Per-frame ease toward the target (0..1; lower = slower + more perceived delay/lag,
# since an exponential ease-out lags its target). Zoom eases a touch slower than pan
# so the zoom trails the pan slightly (#1315 feedback: "slower, with a little delay").
_PAN_LERP = 0.07
_ZOOM_LERP = 0.05


def _fit_scale(box):
    """The zoom at which the 960x540 view exactly fills `box` — the zoom-OUT ceiling
    for that clamp box. Screen / box size, taking the tighter (larger-scale) dimension
    so the view never exceeds the box."""
    left, top, right, bottom = box
    return max(SCREEN_WIDTH / (right - left), SCREEN_HEIGHT / (bottom - top))


class Camera:
    """Auto follow+zoom framer + oversized-surface transform. One per battle."""

    def __init__(self):
        # View center (world coords) + scale (screen px per world px). Start at the
        # base view so the first frame after toggle-on eases out from identity.
        self.cx = SCREEN_WIDTH / 2
        self.cy = SCREEN_HEIGHT / 2
        self.scale = 1.0
        # Set each frame from runtime_settings.dev_mode() by the caller. When True:
        # draw the zone overlay AND clamp to the wider Dead box (see all three zones);
        # when False: clamp to CamLimit (the PM-faithful, stage-always-visible feel).
        self.dev_overlay = False
        self._world_surf = None  # allocated lazily on first render (needs pygame)

    def _clamp_box(self):
        """The box the camera pan + zoom-out clamp to: Dead when the dev overlay is on
        (so both zone rects are reachable/visible), else CamLimit (PM-faithful feel)."""
        return _DEAD_BOX if self.dev_overlay else _CAMLIMIT_BOX

    def _target(self, players):
        """Desired (cx, cy, scale) framing the alive fighters' box + margin, zoom
        clamped to [fit-the-clamp-box, _SCALE_MAX] and the center clamped so the view
        stays inside the clamp box (CamLimit or Dead) — so the stage never leaves frame."""
        box = self._clamp_box()
        scale_min = _fit_scale(box)
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
        s = max(scale_min, min(_SCALE_MAX, s))
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        # Clamp center so the [c ± half-view] rect stays inside the clamp box. If the
        # view is larger than the box on an axis (can't normally happen at scale_min),
        # center on the box on that axis.
        left, top, right, bottom = box
        half_w = SCREEN_WIDTH / (2 * s)
        half_h = SCREEN_HEIGHT / (2 * s)
        lo_x, hi_x = left + half_w, right - half_w
        lo_y, hi_y = top + half_h, bottom - half_h
        cx = max(lo_x, min(hi_x, cx)) if lo_x <= hi_x else (left + right) / 2
        cy = max(lo_y, min(hi_y, cy)) if lo_y <= hi_y else (top + bottom) / 2
        return cx, cy, s

    def update(self, players):
        """Ease the live (cx, cy, scale) toward the target framing (pan + zoom lerp)."""
        tcx, tcy, ts = self._target(players)
        self.cx += (tcx - self.cx) * _PAN_LERP
        self.cy += (tcy - self.cy) * _PAN_LERP
        self.scale += (ts - self.scale) * _ZOOM_LERP

    def _draw_zones(self, surface):
        """Draw the CamLimit (inner) + Dead (outer) boxes as outline-only rects on the
        background (behind the fighters), shifted by BASE like the rest of the world.
        Dev-only; the caller gates this on runtime_settings.dev_mode()."""
        ox, oy = BASE_OFFSET
        for box, color in ((_DEAD_BOX, _DEAD_COLOR), (_CAMLIMIT_BOX, _CAMLIMIT_COLOR)):
            left, top, right, bottom = box
            pygame.draw.rect(surface, color, (left + ox, top + oy, right - left, bottom - top), _ZONE_OUTLINE_W)

    def render_world(self, surface, players, platforms, attacks):
        """Render the camera-transformed world (zone overlay + platforms + fighters +
        attacks) onto `surface` (the 960x540 window). HUD is the caller's job, drawn in
        screen space AFTER this so it is not warped by the camera."""
        # Import here (not at module load) to avoid a render<->camera import cycle; the
        # shared seam (#1339 D1) is the SAME entry the fixed view calls, just onto the
        # oversized surface at BASE_OFFSET — one world-draw path, no camera fork.
        from .battle import render_world as draw_world_seam

        if self._world_surf is None:
            self._world_surf = pygame.Surface((_EXT_W, _EXT_H))
        world = self._world_surf
        world.fill(BG_COLOR)
        if self.dev_overlay:
            self._draw_zones(world)  # on the background, behind the fighters
        draw_world_seam(world, players, platforms, attacks, offset=BASE_OFFSET)

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
