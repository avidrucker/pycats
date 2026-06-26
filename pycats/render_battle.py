# pycats/render_battle.py
"""Shared battle renderer: draws the stage, fighters, and attacks onto a surface.
Extracted from game.py so the live game, pause screen, and sim presenters all
use one renderer."""
import math

import pygame

# Dizzy stars drawn above a shield-broken (#12) fighter's head. Cosmetic only
# (rendering is not golden-snapshotted), so these live here in the renderer.
DIZZY_STAR_COUNT = 3       # stars orbiting the head
DIZZY_ORBIT_RADIUS = 16    # horizontal orbit radius (px)
DIZZY_ORBIT_LIFT = 8       # gap above the ear tips
DIZZY_STAR_OUTER = 5       # star spike radius
DIZZY_STAR_INNER = 2       # star inner radius
DIZZY_SPIN_SPEED = 0.18    # radians of orbit advance per frame (per stun tick)

from .config import (
    EYE_OFFSET_X, EYE_OFFSET_Y, EYE_RADIUS, GLINT_OFFSET_X, GLINT_OFFSET_Y,
    GLINT_RADIUS, EAR_WIDTH, EAR_HEIGHT, EAR_SPACING, EAR_PADDING,
    WHISKER_LENGTH, WHISKER_THICKNESS, WHISKER_COUNT, WHISKER_ANGLE,
    WHISKER_OFFSET_Y, WHISKER_OFFSET_X, STRIPE_COUNT, STRIPE_WIDTH,
    STRIPE_HEIGHT, STRIPE_SPACING, SHIELD_COLOR, SHIELD_MAX_HP,
    MAX_SHIELD_RADIUS, MIN_SHIELD_RADIUS, WHITE, RED, YELLOW, PLAYER_SIZE,
)
from . import text_utils
from . import cat_faces
from .entities import Player


# --- draw helpers moved verbatim from game.py ---

def draw_eye(surface, p: Player, eye=True):
    if eye:
        x = (
            p.rect.right - EYE_OFFSET_X
            if p.facing_right
            else p.rect.left + EYE_OFFSET_X
        )
        y = p.rect.top + EYE_OFFSET_Y
        pygame.draw.circle(surface, p.eye_color, (x, y), EYE_RADIUS)
    else:  # we will draw a glint instead of an eye
        x = (
            p.rect.right - GLINT_OFFSET_X
            if p.facing_right
            else p.rect.left + GLINT_OFFSET_X
        )
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

    # for both ears, if the player if facing right, move the ears to the left by PADDING, else, move the ears to the right by PADDING
    if p.facing_right:
        left_ear_points = [(x - EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x - EAR_PADDING, y) for x, y in right_ear_points]
    else:
        left_ear_points = [(x + EAR_PADDING, y) for x, y in left_ear_points]
        right_ear_points = [(x + EAR_PADDING, y) for x, y in right_ear_points]

    # Draw ears
    pygame.draw.polygon(surface, p.char_color, left_ear_points)
    pygame.draw.polygon(surface, p.char_color, right_ear_points)

    # Draw whiskers (lines)
    whisker_start_x = (
        p.rect.right - WHISKER_OFFSET_X
        if p.facing_right
        else p.rect.left + WHISKER_OFFSET_X
    )
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

        # Use WHITE color for all whiskers instead of eye_color
        pygame.draw.line(surface, WHITE, start_pos, end_pos, WHISKER_THICKNESS)


def draw_stripes(surface, p: Player):
    """Draws triangular stripes on the player's back for pattern."""
    # Calculate stripe positions on the back of the player
    back_center_x = p.rect.centerx + (-10 if p.facing_right else 10)
    back_start_y = p.rect.top + 15  # Start stripes a bit down from the top

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

        # Draw the triangular stripe
        pygame.draw.polygon(surface, p.stripe_color, stripe_points)


