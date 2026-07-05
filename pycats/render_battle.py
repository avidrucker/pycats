# pycats/render_battle.py
"""Shared battle renderer: draws the stage, fighters, and attacks onto a surface.
Extracted from game.py so the live game, pause screen, and sim presenters all
use one renderer."""

import math
from typing import NamedTuple

import pygame

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

from . import cat_faces, runtime_settings, text_utils
from .combat.data import GETUP_ATTACK
from .combat.geometry import resolve_circle
from .config import (
    ATTACK_SIZE,
    DODGE_TIME,
    EAR_HEIGHT,
    EAR_PADDING,
    EAR_SPACING,
    EAR_WIDTH,
    EYE_OFFSET_X,
    EYE_OFFSET_Y,
    EYE_RADIUS,
    FPS,
    GETUP_ROLL_FRAMES,
    GLINT_OFFSET_X,
    GLINT_OFFSET_Y,
    GLINT_RADIUS,
    HUD_PADDING,
    HUD_SPACING,
    KNOCKDOWN_PRONE_FRAMES,
    LEDGE_HANG_FRAMES,
    LEDGE_REGRAB_LOCKOUT_FRAMES,
    MAX_SHIELD_RADIUS,
    MIN_SHIELD_RADIUS,
    P1_UI_COLOR,
    P2_UI_COLOR,
    PLAYER_SIZE,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_BREAK_STUN_MAX,
    SHIELD_COLOR,
    SHIELD_DRAIN_PER_FRAME,
    SHIELD_MAX_HP,
    SMASH_CHARGE_FRAMES,
    STATUS_BAR_LABEL_SIZE,
    STATUS_BAR_SECONDS_SIZE,
    STRIPE_COUNT,
    STRIPE_HEIGHT,
    STRIPE_SPACING,
    STRIPE_WIDTH,
    TAIL_SEGMENT_LENGTH,
    TAIL_SEGMENT_WIDTH,
    TAPER_MODIFER,
    WHISKER_ANGLE,
    WHISKER_COUNT,
    WHISKER_LENGTH,
    WHISKER_OFFSET_X,
    WHISKER_OFFSET_Y,
    WHISKER_THICKNESS,
    WHITE,
    YELLOW,
)
from .entities import Player
from .input_history import format_line

# Hit/hurtbox debug overlay (#219). Outline-only circles in two distinct colours
# so an active attack's hitbox(es) and each fighter's hurtbox are directly
# visible. Cosmetic + default-OFF (runtime_settings), so no golden impact.
# Platform fill colours (#317/H-b): moved out of Platform (which no longer owns a
# Surface) so the adapter paints the rect. Thick = solid stage, thin = pass-through.
PLATFORM_THICK = (164, 113, 73)
PLATFORM_THIN = (193, 153, 112)

# Attack visual colours (#326/H-b): moved out of Attack with its Surface-building.
ATTACK_SINGLE_FILL = (255, 60, 60, 180)  # legacy single-hitbox flat red
ATTACK_FILL = (255, 60, 60, 120)  # per-circle semi-transparent red fill
ATTACK_OUTLINE = (255, 230, 120, 220)  # per-circle outline
ATTACK_OUTLINE_WIDTH = 2  # per-circle outline stroke width (px)

HITBOX_OVERLAY_COLOR = RED  # attack hitbox circles
HURTBOX_OVERLAY_COLOR = (0, 255, 255)  # cyan — fighter hurtbox circles
OVERLAY_LINE_WIDTH = 2  # >0 → pygame draws an outline, not a disc

# Fighter sprite drawing (#415: named from inline literals). Purely-local render
# geometry/colour — cosmetic, so an identity extraction (values unchanged).
STRIPE_BACK_OFFSET_X = 10  # stripes sit this far toward the back from center-x
STRIPE_START_Y_OFFSET = 15  # first stripe starts this far below the head top
FACE_BLIT_OFFSET_Y = 10  # glyph face centred this far below the head top
NAME_FONT_SIZE = 20  # player-name label above the cat
NAME_LABEL_OFFSET_Y = 25  # name sits this far above the head top
# Name-label colours are the shared player accents (#450: config.P1_UI_COLOR/P2_UI_COLOR).
SHIELD_FILL_ALPHA = 100  # alpha of the translucent shield-bubble fill


# --- draw helpers moved verbatim from game.py ---


def draw_eye(surface, p: Player, eye=True):
    if eye:
        x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
        y = p.rect.top + EYE_OFFSET_Y
        pygame.draw.circle(surface, p.eye_color, (x, y), EYE_RADIUS)
    else:  # we will draw a glint instead of an eye
        x = p.rect.right - GLINT_OFFSET_X if p.facing_right else p.rect.left + GLINT_OFFSET_X
        y = p.rect.top + GLINT_OFFSET_Y
        pygame.draw.circle(surface, WHITE, (x, y), GLINT_RADIUS)


