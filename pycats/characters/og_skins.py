"""Archived OG cat colour-skins (#131 Part 1; sourced from palettes.json in #221 Part 2).

These six palettes were the original selectable "characters" in
`config.CAT_CHARACTERS`. They are not characters — they are pure colour-skins of
one cat (`{name, color, stripe_color, eye_color, description}`).

**Part 2 (#221):** the skins now live in a presentation-only **palette** source
(`palettes.json`, loaded via `palettes.load_palettes`), so the colour data has a
single source of truth and a safe, validate-on-load path. This module re-exports
that data as `OG_SKINS` (and `config.CAT_CHARACTERS` re-exports it in turn), so
every existing consumer (char_select, game, sim/runner, battle_screen) keeps
reading the same `{name, color, stripe_color, eye_color, description}` shape with
tuple colours and the same values — a non-breaking re-source.

The character/skin *separation* and the CSS palette picker are Part 3 of #127.
"""
from .palettes import load_palettes

OG_SKINS = load_palettes()
