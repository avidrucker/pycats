"""
Purpose: Aggregates exports from platform.py, attack.py, and player.py.

Use: Allows you to import all entities with:
`from pycats.entities import Player, Platform, Attack`
"""

from .platform import Platform
from .attack   import Attack
from .player   import Player, PState