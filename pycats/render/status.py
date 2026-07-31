# pycats/render/status.py
"""Above-head status feedback drawing (#12/#111/#340/#657): the dizzy-star halo,
the stacked timer bars, and the grabs-left dot row. The *shapes* to draw come
from the pure model (`systems.status_model.timer_bar_specs` / `grabs_left_dots`);
this module only paints them.

Extracted verbatim from render_battle (#900, child 3 of #833). Cosmetic (not
golden-snapshotted), byte-identical to the pre-#900 draws.
"""

import math

import pygame

from .. import text_utils
from ..config import (
    EAR_HEIGHT,
    PLAYER_SIZE,
    STATUS_BAR_LABEL_SIZE,
    STATUS_BAR_SECONDS_SIZE,
    WHITE,
    YELLOW,
)
from ..systems.status_model import INTANGIBLE_BAR_COLOR

# Dizzy stars drawn above a shield-broken (#12) fighter's head. Cosmetic only
# (rendering is not golden-snapshotted), so these live here in the renderer.
DIZZY_STAR_COUNT = 3  # stars orbiting the head
DIZZY_ORBIT_RADIUS = 16  # horizontal orbit radius (px)
DIZZY_ORBIT_LIFT = 8  # gap above the ear tips
DIZZY_STAR_OUTER = 5  # star spike radius
DIZZY_STAR_INNER = 2  # star inner radius
DIZZY_SPIN_SPEED = 0.18  # radians of orbit advance per frame (per stun tick)
DIZZY_STAR_POINTS = 5  # spikes per orbiting star
DIZZY_ELLIPSE_FLATTEN = 0.4  # vertical-squash of the orbit (circle → head-hugging ellipse)


def _star_points(cx, cy, outer, inner, points, rot):
    """Vertices of a `points`-pointed star centred at (cx, cy), rotated `rot`."""
    pts = []
    for k in range(points * 2):
        r = outer if k % 2 == 0 else inner
        a = rot + k * math.pi / points
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_dizzy_stars(surface, p):
    """Orbiting 'dizzy' stars above a stunned fighter's head (#12).

    Drawn while ``stun_timer > 0``. The orbit phase is derived from stun_timer
    itself (which ticks down one per frame), so the stars advance one step each
    frame with no external clock — and freeze deterministically when paused.
    The orbit is flattened into an ellipse so it reads as circling the head.
    """
    if p.fighter.stun_timer <= 0:
        return
    cx = p.rect.centerx
    cy = p.rect.top - EAR_HEIGHT - DIZZY_ORBIT_LIFT
    phase = p.fighter.stun_timer * DIZZY_SPIN_SPEED
    for i in range(DIZZY_STAR_COUNT):
        ang = phase + i * (2 * math.pi / DIZZY_STAR_COUNT)
        sx = cx + math.cos(ang) * DIZZY_ORBIT_RADIUS
        sy = cy + math.sin(ang) * DIZZY_ORBIT_RADIUS * DIZZY_ELLIPSE_FLATTEN  # ellipse
        pygame.draw.polygon(
            surface,
            YELLOW,
            _star_points(sx, sy, DIZZY_STAR_OUTER, DIZZY_STAR_INNER, DIZZY_STAR_POINTS, ang),
        )


# --- above-head timer bars (#111 -> generalised in #340, epic #334) ----------
# Small bars floating above a fighter, one per active player timer, showing how
# long it lasts. Each bar is a static full-width background rect with a coloured
# foreground rect on top whose width tracks a 0..1 `ratio` (a count-down drains
# to empty; a fill grows 0->100% — the difference is purely how the caller
# computes `ratio`), plus a text readout and an optional short word label.
# Bars STACK above the dizzy-star halo, `specs[0]` nearest the head and each
# later spec one row higher (newest-on-top ordering is the caller's).
STATUS_BAR_WIDTH = int(1.5 * PLAYER_SIZE[0])  # ~1.5x the cat body width (tail excluded)
STATUS_BAR_HEIGHT = 6
STATUS_BAR_BG = (30, 30, 30)  # background (drained) rect colour
# STATUS_BAR_SECONDS_SIZE / STATUS_BAR_LABEL_SIZE now live in config.py (the single
# font-size source, #344) and are imported above.
STATUS_BAR_LABEL_GAP = 4  # gap between the label and the bar's left edge
# Vertical stride between stacked bars: one bar row + its readout text + a gap,
# so a bar and its "Ns" never overlap the bar above it.
STATUS_BAR_STACK_STRIDE = STATUS_BAR_HEIGHT + STATUS_BAR_SECONDS_SIZE + 4
# Lift the bars above the dizzy-star halo so the two never overlap. The stars
# orbit at (EAR_HEIGHT + DIZZY_ORBIT_LIFT) above the head with a vertical reach
# of ~(DIZZY_ORBIT_RADIUS*0.4 + DIZZY_STAR_OUTER); clear that plus a small gap.
_STAR_HALO = DIZZY_ORBIT_RADIUS * DIZZY_ELLIPSE_FLATTEN + DIZZY_STAR_OUTER
STATUS_BAR_GAP_ABOVE_STARS = 6

