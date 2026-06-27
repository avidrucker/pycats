"""Archived OG cat colour-skins (#131, Part 1 of epic #127).

These six palettes were the original selectable "characters" in
`config.CAT_CHARACTERS`. They are not characters — they are pure colour-skins of
one cat (`{name, color, stripe_color, eye_color, description}`). As the
PM-archetype roster (#117: Nalio/Narz/Gnok/Birky/Xoff) becomes the real,
moveset-bearing roster, these palettes are archived here as the single source of
truth so they can later be repurposed as reusable skins (Parts 2-3).

Part 1 is a **non-breaking relocation only**: the data is byte-for-byte identical
to the old `config.py` literals, `config.CAT_CHARACTERS` re-exports this dict, and
every existing consumer (char_select, game, sim/runner) keeps reading the same
object. The JSON-vs-registry format decision and the character/skin separation are
deferred to Part 2/Part 3.

Colours are stored as literal RGB tuples (no `config` import) to keep this module
dependency-free and avoid a circular import with `config`.
"""

OG_SKINS = {
    "ghost": {
        "name": "Ghost",
        "color": (255, 255, 255),  # white
        "stripe_color": (220, 220, 220),
        "eye_color": (100, 100, 255),
        "description": "White ghost cat",
    },
    "calico": {
        "name": "Calico",
        "color": (255, 160, 64),  # orange
        "stripe_color": (204, 102, 0),  # dark orange
        "eye_color": (34, 139, 34),  # forest green
        "description": "Orange calico cat",
    },
    "tabby": {
        "name": "Tabby",
        "color": (128, 128, 128),  # gray
        "stripe_color": (64, 64, 64),  # dark gray
        "eye_color": (255, 215, 0),  # gold
        "description": "Gray tabby cat",
    },
    "void": {
        "name": "Void",
        "color": (20, 20, 20),  # very dark gray/black
        "stripe_color": (0, 0, 0),  # black
        "eye_color": (0, 255, 0),  # bright green
        "description": "Black void cat",
    },
    "tiger": {
        "name": "Tiger",
        "color": (255, 140, 0),  # dark orange
        "stripe_color": (0, 0, 0),  # black stripes
        "eye_color": (255, 215, 0),  # gold
        "description": "Orange tiger cat",
    },
    "bengal": {
        "name": "Bengal",
        "color": (245, 245, 220),  # beige/cream
        "stripe_color": (139, 69, 19),  # brown
        "eye_color": (0, 191, 255),  # deep sky blue
        "description": "Bengal spotted cat",
    },
}
