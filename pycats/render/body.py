# pycats/render/body.py
"""The fighter sprite: cat body composite (fill + stripes + face/features + ears
+ whiskers + name), its per-look cache, the slot-accent silhouette ring, the
idle-breathing waveform, and the Verlet-tail renderer.

Extracted verbatim from render_battle (#900, child 3 of #833). Pixel output is
unchanged — the render-parity oracle and the body-cache identity tests guard it.
"""

import math

import pygame

from .. import cat_faces, text_utils
from ..config import (
    BLACK,
    EAR_HEIGHT,
    EAR_PADDING,
    EAR_SPACING,
    EAR_WIDTH,
    EYE_OFFSET_X,
    EYE_OFFSET_Y,
    EYE_RADIUS,
    FIGHTER_OUTLINE_COLOR,
    FIGHTER_OUTLINE_WIDTH,
    GLINT_OFFSET_X,
    GLINT_OFFSET_Y,
    GLINT_RADIUS,
    P1_UI_COLOR,
    P2_UI_COLOR,
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
)
from ..entities import Player
from .tint import _blend, active_tint, body_tint

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

# Idle breathing (#567): a subtle looping vertical body-height oscillation applied
# only in the idle FSM state, feet planted, so a resting cat reads as alive.
# Render-only — driven by the per-player `_breath_phase` accumulator, never the sim.
#
# Motion (#760): GIF frame-analysis of Mario `Wait1` shows the idle is mostly a
# whole-body vertical BOB (translation, ±5.3% of body height — the feet lift too),
# with only a minor SQUASH (body-height change, ±2.4%). So the effect is a bob plus
# a small in-phase squash, NOT the feet-planted squash-only of the first #567 pass.
# Amplitudes = the GIF fraction × Nalio's 60px body box (`repros/idle-breathing/
# mario_wait1.gif`; measurement in docs/research/2026-07-15-idle-breathing-cycle.md).
IDLE_BREATH_BOB_PX = 3  # whole-body translation amplitude (GIF ±5.3% × 60px ≈ ±3.2px, #760)
IDLE_BREATH_SQUASH_PX = 1  # in-phase body-height squash amplitude (GIF ±2.4% × 60px ≈ ±1.4px, #760)
# Period, PER ARCHETYPE, in render-frames for ONE breath. Sourced, not guessed:
# the PM `Wait1` idle subaction LOOP length is datamined from the .pac via
# brawllib_rs (#753), and the number of breaths per loop is read off the rendered
# GIF (#567 review). Nalio = Mario: Wait1 loop = 51 frames containing 2 breaths,
# so one breath = 51/2 = 25.5 frames (~0.43s at FPS=60). An archetype ABSENT from
# this map does not breathe yet — its own Wait1 must be datamined first (one #567
# follow-up per archetype: Narz, Birky, …).
_NALIO_WAIT1_LOOP_FRAMES = 51  # brawllib_rs #753 (FOUND) — PM Mario Wait1 loop length
_NALIO_BREATHS_PER_LOOP = 2  # GIF-verified (#567): two rise/falls per Wait1 loop
_IDLE_BREATH_PERIOD_FRAMES = {
    "nalio": _NALIO_WAIT1_LOOP_FRAMES / _NALIO_BREATHS_PER_LOOP,  # 25.5 frames/breath
}


def idle_breath_wave(character_key, state, phase, *, enabled=True):
    """Gated unit breathing waveform in [-1, 1] for the idle loop (#567/#760).

    Returns 0.0 unless breathing is `enabled`, the fighter is in the `idle` state, and
    `character_key` names an archetype with a datamined period (`_IDLE_BREATH_PERIOD_FRAMES`).
    Otherwise returns `sin(2π * phase / period)` — the raw waveform the caller scales into
    a bob (`IDLE_BREATH_BOB_PX`) and a squash (`IDLE_BREATH_SQUASH_PX`). Pure — no pygame,
    no player state — so the gate + waveform are unit-testable in isolation."""
    if not enabled or state != "idle":
        return 0.0
    period = _IDLE_BREATH_PERIOD_FRAMES.get(character_key)
    if not period:
        return 0.0
    return math.sin(2 * math.pi * phase / period)


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
