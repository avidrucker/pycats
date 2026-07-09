"""
Purpose: The driving-adapter shell object (#707, C3 of #280).

`App` is the concrete driving adapter that the C1→C2→C3 shell extraction was for. It owns
the runtime collaborators (the #698 `DisplayManager`, the `BattleScreen`, the stage, the
`ScreenStateManager`, the clock) as instance state and exposes **`step()` = exactly one
frame** of the game loop — poll → dispatch events → update → quit-check → render → present.
Moving that body onto an object gives the loop wiring its first unit coverage (the loop
used to be inline in game.py's `while running:`, unreachable in isolation — the #386-class
blindspot); `game.py`'s `main()` now just boots pygame and drives `while app.running:
app.step()`.

Design (ruled on #707, 2026-07-08):
- **Inject the event source only** — `poll` defaults to `input_poll.poll`; tests pass a
  fake that scripts `(InputFrame, events)`. Everything else App builds itself, headlessly
  (the #698 DisplayManager tests prove `set_mode` works under SDL dummy).
- **Compose, not inject, up to App** — App takes a plain `prefs` dict, never calls
  `settings.load()`; `main()` loads + seeds and hands the dict in, so App construction does
  zero file I/O (avoids the #345 settings-file test trap). App still owns the persist half
  (`save_prefs` → `settings.save`) and the Options `_display_hooks` — the change-then-save
  composite #280 placed on the orchestration layer.
- **App assumes pygame is already initialized** (like `DisplayManager`); `main()` owns
  `pygame.init()` + the drive loop, so there is no untestable `App.run()`.
"""

import pygame  # type: ignore

from . import cat_faces, display, screen_render, settings
from . import input_poll as inp
from .battle_screen import BattleScreen
from .config import FPS
from .core.keymap import Keymap
from .display_manager import DisplayManager
from .entities.stages import DEFAULT_PLAYER_STAGE
from .screen_manager import ScreenStateManager

# Rebindable per-player keymaps (#439/#447): the same `Keymap` instance is shared by the
# battle and the Options screen, so a rebind there takes effect live. A `Keymap` is a
# `dict` subclass, so every downstream `controls[...]`/`.get()` read is unchanged; the
# factory defaults below are what "reset to defaults" restores.
#
# Module scope is import-safe: `Keymap(dict(...))` over `pygame.K_*` constants is a pure
# build (the constants exist after `import pygame`, before `pygame.init()`) — nothing here
# touches pygame/display/file state (#701/#707).
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