def draw_player_name(surface, p: Player):
    """Draw the player name above the cat."""
    # Choose color based on player name
    if p.char_name == "P1":
        color = (255, 100, 100)  # Red
    else:
        color = (100, 100, 255)  # Blue

    text_utils.render_text(
        surface, p.char_name, (p.rect.centerx, p.rect.top - 25), 20, color, center=True
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
_body_cache: dict = {}


class _CatShim:
    """Minimal stand-in exposing the attributes the draw_* helpers read, with a
    virtual rect positioned inside the composite surface."""
    __slots__ = ("rect", "facing_right", "char_color", "eye_color",
                 "stripe_color", "char_name")

    def __init__(self, rect, facing_right, char_color, eye_color, stripe_color,
                 char_name):
        self.rect = rect
        self.facing_right = facing_right
        self.char_color = char_color
        self.eye_color = eye_color
        self.stripe_color = stripe_color
        self.char_name = char_name


def body_tint(p):
    """The body fill colour for a fighter this frame (#75 / D1 slice 1).

    Pure function of observable state: RED while hurt, YELLOW while stunned,
    WHITE while dodging, else the character colour. Replaces the old
    Player.image.fill(...) adapter mutations — the entity no longer carries its
    own pixels; the tint is computed here at render time. Timer-driven (not
    state-label-driven) to match the old fill exactly: the flash is present
    while the timer is live and clears the frame it hits 0.
    """
    if p.hurt_timer > 0:
        return RED
    if p.stun_timer > 0:
        return YELLOW
    if p.dodge_timer > 0:
        return WHITE
    return p.char_color


def _cat_body_surface(p, face_style=cat_faces.PRIMITIVES):
    """Return the cached body composite for player `p` (built on first use).

    `face_style` (#108) selects how the face is drawn: PRIMITIVES (default —
    eyes + ears + whiskers) or a glyph style (kaomoji/emoji) blitted over the
    head. It is part of the cache key so toggling re-renders."""
    w, h = PLAYER_SIZE
    tint = tuple(body_tint(p))
    key = (tuple(p.char_color), tuple(p.stripe_color), tuple(p.eye_color),
           p.char_name, p.facing_right, tint, face_style)
    surf = _body_cache.get(key)
    if surf is None:
        cw = w + 2 * _BODY_PAD_X
        ch = _BODY_PAD_TOP + h + _BODY_PAD_BOT
        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        vrect = pygame.Rect(_BODY_PAD_X, _BODY_PAD_TOP, w, h)
        shim = _CatShim(vrect, p.facing_right, p.char_color, p.eye_color,
                        p.stripe_color, p.char_name)
        body = pygame.Surface((w, h))
        body.fill(tint)
        surf.blit(body, vrect)
        draw_stripes(surf, shim)
        # Face: a glyph style replaces the primitive eyes + ears + whiskers;
        # falls back to primitives when the glyph can't render (font missing).
        face = cat_faces.render_face(
            face_style, p.facing_right, cat_faces.ink_for(p.char_color)
        )
        if face is not None:
            surf.blit(face, face.get_rect(center=(vrect.centerx, vrect.top + 10)))
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
    if p.stun_timer <= 0:
        return
    cx = p.rect.centerx
    cy = p.rect.top - EAR_HEIGHT - DIZZY_ORBIT_LIFT
    phase = p.stun_timer * DIZZY_SPIN_SPEED
    for i in range(DIZZY_STAR_COUNT):
        ang = phase + i * (2 * math.pi / DIZZY_STAR_COUNT)
        sx = cx + math.cos(ang) * DIZZY_ORBIT_RADIUS
        sy = cy + math.sin(ang) * DIZZY_ORBIT_RADIUS * 0.4   # flatten to an ellipse
        pygame.draw.polygon(
            surface, YELLOW,
            _star_points(sx, sy, DIZZY_STAR_OUTER, DIZZY_STAR_INNER, 5, ang),
        )


def render_battle(surface, players, platforms):
    """Draw platforms, alive fighters, and their attacks onto `surface`.
    Mirrors game.py's playing-branch draw block (no HUD/controls/FPS text)."""
    for pl in platforms:
        surface.blit(pl.image, pl.rect)
    for p in players:
        if not p.is_alive:
            continue
        p.tail.draw(surface)
        # Body composite (rect + stripes + eyes + ears + whiskers + name).
        body = _cat_body_surface(p, getattr(p, "face_style", cat_faces.PRIMITIVES))
        surface.blit(body, (p.rect.x - _BODY_PAD_X, p.rect.y - _BODY_PAD_TOP))
        if p.stun_timer > 0:
            draw_dizzy_stars(surface, p)
        if p.state == "shield":
            ratio = p.shield_hp / SHIELD_MAX_HP
            shield_radius = int(MAX_SHIELD_RADIUS * ratio)
            r = max(MIN_SHIELD_RADIUS, shield_radius)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*SHIELD_COLOR, 100), (r, r), r)
            surface.blit(s, (p.rect.centerx - r, p.rect.centery - r))


def render_attacks(surface, attacks):
    for a in attacks:
        surface.blit(a.image, a.rect)
