"""
Purpose: Pure windowed-scale helpers for the display layer (#82).

The sim renders at a fixed 960x540 internal resolution; these helpers decide how
that internal surface is presented in a window at a chosen scale preset. They are
intentionally free of pygame side effects so the sizing/mode/cycle logic is unit
-testable headlessly; game.py owns the actual surface creation and blitting.

Use: window_size_for / blit_mode_for / cycle_preset from game.py's present path.
"""
import pygame  # type: ignore

from .config import SCREEN_WIDTH, SCREEN_HEIGHT

# Selectable windowed-scale presets (multiples of the 960x540 base). Integer
# steps (1x, 2x) are pixel-crisp; fractional steps (1.5x, 2.5x) are smooth-scaled.
WINDOWED_SCALE_PRESETS = (1.0, 1.5, 2.0, 2.5)

# Fullscreen magnification cycle (#85): the game view is drawn at this zoom and
# centred (letterboxed) inside the full-monitor window. "fit" is the auto crisp
# max-fit; the numeric presets are clamped to what the monitor can show.
FULLSCREEN_ZOOM_PRESETS = ("fit", 1.0, 1.5, 2.0, 2.5)


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
