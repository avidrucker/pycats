"""
Purpose: Pure windowed-scale helpers for the display layer (#82).

The sim renders at a fixed 960x540 internal resolution; these helpers decide how
that internal surface is presented in a window at a chosen scale preset. They are
intentionally free of pygame side effects so the sizing/mode/cycle logic is unit
-testable headlessly; game.py owns the actual surface creation and blitting.

Use: window_size_for / blit_mode_for / cycle_preset from game.py's present path.
"""
import pygame  # type: ignore

from .config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

# How long the zoom toast stays on screen after an F10 change (#89).
TOAST_DURATION_FRAMES = 3 * FPS

# Selectable windowed-scale presets (multiples of the 960x540 base). Integer
# steps (1x, 2x) are pixel-crisp; fractional steps (1.5x, 2.5x) are smooth-scaled.
WINDOWED_SCALE_PRESETS = (1.0, 1.5, 2.0, 2.5)

def fit_scale(display_size, base=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Largest scale that fits `base` inside `display_size`, preferring a crisp
    whole-number multiple. If no integer >= 1 fits (display smaller than base on
    some axis), fall back to the largest fractional scale that fits."""
    dw, dh = display_size
    base_w, base_h = base
    max_int = min(dw // base_w, dh // base_h)
    if max_int >= 1:
        return float(max_int)
    return min(dw / base_w, dh / base_h)


def clamp_scale(scale, display_size, base=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """`scale` reduced (never increased) so `base * scale` still fits inside
    `display_size`. Keeps the chosen fractional value when it fits — only the
    limiting axis can pull it down. Guarantees the full stage stays on-screen."""
    dw, dh = display_size
    base_w, base_h = base
    return min(scale, dw / base_w, dh / base_h)


def achievable_zoom_scales(display_size, base=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Sorted, de-duplicated list of the *distinct* fullscreen zoom sizes a given
    monitor can actually show (#92): the auto fit_scale plus each windowed preset
    clamped to fit. Presets that clamp onto the same size collapse to one entry,
    so cycling this list changes the rendered size on every step (no dead F10
    presses). The largest entry is the most-zoomed-in size that still fits."""
    candidates = [fit_scale(display_size, base)]
    candidates += [clamp_scale(p, display_size, base) for p in WINDOWED_SCALE_PRESETS]
    distinct = {}
    for s in candidates:
        distinct.setdefault(round(s, 4), s)  # first value wins per rounded key
    return sorted(distinct.values())


def fullscreen_zoom_label(scale, scales):
    """Toast label for a fullscreen zoom: the largest achievable scale reads
    "Fit" (it is "as big as fits" — a clean integer like 2x or a clamped
    fractional like 1.42x), smaller clean presets read their value ("1×", ...)."""
    if scale == scales[-1]:
        return "Fit"
    return format_scale_label(scale)


def window_size_for(scale, base=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """(width, height) in pixels for a window at `scale` times the base size.

    Rounded to whole pixels; every shipped preset divides the 960x540 base
    evenly, so the result is exact for the presets.
    """
    base_w, base_h = base
    return (round(base_w * scale), round(base_h * scale))


def blit_mode_for(scale):
    """How to present the internal surface at `scale`:

    - "flip"   at 1x — no scaling; blit/flip the surface 1:1.
    - "crisp"  at whole multiples (2x, 3x, ...) — nearest-neighbour, pixel-perfect.
    - "smooth" at fractional scales (1.5x, 2.5x) — anti-aliased smoothscale, which
      reads cleanly for pycats' primitive-drawn art (no pixel-art grid to break).
    """
    if scale == 1.0:
        return "flip"
    if float(scale).is_integer():
        return "crisp"
    return "smooth"


def cycle_preset(current, step=1, presets=WINDOWED_SCALE_PRESETS):
    """Next preset after `current`, wrapping around the list.

    `step` is +1 (forward) or -1 (backward). If `current` is not a known preset
    (e.g. a fullscreen-derived scale), snap to the first preset.
    """
    try:
        i = presets.index(current)
    except ValueError:
        return presets[0]
    return presets[(i + step) % len(presets)]


def format_scale_label(value):
    """Short human label for a scale/zoom value: 1.0 -> "1×", 1.5 -> "1.5×",
    2.0 -> "2×", and the "fit" choice -> "Fit"."""
    if value == "fit":
        return "Fit"
    return f"{value:g}×"


class Toast:
    """A transient on-screen message with a frame countdown (#89).

    Pure timer/state holder — no pygame. game.py calls show() on an F10 change,
    tick() once per presented frame, and draws self.text while self.active."""

    def __init__(self):
        self.text = ""
        self.frames_left = 0

    def show(self, text, frames=TOAST_DURATION_FRAMES):
        """Display `text` for `frames` frames, resetting any current toast."""
        self.text = text
        self.frames_left = frames

    @property
    def active(self):
        return self.frames_left > 0

    def tick(self):
        """Advance one frame; clamps at 0 (idempotent once expired)."""
        if self.frames_left > 0:
            self.frames_left -= 1


def scale_surface(surface, scale):
    """Return `surface` presented at `scale`, picking the transform per
    blit_mode_for: the source itself at 1x (no copy), nearest-neighbour at whole
    multiples (crisp), smoothscale at fractional scales (anti-aliased)."""
    mode = blit_mode_for(scale)
    if mode == "flip":
        return surface
    target = window_size_for(scale, surface.get_size())
    if mode == "crisp":
        return pygame.transform.scale(surface, target)
    return pygame.transform.smoothscale(surface, target)
