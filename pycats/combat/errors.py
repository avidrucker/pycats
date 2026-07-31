"""
pycats/combat/errors.py

Combat-layer exceptions. Home for exception types raised by the combat data
seam (`pycats/combat/data.py`) and future combat modules.
"""

from __future__ import annotations


class UnknownCharacter(ValueError):
    """Raised by `load_fighter_data` when a key resolves to no fighter (#887/#881).

    Subclasses `ValueError` so existing `except ValueError` sites still catch it,
    mirroring `core.keymap.KeyBindingConflict(ValueError)`. `.key` names the
    offending key so a caller can report it.

    Since #881 the runtime has no Python default fallback: only the intended-
    default keys (`"default"`, `"P1"`, `"P2"`, `"testcat"`) and the archetype
    keys resolve; every other key is a programming error and raises this.
    """

    def __init__(self, key, valid):
        super().__init__(f"unknown character key {key!r}; valid keys: {', '.join(valid)}")
        self.key = key
