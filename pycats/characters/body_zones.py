"""Body-relative vertical zones for authoring hitbox dy offsets (#309).

A hitbox `Circle(dx, dy, r)` offsets from the fighter's body **top-left**, so `dy`
grows downward: `dy = 0` is the head/top, `dy = H` is the feet/bottom, for a body of
standing height `H`. Historically each `*_cat.py` hardcoded an absolute `dy` tuned to
the default 60-tall body. When a fighter has a different body height (Birky is 44,
#275) those absolute offsets sit at the wrong place — worst case Birky's d-tilt hung
*below the feet, into the floor*.

`zone_dy` resolves a **named vertical zone** against the fighter's own body height, so
a move authored "at the feet" lands at the feet on any body size — the same authoring
scheme works for Kirby-small and DK-big bodies as the #117 roster grows. Values are
still `⚠ playtest starting point`s (per ADR-0003); the zone fractions just make the
placement body-relative instead of pinned to one body. Faithful OG-derived positions
are the separate #310 research spike.
"""

from __future__ import annotations

# Vertical zones as a fraction of the fighter's standing body height, measured from
# the body top-left (0.0 = head, 1.0 = feet). Chosen so that on the default 60-tall
# body they reproduce the historical placements (head ~9, center ~30, feet ~51) and,
# critically, on any body a "feet" move stays ON the body while "below_feet" is a
# bounded spike just past the feet.
BODY_ZONES: dict[str, float] = {
    "head": 0.15,  # up at/over the head — juggle & anti-air (u-tilt, u-air)
    "center": 0.50,  # mid-body — jabs and most normals/aerials
    "feet": 0.85,  # low on the body near the feet — low pokes (d-tilt)
    "below_feet": 1.10,  # just past the feet — bounded downward spikes (d-air)
}


def zone_dy(zone: str, body_h: int, nudge: int = 0) -> int:
    """Resolve a named vertical zone to an absolute dy (px from the body top-left).

    Args:
        zone:   one of BODY_ZONES ("head" / "center" / "feet" / "below_feet").
        body_h: the fighter's standing body height in px (e.g. `stand_size[1]`).
        nudge:  a small px shift within the zone, to preserve the relative ordering
                of a move's multiple hitboxes (e.g. a two-box poke). Defaults to 0.

    Returns:
        The pixel dy for a Circle, body-relative so the zone lands correctly on any
        body height. Raises KeyError on an unknown zone (a typo shouldn't silently
        place a hitbox at 0).
    """
    return round(BODY_ZONES[zone] * body_h) + nudge
