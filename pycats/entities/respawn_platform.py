"""Weave per-fighter revival platforms into the frame's platform list (#1334).

The stage platform list is owned by the driver (`sim/runner`, `screens/battle_screen`)
and passed into the sim each frame. A revival platform, by contrast, is transient and
per-fighter — it lives on `Fighter.respawn_platform` for the duration of a REBIRTH. This
helper merges any live revival platforms into the stage list so collision (fighter stands
on / drops through it), player-push, projectile bounce, and render all see it, without
changing the driver's ownership of the base stage.

Byte-identical when nobody is respawning: with no live revival platform it returns the
caller's list object unchanged (the golden/no-KO path is untouched)."""

from __future__ import annotations


def active_platforms(players, platforms):
    """`platforms` plus each player's live `respawn_platform` (a thin Platform), or the
    unchanged `platforms` when no fighter is in REBIRTH."""
    extra = [p.fighter.respawn_platform for p in players if p.fighter.respawn_platform is not None]
    if not extra:
        return platforms
    return list(platforms) + extra
