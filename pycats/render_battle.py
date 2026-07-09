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
    BLACK,
    DODGE_TIME,
    EAR_HEIGHT,
    EAR_PADDING,
    EAR_SPACING,
    EAR_WIDTH,
    EYE_OFFSET_X,
    EYE_OFFSET_Y,
    EYE_RADIUS,
    FIGHTER_OUTLINE_COLOR,
    FIGHTER_OUTLINE_WIDTH,
    FPS,
    GETUP_ROLL_FRAMES,
    GLINT_OFFSET_X,
    GLINT_OFFSET_Y,
    GLINT_RADIUS,
    HUD_EMPHASIS_SIZE,
    HUD_PADDING,
    HUD_SPACING,
    KNOCKDOWN_PRONE_FRAMES,
    LEDGE_REGRAB_INVULN_CUTOFF,
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

# #694 (DP1 of #672): black-outline stroke width for the flat-gray placeholder's
# otherwise-invisible eyes + stripes, so they read against the same-gray body.
PLACEHOLDER_FEATURE_OUTLINE_WIDTH = 2

# Fighter sprite drawing (#415: named from inline literals). Purely-local render
# geometry/colour — cosmetic, so an identity extraction (values unchanged).
STRIPE_BACK_OFFSET_X = 10  # stripes sit this far toward the back from center-x
STRIPE_START_Y_OFFSET = 15  # first stripe starts this far below the head top
FACE_BLIT_OFFSET_Y = 10  # glyph face centred this far below the head top
NAME_FONT_SIZE = 20  # player-name label above the cat
NAME_LABEL_OFFSET_Y = 35  # name sits this far above the head top (clears EAR_HEIGHT + label glyph, #573)
# Name-label colours are the shared player accents (#450: config.P1_UI_COLOR/P2_UI_COLOR).
SHIELD_FILL_ALPHA = 100  # alpha of the translucent shield-bubble fill


# --- draw helpers moved verbatim from game.py ---


def draw_eye(surface, p: Player, eye=True):
    if eye:
        x = p.rect.right - EYE_OFFSET_X if p.facing_right else p.rect.left + EYE_OFFSET_X
        y = p.rect.top + EYE_OFFSET_Y
        pygame.draw.circle(surface, p.eye_color, (x, y), EYE_RADIUS)
        # #694: outline the placeholder's body-coloured (invisible) eye in black so it reads.
        if getattr(p, "feature_outline", False):
            pygame.draw.circle(surface, BLACK, (x, y), EYE_RADIUS, PLACEHOLDER_FEATURE_OUTLINE_WIDTH)
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
        # #694: outline the placeholder's body-coloured (invisible) stripe in black so it reads.
        if getattr(p, "feature_outline", False):
            pygame.draw.polygon(surface, BLACK, stripe_points, PLACEHOLDER_FEATURE_OUTLINE_WIDTH)


def slot_accent_color(p: Player):
    """The player *slot*'s accent colour — P1 red / P2 blue (#450) — keyed off
    `char_name` (the win-attribution identity, `battle_screen.py`), not the
    displayed text. One source shared by the name label and the fighter outline
    (#572), so both stay the same colour per slot."""
    return P1_UI_COLOR if p.char_name == "P1" else P2_UI_COLOR


def draw_player_name(surface, p: Player):
    """Draw the fighter's name above the cat: the `nickname` if set (#478), else the
    "P1"/"P2" identity.

    Colour is the slot accent (`slot_accent_color`) — NOT the displayed text, so
    setting a nickname changes the label while keeping the slot's accent colour.
    `nickname` None → the label is `char_name` in the same colour as before
    (byte-identical default → the render-parity oracle stays green)."""
    color = slot_accent_color(p)
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
_body_cache: dict = {}  # key -> merged composite (ring + body + name), one surface
_body_layers_cache: dict = {}  # key -> (ring_layer, body_layer) for the split #585 draw


