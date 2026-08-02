# pycats/render/battle.py
"""The battle renderer's top-level draw entry points: `render_battle` (platforms +
fighters + posture/breath animation + shield bubble + status feedback) and
`render_attacks` (the attack hitbox visuals).

Extracted from render_battle.py (#900, child 3 of #833) — this module wires the
body / tint / status submodules and the pure status model into the per-frame draw
loop. Byte-identical to the pre-#900 renderer; the render-parity oracle guards it.
"""

import pygame

from .. import cat_faces, runtime_settings
from ..config import (
    ATTACK_SIZE,
    MAX_SHIELD_RADIUS,
    MIN_SHIELD_RADIUS,
    SHIELD_COLOR,
    SHIELD_MAX_HP,
)
from ..systems.status_model import grabs_left_dots, timer_bar_specs
from .body import (
    _BODY_PAD_TOP,
    _BODY_PAD_X,
    _IDLE_BREATH_PERIOD_FRAMES,
    IDLE_BREATH_BOB_PX,
    IDLE_BREATH_SQUASH_PX,
    _cat_body_layers,
    idle_breath_wave,
    render_tail,
    slot_accent_color,
)
from .status import draw_dizzy_stars, draw_grabs_left_dots, draw_timer_bars
from .tint import tinted

# Platform fill colours (#317/H-b): moved out of Platform (which no longer owns a
# Surface) so the adapter paints the rect. Thick = solid stage, thin = pass-through.
PLATFORM_THICK = (164, 113, 73)
PLATFORM_THIN = (193, 153, 112)

# Attack visual colours (#326/H-b): moved out of Attack with its Surface-building.
ATTACK_SINGLE_FILL = (255, 60, 60, 180)  # legacy single-hitbox flat red
ATTACK_FILL = (255, 60, 60, 120)  # per-circle semi-transparent red fill
ATTACK_OUTLINE = (255, 230, 120, 220)  # per-circle outline
ATTACK_OUTLINE_WIDTH = 2  # per-circle outline stroke width (px)

SHIELD_FILL_ALPHA = 100  # alpha of the translucent shield-bubble fill

# Crouch squash easing (#124): fraction of the stand→crouch transition covered
# per rendered frame (~3 frames to settle). Render-only; not part of the sim.
_CROUCH_ANIM_RATE = 0.34


def render_battle(surface, players, platforms):
    """Draw platforms, alive fighters, and their attacks onto `surface`.
    Mirrors game.py's playing-branch draw block (no HUD/controls/FPS text)."""
    for pl in platforms:
        # #317/H-b: the platform holds only data (rect + thin); the adapter paints
        # its thickness colour (was Platform.image, an entity-owned Surface). The
        # sim box is a pygame-free FrozenRect (#975); pygame.draw.rect takes an
        # (x, y, w, h) sequence, so hand it the box's tuple form at this boundary.
        r = pl.rect
        pygame.draw.rect(surface, PLATFORM_THIN if pl.thin else PLATFORM_THICK, (r.x, r.y, r.w, r.h))
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
        # Idle breathing (#567): advance the render-only phase clock only while the
        # effect is live (idle state, breathing on, this archetype has a datamined
        # period), then read the px height delta. Mutually exclusive with the crouch/
        # prone squash below — breathing fires only in idle, where low_h == stand_h —
        # so the two never fight over the body height.
        breath_key = getattr(getattr(p, "character", None), "key", None)
        breath_on = runtime_settings.show_idle_breathing()
        if breath_on and p.state == "idle" and breath_key in _IDLE_BREATH_PERIOD_FRAMES:
            p._breath_phase = getattr(p, "_breath_phase", 0.0) + 1.0
        breath_w = idle_breath_wave(breath_key, p.state, getattr(p, "_breath_phase", 0.0), enabled=breath_on)
        if anim > 0.0 and low_h != stand_h:
            s = (stand_h + (low_h - stand_h) * anim) / stand_h
            size = (ring_layer.get_width(), max(1, round(ring_layer.get_height() * s)))
            ring_layer = pygame.transform.scale(ring_layer, size)
            body_layer = pygame.transform.scale(body_layer, size)
            blit_y = round(p.rect.bottom - (_BODY_PAD_TOP + stand_h) * s)
        elif breath_w:
            # Idle breathing (#567/#760): a whole-body BOB (translation) plus a small
            # in-phase SQUASH, driven by the same waveform. At the top of the breath
            # (w > 0) the body lifts by `bob_px` AND stretches a touch taller (inhale);
            # at the bottom it settles and shortens. GIF-measured on Nalio's 60px body.
            squash_px = IDLE_BREATH_SQUASH_PX * breath_w
            bob_px = IDLE_BREATH_BOB_PX * breath_w
            s = (stand_h + squash_px) / stand_h
            size = (ring_layer.get_width(), max(1, round(ring_layer.get_height() * s)))
            ring_layer = pygame.transform.scale(ring_layer, size)
            body_layer = pygame.transform.scale(body_layer, size)
            # feet-anchored squash, then lift the whole composite by the bob (feet lift too)
            blit_y = round(p.rect.bottom - (_BODY_PAD_TOP + stand_h) * s - bob_px)
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
        # blit uses only the dest rect's topleft; a.rect is a pygame-free
        # FrozenRect (#975), so pass its topleft tuple at this render boundary.
        surface.blit(_attack_surface(a), a.rect.topleft)