class App:
    """Owns the runtime collaborators and runs one frame per `step()`.

    Constructed by `main()` with the loaded prefs + the real `inp.poll`; constructed by
    tests with a literal prefs dict + a fake poll. Assumes `pygame.init()` has run."""

    def __init__(self, prefs, poll=inp.poll):
        self._poll = poll

        # Players get a single stage for v1: "Starting Point", pycats' flat Final
        # Destination (#660). Stage selection is post-v1; the demos/sims keep their own
        # Battlefield-like arena (sim/runner.build_stage) — unchanged.
        self.platforms = DEFAULT_PLAYER_STAGE.build()

        # Battle state + per-frame sim are owned by BattleScreen (#193); App reads
        # battle.player1/player2 rather than module globals.
        self.battle = BattleScreen(P1_KEYS, P2_KEYS)

        # The display/window shell (#698): plain values in (compose, not inject).
        self.dm = DisplayManager(prefs["windowed_scale"], prefs["fullscreen"])

        self.clock = pygame.time.Clock()

        # Options display hooks (#121): a menu change reuses the F10/F11 machinery so it
        # applies live AND persists (save_prefs), like the hotkeys. Read dm's state at call
        # time (it's mutated in place by the transitions).
        self._display_hooks = {
            "get_windowed_scale": lambda: self.dm.windowed_scale,
            "cycle_windowed_scale": self._opt_cycle_windowed_scale,
            "is_fullscreen": lambda: self.dm.is_fullscreen,
            "toggle_fullscreen": self._opt_toggle_fullscreen,
        }
        self.screen_manager = ScreenStateManager(P1_KEYS, P2_KEYS, display_hooks=self._display_hooks)

        self.running = True

    # ------------------------------------------------ persist composite
    def save_prefs(self):
        """Persist the current display preferences (#95): windowed scale + fullscreen.
        Called after an F10/F11 change. No-op when persistence is disabled. The display
        transitions live on `dm` (#698); this is the persist half of the change-then-save
        composite the orchestration layer keeps out of DisplayManager (#280)."""
        settings.save({"windowed_scale": self.dm.windowed_scale, "fullscreen": self.dm.is_fullscreen})

    def _opt_cycle_windowed_scale(self):
        self.dm.set_windowed_scale(display.cycle_preset(self.dm.windowed_scale))
        self.save_prefs()

    def _opt_toggle_fullscreen(self):
        self.dm.toggle_fullscreen()
        self.save_prefs()

    # ------------------------------------------------ one frame
    def step(self):
        """Run exactly one frame: poll → dispatch events → update → quit-check → render →
        present. Sets `self.running = False` on QUIT or when the FSM asks to quit."""
        self.clock.tick(FPS)  # cap the frame rate (return value unused)
        frame_input, events = self._poll()

        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F11:
                    self.dm.toggle_fullscreen()
                    self.save_prefs()
                elif ev.key == pygame.K_F10:
                    if self.dm.is_fullscreen:
                        # Advance to the next *distinct* achievable zoom (wraps), so
                        # every press visibly changes the rendered size (#92).
                        self.dm.set_fullscreen_zoom_index(
                            (self.dm.fullscreen_zoom_index + 1) % len(self.dm.fullscreen_scales)
                        )
                        scale = self.dm.fullscreen_scales[self.dm.fullscreen_zoom_index]
                        self.dm.zoom_toast.show(display.fullscreen_zoom_label(scale, self.dm.fullscreen_scales))
                    else:
                        # Windowed: cycle the window-size presets (resizes the window).
                        self.dm.set_windowed_scale(display.cycle_preset(self.dm.windowed_scale))
                        self.dm.zoom_toast.show(display.format_scale_label(self.dm.windowed_scale))
                        self.save_prefs()
                elif ev.key == pygame.K_e and self.battle.player1 is not None:
                    # Debug (#108): cycle P1's cat-face style; toast the new style.
                    self.battle.player1.face_style = cat_faces.cycle_face_style(
                        getattr(self.battle.player1, "face_style", cat_faces.PRIMITIVES)
                    )
                    self.dm.zoom_toast.show("P1 face: " + cat_faces.face_style_label(self.battle.player1.face_style))
                elif ev.key == pygame.K_SEMICOLON and self.battle.player2 is not None:
                    # Debug (#108): cycle P2's cat-face style; toast the new style.
                    self.battle.player2.face_style = cat_faces.cycle_face_style(
                        getattr(self.battle.player2, "face_style", cat_faces.PRIMITIVES)
                    )
                    self.dm.zoom_toast.show("P2 face: " + cat_faces.face_style_label(self.battle.player2.face_style))

        # Update screen state manager. `platforms` is threaded so the playing state's
        # engine action owns the per-frame battle.step + winner-set (#246).
        self.screen_manager.update(frame_input, self.battle, self.platforms)

        # Check if we should quit (2s ESC-hold at main_menu, QUIT already handled above).
        if self.screen_manager.should_quit_game():
            self.running = False
            return

        current_state = self.screen_manager.get_state()
        # The per-state render dispatch lives in screen_render.render_active_screen so it is
        # importable + unit-testable (see tests/test_game_render_dispatch.py). The per-frame
        # update (player creation, battle.step, winner-set) already ran in
        # screen_manager.update above (#246); the frame body only renders now.
        screen_render.render_active_screen(
            current_state,
            self.screen_manager,
            self.dm.render_surface(),
            battle=self.battle,
            platforms=self.platforms,
            is_fullscreen=self.dm.is_fullscreen,
            frame_input=frame_input,
            fps=self.clock.get_fps(),
        )

        self.dm.present()
