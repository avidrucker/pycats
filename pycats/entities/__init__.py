"""
Purpose: Aggregates exports from platform.py, attack.py, player.py, and tail.py.

Use: Allows you to import all entities with:
`from pycats.entities import Player, Platform, Attack, Tail`
"""

from .platform import Platform
from .attack import Attack
from .player import Player, PState
from .tail import Tail