def draw_cat_features(surface, p: Player):
    """Draws cat ears and whiskers on the player. These are purely cosmetic and don't affect collision."""
    # Draw cat ears (triangles)
    head_center_x = p.rect.centerx
    head_top_y = p.rect.top

    # Left ear coordinates
    left_ear_points = [
        (head_center_x - EAR_SPACING // 2, head_top_y),  # Bottom right point
        (head_center_x - EAR_SPACING // 2 - EAR_WIDTH, head_top_y),  # Bottom left point
        (
            head_center_x - EAR_SPACING // 2 - EAR_WIDTH // 2,
            head_top_y - EAR_HEIGHT,
        ),  # Top point
    ]

    # Right ear coordinates
    right_ear_points = [
        (head_center_x + EAR_SPACING // 2, head_top_y),  # Bottom left point
        (
            head_center_x + EAR_SPACING // 2 + EAR_WIDTH,
            head_top_y,
        ),  # Bottom right point
        (
            head_center_x + EAR_SPACING // 2 + EAR_WIDTH // 2,
            head_top_y - EAR_HEIGHT,
        ),  # Top point
    ]

    # for both ears, if the player if facing right, move the ears to the left by PADDING,
    # else, move the ears to the right by PADDING
    if p.facing_right:
        left_ear_points = [(x - EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x - EAR_PADDING, y) for x, y in right_ear_points]
    else:
        left_ear_points = [(x + EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x + EAR_PADDING, y) for x, y in right_ear_points]

    # Draw ears — tinted with the body so the whole head flashes (#109).
    ear_color = _blend(p.char_color, getattr(p, "tint", None))
    pygame.draw.polygon(surface, ear_color, left_ear_points)
    pygame.draw.polygon(surface, ear_color, right_ear_points)

    # Draw whiskers (lines)
    whisker_start_x = p.rect.right - WHISKER_OFFSET_X if p.facing_right else p.rect.left + WHISKER_OFFSET_X
    whisker_start_y = p.rect.top + WHISKER_OFFSET_Y + EYE_RADIUS // 2

    # Direction of whiskers depends on facing direction
    direction = 1 if p.facing_right else -1

    # Draw multiple whisker lines in a fan pattern
    import math

    # Draw middle whisker first (horizontal)
    middle_index = WHISKER_COUNT // 2

    for i in range(WHISKER_COUNT):
        # Calculate angle for each whisker (-WHISKER_ANGLE for top, 0 for middle, WHISKER_ANGLE for bottom)
        angle_degrees = (i - middle_index) * WHISKER_ANGLE
        angle_radians = math.radians(angle_degrees)

        # Calculate end point using trigonometry
        x_offset = direction * WHISKER_LENGTH * math.cos(angle_radians)
        y_offset = WHISKER_LENGTH * math.sin(angle_radians)

        start_pos = (whisker_start_x, whisker_start_y)
        end_pos = (whisker_start_x + x_offset, whisker_start_y + y_offset)

        # Whiskers are WHITE, blended with the body flash so they tint too (#109)
        whisker_color = _blend(WHITE, getattr(p, "tint", None))
        pygame.draw.line(surface, whisker_color, start_pos, end_pos, WHISKER_THICKNESS)


def draw_stripes(surface, p: Player):
    """Draws triangular stripes on the player's back for pattern."""
    # Calculate stripe positions on the back of the player
    back_center_x = p.rect.centerx + (-STRIPE_BACK_OFFSET_X if p.facing_right else STRIPE_BACK_OFFSET_X)
    back_start_y = p.rect.top + STRIPE_START_Y_OFFSET  # a bit down from the top

    for i in range(STRIPE_COUNT):
        # Calculate vertical position for each stripe
        stripe_y = back_start_y + i * STRIPE_SPACING

        # Make sure we don't draw stripes outside the player rectangle
        if stripe_y + STRIPE_HEIGHT > p.rect.bottom:
            break

        # Create triangular stripe points pointing toward the front of the cat
        if p.facing_right:
            # Right-facing cat: triangle points right, flat side on the left (back)
            stripe_points = [
                (back_center_x - STRIPE_WIDTH // 2, stripe_y),  # Back top
                (
                    back_center_x - STRIPE_WIDTH // 2,
                    stripe_y + STRIPE_HEIGHT,
                ),  # Back bottom
                (
                    back_center_x + STRIPE_WIDTH // 2,
                    stripe_y + STRIPE_HEIGHT // 2,
                ),  # Front point
            ]
        else:
            # Left-facing cat: triangle points left, flat side on the right (back)
            stripe_points = [
                (back_center_x + STRIPE_WIDTH // 2, stripe_y),  # Back top
                (
                    back_center_x + STRIPE_WIDTH // 2,
                    stripe_y + STRIPE_HEIGHT,
                ),  # Back bottom
                (
                    back_center_x - STRIPE_WIDTH // 2,
                    stripe_y + STRIPE_HEIGHT // 2,
                ),  # Front point
            ]

        # Draw the triangular stripe — tinted with the body flash (#109)
        pygame.draw.polygon(surface, _blend(p.stripe_color, getattr(p, "tint", None)), stripe_points)


def draw_player_name(surface, p: Player):
    """Draw the fighter's name above the cat: the `nickname` if set (#478), else the
    "P1"/"P2" identity.

    Colour is selected by the player *slot* — `char_name`, the win-attribution identity
    (`battle_screen.py`) — NOT by the displayed text, so setting a nickname changes the
    label while keeping the slot's accent colour. `nickname` None → the label is
    `char_name` in the same colour as before (byte-identical default → the render-parity
    oracle stays green)."""
    color = P1_UI_COLOR if p.char_name == "P1" else P2_UI_COLOR
    label = getattr(p, "nickname", None) or p.char_name

    text_utils.render_text(
        surface, label, (p.rect.centerx, p.rect.top - NAME_LABEL_OFFSET_Y), NAME_FONT_SIZE, color, center=True
    )


# --- cat-body composite cache -------------------------------------------------
# A fighter's body (rect fill + stripes + eyes + glint + ears + whiskers + name)
# is fully determined by its colours, facing, name, and current tint (the body
# fill, which flips to RED/WHITE/YELLOW while hurt/dodging/stunned). We render
# that composite once per distinct look and blit it each frame. The composite is
# pixel-identical to the per-call draw: every shape is opaque and font.render
# already yields alpha-antialiased text, so baking it into a transparent surface
# and re-blitting reproduces the same pixels.
_BODY_PAD_X = 48
_BODY_PAD_TOP = 56
_BODY_PAD_BOT = 12

# Crouch squash easing (#124): fraction of the stand→crouch transition covered
# per rendered frame (~3 frames to settle). Render-only; not part of the sim.
_CROUCH_ANIM_RATE = 0.34
_body_cache: dict = {}


class _CatShim:
    """Minimal stand-in exposing the attributes the draw_* helpers read, with a
    virtual rect positioned inside the composite surface."""

    __slots__ = ("rect", "facing_right", "char_color", "eye_color", "stripe_color", "char_name", "nickname", "tint")

    def __init__(self, rect, facing_right, char_color, eye_color, stripe_color, char_name, nickname=None, tint=None):
        self.rect = rect
        self.facing_right = facing_right
        self.char_color = char_color
        self.eye_color = eye_color
        self.stripe_color = stripe_color
        self.char_name = char_name
        self.nickname = nickname  # #478: the name label draws this if set, else char_name
        # #109: the active flash overlay (RED/YELLOW/WHITE) or None. The draw_*
        # helpers blend it 50% over each part's base colour via `_blend`, so the
        # whole sprite flashes from one source instead of per-part char_color.
        self.tint = tint


TINT_STRENGTH = 0.5  # #109: blend the flash 50% over each part's base colour


def active_tint(p):
    """The flash *overlay* colour for a fighter this frame, or None when calm.

    Derived from `STATUS_SOURCES` (#522): the first source (by precedence) that is
    live and declares a `tint` wins — RED while hurt, YELLOW while stunned, WHITE
    while dodging (#75), else None. `tinted()` blends it over a part's base colour
    and `body_tint()` resolves it for the body fill. Timer-driven (a flash is present
    while its timer is live and clears the frame it hits 0). Table defined below.
    """
    f = p.fighter
    for s in sorted(STATUS_SOURCES, key=lambda src: src.precedence):
        if s.tint is not None and s.active(f, p):
            return s.tint
    return None


def _blend(base, overlay, strength=TINT_STRENGTH):
    """`base` blended `strength` of the way toward `overlay`; `base` if overlay
    is None. The low-level mix every tinted part shares (#109)."""
    if overlay is None:
        return tuple(base)
    return tuple(round(b + (o - b) * strength) for b, o in zip(base, overlay))


def tinted(base_color, p, strength=TINT_STRENGTH):
    """A part's drawn colour this frame: `base_color` softened ~50% toward the
    active hurt/stun/dodge flash, or unchanged when the fighter is calm (#109).

    The one helper every body part derives its colour from — body fill, ears,
    whiskers, stripes (via the body composite) and the tail (`render_tail`) — so
    no part keeps a hardcoded `char_color` path that can drift out of the flash.
    """
    return _blend(base_color, active_tint(p), strength)


def body_tint(p):
    """The body fill *selector* for a fighter this frame (#75 / D1 slice 1).

    Returns the solid overlay (RED hurt / YELLOW stun / WHITE dodge) or the
    character colour when calm — unchanged contract: callers and the composite
    cache key still distinguish the four states by this value. The 50% softening
    lives in `tinted()`, applied where the body is actually filled.
    """
    return active_tint(p) or p.char_color


def _cat_body_surface(p, face_style=cat_faces.PRIMITIVES):
    """Return the cached body composite for player `p` (built on first use).

    `face_style` (#108) selects how the face is drawn: PRIMITIVES (default —
    eyes + ears + whiskers) or a glyph style (kaomoji/emoji) blitted over the
    head. It is part of the cache key so toggling re-renders."""
    # Per-fighter body size (#282 fix for the #275 regression): the composite must
    # match the fighter's collision box (stand_size), not the global PLAYER_SIZE —
    # else a small archetype renders full-height and clips below its feet. (w, h) is
    # in the cache key so different-sized fighters don't share one cached body.
    w, h = p.fighter.stand_size
    tint = tuple(body_tint(p))
    # nickname (#478) is in the key so a nickname change re-renders the label instead of
    # serving a stale composite; None (the default) leaves the key byte-identical.
    key = (
        tuple(p.char_color),
        tuple(p.stripe_color),
        tuple(p.eye_color),
        p.char_name,
        getattr(p, "nickname", None),
        p.fighter.facing_right,
        tint,
        face_style,
        (w, h),
    )
    surf = _body_cache.get(key)
    if surf is None:
        cw = w + 2 * _BODY_PAD_X
        ch = _BODY_PAD_TOP + h + _BODY_PAD_BOT
        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        vrect = pygame.Rect(_BODY_PAD_X, _BODY_PAD_TOP, w, h)
        overlay = active_tint(p)
        shim = _CatShim(
            vrect,
            p.fighter.facing_right,
            p.char_color,
            p.eye_color,
            p.stripe_color,
            p.char_name,
            nickname=getattr(p, "nickname", None),
            tint=overlay,
        )
        body = pygame.Surface((w, h))
        body.fill(_blend(p.char_color, overlay))
        surf.blit(body, vrect)
        draw_stripes(surf, shim)
        # Face: a glyph style replaces the primitive eyes + ears + whiskers;
        # falls back to primitives when the glyph can't render (font missing).
        face = cat_faces.render_face(face_style, p.fighter.facing_right, cat_faces.ink_for(p.char_color))
        if face is not None:
            surf.blit(face, face.get_rect(center=(vrect.centerx, vrect.top + FACE_BLIT_OFFSET_Y)))
        else:
            draw_eye(surf, shim)
            draw_eye(surf, shim, eye=False)
            draw_cat_features(surf, shim)
        draw_player_name(surf, shim)
        _body_cache[key] = surf
    return surf


def _star_points(cx, cy, outer, inner, points, rot):
    """Vertices of a `points`-pointed star centred at (cx, cy), rotated `rot`."""
    pts = []
    for k in range(points * 2):
        r = outer if k % 2 == 0 else inner
        a = rot + k * math.pi / points
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_dizzy_stars(surface, p: Player):
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

# Per-timer bar colours (#334 spec). These are the BAR hues only — distinct from
# the shared SHIELD_COLOR (shield bubble) / YELLOW (dizzy stars + body flash),
# which are left untouched so only the above-head bars recolour.
SHIELD_BAR_COLOR = (70, 130, 255)  # blue — shield resource (#364)
DIZZY_BAR_COLOR = (210, 90, 220)  # magenta — shield-break stun (#364)
HANG_BAR_COLOR = (0, 210, 200)  # teal — ledge-hang timeout (#348)
DOWN_BAR_COLOR = (255, 140, 45)  # orange — knockdown/getup window (#350)
LOCKOUT_BAR_COLOR = (230, 70, 70)  # red — post-drop regrab lockout (#357)
INVULN_BAR_COLOR = (95, 225, 120)  # green — intangibility window (#358)
CHARGE_BAR_COLOR = (255, 205, 40)  # gold — smash charge, the one FILL bar (#380)

# The getup-attack (#225) intangibility window = the whole swing, so its bar's
# max is the move's total frames (kept in sync with the move data, not hardcoded).
_GETUP_ATTACK_FRAMES = GETUP_ATTACK.startup + GETUP_ATTACK.active + GETUP_ATTACK.recovery

# Recency sentinel: the shield bar is a *resource* gauge (shield_hp), not a frame
# counter, so it has no comparable "frames elapsed since start". Give it a key
# that sorts it LAST (a held shield reads as background; action count-downs stack
# newest-on-top above it). See timer_bar_specs' recency ordering (#357).
_SHIELD_RECENCY_KEY = float("inf")


class TimerBar(NamedTuple):
    """One above-head bar: a coloured 0..1 fill, a text readout, and an optional
    label. `label=None` renders no label (byte-identical to the #111 bar)."""

    ratio: float  # 0..1 fill fraction (drawer clamps)
    readout: str  # e.g. "3s" (count-down) or "60% · 1.2s" (fill)
    color: tuple  # bar fill + label colour
    label: str | None = None


def _invuln_remaining_max(p):
    """The active intangibility window as `(remaining, max)` frames, or None.

    Per-source resolve (#358, option 1): `fighter.invulnerable` is a bool driven
    by several actions, each with its own timer and constant max — dodge
    (DODGE_TIME), getup-roll (GETUP_ROLL_FRAMES), getup-attack (the whole swing).
    Gated on the `invulnerable` bool so the bar shows only while actually
    intangible, and **suppressed while ledge-hanging** (the HANG bar already shows
    that clock — no redundant duplicate). Returns None when not intangible or the
    source has no tracked frame window (e.g. respawn grants no count-down invuln).
    """
    f = p.fighter
    if not f.invulnerable or p.state == "ledge_hang":
        return None
    if f.dodge_timer > 0:
        return (f.dodge_timer, DODGE_TIME)
    if f.getup_roll_timer > 0:
        return (f.getup_roll_timer, GETUP_ROLL_FRAMES)
    if f.getup_attack_timer > 0:
        return (f.getup_attack_timer, _GETUP_ATTACK_FRAMES)
    return None


def _secs(frames):
    """The `"Ns"` count-down readout shared by every COUNTDOWN bar (#111)."""
    return f"{math.ceil(frames / FPS)}s"


class StatusSource(NamedTuple):
    """One declarative status feedback source (#522) — the single description that
    both `active_tint` and `timer_bar_specs` derive from, so a status is defined in
    ONE place and adding one (e.g. #531 ledge-invuln, #506 respawn) is a single record
    with no new branches. Callables take `(f, p)` (fighter, player).

    `kind` documents the value-shape (COUNTDOWN / RESOURCE / FILL); the per-source
    `ratio`/`readout`/`recency` callables encode it (kept explicit so the migration is
    byte-identical to the pre-#522 inline logic)."""

    name: str
    precedence: int                # tint order + exclusive-bar selection order (low first)
    active: object                 # (f, p) -> bool: is this source live?
    kind: object = None            # "COUNTDOWN" | "RESOURCE" | "FILL" (documentation)
    tint: object = None            # body-flash overlay colour, or None
    bar_color: object = None       # timer-bar colour, or None
    bar_label: object = None
    bar_class: object = None       # "exclusive" | "overlay"
    ratio: object = None           # (f, p) -> float  (0..1 fill; drawer clamps)
    readout: object = None         # (f, p) -> str
    recency: object = None         # (f, p) -> float  (sort key; lower = nearer head)


# The single source of truth for status tints + above-head bars (#522). Order here is
# precedence order; `active_tint` returns the first live source with a `tint`, and
# `timer_bar_specs` takes the first live EXCLUSIVE bar + all live OVERLAY bars. Byte-
# identical to the pre-#522 `active_tint` if-chain and `timer_bar_specs` branches.
# The dizzy star-halo (draw_dizzy_stars) is a separate render path, not modelled here.
STATUS_SOURCES = [
    StatusSource("hurt", 0, kind="COUNTDOWN", tint=RED,
                 active=lambda f, p: f.hurt_timer > 0),
    StatusSource("shield", 1, kind="RESOURCE",
                 active=lambda f, p: p.state == "shield",
                 bar_color=SHIELD_BAR_COLOR, bar_label="SHIELD", bar_class="exclusive",
                 ratio=lambda f, p: f.shield_hp / SHIELD_MAX_HP,
                 readout=lambda f, p: f"{math.ceil(f.shield_hp / (SHIELD_DRAIN_PER_FRAME * FPS))}s",
                 recency=lambda f, p: _SHIELD_RECENCY_KEY),
    StatusSource("stun", 2, kind="COUNTDOWN", tint=YELLOW,
                 active=lambda f, p: f.stun_timer > 0,
                 bar_color=DIZZY_BAR_COLOR, bar_label="DIZZY", bar_class="exclusive",
                 ratio=lambda f, p: f.stun_timer / SHIELD_BREAK_STUN_MAX,
                 readout=lambda f, p: _secs(f.stun_timer),
                 recency=lambda f, p: SHIELD_BREAK_STUN_MAX - f.stun_timer),
    StatusSource("dodge", 3, kind="COUNTDOWN", tint=WHITE,
                 active=lambda f, p: f.dodge_timer > 0),
    StatusSource("ledge_hang", 4, kind="COUNTDOWN",
                 active=lambda f, p: p.state == "ledge_hang" and f.ledge_hang_timer > 0,
                 bar_color=HANG_BAR_COLOR, bar_label="HANG", bar_class="exclusive",
                 ratio=lambda f, p: f.ledge_hang_timer / LEDGE_HANG_FRAMES,
                 readout=lambda f, p: _secs(f.ledge_hang_timer),
                 recency=lambda f, p: LEDGE_HANG_FRAMES - f.ledge_hang_timer),
    StatusSource("prone", 5, kind="COUNTDOWN",
                 active=lambda f, p: p.state == "prone" and f.prone_timer > 0,
                 bar_color=DOWN_BAR_COLOR, bar_label="DOWN", bar_class="exclusive",
                 ratio=lambda f, p: f.prone_timer / KNOCKDOWN_PRONE_FRAMES,
                 readout=lambda f, p: _secs(f.prone_timer),
                 recency=lambda f, p: KNOCKDOWN_PRONE_FRAMES - f.prone_timer),
    StatusSource("lockout", 6, kind="COUNTDOWN",
                 active=lambda f, p: f.ledge_regrab_lockout_timer > 0,
                 bar_color=LOCKOUT_BAR_COLOR, bar_label="LOCKOUT", bar_class="overlay",
                 ratio=lambda f, p: f.ledge_regrab_lockout_timer / LEDGE_REGRAB_LOCKOUT_FRAMES,
                 readout=lambda f, p: _secs(f.ledge_regrab_lockout_timer),
                 recency=lambda f, p: LEDGE_REGRAB_LOCKOUT_FRAMES - f.ledge_regrab_lockout_timer),
    # INVULN — the dodge / getup-roll / getup-attack intangibility window, resolved
    # (with its `invulnerable`-bool gate + ledge-hang suppression) by
    # _invuln_remaining_max. One overlay bar; #531 (ledge-invuln) and #506 (respawn)
    # each add their OWN separate source rather than extend this resolver.
    StatusSource("invuln", 7, kind="COUNTDOWN",
                 active=lambda f, p: _invuln_remaining_max(p) is not None,
                 bar_color=INVULN_BAR_COLOR, bar_label="INVULN", bar_class="overlay",
                 ratio=lambda f, p: _invuln_remaining_max(p)[0] / _invuln_remaining_max(p)[1],
                 readout=lambda f, p: _secs(_invuln_remaining_max(p)[0]),
                 recency=lambda f, p: _invuln_remaining_max(p)[1] - _invuln_remaining_max(p)[0]),
    # CHARGE (#380) — the one FILL bar: grows 0->100% as smash_charge_timer accumulates
    # rather than draining; recency = the up-count (frames elapsed since charge began).
    StatusSource("charge", 8, kind="FILL",
                 active=lambda f, p: f.smash_charge_timer > 0,
                 bar_color=CHARGE_BAR_COLOR, bar_label="CHARGE", bar_class="overlay",
                 ratio=lambda f, p: min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES),
                 readout=lambda f, p: (
                     f"{round(min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES) * 100)}%·"
                     f"{math.ceil((SMASH_CHARGE_FRAMES - f.smash_charge_timer) / FPS)}s"),
                 recency=lambda f, p: f.smash_charge_timer),
]


def _bar_for(s, f, p):
    """Build the `(recency, TimerBar)` pair for a live bar source `s`."""
    return (s.recency(f, p), TimerBar(s.ratio(f, p), s.readout(f, p), s.bar_color, s.bar_label))


def timer_bar_specs(p):
    """The active above-head timer bars for fighter `p`, ordered newest-on-top.

    Pure function of live state (#111): each fill is the remaining value over the
    *known constant max* — shield -> shield_hp/SHIELD_MAX_HP, stun ->
    stun_timer/SHIELD_BREAK_STUN_MAX, etc. — so no per-instance start value is
    stored and a bar tracks mid-effect changes (e.g. a blocked hit chipping
    shield). Honours the live status-bars toggle (runtime_settings, #111/#121).

    Two kinds of bar (#357):
    - **Exclusive-state** bars (shield / stun / hang / prone) — mutually exclusive
      states, so at most one is added (shield takes precedence, via the elif
      chain: a shielding fighter is never simultaneously stunned).
    - **Overlay** timers — state-independent, so they co-activate with the above:
      LOCKOUT (post-drop regrab suppression, #357) and INVULN (intangibility
      window, #358; per-source resolve via _invuln_remaining_max).

    Bars are returned **newest-on-top**: sorted by recency = frames elapsed since
    the timer started (`max - remaining`), ascending, so the most recently started
    bar is `specs[0]` (drawn nearest the head by draw_timer_bars). The shield
    resource gauge has no frame elapsed and sorts last (`_SHIELD_RECENCY_KEY`).
    Ordering is stable, so equal-recency bars keep insertion order. Single-bar
    cases return the same one bar as before this slice (byte-identity preserved).
    """
    if not runtime_settings.show_status_timer_bars():
        return []
    f = p.fighter
    ordered = sorted(STATUS_SOURCES, key=lambda s: s.precedence)
    bars = []  # (recency_key, TimerBar); lower key = more recent = nearer head

    # --- exclusive-state bar (at most one): first live one, by precedence ---
    for s in ordered:
        if s.bar_class == "exclusive" and s.bar_color is not None and s.active(f, p):
            bars.append(_bar_for(s, f, p))
            break

    # --- overlay bars (state-independent; co-activate with the exclusive) ---
    for s in ordered:
        if s.bar_class == "overlay" and s.bar_color is not None and s.active(f, p):
            bars.append(_bar_for(s, f, p))

    bars.sort(key=lambda kb: kb[0])  # newest-on-top (least elapsed first)
    return [bar for _, bar in bars]


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


# (width, deg°, color) -> rotated SRCALPHA segment surface. Module-level (#330/H-b,
# was Tail._seg_cache): the key is position-independent so it's shareable across
# tails; cleared by the render_isolation fixture (surfaces go stale after a
# pygame.quit(), #63) like _body_cache.
_tail_seg_cache: dict = {}


def render_tail(surface, tail, color):
    """Draw a fighter's Verlet `tail` as cached, rotated, tapering rects in `color`
    (#330/H-b — was Tail.draw; the entity holds only sim data now). `color` is the
    already-resolved tint the caller computes (#265)."""
    cache = _tail_seg_cache
    color = tuple(color)
    length = TAIL_SEGMENT_LENGTH
    n = len(tail.segments)
    blit = surface.blit
    for i, segment in enumerate(tail.segments):
        width = int(TAIL_SEGMENT_WIDTH * (1.0 - (i / n) * TAPER_MODIFER))
        deg = int(round(-math.degrees(segment.angle))) % 360
        # `color` is in the key so a flash doesn't serve stale untinted segment
        # surfaces (the cache spans tint states across frames).
        key = (width, deg, color)
        surf = cache.get(key)
        if surf is None:
            base = pygame.Surface((length, width), pygame.SRCALPHA)
            base.fill(color)
            surf = pygame.transform.rotate(base, deg)
            cache[key] = surf
        rect = surf.get_rect()
        rect.center = (int(segment.x), int(segment.y))
        blit(surf, rect)


def render_battle(surface, players, platforms):
    """Draw platforms, alive fighters, and their attacks onto `surface`.
    Mirrors game.py's playing-branch draw block (no HUD/controls/FPS text)."""
    for pl in platforms:
        # #317/H-b: the platform holds only data (rect + thin); the adapter paints
        # its thickness colour (was Platform.image, an entity-owned Surface).
        pygame.draw.rect(surface, PLATFORM_THIN if pl.thin else PLATFORM_THICK, pl.rect)
    for p in players:
        if not p.fighter.is_alive:
            continue
        render_tail(surface, p.tail, tinted(p.char_color, p))  # #330: adapter draws the tail
        # Body composite (rect + stripes + eyes + ears + whiskers + name).
        body = _cat_body_surface(p, getattr(p, "face_style", cat_faces.PRIMITIVES))
        # Posture squash (#124 crouch / #173 prone): vertically scale the body
        # toward the active lowered height, feet planted, eased over a few frames.
        # Purely visual — driven by a render-only progress var, so the
        # deterministic sim is untouched (the collision Rect itself snaps in
        # Player._apply_posture_geometry).
        stand_h = p.fighter.stand_size[1]
        if p.state == "crouch" and p.fighter.crouch_size:
            low_h = p.fighter.crouch_size[1]
        elif p.state == "prone" and p.fighter.prone_size:
            low_h = p.fighter.prone_size[1]
        else:
            low_h = stand_h
        target = 1.0 if low_h != stand_h else 0.0
        anim = getattr(p, "_crouch_anim", 0.0)
        anim = min(target, anim + _CROUCH_ANIM_RATE) if anim < target else max(target, anim - _CROUCH_ANIM_RATE)
        p._crouch_anim = anim
        if anim > 0.0 and low_h != stand_h:
            s = (stand_h + (low_h - stand_h) * anim) / stand_h
            body = pygame.transform.scale(body, (body.get_width(), max(1, round(body.get_height() * s))))
            blit_y = round(p.rect.bottom - (_BODY_PAD_TOP + stand_h) * s)
        else:
            blit_y = p.rect.y - _BODY_PAD_TOP
        surface.blit(body, (p.rect.x - _BODY_PAD_X, blit_y))
        if p.fighter.stun_timer > 0:
            draw_dizzy_stars(surface, p)
        if p.state == "shield":
            ratio = p.fighter.shield_hp / SHIELD_MAX_HP
            shield_radius = int(MAX_SHIELD_RADIUS * ratio)
            r = max(MIN_SHIELD_RADIUS, shield_radius)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*SHIELD_COLOR, SHIELD_FILL_ALPHA), (r, r), r)
            surface.blit(s, (p.rect.centerx - r, p.rect.centery - r))
        # Above-head timer bars (#111 -> #340) — drawn last so they sit above the
        # dizzy stars; the spec list is empty when SHOW_STATUS_TIMER_BARS is off.
        draw_timer_bars(surface, p, timer_bar_specs(p))


def _attack_surface(a):
    """Build an attack's visual Surface from its resolved circles (#326/H-b — was
    Attack.image). Pure presentation, rebuilt per frame; combat uses `a.resolved`,
    not this. Single-hitbox keeps the legacy flat-red `ATTACK_SIZE` rect; multi
    draws each circle (fill + outline) offset by the attack's rect top-left."""
    if len(a.resolved) == 1:
        surf = pygame.Surface(ATTACK_SIZE, pygame.SRCALPHA)
        surf.fill(ATTACK_SINGLE_FILL)
        return surf
    surf = pygame.Surface(a.rect.size, pygame.SRCALPHA)
    left, top = a.rect.topleft
    for cx, cy, r, _hb in a.resolved:
        local = (round(cx - left), round(cy - top))
        pygame.draw.circle(surf, ATTACK_FILL, local, round(r))
        pygame.draw.circle(surf, ATTACK_OUTLINE, local, round(r), ATTACK_OUTLINE_WIDTH)
    return surf


def render_attacks(surface, attacks):
    for a in attacks:
        surface.blit(_attack_surface(a), a.rect)


def _active_hurtbox(p):
    """The hurtbox combat.process_hits actually tests against `p` this frame.

    Mirrors that resolver's selection (#124 crouch / #173 prone lower the box so
    high attacks whiff) so the overlay shows the *true* vulnerable region, not a
    stale stand box. Read defensively — a minimal combat stand-in may lack
    `crouch_hurtbox`/`prone_hurtbox`/`state`."""
    hurtbox = p.fighter_data.hurtbox
    state = getattr(p, "state", None)
    if state == "crouch" and getattr(p.fighter, "crouch_hurtbox", None) is not None:
        return p.fighter.crouch_hurtbox
    if state == "prone" and getattr(p.fighter, "prone_hurtbox", None) is not None:
        return p.fighter.prone_hurtbox
    return hurtbox


def render_hitbox_overlay(surface, players, attacks):
    """Draw the hit/hurtbox debug overlay (#219), gated on the live toggle.

    Render-only: reads the SAME data combat.process_hits resolves — `atk.resolved`
    for active hitbox circles, `resolve_circle` on each fighter's active hurtbox —
    and outlines them in two distinct colours. Default OFF, so the live game and
    goldens are untouched until a dev flips it on from Options."""
    if not runtime_settings.show_hitbox_overlay():
        return
    for a in attacks:
        for cx, cy, r, _box in getattr(a, "resolved", ()):
            pygame.draw.circle(surface, HITBOX_OVERLAY_COLOR, (int(cx), int(cy)), int(r), OVERLAY_LINE_WIDTH)
    for p in players:
        if not p.fighter.is_alive:
            continue
        for c in _active_hurtbox(p).circles:
            cx, cy, r = resolve_circle(c, p.rect.x, p.rect.y, p.fighter.facing_right, p.rect.width)
            pygame.draw.circle(surface, HURTBOX_OVERLAY_COLOR, (int(cx), int(cy)), int(r), OVERLAY_LINE_WIDTH)


# HUD / text-overlay layout (#415: named from inline literals). The overlay font
# size was repeated at ~10 call sites; the line counts + block gap couple the
# controls / input-history blocks' start-y to the HUD's row count.
HUD_FONT_SIZE = 24  # shared size for HUD / controls / input-history / chrome text
HUD_LINE_COUNT = 7  # rows drawn by draw_hud (label + 6 stats)
CONTROLS_LINE_COUNT = 7  # rows drawn by draw_controls (header + 6 controls)
HUD_BLOCK_GAP = 20  # vertical gap between stacked text blocks


def draw_hud(surface, p: Player, label, topright=False):
    """Draws the HUD for a player, showing their state, jumps left, shield HP, lives, and damage percent."""
    fsm = f"FSM: {p.state.capitalize()}"
    jumps = f"{p.fighter.jumps_remaining} jump{'s' if p.fighter.jumps_remaining != 1 else ''} left"
    shield = f"Shield HP: {p.fighter.shield_hp}"
    shield_attempting = f"Shield Attempting: {'Yes' if p.fighter.shield_attempting else 'No'}"
    stocks = f"Lives: {p.fighter.lives}"
    percent = f"Damage: {int(p.fighter.percent)}%"
    for i, txt in enumerate((label, fsm, jumps, shield, shield_attempting, stocks, percent)):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = HUD_PADDING + i * HUD_SPACING

        text_utils.render_text(surface, txt, (x_pos, y_pos), HUD_FONT_SIZE, WHITE, right_align=topright)


def draw_controls(surface, p: Player, label, topright=False):
    """Draws the control scheme for a player below the HUD."""
    # Convert pygame key constants to readable strings with Unicode arrows where appropriate
    key_names = {
        pygame.K_a: "A",
        pygame.K_d: "D",
        pygame.K_w: "W",
        pygame.K_s: "S",
        pygame.K_v: "V",
        pygame.K_c: "C",
        pygame.K_x: "X",
        pygame.K_LEFT: "←",
        pygame.K_RIGHT: "→",
        pygame.K_UP: "↑",
        pygame.K_DOWN: "↓",
        pygame.K_SLASH: "/",
        pygame.K_PERIOD: ".",
        pygame.K_COMMA: ",",
        pygame.K_b: "B",  # P1 default smash (#462)
        pygame.K_QUOTE: "'",  # P2 default smash — apostrophe glyph, not a typo (#462)
    }

    controls = [
        f"{label} Controls:",
        f"Move: {key_names.get(p.controls['left'], '?')}/{key_names.get(p.controls['right'], '?')}",
        f"Jump: {key_names.get(p.controls['up'], '?')}",
        f"Down: {key_names.get(p.controls['down'], '?')}",
        f"Attack: {key_names.get(p.controls['attack'], '?')}",
        f"Shield: {key_names.get(p.controls['shield'], '?')}",
        f"Special: {key_names.get(p.controls['special'], '?')}",
        f"Smash: {key_names.get(p.controls.get('smash'), '?')}",  # #462
    ]

    # Start drawing below the HUD (7 lines of HUD + some spacing)
    start_y = HUD_PADDING + HUD_LINE_COUNT * HUD_SPACING + HUD_BLOCK_GAP

    for i, txt in enumerate(controls):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = start_y + i * HUD_SPACING

        # Use mixed text rendering for Unicode arrow support
        if topright:
            # For right-aligned text, we need to calculate positioning differently
            text_width = text_utils.text_renderer._get_font(None, HUD_FONT_SIZE).size(txt)[0]
            adjusted_x = x_pos - text_width
            text_utils.text_renderer.render_text_mixed(txt, HUD_FONT_SIZE, WHITE, surface, (adjusted_x, y_pos))
        else:
            text_utils.text_renderer.render_text_mixed(txt, HUD_FONT_SIZE, WHITE, surface, (x_pos, y_pos))


def draw_input_history(surface, history, label, topright=False):
    """Draw a fighter's recent-input strip (#21) below the controls block.

    ``history`` is an :class:`~pycats.input_history.InputHistory`; entries render
    oldest->newest as absolute-direction arrows + A/B/S, joined by ' · '. Unicode
    arrows go through ``render_text_mixed`` (same path draw_controls uses). One
    line, anchored under the HUD (7 lines) + controls (7 lines) blocks."""
    line = format_line(label, history.entries())

    # Below the HUD (7 lines) and the controls block (header + 6 rows).
    y_pos = HUD_PADDING + (HUD_LINE_COUNT + CONTROLS_LINE_COUNT) * HUD_SPACING + 2 * HUD_BLOCK_GAP
    x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING

    if topright:
        text_width = text_utils.text_renderer._get_font(None, HUD_FONT_SIZE).size(line)[0]
        text_utils.text_renderer.render_text_mixed(line, HUD_FONT_SIZE, WHITE, surface, (x_pos - text_width, y_pos))
    else:
        text_utils.text_renderer.render_text_mixed(line, HUD_FONT_SIZE, WHITE, surface, (x_pos, y_pos))


def draw_pause_hint(surface):
    """The static 'P: Pause Game' battle-HUD hint, drawn during the playing state.

    It reads no shell state (a constant string), so it is battle HUD, not shell
    chrome — BattleScreen.render owns it (#279), beside draw_hud/draw_controls."""
    text_utils.render_text(
        surface,
        "P: Pause Game",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 3),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )


def draw_shell_chrome(surface, fps, is_fullscreen, frame_input):
    """Draw the playing-state SHELL overlays — debug input, FPS, fullscreen hints.

    These read shell/loop state (fps, is_fullscreen, frame_input), NOT battle state,
    so game.py's loop calls this helper with the state it owns instead of inlining the
    draws (#279). Kept out of BattleScreen so the battle object stays free of shell
    state (cf. #100 Risks, #246). Byte-identical to the old inline block."""
    if frame_input:
        text_utils.render_text(
            surface,
            frame_input.__str__(),
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
            HUD_FONT_SIZE,
            WHITE,
        )
    text_utils.render_text(
        surface,
        f"FPS: {fps:.2f}",
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )
    fs_text = (
        "F11: Toggle Fullscreen | "
        + ("F10: Fullscreen Zoom" if is_fullscreen else "F10: Window Size")
        + (" | ESC: Exit Fullscreen" if is_fullscreen else "")
    )
    text_utils.render_text(
        surface,
        fs_text,
        (SCREEN_WIDTH - HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
        HUD_FONT_SIZE,
        WHITE,
        right_align=True,
    )
