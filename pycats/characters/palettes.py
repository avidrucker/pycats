"""Presentation-only colour-palette source — Part 2 of epic #127 (#221).

Loads the alternate cat colour palettes from `palettes.json` (a sibling file) via a
safe, validate-on-load loader modelled on `pycats/settings.py`:

- **Never raises.** A missing / unreadable / non-JSON file falls back to the
  built-in `_DEFAULT_PALETTES` (the original six OG skins). A readable-but-partial
  file is taken as-is (validated) — a palette file is a hint, not authority.
- **Snaps** out-of-range colour channels to `[0, 255]`.
- **Skips** unrepairable entries (missing/short/non-numeric colour, missing name).
- `[r, g, b]` lists become `(r, g, b)` tuples at the boundary, so every consumer
  keeps reading tuples exactly like the old `OG_SKINS` literals.

A palette is the same dict shape the OG skins always had —
`{name, color, stripe_color, eye_color, description}` — so this is a non-breaking
re-source of `og_skins.OG_SKINS` / `config.CAT_CHARACTERS` (the character/skin
*separation* and the CSS picker are Part 3). Stdlib-only, no `config` import, to
stay dependency-free.
"""
from __future__ import annotations

import json
import os

_PALETTES_PATH = os.path.join(os.path.dirname(__file__), "palettes.json")

_COLOR_FIELDS = ("color", "stripe_color", "eye_color")

# Built-in fallback == the original six OG skins (#131). Kept in sync with
# palettes.json; the loader falls back to this when the file is missing/corrupt.
_DEFAULT_PALETTES = {
    "ghost":  {"name": "Ghost",  "color": (255, 255, 255), "stripe_color": (220, 220, 220), "eye_color": (100, 100, 255), "description": "White ghost cat"},
    "calico": {"name": "Calico", "color": (255, 160, 64),  "stripe_color": (204, 102, 0),   "eye_color": (34, 139, 34),   "description": "Orange calico cat"},
    "tabby":  {"name": "Tabby",  "color": (128, 128, 128), "stripe_color": (64, 64, 64),     "eye_color": (255, 215, 0),   "description": "Gray tabby cat"},
    "void":   {"name": "Void",   "color": (20, 20, 20),    "stripe_color": (0, 0, 0),        "eye_color": (0, 255, 0),     "description": "Black void cat"},
    "tiger":  {"name": "Tiger",  "color": (255, 140, 0),   "stripe_color": (0, 0, 0),        "eye_color": (255, 215, 0),   "description": "Orange tiger cat"},
    "bengal": {"name": "Bengal", "color": (245, 245, 220), "stripe_color": (139, 69, 19),    "eye_color": (0, 191, 255),   "description": "Bengal spotted cat"},
}


def _clamp_channel(v):
    """Coerce one colour channel to an int snapped into [0, 255]; None if not numeric."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return max(0, min(255, int(v)))


def _validated_color(raw):
    """A 3-tuple of snapped channels, or None if the colour is unrepairable."""
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        return None
    chans = [_clamp_channel(c) for c in raw]
    if any(c is None for c in chans):
        return None
    return tuple(chans)


def _validated(raw):
    """Known palettes from `raw`, validated. Bad colours snapped, unrepairable
    entries skipped, never raises. Mirrors settings.py's `_validated` discipline."""
    out = {}
    if not isinstance(raw, dict):
        return out
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        colors = {f: _validated_color(entry.get(f)) for f in _COLOR_FIELDS}
        if any(c is None for c in colors.values()):
            continue  # unrepairable colour -> skip the whole entry
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            continue
        out[key] = {
            "name": name,
            "description": entry.get("description", "") if isinstance(entry.get("description", ""), str) else "",
            **colors,
        }
    return out


def load_palettes(path=None):
    """Load the colour palettes, validated. Never raises.

    `path` defaults to the shipped `palettes.json`. A missing / unreadable /
    non-JSON file falls back to `_DEFAULT_PALETTES`; a readable file is validated
    and returned as-is (may be a subset if some entries were unrepairable).
    """
    if path is None:
        path = _PALETTES_PATH
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):  # missing / unreadable / not valid JSON
        return {k: dict(v) for k, v in _DEFAULT_PALETTES.items()}
    return _validated(raw)