def _dilated_silhouette(src, color, width, pad=0):
    """`src`'s own alpha silhouette, dilated by `width` px and filled with `color`,
    on a surface grown by `pad` px per side (#564).

    Blit the real sprite on top of the returned surface to get an outline that
    hugs the true silhouette and sits *behind* the sprite — the ring shows only
    outside the silhouette, so interior pixels are never overpainted and no border
    segment cuts across the sprite (the #546 torso-box rect did both).

    `pad` >= `width` prevents the ring clipping when `src` has no transparent
    margin of its own (e.g. a rotated tail-segment rect). The body composite
    already carries ample _BODY_PAD_* margin, so it passes pad=0 and keeps the
    same surface size (blit offsets in render_battle are unchanged)."""
    mask = pygame.mask.from_surface(src)
    stamp = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    w, h = src.get_size()
    out = pygame.Surface((w + 2 * pad, h + 2 * pad), pygame.SRCALPHA)
    blit = out.blit
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if (dx or dy) and dx * dx + dy * dy <= width * width:  # round dilation
                blit(stamp, (pad + dx, pad + dy))
    return out


class _CatShim:
    """Minimal stand-in exposing the attributes the draw_* helpers read, with a
    virtual rect positioned inside the composite surface."""

    __slots__ = (
        "rect",
        "facing_right",
        "char_color",
        "eye_color",
        "stripe_color",
        "char_name",
        "nickname",
        "tint",
        "feature_outline",
    )

    def __init__(
        self,
        rect,
        facing_right,
        char_color,
        eye_color,
        stripe_color,
        char_name,
        nickname=None,
        tint=None,
        feature_outline=False,
    ):
        self.rect = rect
        self.facing_right = facing_right
        self.char_color = char_color
        self.eye_color = eye_color
        self.stripe_color = stripe_color
        self.char_name = char_name
        self.nickname = nickname  # #478: the name label draws this if set, else char_name
        # #694: True for the flat-uniform-gray placeholder, whose eyes/stripes are
        # body-coloured and would vanish. draw_eye / draw_stripes then stroke a black
        # outline so the features read (the #546 outline-legibility basis, DP1 of #672).
        self.feature_outline = feature_outline
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


def _body_cache_key(p, face_style):
    """The cache key shared by the body layers and the merged composite.

    `face_style` (#108) is keyed so toggling the face re-renders. nickname (#478)
    is keyed so a label change re-renders instead of serving a stale composite
    (None — the default — keeps the key byte-identical). `outline` (#572) is a
    function of char_name (already keyed) but keying the resolved colour is
    explicit so the two slots never share a cached ring. (w, h) is keyed (#282 fix
    for #275) so different-sized archetypes don't share one cached body."""
    w, h = p.fighter.stand_size
    return (
        tuple(p.char_color),
        tuple(p.stripe_color),
        tuple(p.eye_color),
        p.char_name,
        getattr(p, "nickname", None),
        p.fighter.facing_right,
        tuple(body_tint(p)),
        face_style,
        (w, h),
        tuple(slot_accent_color(p)),  # #572: P1 red / P2 blue silhouette ring
    )


def _draw_body_features(p, face_style):
    """Draw a fighter's body fill + stripes + face/features (NO ring, NO name) onto
    a fresh padded SRCALPHA surface. Return (feat, shim) — the raw silhouette from
    which both the ring and the merged composite are built."""
    # The composite matches the fighter's collision box (stand_size), not the global
    # PLAYER_SIZE, so a small archetype doesn't render full-height and clip its feet.
    w, h = p.fighter.stand_size
    cw = w + 2 * _BODY_PAD_X
    ch = _BODY_PAD_TOP + h + _BODY_PAD_BOT
    feat = pygame.Surface((cw, ch), pygame.SRCALPHA)
    vrect = pygame.Rect(_BODY_PAD_X, _BODY_PAD_TOP, w, h)
    overlay = active_tint(p)
    # #694 (DP1 of #672): the placeholder is the one fighter whose body, stripe and eye
    # are the same colour (flat uniform gray) — its features vanish, so draw_eye /
    # draw_stripes give them a black outline. Named cats have contrasting features (the
    # #636 distinctness test asserts it), so this never fires for them → byte-identical.
    feature_outline = tuple(p.char_color) == tuple(p.eye_color) == tuple(p.stripe_color)
    shim = _CatShim(
        vrect,
        p.fighter.facing_right,
        p.char_color,
        p.eye_color,
        p.stripe_color,
        p.char_name,
        nickname=getattr(p, "nickname", None),
        tint=overlay,
        feature_outline=feature_outline,
    )
    body = pygame.Surface((w, h))
    body.fill(_blend(p.char_color, overlay))
    feat.blit(body, vrect)
    draw_stripes(feat, shim)
    # Face: a glyph style replaces the primitive eyes + ears + whiskers; falls back
    # to primitives when the glyph can't render (font missing).
    face = cat_faces.render_face(face_style, p.fighter.facing_right, cat_faces.ink_for(p.char_color))
    if face is not None:
        feat.blit(face, face.get_rect(center=(vrect.centerx, vrect.top + FACE_BLIT_OFFSET_Y)))
    else:
        draw_eye(feat, shim)
        draw_eye(feat, shim, eye=False)
        draw_cat_features(feat, shim)
    return feat, shim


