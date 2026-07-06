"""The `testcat` fixture renders as an unmistakable opaque-gray placeholder (#636).

`testcat` is the minimal test fixture (#591), not a playable cat — on screen it must
read as clearly non-standard, not like a real archetype. Its cosmetic palette resolves
through `roster.palette_for`, which drives the rendered body/stripe/eye colours
(`battle_screen` passes `palette_for(key)["color"]`/`["eye_color"]` straight into Player).

The placeholder signal is **full achromaticity** — mid-gray body, gray stripe, and
crucially *gray eyes*: every real archetype has coloured eyes (nalio green, birky blue,
narz green), so colourless eyes uniquely mark the fixture. Opaque (not alpha) so it stays
legible against the dark stage (#546).

Able-to-fail: without the dedicated `testcat` palette it falls back to the generic
`_NEUTRAL` (light gray 200) shared by any unknown key — which fails the mid-gray band
below.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pycats.characters.roster import ARCHETYPE_ROSTER, palette_for  # noqa: E402

_FIELDS = ("color", "stripe_color", "eye_color")


def _is_gray(rgb):
    r, g, b = rgb[:3]
    return r == g == b


def test_testcat_is_opaque_mid_gray_and_fully_achromatic():
    pal = palette_for("testcat")
    for field in _FIELDS:
        assert _is_gray(pal[field]), f"testcat {field} must be achromatic gray, got {pal[field]}"
    body = pal["color"][0]
    # Mid ("50%") gray, not the light _NEUTRAL fallback (200) and not near-black: reads as a
    # deliberate placeholder while staying visible.
    assert 96 <= body <= 160, f"testcat body should be opaque mid-gray (~128), got {body}"
    # Opaque: if an alpha channel is present it must be full.
    assert len(pal["color"]) < 4 or pal["color"][3] == 255, "testcat body must be opaque (no alpha)"


def test_testcat_distinct_from_every_named_archetype():
    tcolor = palette_for("testcat")["color"][:3]
    for key in ARCHETYPE_ROSTER:
        assert palette_for(key)["color"][:3] != tcolor, f"testcat body collides with {key}"
    # The distinguishing signal: real archetypes have COLOURED eyes; the placeholder does not.
    for key in ARCHETYPE_ROSTER:
        assert not _is_gray(palette_for(key)["eye_color"]), (
            f"{key} unexpectedly has gray eyes — breaks the 'gray eyes = placeholder' marker"
        )
    assert _is_gray(palette_for("testcat")["eye_color"]), "testcat must have gray (colourless) eyes"
