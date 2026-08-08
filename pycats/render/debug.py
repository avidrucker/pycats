# pycats/render/debug.py
"""The hit/hurtbox debug overlay (#219): outline-only circles over active attack
hitboxes and each fighter's true (posture/move-resolved) hurtbox. Default OFF via
runtime_settings, so the live game and goldens are untouched until toggled on.

Extracted verbatim from render_battle (#900, child 3 of #833).
"""

import pygame

from ..combat.geometry import resolve_circle
from ..config import RED
from ..storage import runtime_settings

HITBOX_OVERLAY_COLOR = RED  # attack hitbox circles
HURTBOX_OVERLAY_COLOR = (0, 255, 255)  # cyan — fighter hurtbox circles
OVERLAY_LINE_WIDTH = 2  # >0 → pygame draws an outline, not a disc


def _active_hurtbox(p):
    """The hurtbox hit_resolution.process_hits actually tests against `p` this frame.

    Mirrors that resolver's selection (#124 crouch / #173 prone lower the box so
    high attacks whiff) so the overlay shows the *true* vulnerable region, not a
    stale stand box. Read defensively — a minimal combat stand-in may lack
    `crouch_hurtbox`/`prone_hurtbox`/`state`."""
    hurtbox = p.fighter_data.hurtbox
    # Per-move hurtbox override (#835, R2): mirror the sim resolver
    # (hit_resolution.process_hits) — an executing move's own Hurtbox REPLACES the
    # posture box, so the overlay shows the true region. Kept in lockstep with
    # the sim; a divergence is a bug.
    active_move = getattr(p, "current_move", None)
    if active_move is not None and active_move.hurtbox is not None:
        return active_move.hurtbox
    state = getattr(p, "state", None)
    if state == "crouch" and getattr(p.fighter, "crouch_hurtbox", None) is not None:
        return p.fighter.crouch_hurtbox
    if state == "prone" and getattr(p.fighter, "prone_hurtbox", None) is not None:
        return p.fighter.prone_hurtbox
    return hurtbox


def render_hitbox_overlay(surface, players, attacks):
    """Draw the hit/hurtbox debug overlay (#219), dev-gated + backtick-coupled.

    Render-only: reads the SAME data hit_resolution.process_hits resolves — `atk.resolved`
    for active hitbox circles, `resolve_circle` on each fighter's active hurtbox —
    and outlines them in two distinct colours.

    Gate (#1324, B2 reconciliation on #1297): renders only when BOTH the process-wide
    dev-mode gate (#1312) AND the dev-HUD master switch (#1319) are on. Outside dev mode
    it never draws — so the shipping game and goldens are untouched. Inside dev mode it
    follows backtick: game.main seeds dev_hud = dev_mode() at boot (overlay defaults ON),
    and each backtick press flips the text dev HUD and this overlay together."""
    if not (runtime_settings.dev_mode() and runtime_settings.dev_hud()):
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
