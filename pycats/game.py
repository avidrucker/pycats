"""
Purpose: Entry point — boot pygame and drive the game loop.

Use: `python -m pycats.game`. The runtime lives in `main()` behind an `if __name__ ==
"__main__"` guard (#701, C2 of #280), so **importing this module has no side effects** —
no pygame.init, no window, no settings I/O, no loop. `main()` boots pygame, loads prefs,
and drives `while app.running: app.step()`; the per-frame body and the runtime
collaborators live on `App` (#707, C3 — see pycats/app.py).

#### TODO: implement menu options for pause screen such as restart, quit, etc.
#### TODO: increase player jump height, and increase thin platforms height
#### TODO: implement coyote time where players can, for a single frame after leaving the ledge, still have 2 jumps
#### TODO: fix bug where players can jump sideways through the thick platform
#### TODO: implement stage selection w/ various platform layouts (NOT YET)
#### TODO: implement player pushing & sliding where players can push each other left/right
# (if both players are pushing on each other, there is no horizontal movement, else, there
# is slowed movement in the pushed direction) and when one lands on the other they also get
# pushed apart and the bottom character gets their vertical velocity downward increased if
# they are both in the air and the top character gets their vertical velocity upward
# increased with a short hop/bounce up
"""

import sys

import pygame  # type: ignore

from . import runtime_settings, settings
from .app import App


def main():
    """Boot pygame, restore prefs, and drive the game loop until quit.

    All side-effectful setup (pygame.init, settings I/O) and the drive live here, not at
    module scope, so `import pycats.game` stays inert (#701). The per-frame body lives on
    `App.step()` (#707); this owns only the pygame boot + the drive loop."""
    pygame.init()
    pygame.display.set_caption("PyCats - Smash-Draft Rev 6 (fsm)")

    # Restore persisted display preferences (#95); defaults if none/invalid. Loaded here
    # (not in App) so App construction does zero file I/O — plain values in (#707 Q2).
    prefs = settings.load()
    # Seed the live present-layer settings (#121) so the render path reads the saved HUD
    # toggles immediately; the Options sub-menu mutates this live.
    runtime_settings.seed(prefs)

    app = App(prefs=prefs)
    while app.running:
        app.step()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