# Grabs-left dots (#657): a discrete above-head budget of remaining full-intangible ledge
# grabs (of LEDGE_REGRAB_INTANGIBLE_CUTOFF) before PM's anti-plank cutoff. They sit BELOW
# the timer bars — the #720 stack is (A) intangible bar / (B) these dots / (C) the cat —
# and are a separate render pass, so they never suppress a bar (or vice versa). Spec:
# docs/pm-reference/ledge-regrab-intangible-and-display.md.
GRABS_LEFT_DOT_COLOR = INTANGIBLE_BAR_COLOR  # green — same family as the intangible window
GRABS_LEFT_DOT_RADIUS = 4
GRABS_LEFT_DOT_SPACING = 12  # dot centre-to-centre
GRABS_LEFT_DOT_LIFT = 12  # dot-row centre above the ear tops (below the bar stack)
GRABS_LEFT_LABEL = "grabs left"


def draw_timer_bars(surface, p, specs):
    """Stack `specs` above p's dizzy-star halo, specs[0] nearest the head.

    Each bar: a background rect + a coloured foreground rect (width = clamped
    `ratio`), an "Ns"/"%"-style `readout` above it, and — when present — a short
    `label` right-aligned to the bar's left. A single `label=None` spec draws at
    the exact #111 position (the byte-identity guard for shield/stun)."""
    cx = p.rect.centerx
    star_cy = p.rect.top - EAR_HEIGHT - DIZZY_ORBIT_LIFT
    base_bottom = int(star_cy - _STAR_HALO - STATUS_BAR_GAP_ABOVE_STARS)
    bar_left = cx - STATUS_BAR_WIDTH // 2

    for i, spec in enumerate(specs):
        ratio = max(0.0, min(1.0, spec.ratio))
        bar_bottom = base_bottom - i * STATUS_BAR_STACK_STRIDE
        bar_top = bar_bottom - STATUS_BAR_HEIGHT

        # Background rect (full width) then the foreground rect on top.
        pygame.draw.rect(surface, STATUS_BAR_BG, (bar_left, bar_top, STATUS_BAR_WIDTH, STATUS_BAR_HEIGHT))
        fg_w = int(STATUS_BAR_WIDTH * ratio)
        if fg_w > 0:
            pygame.draw.rect(surface, spec.color, (bar_left, bar_top, fg_w, STATUS_BAR_HEIGHT))

        # Readout sits just above the bar (and thus above the stars).
        text_utils.render_text(
            surface,
            spec.readout,
            (cx, bar_top - STATUS_BAR_SECONDS_SIZE // 2 - 2),
            STATUS_BAR_SECONDS_SIZE,
            WHITE,
            center=True,
        )

        # Optional label, right-aligned just left of the bar in the bar's colour.
        # A None label draws nothing (the drawer stays label-agnostic).
        if spec.label:
            text_utils.render_text(
                surface,
                spec.label,
                (bar_left - STATUS_BAR_LABEL_GAP, bar_top + STATUS_BAR_HEIGHT // 2),
                STATUS_BAR_LABEL_SIZE,
                spec.color,
                center=True,
                right_align=True,
            )


def draw_grabs_left_dots(surface, p, n):
    """Draw `n` grabs-left dots + the "grabs left" label above p's head (#657).

    A row of `n` filled circles centred over the head, with the label right-aligned
    just left of the row (matching the timer-bar label convention). Sits below the
    timer bars and is a separate pass, so it composes with them without suppression
    (the #720 stack). No-op when `n <= 0`."""
    if n <= 0:
        return
    cx = p.rect.centerx
    row_y = p.rect.top - EAR_HEIGHT - GRABS_LEFT_DOT_LIFT
    x0 = cx - ((n - 1) * GRABS_LEFT_DOT_SPACING) // 2
    for i in range(n):
        pygame.draw.circle(
            surface, GRABS_LEFT_DOT_COLOR, (x0 + i * GRABS_LEFT_DOT_SPACING, row_y), GRABS_LEFT_DOT_RADIUS
        )
    text_utils.render_text(
        surface,
        GRABS_LEFT_LABEL,
        (x0 - GRABS_LEFT_DOT_RADIUS - STATUS_BAR_LABEL_GAP, row_y),
        STATUS_BAR_LABEL_SIZE,
        GRABS_LEFT_DOT_COLOR,
        center=True,
        right_align=True,
    )