def _cat_body_layers(p, face_style=cat_faces.PRIMITIVES):
    """Return the cached ``(ring_layer, body_layer)`` for player `p`, both padded
    SRCALPHA surfaces of the same size.

    - ``ring_layer`` — the slot-accent silhouette ring only (#564/#572), nothing else.
    - ``body_layer`` — body fill + stripes + face/features + name label, no ring.

    render_battle draws them at different depths — ring BEHIND the tail, body in
    FRONT — so the outline is one continuous edge behind body + ears + tail and
    never seams at the body↔tail junction (#585). ``_cat_body_surface`` recomposes
    the two for callers that want the fighter as a single surface."""
    key = _body_cache_key(p, face_style)
    layers = _body_layers_cache.get(key)
    if layers is None:
        feat, shim = _draw_body_features(p, face_style)
        # Silhouette ring (#564, was a torso-box rect in #546): the cat's actual
        # alpha silhouette (body + ears) dilated and filled per slot (#572) — P1 red
        # / P2 blue, matching the name label. Built from `feat` (before the name) so
        # the label isn't ringed.
        ring = _dilated_silhouette(feat, tuple(slot_accent_color(p)), FIGHTER_OUTLINE_WIDTH)
        body_layer = feat.copy()
        draw_player_name(body_layer, shim)  # name on top of the body, un-ringed
        layers = (ring, body_layer)
        _body_layers_cache[key] = layers
    return layers


def _cat_body_surface(p, face_style=cat_faces.PRIMITIVES):
    """Return the cached merged body composite (ring behind + body + name) as one
    surface. Byte-identical to the pre-#585 single-surface build — the render-cache
    parity oracle and the silhouette tests read this. render_battle itself draws the
    split ``_cat_body_layers`` so the ring can sit behind the tail (#585)."""
    key = _body_cache_key(p, face_style)
    surf = _body_cache.get(key)
    if surf is None:
        feat, shim = _draw_body_features(p, face_style)
        surf = _dilated_silhouette(feat, tuple(slot_accent_color(p)), FIGHTER_OUTLINE_WIDTH)
        surf.blit(feat, (0, 0))  # sprite over its own halo -> ring shows only outside it
        draw_player_name(surf, shim)  # on top of the ring, un-haloed
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
# (HANG_BAR_COLOR removed with the ledge-hang timeout — #475)
DOWN_BAR_COLOR = (255, 140, 45)  # orange — knockdown/getup window (#350)
LOCKOUT_BAR_COLOR = (230, 70, 70)  # red — post-drop regrab lockout (#357)
INVULN_BAR_COLOR = (95, 225, 120)  # green — intangibility window (#358)
CHARGE_BAR_COLOR = (255, 205, 40)  # gold — smash charge, the one FILL bar (#380)
RECHARGE_BAR_COLOR = (60, 200, 140)  # teal — shield HP regen after release (#597)

