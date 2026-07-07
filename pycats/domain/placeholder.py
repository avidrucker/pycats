"""The placeholder fighter — one non-selectable (Character, Skin) (#672 domain, spec §4).

The placeholder is a *normal* Character + Skin that is simply **absent from the
selectable registries** (``domain.registry``). "Doesn't use the regular palette"
means "not a member of the selectable roster", NOT a render bypass — so it needs
zero ``if key == "testcat"`` special-cases anywhere.

The Skin values are the DP1-ratified **flat uniform gray** (#672 ruling,
2026-07-06): body / stripe / eye all ``(128, 128, 128)``. Legibility on the dark
stage is carried by **black outlines on the placeholder's features**, added in a
separate render slice — NOT by colour contrast, and NOT here.

Pure: imports no pygame / sim / UI.
"""

from __future__ import annotations

from .character import Character
from .skin import Skin

PLACEHOLDER_CHARACTER = Character(key="testcat", name="Test", default_skin_key="placeholder")

PLACEHOLDER_SKIN = Skin(
    key="placeholder",
    name="Test",
    color=(128, 128, 128),
    stripe_color=(128, 128, 128),
    eye_color=(128, 128, 128),
    description="unselectable fixture placeholder (flat uniform gray; features read by black outline)",
)
