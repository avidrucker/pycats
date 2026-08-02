"""FrozenRect — the sim's immutable, pygame-free axis-aligned box (#975/#833 §6).

The simulation ran on `pygame.Rect` as its body/attack/platform box. That coupled
the deterministic sim to pygame (against ADR-0004) and, worse, made the box a
*mutable alias*: physics mutated `fighter.rect.left`/`.bottom` in place, so a rect
handed to two readers could change under one of them. `FrozenRect` replaces it
with a frozen value type — every "move" returns a new box (`with_*`), so there is
no in-place mutation and no shared-alias risk, and the `core` package imports with
pygame absent.

**Faithful to `pygame.Rect`'s integer arithmetic — on purpose.** pygame stores rect
coords as ints and truncates a float toward zero on assignment; the physics depends
on that (e.g. `core.physics.move_rect` lets `rect.y += vel.y` truncate each frame —
rounding it would move the golden sims, #949/#979). So FrozenRect:

- truncates every coordinate toward zero at construction (``int(v)``), exactly like
  a ``pygame.Rect`` assignment;
- derives centres with floor division (``centerx = x + w // 2``), matching pygame;
- ``colliderect`` excludes touching edges and treats an empty (w<=0 or h<=0) rect as
  non-colliding, matching pygame/SDL.

`test_geometry.py` pins this parity against real `pygame.Rect` across a grid of
sizes and positions. Read-only consumers (render, controllers, golden snapshots)
use the same accessor names as pygame.Rect, so they are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrozenRect:
    """Immutable integer box mirroring the subset of ``pygame.Rect`` the sim uses.

    Coordinates are truncated toward zero at construction (pygame assignment
    semantics). Mutating operations are spelled ``with_*`` and return a new
    ``FrozenRect``; the original is never changed.
    """

    x: int
    y: int
    w: int
    h: int

    def __post_init__(self) -> None:
        # Truncate toward zero, exactly like assigning a float to a pygame.Rect
        # coord. object.__setattr__ is the frozen-dataclass idiom for coercing in
        # __post_init__.
        object.__setattr__(self, "x", int(self.x))
        object.__setattr__(self, "y", int(self.y))
        object.__setattr__(self, "w", int(self.w))
        object.__setattr__(self, "h", int(self.h))

    # ---------- read accessors (names match pygame.Rect) ----------
    @property
    def width(self) -> int:
        return self.w

    @property
    def height(self) -> int:
        return self.h

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def centerx(self) -> int:
        return self.x + self.w // 2

    @property
    def centery(self) -> int:
        return self.y + self.h // 2

    @property
    def center(self) -> tuple[int, int]:
        return (self.centerx, self.centery)

    @property
    def midbottom(self) -> tuple[int, int]:
        return (self.centerx, self.bottom)

    @property
    def midtop(self) -> tuple[int, int]:
        return (self.centerx, self.top)

    @property
    def topleft(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def size(self) -> tuple[int, int]:
        return (self.w, self.h)

    def colliderect(self, other) -> bool:
        """True iff this box overlaps ``other`` (any object exposing x/y/w/h).

        Matches pygame/SDL: touching edges do NOT collide, and an empty box
        (w<=0 or h<=0) on either side never collides.
        """
        if self.w <= 0 or self.h <= 0 or other.w <= 0 or other.h <= 0:
            return False
        return (
            self.x < other.x + other.w
            and self.y < other.y + other.h
            and self.x + self.w > other.x
            and self.y + self.h > other.y
        )

    # ---------- with_* (return a new FrozenRect; nothing mutates in place) ----------
    # Each truncates its input toward zero before the integer arithmetic, so the
    # result matches the corresponding pygame.Rect attribute assignment.
    def with_x(self, value) -> FrozenRect:
        return FrozenRect(int(value), self.y, self.w, self.h)

    def with_y(self, value) -> FrozenRect:
        return FrozenRect(self.x, int(value), self.w, self.h)

    def with_left(self, value) -> FrozenRect:
        return FrozenRect(int(value), self.y, self.w, self.h)

    def with_top(self, value) -> FrozenRect:
        return FrozenRect(self.x, int(value), self.w, self.h)

    def with_right(self, value) -> FrozenRect:
        return FrozenRect(int(value) - self.w, self.y, self.w, self.h)

    def with_bottom(self, value) -> FrozenRect:
        return FrozenRect(self.x, int(value) - self.h, self.w, self.h)

    def with_centerx(self, value) -> FrozenRect:
        return FrozenRect(int(value) - self.w // 2, self.y, self.w, self.h)

    def with_centery(self, value) -> FrozenRect:
        return FrozenRect(self.x, int(value) - self.h // 2, self.w, self.h)

    def with_topleft(self, pos) -> FrozenRect:
        return FrozenRect(pos[0], pos[1], self.w, self.h)

    def with_center(self, pos) -> FrozenRect:
        return FrozenRect(int(pos[0]) - self.w // 2, int(pos[1]) - self.h // 2, self.w, self.h)

    def with_midbottom(self, pos) -> FrozenRect:
        return FrozenRect(int(pos[0]) - self.w // 2, int(pos[1]) - self.h, self.w, self.h)

    def with_size(self, size) -> FrozenRect:
        # pygame's `.size =` keeps the topleft and changes w/h (center shifts).
        return FrozenRect(self.x, self.y, size[0], size[1])

    def moved(self, dx, dy) -> FrozenRect:
        """New box translated by (dx, dy), truncating toward zero (pygame semantics
        for `rect.x += dx; rect.y += dy`). Used by the physics step."""
        return FrozenRect(int(self.x + dx), int(self.y + dy), self.w, self.h)
