# pycats/render/tint.py
"""Body-flash tint resolution (#109/#75): the one place a fighter's per-frame
flash overlay (RED hurt / YELLOW stun / WHITE dodge) is selected from the shared
`STATUS_SOURCES` table and blended into each part's base colour.

Extracted verbatim from render_battle (#900). Depends only on the pure status
model (`systems.status_model`) and config colours — render → systems, the
sanctioned direction.
"""

from ..systems import status_model

TINT_STRENGTH = 0.5  # #109: blend the flash 50% over each part's base colour


def active_tint(p):
    """The flash *overlay* colour for a fighter this frame, or None when calm.

    Derived from `STATUS_SOURCES` (#522): the first source (by precedence) that is
    live and declares a `tint` wins — RED while hurt, YELLOW while stunned, WHITE
    while dodging (#75), else None. `tinted()` blends it over a part's base colour
    and `body_tint()` resolves it for the body fill. Timer-driven (a flash is present
    while its timer is live and clears the frame it hits 0). Table defined below.

    Reads the table through the `status_model` module (not a from-import binding) so
    it and `status_model.timer_bar_specs` share a single `STATUS_SOURCES` lookup —
    registering a status (or a test monkeypatching the table) drives both (#522/#900).
    """
    f = p.fighter
    for s in sorted(status_model.STATUS_SOURCES, key=lambda src: src.precedence):
        if s.tint is not None and s.active(f, p):
            return s.tint
    return None


def _blend(base, overlay, strength=TINT_STRENGTH):
    """`base` blended `strength` of the way toward `overlay`; `base` if overlay
    is None. The low-level mix every tinted part shares (#109)."""
    if overlay is None:
        return tuple(base)
    return tuple(round(b + (o - b) * strength) for b, o in zip(base, overlay))


def tinted(base_color, p, strength=TINT_STRENGTH):
    """A part's drawn colour this frame: `base_color` softened ~50% toward the
    active hurt/stun/dodge flash, or unchanged when the fighter is calm (#109).

    The one helper every body part derives its colour from — body fill, ears,
    whiskers, stripes (via the body composite) and the tail (`render_tail`) — so
    no part keeps a hardcoded `char_color` path that can drift out of the flash.
    """
    return _blend(base_color, active_tint(p), strength)


def body_tint(p):
    """The body fill *selector* for a fighter this frame (#75 / D1 slice 1).

    Returns the solid overlay (RED hurt / YELLOW stun / WHITE dodge) or the
    character colour when calm — unchanged contract: callers and the composite
    cache key still distinguish the four states by this value. The 50% softening
    lives in `tinted()`, applied where the body is actually filled.
    """
    return active_tint(p) or p.char_color
