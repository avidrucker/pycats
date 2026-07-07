"""
Purpose: Main game loop and top-level orchestration.

Contents:
- Initializes Pygame and window.
- Creates players, platforms, and attack sprite groups.
- Runs the game loop (handling input, updating, rendering).
- Renders eye, shield bubble, HUD.

Use: This is the entry point for running the game. The whole runtime lives in `main()`
behind an `if __name__ == "__main__"` guard (#701, C2 of #280), so **importing this module
has no side effects** — no pygame.init, no window, no settings I/O, no loop. That makes
`pycats.game` importable and unit-testable (the module-level loop used to run on import,
the #386-class blindspot); launch is unchanged via `python -m pycats.game`.
"""

#### DONE: implement game pause w/ P key press (IMPLEMENTED - pause with P, resume with P/V/)
#### DONE: implement win screen when one player runs out of stocks
#### TODO: implement menu options for pause screen such as restart, quit, etc.
#### TODO: increase player jump height, and increase thin platforms height
#### TODO: implement coyote time where players can, for a single frame after leaving the ledge, still have 2 jumps
#### TODO: fix bug where players can jump sideways through the thick platform

# ------------------------------------------------ stage & sprites
#### TODO: implement stage selection w/ various platform layouts (NOT YET)
#### TODO: implement player pushing & sliding where players can push each other left/right
# (if both players are pushing on each other, there is no horizontal movement, else, there
# is slowed movement in the pushed direction) and when one lands on the other they also get
# pushed apart and the bottom character gets their vertical velocity downward increased if
# they are both in the air and the top character gets their vertical velocity upward
# increased with a short hop/bounce up

import sys

import pygame  # type: ignore

from . import cat_faces, display, runtime_settings, screen_render, settings
from . import input_poll as inp
from .battle_screen import BattleScreen

# Explicit config imports — was `from .config import *` (#486 slice 2 / #490), which
# blinded pyflakes to game.py (the one untested module). Only the names game.py uses;
# the prior dead EAR_*/WHISKER_*/STRIPE_*/CAT_CHARACTERS block (nothing referenced it,
# here or elsewhere) was dropped. The display constants (SCREEN_*, WHITE, HUD_PADDING)
# moved with the present path into DisplayManager (#698); GAME_HUD_FONT_SIZE went with
# the dead font block removed in #701.
from .config import FPS
from .core.keymap import Keymap
from .display_manager import DisplayManager
from .entities.stages import DEFAULT_PLAYER_STAGE
from .screen_manager import ScreenStateManager

# Rebindable per-player keymaps (#439/#447): the same `Keymap` instance is shared
# by the battle and the Options screen, so a rebind there takes effect live. A
# `Keymap` is a `dict` subclass, so every downstream `controls[...]`/`.get()` read is
# unchanged; the factory defaults below are what "reset to defaults" restores.
#
# These stay at module scope: `Keymap(dict(...))` over `pygame.K_*` constants is a pure
# build (the constants exist after `import pygame`, before `pygame.init()`), so it is
# import-safe — nothing here touches pygame/display/file state (#701).
P1_KEYS = Keymap(
    dict(
        left=pygame.K_a,
        right=pygame.K_d,
        up=pygame.K_w,
        down=pygame.K_s,
        attack=pygame.K_v,
        special=pygame.K_c,
        shield=pygame.K_x,
        smash=pygame.K_b,  # dedicated smash input (#331, slice 1 of #327)
    )
)
P2_KEYS = Keymap(
    dict(
        left=pygame.K_LEFT,
        right=pygame.K_RIGHT,
        up=pygame.K_UP,
        down=pygame.K_DOWN,
        attack=pygame.K_SLASH,
        special=pygame.K_PERIOD,
        shield=pygame.K_COMMA,
        smash=pygame.K_QUOTE,  # dedicated smash input (#331, slice 1 of #327)
    )
)


