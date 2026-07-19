"""Palette source loader — Part 2 of epic #127 (#221).

Palettes are presentation-only colour identities extracted from the OG skins
(#131, Part 1). They load from pycats/characters/palettes.json via a safe,
validate-on-load loader modelled on settings.py: never raises, snaps out-of-range
colours, skips unrepairable entries, [r,g,b] -> tuple at the boundary. A
missing/corrupt file falls back to the built-in six.
"""
import json

from pycats.characters.palettes import load_palettes

# Exact RGB values that must survive the JSON round-trip (== today's OG_SKINS).
_EXPECTED = {
    "ghost":  {"color": (255, 255, 255), "stripe_color": (220, 220, 220), "eye_color": (100, 100, 255)},
    "calico": {"color": (255, 160, 64),  "stripe_color": (204, 102, 0),   "eye_color": (34, 139, 34)},
    "tabby":  {"color": (128, 128, 128), "stripe_color": (64, 64, 64),     "eye_color": (255, 215, 0)},
    "void":   {"color": (20, 20, 20),    "stripe_color": (0, 0, 0),        "eye_color": (0, 255, 0)},
    "tiger":  {"color": (255, 140, 0),   "stripe_color": (0, 0, 0),        "eye_color": (255, 215, 0)},
    "bengal": {"color": (245, 245, 220), "stripe_color": (139, 69, 19),    "eye_color": (0, 191, 255)},
}


def test_shipped_palettes_load_with_exact_rgb_tuples():
    pals = load_palettes()
    # The original six survive with their exact RGBs (a fidelity pin, not a frozen
    # census — the live set is free to grow with new skins, e.g. #677 base themes).
    assert set(_EXPECTED) <= set(pals)
    for key, exp in _EXPECTED.items():
        for field, want in exp.items():
            got = pals[key][field]
            assert got == want, f"{key}.{field}: {got} != {want}"
            assert isinstance(got, tuple), f"{key}.{field} should be a tuple, got {type(got)}"


def test_missing_file_falls_back_to_builtin_defaults(tmp_path):
    pals = load_palettes(path=tmp_path / "nope.json")  # file does not exist
    assert set(_EXPECTED) <= set(pals)  # builtins include the original six…
    assert pals["calico"]["color"] == (255, 160, 64)  # …with correct tuple values


def test_corrupt_file_never_raises_and_defaults(tmp_path):
    bad = tmp_path / "palettes.json"
    bad.write_text("{ not valid json ::::")
    pals = load_palettes(path=bad)  # must not raise
    assert set(_EXPECTED) <= set(pals)
    assert pals["void"]["color"] == (20, 20, 20)


def test_out_of_range_colour_is_snapped(tmp_path):
    f = tmp_path / "palettes.json"
    f.write_text(json.dumps({
        "x": {"name": "X", "color": [300, -5, 128],
              "stripe_color": [0, 0, 0], "eye_color": [0, 0, 0]},
    }))
    pals = load_palettes(path=f)
    assert pals["x"]["color"] == (255, 0, 128)  # clamped to [0, 255]


def test_unrepairable_entry_is_skipped(tmp_path):
    f = tmp_path / "palettes.json"
    f.write_text(json.dumps({
        "good": {"name": "Good", "color": [1, 2, 3], "stripe_color": [4, 5, 6], "eye_color": [7, 8, 9]},
        "bad":  {"name": "Bad",  "color": "purple",  "stripe_color": [0, 0, 0], "eye_color": [0, 0, 0]},
    }))
    pals = load_palettes(path=f)
    assert "good" in pals and "bad" not in pals  # malformed colour -> entry skipped
    assert pals["good"]["color"] == (1, 2, 3)


# Per-Character base colour-theme Skins (#677) — normal members of the growable
# live skin set, distinct from the OG six. Provisional RGBs (legible on the dark
# stage per the #546 outline basis), tweakable later.
_BASE_THEMES = {
    "red-blue":   {"color": (210, 55, 50),  "stripe_color": (60, 100, 210)},   # Nalio
    "blue-black": {"color": (60, 105, 205), "stripe_color": (18, 18, 22)},      # Narz
    "pink-red":   {"color": (240, 130, 175), "stripe_color": (205, 55, 50)},    # Birky
}


def test_base_theme_skins_load_with_their_theme_rgbs():
    pals = load_palettes()
    for key, exp in _BASE_THEMES.items():
        assert key in pals, f"base theme {key!r} missing from the skin set"
        for field, want in exp.items():
            got = pals[key][field]
            assert got == want, f"{key}.{field}: {got} != {want}"
            assert isinstance(got, tuple), f"{key}.{field} should be a tuple"
