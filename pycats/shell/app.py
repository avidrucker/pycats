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

from ..config import tick_fps
from ..core.keymap import Keymap
from ..entities.stages import DEFAULT_PLAYER_STAGE
from ..screens.battle_screen import BattleScreen
from ..storage import runtime_settings, settings
from ..ui import cat_faces
from . import display, screen_render
from . import input_poll as inp
from .display_manager import DisplayManager
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

    def __init__(self, prefs, poll=inp.poll, speed=1.0):
        self._poll = poll

        # Present-rate slow-motion factor (#932): 1.0 = real time (default, unchanged),
        # 0.5 = half speed, etc. Paces only how long each already-computed frame is
        # DISPLAYED (via tick_fps in step) — never the sim step, so outcomes/goldens are
        # identical at any speed (the sim is fixed-timestep). Applies to the BATTLE only
        # (#938, see _present_speed). Set at launch from a CLI arg; the in-app Options
        # picker is the post-v1 sibling (#933).
        self.speed = speed

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

    # ------------------------------------------------ present-rate gating
    # `--speed` slow-motion applies to the BATTLE only (#938). The menu hold-to-quit/back
    # timers are FRAME-counted (EscHoldTimer(120) = "2s @ 60fps", esc_hold.py), ticked once
    # per step(); if a menu ran at the reduced rate, a 120-frame hold would take 2x/4x the
    # wall-clock. So the factor is gated on the playing FSM state — every menu/non-battle
    # state paces at full FPS. An allowlist of one (not a denylist) so `pause` and any
    # future menu state stay full-speed by default.
    _BATTLE_STATE = "playing"

    def _present_speed(self):
        """The speed factor to pace this frame at: `self.speed` while the FSM is in the
        battle (`playing`) state, else 1.0 (full 60 FPS) in every menu state (#938)."""
        return self.speed if self.screen_manager.get_state() == self._BATTLE_STATE else 1.0

    # ------------------------------------------------ one frame
    def step(self):
        """Run exactly one frame: poll → dispatch events → update → quit-check → render →
        present. Sets `self.running = False` on QUIT or when the FSM asks to quit."""
        self.clock.tick(tick_fps(self._present_speed()))  # slow the battle only (#938)
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
                elif ev.key == pygame.K_BACKQUOTE:
                    # Dev-HUD toggle (#1319, ruling C1–C4 on #1297): backtick/tilde flips
                    # the in-battle dev HUD (full stat rows + FPS + raw input + input-history
                    # grid) vs. the minimal default (player label + Lives/Damage %). Shipping-
                    # available for everyone — deliberately NOT gated on dev_mode(). Runtime-
                    # only + not persisted (survives pause), so no save_prefs here.
                    on = runtime_settings.toggle_dev_hud()
                    self.dm.zoom_toast.show("Dev HUD: " + ("ON" if on else "OFF"))
                elif ev.key == pygame.K_F1:
                    # In-game dev-mode toggle (#1328, A1's 3rd door on #1297): F1 flips
                    # dev_mode live and syncs dev_hud to the new state on BOTH edges, so
                    # F1-on shows the dev HUD + hit/hurtbox overlay (the overlay gate is
                    # dev_mode() and dev_hud(), #1324) and F1-off restores the shipping
                    # default look. Model A — no debug screen; dev mode just changes what
                    # renders. Runtime-only + not persisted (mirrors backtick), so no
                    # save_prefs here. Downstream dev-mode surfaces (char-select roster
                    # #1292) re-read dev_mode() when next built, so they track the toggle.
                    on = runtime_settings.toggle_dev_mode()
                    runtime_settings.set_dev_hud(on)
                    self.dm.zoom_toast.show("Dev mode: " + ("ON" if on else "OFF"))

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
