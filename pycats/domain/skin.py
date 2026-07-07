"""Skin — a cat's cosmetic value object (#672 domain, spec §1).

Pure: imports no pygame / sim / UI. Colours are ``(r, g, b)`` tuples at the
boundary, matching the palette dicts produced by
``characters.palettes.load_palettes()``. The OG skins are Skins; so is the
placeholder (see ``domain.placeholder``).
"""

from __future__ import annotations

from dataclasses import dataclass

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class Skin:
    """One cosmetic theme. Frozen + hashable so it can be a value in a Selection."""

    key: str
    name: str
    color: RGB
    stripe_color: RGB
    eye_color: RGB
    description: str = ""

    @classmethod
    def from_palette_dict(cls, key: str, d: dict) -> Skin:
        """Build from a `load_palettes()` entry (the migration bridge)."""
        return cls(
            key=key,
            name=d["name"],
            color=tuple(d["color"]),
            stripe_color=tuple(d["stripe_color"]),
            eye_color=tuple(d["eye_color"]),
            description=d.get("description", ""),
        )

    def to_palette_dict(self) -> dict:
        """Render back to the legacy palette-dict shape for adapters that still index by string."""
        return {
            "name": self.name,
            "color": self.color,
            "stripe_color": self.stripe_color,
            "eye_color": self.eye_color,
            "description": self.description,
        }
