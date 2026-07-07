"""The `testcat` fixture renders as an unmistakable opaque-gray placeholder (#636).

`testcat` is the minimal test fixture (#591), not a playable cat — on screen it must
read as clearly non-standard, not like a real archetype. Its cosmetic palette resolves
through `roster.palette_for`, which drives the rendered body/stripe/eye colours
(`battle_screen` passes `palette_for(key)["color"]`/`["eye_color"]` straight into Player).

The placeholder signal is **full achromaticity** — mid-gray body, gray stripe, and
crucially *gray eyes*: every real archetype has coloured eyes (nalio green, birky blue,
narz green), so colourless eyes uniquely mark the fixture. Opaque (not alpha) so it stays
legible against the dark stage (#546).

Under DP1 (#672 ruling, 2026-07-06) the placeholder is **flat uniform gray** — body,
stripe and eye are the *same* `(128, 128, 128)`, not the #636 three-tone gray. Features
then vanish by colour and read via black outlines drawn in render_battle (#694). The
uniform-value assertion below is able-to-fail against the retired three-tone palette.

Able-to-fail: without the dedicated `testcat` palette it falls back to the generic
`_NEUTRAL` (light gray 200) shared by any unknown key — which fails the mid-gray band
below.
"""

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


def test_testcat_is_flat_uniform_gray():
    """DP1 (#672): body, stripe and eye are the SAME gray — not the retired three-tone.

    Able-to-fail against the old palette (stripe 96 / eye 64 both differed from body 128);
    green only when all three are the uniform (128, 128, 128). The rendered features then
    vanish by colour and depend on the #694 black outlines for legibility.
    """
    pal = palette_for("testcat")
    body, stripe, eye = pal["color"][:3], pal["stripe_color"][:3], pal["eye_color"][:3]
    assert body == stripe == eye == (128, 128, 128), (
        f"placeholder must be flat uniform gray (128,128,128); got body={body} stripe={stripe} eye={eye}"
    )


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
