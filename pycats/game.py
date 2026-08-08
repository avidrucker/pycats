"""
Purpose: Entry point — boot pygame and drive the game loop.

Use: `python -m pycats.game`. The runtime lives in `main()` behind an `if __name__ ==
"__main__"` guard (#701, C2 of #280), so **importing this module has no side effects** —
no pygame.init, no window, no settings I/O, no loop. `main()` boots pygame, loads prefs,
and drives `while app.running: app.step()`; the per-frame body and the runtime
collaborators live on `App` (#707, C3 — see pycats/shell/app.py).

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

import argparse
import os
import sys

import pygame  # type: ignore

from .shell.app import P1_KEYS, P2_KEYS, App
from .storage import keybind_store, runtime_settings, settings


def parse_args(argv):
    """Parse the game's launch flags. Pure (no I/O, no pygame) so it's unit-testable.

    `--speed` sets a present-rate slow-motion factor (#932): 1.0 = real time (default),
    0.5 = half speed, 0.25 = quarter speed. It paces only how long each already-computed
    frame is DISPLAYED (App.step → tick_fps) — never the sim — mirroring the sim-side
    `watch.py --demo-speed` (#351). The in-app Options picker is the post-v1 sibling (#933).

    `--dev` requests dev mode (#1312, ruling A1 on #1297): main() resolves it (with the
    PYCATS_DEV env var) into the process-wide runtime_settings.dev_mode gate. Default off;
    this slice only sets the flag — no surface changes behaviour on it yet."""
    ap = argparse.ArgumentParser(prog="pycats.game", description="Run the interactive game.")
    ap.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="present-rate speed factor (1.0 real time, 0.5 half, 0.25 quarter); "
        "presentation-only, the sim is unchanged.",
    )
    ap.add_argument(
        "--dev",
        action="store_true",
        default=False,
        help="launch in dev mode (sets runtime_settings.dev_mode); also settable via the "
        "PYCATS_DEV env var. Enables dev surfaces as later slices land (#1311).",
    )
    return ap.parse_args(argv)


def resolve_dev_mode(args):
    """Whether dev mode is on for this launch: the `--dev` CLI flag OR a truthy `PYCATS_DEV`
    env var (#1312). Env truthiness mirrors dev_log.enabled() (#587). The third ruled door,
    the in-game F1 debug screen, is a later #1311 slice — this resolves only the two
    boot-time doors. Pure apart from the env read, so it's unit-testable."""
    return bool(args.dev) or bool(os.environ.get("PYCATS_DEV"))


def main():
    """Boot pygame, restore prefs, and drive the game loop until quit.

    All side-effectful setup (pygame.init, settings I/O) and the drive live here, not at
    module scope, so `import pycats.game` stays inert (#701). The per-frame body lives on
    `App.step()` (#707); this owns only the pygame boot + the drive loop."""
    args = parse_args(sys.argv[1:])

    pygame.init()
    pygame.display.set_caption("PyCats - Smash-Draft Rev 6 (fsm)")

    # Restore persisted display preferences (#95); defaults if none/invalid. Loaded here
    # (not in App) so App construction does zero file I/O — plain values in (#707 Q2).
    prefs = settings.load()
    # Seed the live present-layer settings (#121) so the render path reads the saved HUD
    # toggles immediately; the Options sub-menu mutates this live.
    runtime_settings.seed(prefs)
    # Resolve the process-wide dev-mode gate (#1312, ruling A1 on #1297) from the --dev
    # flag / PYCATS_DEV env and set it as the one owner every dev-gated surface reads.
    # Set after seed() because dev_mode is a launch flag, not a persisted pref — seed()
    # replaces the pref state but never touches dev_mode. No consumer flips behaviour on
    # it yet; later #1311 slices (char-select, HUD, overlays, F1 screen) read it.
    runtime_settings.set_dev_mode(resolve_dev_mode(args))
    # Seed the dev-HUD master switch to the dev-mode gate (#1324, B2 reconciliation on
    # #1297): inside dev mode the text dev HUD (#1319) AND the hit/hurtbox overlay (#219)
    # default ON, and backtick flips both together; outside dev mode dev_hud stays OFF and
    # the overlay never renders. Seeded here (after set_dev_mode) because dev_hud is a
    # per-session launch state, not a persisted pref — seed() never touches it.
    runtime_settings.set_dev_hud(runtime_settings.dev_mode())
    # Restore the implicit "last used" keybindings (#1306, ruling C on #1305) onto the
    # shared P1/P2 keymaps before App wires them into the battle + Options screens, so a
    # rebind from a prior session survives a restart. Missing/invalid slot -> factory
    # defaults (keybind_store.load_last_used). Loaded here, not in App, for the same
    # reason as settings.load: App construction does zero file I/O (#707 Q2).
    keybind_store.load_last_used(P1_KEYS, P2_KEYS)

    app = App(prefs=prefs, speed=args.speed)
    while app.running:
        app.step()

    # Persist the bindings the player is quitting with as the "last used" slot (#1306).
    # On-exit realizes the "last used" semantic exactly — whatever the live keymaps hold
    # at quit (a rebind, a reset, or a loaded named scheme) is what next launch restores.
    keybind_store.save_last_used(P1_KEYS, P2_KEYS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
