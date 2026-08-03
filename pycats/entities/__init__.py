"""
Purpose: Aggregates exports from platform.py, attack.py, player.py, and tail.py.

Use: Allows you to import all entities with:
`from pycats.entities import Player, Platform, Attack, Tail`
"""

from .attack import Attack
from .platform import Platform
from .player import Player, PState
from .tail import Tail

# Public re-exports (this package is an export aggregator — see module docstring).
# `__all__` both documents the API and tells ruff these F401 imports are intentional.
__all__ = ["Platform", "Attack", "Player", "PState", "Tail"]
