"""Grabbable stage edges (#14). A Ledge is a solid platform's top corner plus a
catch region and the hang/getup geometry. occupied_by enforces the one-occupant
lockout (PM edge-hog without trump; trump is a deferred follow-up)."""
from __future__ import annotations

import pygame  # type: ignore

from .. import config

LEFT = "left"
RIGHT = "right"


def ledge_invuln_frames(percent: float) -> int:
    """Ledge-grab intangibility burst, scaled by the occupant's percent (#311).

    Monotonic non-decreasing: a Brawl-baseline burst at 0% that grows with damage
    (higher % -> longer invincibility, the PM edge-hog fidelity), capped. Replaces
    #14's flat full-hang intangibility. ⚠ playtest curve; per-character later (#117).
    """
    frames = config.LEDGE_INVULN_BASE_FRAMES + round(percent * config.LEDGE_INVULN_PER_PERCENT)
    return min(frames, config.LEDGE_INVULN_MAX_FRAMES)


class Ledge:
    """One grabbable stage edge.

    side       — LEFT or RIGHT (which corner of the solid platform).
    ax, ay     — the corner anchor: the stage edge x and the lip (platform top) y.
    occupied_by — the fighter/player currently hanging here, or None.
    """

    def __init__(self, side: str, ax: int, ay: int):
        self.side = side
        self.ax = ax
        self.ay = ay
        self.occupied_by = None

    def catch_rect(self) -> pygame.Rect:
        """The off-stage box that, when the fighter's body overlaps it while
        descending, triggers a grab. Hangs outward from the corner and below the
        lip."""
        w, h = config.LEDGE_CATCH_W, config.LEDGE_CATCH_H
        left = self.ax - w if self.side == LEFT else self.ax
        return pygame.Rect(left, self.ay, w, h)

    def hang_topleft(self, size):
        """Rect top-left a hanging fighter snaps to — body just off the lip, on the
        off-stage side."""
        w, _h = size
        x = self.ax - w if self.side == LEFT else self.ax
        return (x, self.ay)

    def getup_topleft(self, size):
        """Rect top-left for standing on the stage at the corner (feet on the lip)."""
        w, h = size
        x = self.ax if self.side == LEFT else self.ax - w
        return (x, self.ay - h)

    def facing_right(self) -> bool:
        """A hanging fighter faces toward the stage."""
        return self.side == LEFT

    def away_held(self, left_held: bool, right_held: bool) -> bool:
        """True when the off-stage horizontal direction is held (drop intent)."""
        return left_held if self.side == LEFT else right_held


def ledges_from_platforms(platforms):
    """Build the grabbable edges: one LEFT + one RIGHT per solid (thick) platform.
    Thin/pass-through platforms are not grabbable (owner ruling on #14)."""
    ledges = []
    for p in platforms:
        if getattr(p, "thin", False):
            continue
        r = p.rect
        ledges.append(Ledge(LEFT, r.left, r.top))
        ledges.append(Ledge(RIGHT, r.right, r.top))
    return ledges
