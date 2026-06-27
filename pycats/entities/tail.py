# pycats/entities/tail.py
"""Verlet point-chain tail with secondary motion (#37).

The tail is a chain of point masses simulated with Verlet integration + Jakobsen
distance constraints (Thomas Jakobsen, "Advanced Character Physics", GDC 2001).
Velocity is implicit in (pos - prev_pos), so inertia, air-drag, trailing, whip on
direction changes, and gravity-settling all emerge from the integrator — there is
no hand-authored "follow" logic. The first two points are pinned to the hip (the
second gives the base a backward orientation); the rest swing freely.

Feel knobs live in config: TAIL_GRAVITY (weight), TAIL_AIR_DRAG (floppiness /
trailing), TAIL_CONSTRAINT_ITERS (stiffness).

Preserved from earlier work: the eased hip anchor across a facing flip (#3,
_get_tail_base_position) and the solid-platform floor clamp (#4/#37,
_resolve_platform_collisions). Rendering keeps the cached rotated-rect blit.
"""
import math
from typing import List, Tuple
import pygame as pg  # type: ignore

from ..config import (
    TAIL_SEGMENTS,
    TAIL_SEGMENT_LENGTH,
    TAIL_SEGMENT_WIDTH,
    TAIL_BASE_OFFSET_X,
    TAIL_BASE_OFFSET_Y,
    TAIL_ANCHOR_FLIP_STEP,
    TAIL_GRAVITY,
    TAIL_AIR_DRAG,
    TAIL_CONSTRAINT_ITERS,
    TAIL_CURL,
    TAIL_CURL_STRENGTH,
    TAIL_UNDULATE_AMP,
    TAIL_UNDULATE_SPEED,
    TAIL_UNDULATE_WAVELENGTH,
    TAPER_MODIFER,
)

# How many points at the root are pinned to the body. 1 = the tail dangles from a
# single hip point; 2 = the base also holds a backward orientation (more tail-like)
# while everything past it swings freely.
_PINNED = 2
# Per-frame ease of the base's backward direction across a facing flip (in units
# of the [-1, +1] direction), so the pinned base stub swings to the other side
# smoothly instead of snapping (companion to the #3 hip-anchor ease).
_BASE_TURN_STEP = 0.18


class TailSegment:
    """A single point mass in the Verlet chain (plus a cached draw angle)."""

    def __init__(self, x: float, y: float, angle: float = 0.0):
        self.x = x
        self.y = y
        self.prev_x = x          # Verlet: velocity is (pos - prev_pos)
        self.prev_y = y
        self.angle = angle       # rendering only — direction from the parent point


