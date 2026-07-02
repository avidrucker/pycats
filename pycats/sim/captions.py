# pycats/sim/captions.py
"""On-screen captions for sims/demos (#306, epic #308).

Captions are **plain data** — a `Caption` carries its text, anchor, font, size, colour
and an optional frame window. A demo is just a *list* of them, so it composes with the
choreography seam and is editable without touching any render code. The presenters draw
the captions active on each frame **over** the battle; nothing here touches the sim, so
it is a presentation overlay only (golden-safe).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import pygame

from ..config import WHITE
from .. import text_utils

# Anchors — horizontally centred; vertical position per name.
TOP_CENTER = "top_center"
MIDDLE_CENTER = "middle_center"
BOTTOM_CENTER = "bottom_center"

CAPTION_MARGIN = 24  # px from the top/bottom edge for TOP/BOTTOM anchors


@dataclass(frozen=True)
class Caption:
    """One caption. `font` is a SysFont name OR a .ttf path OR None (the default font);
    `frames=(start, end)` shows it only within that inclusive frame window (None = always).
    `dwell` (#352) = extra frames the presenter FREEZES on this caption so a viewer can
    read it before the action resumes (0 = no hold; presentation-only). `dwell_at` (#412)
    = the frame to freeze on; None freezes the window start (the default), but a beat whose
    action lands late in its window can point it at the payoff frame so the frozen frame
    shows the action, not a pre-action pose. Must lie within `frames` (validated upstream)."""
    text: str
    anchor: str = BOTTOM_CENTER
    size: int = 36
    font: Optional[str] = None
    color: Tuple[int, int, int] = WHITE
    frames: Optional[Tuple[int, int]] = None
    dwell: int = 0
    dwell_at: Optional[int] = None


def is_active(caption: Caption, frame: int) -> bool:
    """Whether `caption` should show on `frame` (untimed captions always show)."""
    if caption.frames is None:
        return True
    start, end = caption.frames
    return start <= frame <= end


def caption_hold_frames(captions: Sequence[Caption], frame: int) -> int:
    """Extra frames the presenter should FREEZE on `frame` because a dwelling caption
    holds here (#352). A caption with `dwell > 0` freezes the display (re-presents the
    same frame) so the viewer reads it before the action resumes. The hold fires on the
    caption's `dwell_at` frame if set, else its window start (#412) — so a late-payoff
    beat can freeze on the action instead of a pre-action pose. Returns the max dwell
    among captions holding on `frame` (0 = no hold). Untimed captions (no window) never
    hold — there is no frame window to anchor to."""
    holds = [c.dwell for c in captions
             if c.dwell and c.frames is not None
             and (c.frames[0] if c.dwell_at is None else c.dwell_at) == frame]
    return max(holds) if holds else 0


def anchored_rect(anchor: str, surface_size, text_size, margin: int = CAPTION_MARGIN) -> pygame.Rect:
    """The blit rect for `text_size` text at `anchor` on a `surface_size` surface —
    horizontally centred; top/bottom inset by `margin`, middle vertically centred."""
    w, h = surface_size
    rect = pygame.Rect(0, 0, text_size[0], text_size[1])
    if anchor == TOP_CENTER:
        rect.midtop = (w // 2, margin)
    elif anchor == MIDDLE_CENTER:
        rect.center = (w // 2, h // 2)
    elif anchor == BOTTOM_CENTER:
        rect.midbottom = (w // 2, h - margin)
    else:
        raise ValueError(f"unknown caption anchor: {anchor!r}")
    return rect


def render_caption_surface(caption: Caption) -> pygame.Surface:
    """Render `caption`'s text to a surface, honouring its font (name/path/default) +
    size + colour. Reuses text_utils' font cache so per-frame draws don't rebuild fonts."""
    font = text_utils.text_renderer._get_font(caption.font, caption.size)
    return font.render(caption.text, True, caption.color)


def draw_caption(surface: pygame.Surface, caption: Caption) -> None:
    """Blit one caption onto `surface` at its anchor (ignores the frame window)."""
    text_surf = render_caption_surface(caption)
    rect = anchored_rect(caption.anchor, surface.get_size(), text_surf.get_size())
    surface.blit(text_surf, rect)


def draw_captions(surface: pygame.Surface, captions: Sequence[Caption], frame: int) -> None:
    """Draw every caption active on `frame`, in list order (later overlaps earlier)."""
    for caption in captions:
        if is_active(caption, frame):
            draw_caption(surface, caption)