# Grabs-left dots (#657): a discrete above-head budget of remaining full-invuln ledge
# grabs (of LEDGE_REGRAB_INVULN_CUTOFF) before PM's anti-plank cutoff. They sit BELOW
# the timer bars — the #720 stack is (A) invuln bar / (B) these dots / (C) the cat —
# and are a separate render pass, so they never suppress a bar (or vice versa). Spec:
# docs/pm-reference/ledge-regrab-invuln-and-display.md.
GRABS_LEFT_DOT_COLOR = INVULN_BAR_COLOR  # green — same family as the invuln window
GRABS_LEFT_DOT_RADIUS = 4
GRABS_LEFT_DOT_SPACING = 12  # dot centre-to-centre
GRABS_LEFT_DOT_LIFT = 12  # dot-row centre above the ear tops (below the bar stack)
GRABS_LEFT_LABEL = "grabs left"

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
    intangible, and **suppressed while ledge-hanging** — the ledge-grab burst gets
    its own dedicated bar in #531; until then the hang shows no intangibility bar
    (the HANG timeout bar it used to defer to is gone, #475). Returns None when not
    intangible or the source has no tracked frame window (e.g. respawn grants none).
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
    precedence: int  # tint order + exclusive-bar selection order (low first)
    active: object  # (f, p) -> bool: is this source live?
    kind: object = None  # "COUNTDOWN" | "RESOURCE" | "FILL" (documentation)
    tint: object = None  # body-flash overlay colour, or None
    bar_color: object = None  # timer-bar colour, or None
    bar_label: object = None
    bar_class: object = None  # "exclusive" | "overlay"
    ratio: object = None  # (f, p) -> float  (0..1 fill; drawer clamps)
    readout: object = None  # (f, p) -> str
    recency: object = None  # (f, p) -> float  (sort key; lower = nearer head)


# The single source of truth for status tints + above-head bars (#522). Order here is
# precedence order; `active_tint` returns the first live source with a `tint`, and
# `timer_bar_specs` takes the first live EXCLUSIVE bar + all live OVERLAY bars. Byte-
# identical to the pre-#522 `active_tint` if-chain and `timer_bar_specs` branches.
# The dizzy star-halo (draw_dizzy_stars) is a separate render path, not modelled here.
STATUS_SOURCES = [
    StatusSource("hurt", 0, kind="COUNTDOWN", tint=RED, active=lambda f, p: f.hurt_timer > 0),
    StatusSource(
        "shield",
        1,
        kind="RESOURCE",
        active=lambda f, p: p.state == "shield",
        bar_color=SHIELD_BAR_COLOR,
        bar_label="SHIELD",
        bar_class="exclusive",
        ratio=lambda f, p: f.shield_hp / SHIELD_MAX_HP,
        readout=lambda f, p: f"{math.ceil(f.shield_hp / (SHIELD_DRAIN_PER_FRAME * FPS))}s",
        recency=lambda f, p: _SHIELD_RECENCY_KEY,
    ),
    StatusSource(
        "stun",
        2,
        kind="COUNTDOWN",
        tint=YELLOW,
        active=lambda f, p: f.stun_timer > 0,
        bar_color=DIZZY_BAR_COLOR,
        bar_label="DIZZY",
        bar_class="exclusive",
        ratio=lambda f, p: f.stun_timer / SHIELD_BREAK_STUN_MAX,
        readout=lambda f, p: _secs(f.stun_timer),
        recency=lambda f, p: SHIELD_BREAK_STUN_MAX - f.stun_timer,
    ),
    StatusSource("dodge", 3, kind="COUNTDOWN", tint=WHITE, active=lambda f, p: f.dodge_timer > 0),
    # LEDGE-INVULN (#531, revived #658) — the fixed ledge-grab intangibility burst
    # (21f full for grabs 1-5, 5f residual for grab 6+ past the cutoff; #656/#683). Its
    # own INVULN overlay bar. #531 suppressed it while `state == "ledge_hang"` — the ONE
    # state in which the timer is ever live — so the bar never rendered (the #531
    # dead-render defect). #658 drops that gate so it shows DURING the hang, stacked
    # above the grabs-left dots (#657; the #720 stack). Ratio is against the *granted*
    # length stored at grab (#538), so a 5f residual grab drains a truthful 5/5->0
    # (normalized per-grant — #720 chose this over a proportional stub). No body tint.
    # The reversal is scoped to THIS bar only: _invuln_remaining_max KEEPS its ledge-hang
    # suppression for the dodge/getup/respawn INVULN bar, so the two never double up
    # during a hang. Spec: docs/pm-reference/ledge-regrab-invuln-and-display.md.
    StatusSource(
        "ledge_invuln",
        4,
        kind="COUNTDOWN",
        active=lambda f, p: f.ledge_invuln_timer > 0,
        bar_color=INVULN_BAR_COLOR,
        bar_label="INVULN",
        bar_class="overlay",
        ratio=lambda f, p: f.ledge_invuln_timer / max(1, f.ledge_invuln_granted),
        readout=lambda f, p: _secs(f.ledge_invuln_timer),
        recency=lambda f, p: f.ledge_invuln_granted - f.ledge_invuln_timer,
    ),
    StatusSource(
        "prone",
        5,
        kind="COUNTDOWN",
        active=lambda f, p: p.state == "prone" and f.prone_timer > 0,
        bar_color=DOWN_BAR_COLOR,
        bar_label="DOWN",
        bar_class="exclusive",
        ratio=lambda f, p: f.prone_timer / KNOCKDOWN_PRONE_FRAMES,
        readout=lambda f, p: _secs(f.prone_timer),
        recency=lambda f, p: KNOCKDOWN_PRONE_FRAMES - f.prone_timer,
    ),
    StatusSource(
        "lockout",
        6,
        kind="COUNTDOWN",
        active=lambda f, p: f.ledge_regrab_lockout_timer > 0,
        bar_color=LOCKOUT_BAR_COLOR,
        bar_label="LOCKOUT",
        bar_class="overlay",
        ratio=lambda f, p: f.ledge_regrab_lockout_timer / LEDGE_REGRAB_LOCKOUT_FRAMES,
        readout=lambda f, p: _secs(f.ledge_regrab_lockout_timer),
        recency=lambda f, p: LEDGE_REGRAB_LOCKOUT_FRAMES - f.ledge_regrab_lockout_timer,
    ),
    # INVULN — the dodge / getup-roll / getup-attack intangibility window, resolved
    # (with its `invulnerable`-bool gate + ledge-hang suppression) by
    # _invuln_remaining_max. One overlay bar; #531 (ledge-invuln) and #506 (respawn)
    # each add their OWN separate source rather than extend this resolver.
    StatusSource(
        "invuln",
        7,
        kind="COUNTDOWN",
        active=lambda f, p: _invuln_remaining_max(p) is not None,
        bar_color=INVULN_BAR_COLOR,
        bar_label="INVULN",
        bar_class="overlay",
        ratio=lambda f, p: _invuln_remaining_max(p)[0] / _invuln_remaining_max(p)[1],
        readout=lambda f, p: _secs(_invuln_remaining_max(p)[0]),
        recency=lambda f, p: _invuln_remaining_max(p)[1] - _invuln_remaining_max(p)[0],
    ),
    # CHARGE (#380) — the one FILL bar: grows 0->100% as smash_charge_timer accumulates
    # rather than draining; recency = the up-count (frames elapsed since charge began).
    StatusSource(
        "charge",
        8,
        kind="FILL",
        active=lambda f, p: f.smash_charge_timer > 0,
        bar_color=CHARGE_BAR_COLOR,
        bar_label="CHARGE",
        bar_class="overlay",
        ratio=lambda f, p: min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES),
        readout=lambda f, p: (
            f"{round(min(1.0, f.smash_charge_timer / SMASH_CHARGE_FRAMES) * 100)}%·"
            f"{math.ceil((SMASH_CHARGE_FRAMES - f.smash_charge_timer) / FPS)}s"
        ),
        recency=lambda f, p: f.smash_charge_timer,
    ),
    # RECHARGE (#597) — shield HP regenerating back to full after release. A FILL bar
    # (fills 0->100% as shield_hp climbs), shown ONLY while regenerating and never
    # during shield-break dizzy: the `stun_timer == 0` clause makes it provably never
    # co-live with the "stun"/DIZZY source (active on stun_timer > 0). Overlay so it
    # composes with a concurrent action bar (e.g. DOWN/LOCKOUT while HP climbs); as a
    # background resource gauge it reuses _SHIELD_RECENCY_KEY to sort last, so action
    # count-downs stack above it (mirrors the SHIELD drain gauge, with which it is
    # state-exclusive: that needs state == "shield", this needs state != "shield").
    StatusSource(
        "recharge",
        9,
        kind="FILL",
        active=lambda f, p: p.state != "shield" and f.shield_hp < SHIELD_MAX_HP and f.stun_timer == 0,
        bar_color=RECHARGE_BAR_COLOR,
        bar_label="RECHARGE",
        bar_class="overlay",
        ratio=lambda f, p: f.shield_hp / SHIELD_MAX_HP,
        readout=lambda f, p: _secs((SHIELD_MAX_HP - f.shield_hp) / SHIELD_DRAIN_PER_FRAME),
        recency=lambda f, p: _SHIELD_RECENCY_KEY,
    ),
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


def grabs_left_dots(p):
    """How many grabs-left dots to show above fighter `p` — 0 for none (#657).

    Each dot is one remaining ledge grab (of `LEDGE_REGRAB_INVULN_CUTOFF`) that still
    grants the full intangibility burst before PM's anti-plank cutoff. Pinned to the
    shipped #656 counter, which is **1 on the first grab**:
    `dots = LEDGE_REGRAB_INVULN_CUTOFF + 1 - ledge_regrab_count`, shown only while the
    fighter is in an active regrab chain (count in `1..CUTOFF`). At count 0 (no chain /
    just reset) or past the cutoff (6+), no dots — so the first grab shows 5, the fifth
    shows 1, and the sixth shows none. Honours the shared status-bars toggle. Spec:
    docs/pm-reference/ledge-regrab-invuln-and-display.md.
    """
    if not runtime_settings.show_status_timer_bars():
        return 0
    count = p.fighter.ledge_regrab_count
    if count < 1 or count > LEDGE_REGRAB_INVULN_CUTOFF:
        return 0
    return LEDGE_REGRAB_INVULN_CUTOFF + 1 - count


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


# (width, deg°, color) -> rotated SRCALPHA segment surface. Module-level (#330/H-b,
# was Tail._seg_cache): the key is position-independent so it's shareable across
# tails; cleared by the render_isolation fixture (surfaces go stale after a
# pygame.quit(), #63) like _body_cache.
_tail_seg_cache: dict = {}
# (seg_width, deg°, outline_color) -> the segment's dilated outline halo (#564).
# The silhouette shape is tint-independent, but the ring colour is per-slot since
# #572 (P1 red / P2 blue), so it's in the key. Cleared with _tail_seg_cache (#63).
_tail_outline_cache: dict = {}


def render_tail(surface, tail, color, outline_color=FIGHTER_OUTLINE_COLOR):
    """Draw a fighter's Verlet `tail` as cached, rotated, tapering rects in `color`
    (#330/H-b — was Tail.draw; the entity holds only sim data now). `color` is the
    already-resolved tint the caller computes (#265); `outline_color` is the slot
    accent for the tail's outline ring (#572, defaults to the shared light ring).

    The tail's outline (#564) is drawn as a first pass BEHIND every segment body,
    so the bodies cover the interior stamps and only the tail's outer silhouette
    ring remains — matching the body outline and keeping a low-luminance tail
    separable from the stage."""
    outline_color = tuple(outline_color)
    cache = _tail_seg_cache
    color = tuple(color)
    length = TAIL_SEGMENT_LENGTH
    n = len(tail.segments)
    blit = surface.blit
    placed = []  # (segment body surf, rect, width, deg) — bodies drawn after the halo pass
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
        placed.append((surf, rect, width, deg))
    # Pass 1: outline halos, behind everything.
    ow = FIGHTER_OUTLINE_WIDTH
    for surf, rect, width, deg in placed:
        okey = (width, deg, outline_color)
        halo = _tail_outline_cache.get(okey)
        if halo is None:
            halo = _dilated_silhouette(surf, outline_color, ow, pad=ow)
            _tail_outline_cache[okey] = halo
        blit(halo, (rect.x - ow, rect.y - ow))
    # Pass 2: segment bodies on top, covering the interior stamps.
    for surf, rect, width, deg in placed:
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
        # Body is drawn in two depth layers (#585) so the silhouette ring is one
        # continuous edge behind body + ears + tail and never seams at the body↔tail
        # junction: ring BEHIND -> tail (its own ring + bodies) -> body pixels + name
        # in FRONT. The tail bodies cover the body ring where the two overlap, so no
        # ring segment is left cutting across the join.
        ring_layer, body_layer = _cat_body_layers(p, getattr(p, "face_style", cat_faces.PRIMITIVES))
        # Posture squash (#124 crouch / #173 prone): vertically scale the body
        # toward the active lowered height, feet planted, eased over a few frames.
        # Purely visual — driven by a render-only progress var, so the
        # deterministic sim is untouched (the collision Rect itself snaps in
        # Player._apply_posture_geometry). Both layers scale identically so they stay
        # aligned.
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
            size = (ring_layer.get_width(), max(1, round(ring_layer.get_height() * s)))
            ring_layer = pygame.transform.scale(ring_layer, size)
            body_layer = pygame.transform.scale(body_layer, size)
            blit_y = round(p.rect.bottom - (_BODY_PAD_TOP + stand_h) * s)
        else:
            blit_y = p.rect.y - _BODY_PAD_TOP
        pos = (p.rect.x - _BODY_PAD_X, blit_y)
        surface.blit(ring_layer, pos)  # silhouette ring, behind everything
        # #330: adapter draws the tail; #572: its outline ring takes the slot accent.
        # Drawn between the ring and the body so the tail sits over the body's ring
        # (killing the junction seam) but still behind the body pixels themselves.
        render_tail(surface, p.tail, tinted(p.char_color, p), slot_accent_color(p))
        surface.blit(body_layer, pos)  # body fill + features + name, in front
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
        # Grabs-left dots (#657) — the ledge anti-plank budget, below the bars (#720
        # stack). Separate pass so it composes with the bars; 0 = nothing drawn.
        draw_grabs_left_dots(surface, p, grabs_left_dots(p))


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
# draw_hud rows split by audience (#545) AND by emphasis (#550). The top-anchored
# "secondary" group holds the player-facing label/jumps/Shield HP rows (always on)
# plus the two implementation-jargon rows (FSM state, Shield Attempting bool) that
# render only when the dev-info flag is on. The two numbers players read constantly
# — Damage % and Lives — are split OUT of this group and drawn larger in the bottom
# corners (see hud_emphasis_rows / draw_hud). HUD_LINE_COUNT is the all-secondary-rows
# total kept for back-compat; layout below anchors on the live hud_line_count().
HUD_PLAYER_LINE_COUNT = 3  # label + jumps + Shield HP (always on; #550 moved Lives/Damage out)
HUD_DEV_LINE_COUNT = 2  # FSM: + Shield Attempting: (dev-info-gated)
HUD_LINE_COUNT = HUD_PLAYER_LINE_COUNT + HUD_DEV_LINE_COUNT  # 5, all secondary rows (dev-info on)
CONTROLS_LINE_COUNT = 7  # rows drawn by draw_controls (header + 6 controls)
HUD_BLOCK_GAP = 20  # vertical gap between stacked text blocks
HUD_EMPHASIS_SPACING = 34  # row pitch for the larger emphasized rows (cf. HUD_SPACING for the size 24 rows)


def hud_line_count():
    """Rows draw_hud actually draws given the live dev-info flag (#545). The
    controls / input-history blocks anchor below the HUD, so they must follow the
    real row count, not the all-rows maximum, or a gap opens when the flag is off."""
    return HUD_PLAYER_LINE_COUNT + (HUD_DEV_LINE_COUNT if runtime_settings.show_dev_info() else 0)


def hud_rows(label, p: Player):
    """The ordered *secondary* HUD row strings for player `p` — the top-anchored,
    standard-size group. Honours the live dev-info flag (#545): the FSM / Shield
    Attempting jargon rows are included only when show_dev_info() is on; the label /
    jumps / Shield HP rows always are. Damage % and Lives are NOT here — they are the
    emphasized bottom-corner rows (see hud_emphasis_rows, #550). Row order matches the
    pre-gate layout so the flag-on secondary render is unchanged."""
    dev = runtime_settings.show_dev_info()
    rows = [label]
    if dev:
        rows.append(f"FSM: {p.state.capitalize()}")
    rows.append(f"{p.fighter.jumps_remaining} jump{'s' if p.fighter.jumps_remaining != 1 else ''} left")
    rows.append(f"Shield HP: {p.fighter.shield_hp}")
    if dev:
        rows.append(f"Shield Attempting: {'Yes' if p.fighter.shield_attempting else 'No'}")
    return rows


def hud_emphasis_rows(p: Player):
    """The two numbers players read constantly — Lives then Damage % — split out of
    the secondary group (#550) to render larger in the bottom corners. Ordered
    top->bottom, so Damage (the most-glanced value) sits closest to the corner."""
    return [f"Lives: {p.fighter.lives}", f"Damage: {int(p.fighter.percent)}%"]


def emphasis_row_y(i, n):
    """Top-y of emphasized row `i` of `n`, bottom-anchored (#550). The block is
    lifted to sit just above the 'P: Pause Game' hint line (draw_pause_hint, at
    SCREEN_HEIGHT - HUD_SPACING*3) so the P2 (bottom-right) rows never overlap it,
    and grows UPWARD as the font scale enlarges the rows. Pure geometry — the
    testable seam for the emphasized-row placement."""
    baseline = SCREEN_HEIGHT - HUD_SPACING * 3 - HUD_BLOCK_GAP
    return baseline - (n - i) * HUD_EMPHASIS_SPACING


def draw_hud_emphasis(surface, p: Player, topright=False):
    """Draws the emphasized Damage %/Lives rows larger in the bottom corner (#550).
    Split from the secondary rows so the two concerns — glanceable stats vs. the
    top-grouped detail — render independently. The size routes through
    text_utils.render_text -> scaled_font_size, so it honours the live font_scale."""
    emphasis = hud_emphasis_rows(p)
    for i, txt in enumerate(emphasis):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = emphasis_row_y(i, len(emphasis))

        text_utils.render_text(surface, txt, (x_pos, y_pos), HUD_EMPHASIS_SIZE, WHITE, right_align=topright)


def draw_hud(surface, p: Player, label, topright=False):
    """Draws the HUD for a player in two groups (#550): the secondary rows (label,
    jumps, Shield HP, plus the dev-info rows FSM/Shield Attempting when the flag is
    on, #545) top-anchored at the standard size, and the emphasized Damage %/Lives
    rows larger in the bottom corner."""
    for i, txt in enumerate(hud_rows(label, p)):
        x_pos = SCREEN_WIDTH - HUD_PADDING if topright else HUD_PADDING
        y_pos = HUD_PADDING + i * HUD_SPACING

        text_utils.render_text(surface, txt, (x_pos, y_pos), HUD_FONT_SIZE, WHITE, right_align=topright)

    draw_hud_emphasis(surface, p, topright=topright)


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
        pygame.K_b: "B",  # #462 P1 default smash (now just a prettifier — pygame names it 'b' too)
        pygame.K_QUOTE: "'",  # #462 P2 default smash — pygame names K_QUOTE 'quote', so the glyph still helps
    }

    def keyname(code):
        # #469: render ANY bound key by name so a rebind (#439) to a key outside the
        # glyph dict shows its actual name instead of '?'. The dict above is now an
        # optional prettifier (arrows/punctuation), not a correctness requirement.
        # None (an unbound action, e.g. missing 'smash') has no name -> stays '?'.
        if code is None:
            return "?"
        return key_names.get(code) or pygame.key.name(code).upper() or "?"

    controls = [
        f"{label} Controls:",
        f"Move: {keyname(p.controls['left'])}/{keyname(p.controls['right'])}",
        f"Jump: {keyname(p.controls['up'])}",
        f"Down: {keyname(p.controls['down'])}",
        f"Attack: {keyname(p.controls['attack'])}",
        f"Shield: {keyname(p.controls['shield'])}",
        f"Special: {keyname(p.controls['special'])}",
        f"Smash: {keyname(p.controls.get('smash'))}",  # #462
    ]

    # Start drawing below the HUD (its live row count + some spacing) — the count
    # shrinks when the dev-info rows are gated off (#545), so read it live.
    start_y = HUD_PADDING + hud_line_count() * HUD_SPACING + HUD_BLOCK_GAP

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
    line, anchored under the HUD (its live row count, #545) + controls (7 lines)
    blocks."""
    line = format_line(label, history.entries())

    # Below the HUD (its live row count, #545) and the controls block (header + 6 rows).
    y_pos = HUD_PADDING + (hud_line_count() + CONTROLS_LINE_COUNT) * HUD_SPACING + 2 * HUD_BLOCK_GAP
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
    # In-battle ESC-hold leave-match hint (#681, from the #549 audit) — gated by the
    # BATTLE show_controls toggle, and only while the ESC-hold affordance is enabled.
    # Worded "hold" + "leave match" so it does not read as the ESC-tap "Exit Fullscreen"
    # above (the #549 disambiguation).
    if runtime_settings.show_controls() and runtime_settings.esc_hold_to_navigate():
        text_utils.render_text(
            surface,
            "Hold ESC to leave match",
            (HUD_PADDING, SCREEN_HEIGHT - HUD_SPACING * 2),
            HUD_FONT_SIZE,
            WHITE,
        )