class Tail:
    """Multi-segment tail driven by Verlet integration (secondary motion)."""

    def __init__(self, player_ref):
        self.player = player_ref
        self.segments: List[TailSegment] = [
            TailSegment(0.0, 0.0) for _ in range(TAIL_SEGMENTS)
        ]
        self._seg_cache: dict = {}  # (width, angle°) -> rotated surface
        self.reset()

    def reset(self):
        """Initialize the tail to its rest layout at the current hip position with
        zero velocity. Called on first load AND on every respawn (#41), so a
        respawn appears exactly like a first load instead of whipping the live
        Verlet chain in from wherever it froze at KO."""
        # Eased horizontal anchor offset (#3): set straight to the facing target.
        self._anchor_offset_x = (
            -TAIL_BASE_OFFSET_X if self.player.fighter.facing_right else TAIL_BASE_OFFSET_X
        )
        # Eased backward direction (-1 tail points left / +1 right); eases across
        # a facing flip so the pinned base stub swings over smoothly (no snap).
        self._base_back = -1.0 if self.player.fighter.facing_right else 1.0
        # Undulation phase clock (#42) — keep it running across reset so the
        # wave doesn't visibly jump when a respawn re-lays the tail out.
        if not hasattr(self, "_t"):
            self._t = 0.0

        # Lay the chain out horizontally backward from the hip with zero velocity
        # (prev == pos) so it settles smoothly instead of snapping/whipping in.
        base_x, base_y = self._get_tail_base_position()
        back = self._base_back
        ang = math.pi if back < 0 else 0.0
        for i, seg in enumerate(self.segments):
            seg.x = base_x + back * TAIL_SEGMENT_LENGTH * i
            seg.y = base_y
            seg.prev_x, seg.prev_y = seg.x, seg.y
            seg.angle = ang

    # ---------------------------------------------------------------- update
    def update(self, platforms=None, dt: float = 1.0):
        """One Verlet step: pin root -> integrate free points -> satisfy length
        constraints -> resolve platform collisions -> compute draw angles.

        `platforms` is passed in (the owning fighter no longer stashes them; #77).
        """
        segs = self.segments
        n = len(segs)
        L = TAIL_SEGMENT_LENGTH
        base_x, base_y = self._get_tail_base_position()

        # Ease the base's backward direction toward the facing target so a turn
        # swings the base stub over smoothly rather than snapping it across.
        target_back = -1.0 if self.player.fighter.facing_right else 1.0
        if self._base_back < target_back:
            self._base_back = min(self._base_back + _BASE_TURN_STEP, target_back)
        elif self._base_back > target_back:
            self._base_back = max(self._base_back - _BASE_TURN_STEP, target_back)

        # 1) Pin the root point(s) to the body. The second pin sits one link
        #    "backward" (eased direction) to give the base an orientation.
        self._pin(segs[0], base_x, base_y)
        if n > 1 and _PINNED >= 2:
            self._pin(segs[1], base_x + self._base_back * L, base_y)

        # 2) Verlet integration of the free points: implicit velocity, air drag,
        #    gravity. This is where inertia / trailing / whip come from.
        for i in range(_PINNED, n):
            s = segs[i]
            vx = (s.x - s.prev_x) * TAIL_AIR_DRAG
            vy = (s.y - s.prev_y) * TAIL_AIR_DRAG
            s.prev_x, s.prev_y = s.x, s.y
            s.x += vx
            s.y += vy + TAIL_GRAVITY

        # 2b) Curl / expression (#42): nudge the free points toward a rest arc
        #     built in the cat's frame from the (eased) base direction — a gently
        #     up-curling pose, plus a traveling sine wave so the tail constantly
        #     undulates/snakes even when idle. The wave is applied perpendicular
        #     to the arc, tapers from ~0 at the base to full amplitude at the tip,
        #     and its phase travels down the length over time. Gravity/inertia
        #     still dominate (it trails on the move). Skipped when fully off.
        self._t += dt
        if TAIL_CURL_STRENGTH and (TAIL_CURL or TAIL_UNDULATE_AMP):
            ang0 = math.pi if self._base_back < 0 else 0.0
            rx, ry = base_x, base_y
            k = TAIL_CURL_STRENGTH
            for i in range(1, n):
                ang0 -= self._base_back * TAIL_CURL   # accumulate the per-link curl
                rx += math.cos(ang0) * L
                ry += math.sin(ang0) * L
                tx, ty = rx, ry
                if TAIL_UNDULATE_AMP:
                    # lateral wave, perpendicular to the current arc direction,
                    # growing toward the tip and travelling down the length.
                    wave = (TAIL_UNDULATE_AMP * (i / n)
                            * math.sin(self._t * TAIL_UNDULATE_SPEED
                                       - i * TAIL_UNDULATE_WAVELENGTH))
                    tx += -math.sin(ang0) * wave
                    ty += math.cos(ang0) * wave
                if i >= _PINNED:
                    s = segs[i]
                    s.x += (tx - s.x) * k
                    s.y += (ty - s.y) * k

        # 3) Jakobsen constraint relaxation: keep adjacent points one link apart.
        #    Pinned points act as infinite mass (never moved).
        for _ in range(TAIL_CONSTRAINT_ITERS):
            for i in range(1, n):
                a, b = segs[i - 1], segs[i]
                dx = b.x - a.x
                dy = b.y - a.y
                d = math.hypot(dx, dy) or 1e-6
                diff = (d - L) / d
                a_pinned = (i - 1) < _PINNED
                b_pinned = i < _PINNED
                if a_pinned and b_pinned:
                    continue
                elif a_pinned:
                    b.x -= dx * diff
                    b.y -= dy * diff
                elif b_pinned:
                    a.x += dx * diff
                    a.y += dy * diff
                else:
                    a.x += dx * 0.5 * diff
                    a.y += dy * 0.5 * diff
                    b.x -= dx * 0.5 * diff
                    b.y -= dy * 0.5 * diff

        # 4) Solid-platform collision (floor clamp; kills downward velocity).
        self._resolve_platform_collisions(platforms)

        # 5) Draw angles: each segment points from its parent.
        segs[0].angle = math.pi if self._base_back < 0 else 0.0
        for i in range(1, n):
            segs[i].angle = math.atan2(segs[i].y - segs[i - 1].y,
                                       segs[i].x - segs[i - 1].x)

    @staticmethod
    def _pin(seg: "TailSegment", x: float, y: float):
        seg.x, seg.y = x, y
        seg.prev_x, seg.prev_y = x, y  # pinned points carry no velocity

    def _get_tail_base_position(self) -> Tuple[float, float]:
        """Hip attachment point, with the facing-flip ease from #3."""
        target_offset = (
            TAIL_BASE_OFFSET_X if not self.player.fighter.facing_right else -TAIL_BASE_OFFSET_X
        )
        delta = target_offset - self._anchor_offset_x
        if delta > TAIL_ANCHOR_FLIP_STEP:
            delta = TAIL_ANCHOR_FLIP_STEP
        elif delta < -TAIL_ANCHOR_FLIP_STEP:
            delta = -TAIL_ANCHOR_FLIP_STEP
        self._anchor_offset_x += delta
        base_x = self.player.rect.centerx + self._anchor_offset_x
        base_y = self.player.rect.bottom - TAIL_BASE_OFFSET_Y
        return base_x, base_y

    def _resolve_platform_collisions(self, platforms):
        """Issue #4/#37: rest the tail on SOLID (thick) platforms — no clipping.

        Within a thick platform's horizontal footprint, clamp seg.y to the top
        surface (a floor clamp, robust to a fast point overshooting past a thin
        platform in one step) and zero the segment's vertical velocity so it
        rests instead of jittering. Thin platforms stay pass-through.
        """
        if not platforms:
            return
        for plat in platforms:
            if getattr(plat, "thin", False):
                continue
            r = plat.rect
            left, right, top = r.left, r.right, r.top
            for seg in self.segments:
                if left <= seg.x <= right and seg.y > top:
                    seg.y = top
                    seg.prev_y = top  # kill downward velocity -> rests on surface

    def draw(self, screen):
        """Draw the segments as cached, rotated, tapering rects."""
        # #109: the tail flashes with the body. `tinted` softens char_color ~50%
        # toward the active hurt/stun/dodge flash (or leaves it unchanged), from
        # the same single source as the body composite. Local import avoids the
        # render_battle → entities.Player import cycle.
        from ..render_battle import tinted
        cache = self._seg_cache
        color = tuple(tinted(self.player.char_color, self.player))
        length = TAIL_SEGMENT_LENGTH
        n = len(self.segments)
        blit = screen.blit
        for i, segment in enumerate(self.segments):
            width = int(TAIL_SEGMENT_WIDTH * (1.0 - (i / n) * TAPER_MODIFER))
            deg = int(round(-math.degrees(segment.angle))) % 360
            # `color` is in the key so a flash doesn't serve stale untinted
            # segment surfaces (the cache spans tint states across frames).
            key = (width, deg, color)
            surf = cache.get(key)
            if surf is None:
                base = pg.Surface((length, width), pg.SRCALPHA)
                base.fill(color)
                surf = pg.transform.rotate(base, deg)
                cache[key] = surf
            rect = surf.get_rect()
            rect.center = (int(segment.x), int(segment.y))
            blit(surf, rect)