def main():
    """Set up pygame + the runtime collaborators and run the game loop until quit.

    All side-effectful setup (pygame.init, the window, settings I/O) and the loop live
    here, not at module scope, so `import pycats.game` stays inert (#701)."""
    pygame.init()
    pygame.display.set_caption("PyCats - Smash-Draft Rev 6 (fsm)")

    # Players get a single stage for v1: "Starting Point", pycats' flat Final Destination
    # (#660). Stage selection is post-v1, so this is the fixed player-facing layout. The
    # demos/sims keep the Battlefield-like arena (see sim/runner.build_stage) — unchanged.
    platforms = DEFAULT_PLAYER_STAGE.build()

    # Players will be created after character selection
    # Battle state + per-frame sim are owned by BattleScreen (#193); game.py reads
    # battle.player1/player2/players/attacks instead of module globals.
    battle = BattleScreen(P1_KEYS, P2_KEYS)

    # ------------------------------------------------ pygame set-up
    # Restore persisted display preferences (#95); defaults if none/invalid.
    _prefs = settings.load()
    # Seed the live present-layer settings (#121) so the render path reads the saved
    # HUD toggles immediately; the Options sub-menu mutates this live.
    runtime_settings.seed(_prefs)

    # Open fullscreen if that's how the player last left it.
    start_fullscreen = _prefs["fullscreen"]
    # Saved windowed-scale preset (1x default; cycle with F10). See pycats.display.
    windowed_scale = _prefs["windowed_scale"]

    # The display/window shell (#698, C1 of #280): owns the window, surfaces, current
    # scale + letterbox offsets, the fullscreen zoom sizes, and the zoom toast as instance
    # state — what used to be ~11 module globals mutated together via `global`. Compose,
    # not inject: it takes plain values (not `settings`); the change-then-persist composite
    # (save_prefs) stays here in the orchestration layer.
    dm = DisplayManager(windowed_scale, start_fullscreen)

    clock = pygame.time.Clock()

    # ------------------------------------------------ helpers
    # Battle draw helpers (draw_eye, draw_cat_features, draw_stripes,
    # draw_player_name) and render_battle/render_attacks now live in
    # pycats/render_battle.py so the live game, pause screen, and sim presenters
    # share one renderer.

    #### TODO: split off damage % and stock lives rendering so that they are rendering last
    # and at the bottom left and right corners of the screen
    #### TODO: implement dev info bool flag that, when True, shows all infos, and when False,
    # only shows what should be shown to players normally
    def save_prefs():
        """Persist the current display preferences (#95): windowed scale + fullscreen.
        Called after an F10/F11 change. No-op when persistence is disabled. The display
        transitions themselves now live on `dm` (#698); this is the persist half of the
        change-then-save composite the orchestration layer keeps out of DisplayManager."""
        settings.save({"windowed_scale": dm.windowed_scale, "fullscreen": dm.is_fullscreen})

    # Display hooks for the Options sub-menu (#121): reuse the F10/F11 machinery so a
    # menu change applies live AND persists (save_prefs), just like the hotkeys. Read
    # dm's state at call time (it's mutated in place by the transitions).
    def _opt_cycle_windowed_scale():
        dm.set_windowed_scale(display.cycle_preset(dm.windowed_scale))
        save_prefs()

    def _opt_toggle_fullscreen():
        dm.toggle_fullscreen()
        save_prefs()

    _display_hooks = {
        "get_windowed_scale": lambda: dm.windowed_scale,
        "cycle_windowed_scale": _opt_cycle_windowed_scale,
        "is_fullscreen": lambda: dm.is_fullscreen,
        "toggle_fullscreen": _opt_toggle_fullscreen,
    }

    # Screen state manager
    screen_manager = ScreenStateManager(P1_KEYS, P2_KEYS, display_hooks=_display_hooks)

    # ------------------------------------------------ main loop
    running = True
    while running:
        clock.tick(FPS)  # cap the frame rate (return value unused)
        frame_input, events = inp.poll()

        for ev in events:
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F11:
                    dm.toggle_fullscreen()
                    save_prefs()
                elif ev.key == pygame.K_F10:
                    if dm.is_fullscreen:
                        # Advance to the next *distinct* achievable zoom (wraps), so
                        # every press visibly changes the rendered size (#92).
                        dm.set_fullscreen_zoom_index((dm.fullscreen_zoom_index + 1) % len(dm.fullscreen_scales))
                        scale = dm.fullscreen_scales[dm.fullscreen_zoom_index]
                        dm.zoom_toast.show(display.fullscreen_zoom_label(scale, dm.fullscreen_scales))
                    else:
                        # Windowed: cycle the window-size presets (resizes the window).
                        dm.set_windowed_scale(display.cycle_preset(dm.windowed_scale))
                        dm.zoom_toast.show(display.format_scale_label(dm.windowed_scale))
                        save_prefs()
                elif ev.key == pygame.K_e and battle.player1 is not None:
                    # Debug (#108): cycle P1's cat-face style; toast the new style.
                    battle.player1.face_style = cat_faces.cycle_face_style(
                        getattr(battle.player1, "face_style", cat_faces.PRIMITIVES)
                    )
                    dm.zoom_toast.show("P1 face: " + cat_faces.face_style_label(battle.player1.face_style))
                elif ev.key == pygame.K_SEMICOLON and battle.player2 is not None:
                    # Debug (#108): cycle P2's cat-face style; toast the new style.
                    battle.player2.face_style = cat_faces.cycle_face_style(
                        getattr(battle.player2, "face_style", cat_faces.PRIMITIVES)
                    )
                    dm.zoom_toast.show("P2 face: " + cat_faces.face_style_label(battle.player2.face_style))

        # Update screen state manager. `platforms` is threaded so the playing state's
        # engine action owns the per-frame battle.step + winner-set (#246).
        screen_manager.update(frame_input, battle, platforms)

        # Check if we should quit
        if screen_manager.should_quit_game():
            running = False
            continue

        # Leaving an active match on a 2s ESC-hold now drops to char_select as a
        # first-class FSM transition (#453); char_select's entry action resets the
        # battle, so no game.py-side reset/force is needed here anymore.

        current_state = screen_manager.get_state()
        # (#230) The pause->win_screen stats wiring + char_select reset are now engine
        # entry/update actions (screen_manager._on_enter_win_screen / _update_char_select),
        # fed by the battle threaded into the engine ctx above — the previous_state loop
        # hack and the should_reset_game poll are retired.
        #
        # The per-state render dispatch lives in screen_render.render_active_screen so it
        # is importable + unit-testable (this loop is module-level and runs on import, so
        # its inline dispatch never was) — see tests/test_game_render_dispatch.py. The
        # per-frame update (player creation, battle.step, winner-set) already ran in
        # screen_manager.update above (#246); the loop body only renders now.
        screen_render.render_active_screen(
            current_state,
            screen_manager,
            dm.render_surface(),
            battle=battle,
            platforms=platforms,
            is_fullscreen=dm.is_fullscreen,
            frame_input=frame_input,
            fps=clock.get_fps(),
        )

        dm.present()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
