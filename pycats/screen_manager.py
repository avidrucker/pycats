"""
Screen state management using FSM for the cat fighting game.

This module handles:
- Managing transitions between different game screens
- Screen state logic and timing
- Input handling for screen transitions
"""

import math

import pygame  # type: ignore

from .char_select import CharacterSelector
from .config import MAIN_MENU_SELECTED_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from .main_menu import MainMenuManager
from .options_menu import OptionsMenu
from .pause_menu import PauseMenuManager
from .systems.screen_engine import make_screen_engine
from .win_screen import WinScreenManager


class ScreenStateManager:
    """Manages screen states and transitions using FSM."""

    def __init__(self, p1_controls, p2_controls, display_hooks=None):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Screen managers
        self.main_menu = MainMenuManager(p1_controls, p2_controls)
        self.char_selector = CharacterSelector(p1_controls, p2_controls)
        self.win_screen_manager = WinScreenManager(p1_controls, p2_controls)
        self.pause_menu = PauseMenuManager(p1_controls, p2_controls)
        # Options sub-menu (#121). display_hooks wires its display rows to game.py
        # (None in headless/tests → those rows are inert; the HUD toggle still works).
        self.options_menu = OptionsMenu(p1_controls, p2_controls, display_hooks=display_hooks)

        # Back to menu timer for character select
        self.back_timer = 0
        self.back_hold_frames = 60  # 1 second at 60 FPS

        # Hold-ESC-to-navigate (#113, generalised #453): a 2-second hold on ESC pops
        # one level up the screen ladder (guards read esc_hold_complete()); at
        # main_menu it quits the app. One shared timer, ticked once per frame in
        # update() regardless of state.
        self.esc_quit_timer = 0
        self.esc_quit_hold_frames = 120  # 2 seconds at 60 FPS

        # Screen-flow engine (epic #100): runs on statecharts-py, the sole screen
        # engine (the legacy FSM was retired across slices 4a/4b/4c, ADR-0002). The
        # transition spec + on_enter/on_update are engine-agnostic; guards/handlers
        # take (ctx). See systems/screen_engine.py.
        transitions = {
            "main_menu": [
                ("char_select", self._guard_menu_to_char_select),
                ("options", self._guard_menu_to_options),
            ],
            "options": [
                ("main_menu", self._guard_options_to_main_menu),
            ],
            "char_select": [
                ("playing", self._guard_char_select_to_playing),
                ("main_menu", self._guard_char_select_to_main_menu),
            ],
            "playing": [
                ("pause", self._guard_playing_to_pause),
                ("win_screen", self._guard_playing_to_win_screen),
                ("char_select", self._guard_playing_to_char_select),
            ],
            "pause": [
                ("playing", self._guard_pause_to_playing),
                ("win_screen", self._guard_pause_to_stats),
                ("char_select", self._guard_pause_to_char_select),
            ],
            "win_screen": [
                ("char_select", self._guard_win_screen_to_char_select),
            ],
        }
        on_enter = {
            "main_menu": self._on_enter_main_menu,
            "options": self._on_enter_options,
            "char_select": self._on_enter_char_select,
            "playing": self._on_enter_playing,
            "pause": self._on_enter_pause,
            "win_screen": self._on_enter_win_screen,
        }
        on_update = {
            "main_menu": self._update_main_menu,
            "options": self._update_options,
            "char_select": self._update_char_select,
            "playing": self._update_playing,
            "pause": self._update_pause,
            "win_screen": self._update_win_screen,
        }
        self.engine = make_screen_engine(
            transitions,
            "main_menu",
            on_enter=on_enter,
            on_update=on_update,
        )

        # Game state data
        self.winner = None
        self.loser = None
        self.should_quit = False

    def update(self, frame_input, battle=None, platforms=None):
        """Update the screen state manager.

        ``battle`` (the BattleScreen, #193) is threaded into the engine ctx so the
        transition side-effects can run as entry/update actions instead of game.py
        loop branches (#230, slice 3 of #100): win_screen's from-pause stats and
        char_select's reset read ``ctx["battle"]``.

        ``platforms`` (the static stage geometry) is threaded too so the playing
        state's update action can own the per-frame ``battle.step`` (#246), instead
        of game.py's loop body running it.
        """
        # Tick the hold-ESC timer once per frame, BEFORE the engine runs, so the
        # per-state guards see the up-to-date hold when they decide to pop a level
        # (#453). on_enter of a target state resets the timer, so popping one level
        # never cascades into a second pop (or an app-quit) on the same hold.
        self._tick_esc_hold(frame_input)
        self.engine.update(
            {"frame_input": frame_input, "screen_manager": self, "battle": battle, "platforms": platforms}
        )
        # main_menu is the top of the ladder: a completed hold there quits the app
        # (there is no parent state to pop to).
        if self.engine.state == "main_menu" and self.esc_hold_complete():
            self.should_quit = True

    def render(self, surface):
        """Render the current screen."""
        if self.engine.state == "main_menu":
            self.main_menu.render(surface)
        elif self.engine.state == "options":
            self.options_menu.render(surface)
        elif self.engine.state == "char_select":
            self.char_selector.render(surface)
        elif self.engine.state == "win_screen":
            self.win_screen_manager.render(surface)
        elif self.engine.state == "pause":
            # Pause menu rendering is handled by the main game loop
            pass
        # Note: "playing" state is handled by the main game loop
        self.render_esc_quit_progress(surface)

    def get_state(self):
        """Get the current state."""
        return self.engine.state

    def reset_to_main_menu(self):
        """Force a return to the main menu (ESC-hold-to-menu from playing). Jumps
        the engine to ``main_menu`` and runs its on_enter — the engine-backed
        replacement for the old direct ``fsm.state = 'main_menu'`` + on_enter call."""
        self.engine.force("main_menu")

    def set_winner(self, winner, loser):
        """Set the winner data for win screen."""
        self.winner = winner
        self.loser = loser

    def get_selected_characters(self):
        """Get the selected characters from character selection."""
        return self.char_selector.get_selected_characters()

    def get_selected_palettes(self):
        """Get the chosen OG-skin per player from character selection (#650)."""
        return self.char_selector.get_selected_palettes()

    def set_stats_data(self, player1, player2):
        """Set stats data for viewing current match stats from pause."""
        # Set both players as winner/loser for stats display
        # The win screen will handle this appropriately
        self.win_screen_manager.set_match_data(player1, player2, from_pause=True)

    def get_pause_menu(self):
        """Get the pause menu manager."""
        return self.pause_menu

    def should_reset_game(self):
        """Check if the game should be reset (when returning from win screen)."""
        # Check if we just transitioned from win screen to char select
        return self.engine.state == "char_select" and self.winner is None and self.loser is None

    # FSM State Enter Handlers
    def _on_enter_main_menu(self, ctx):
        """Called when entering main menu state."""
        self.main_menu.reset()
        self.esc_quit_timer = 0

    def _on_enter_options(self, ctx):
        """Called when entering the Options sub-menu state."""
        self.options_menu.reset()
        self.esc_quit_timer = 0

    def _on_enter_char_select(self, ctx):
        """Called when entering character select state."""
        # Reset character selector if coming from main menu
        if hasattr(self.char_selector, "reset"):
            self.char_selector.reset()
        self.back_timer = 0
        self.esc_quit_timer = 0

    def _on_enter_playing(self, ctx):
        """Called when entering playing state."""
        self.esc_quit_timer = 0

    def _on_enter_pause(self, ctx):
        """Called when entering pause state."""
        # Reset pause menu state
        self.pause_menu.reset()
        self.esc_quit_timer = 0

    def _on_enter_win_screen(self, ctx):
        """Called when entering win screen state."""
        self.esc_quit_timer = 0
        if self.winner and self.loser:
            # Normal win condition (playing -> win_screen): winner/loser were set
            # in the playing loop before the transition.
            self.win_screen_manager.set_match_data(self.winner, self.loser)
        else:
            # From pause -> win_screen (the 'end_match' stats view): wire the stats
            # from the live battle threaded into ctx (#230, replacing game.py's
            # previous_state hack). No battle (or no players) => nothing to show.
            battle = ctx.get("battle")
            if battle is not None and battle.player1 and battle.player2:
                self.win_screen_manager.set_match_data(battle.player1, battle.player2, from_pause=True)

    # FSM State Update Handlers
    def _update_main_menu(self, ctx):
        """Update main menu state."""
        frame_input = ctx["frame_input"]
        self.main_menu.update(frame_input.pressed)

    def _update_options(self, ctx):
        """Update the Options sub-menu state."""
        frame_input = ctx["frame_input"]
        self.options_menu.update(frame_input.pressed)

    def _update_char_select(self, ctx):
        """Update character select state."""
        # Reset the battle when at char_select with no win recorded (#230, replacing
        # game.py's should_reset_game poll). State is char_select here by definition,
        # so the old guard's extra state check is implicit; winner/loser None is the
        # discriminator (a fresh selection, or returning before a match finished).
        if self.winner is None and self.loser is None:
            battle = ctx.get("battle")
            if battle is not None:
                battle.reset()

        frame_input = ctx["frame_input"]
        self.char_selector.update(frame_input.held, frame_input.pressed)

        # Handle back to menu timer
        if self.p1_controls["special"] in frame_input.held or self.p2_controls["special"] in frame_input.held:
            self.back_timer += 1
        else:
            self.back_timer = 0

    def _update_playing(self, ctx):
        """Update playing state — owns the per-frame battle sim + winner-set (#246).

        Runs ``battle.step`` then the win-check in one action, so win detection lands
        on the SAME frame the step produces the KO; the ``playing->win_screen`` hop
        then fires on the NEXT update (when ``_guard_playing_to_win_screen`` sees the
        winner set). game.py's loop body no longer runs the sim step or the winner-set.
        Players are created lazily on the first playing frame (the engine action runs
        before game.py's old loop-body create, so it owns that too)."""
        frame_input = ctx["frame_input"]
        battle = ctx.get("battle")
        if battle is None:
            return
        if battle.player1 is None or battle.player2 is None:
            p1_char, p2_char = self.get_selected_characters()
            p1_palette, p2_palette = self.get_selected_palettes()
            battle.create_from_selection(p1_char, p2_char, p1_palette, p2_palette)
        battle.step(frame_input, ctx.get("platforms"))
        winner, loser = battle.winner()
        if winner:
            self.set_winner(winner, loser)

    def _update_pause(self, ctx):
        """Update pause state."""
        frame_input = ctx["frame_input"]
        self.pause_menu.update(frame_input.pressed)

    def _update_win_screen(self, ctx):
        """Update win screen state."""
        frame_input = ctx["frame_input"]
        self.win_screen_manager.update(frame_input.pressed)

    def should_quit_game(self):
        """Check if the app should exit (from main_menu ESC-hold)."""
        return self.should_quit

    def esc_quit_progress(self):
        """Current ESC-hold progress as a 0..1 ratio for render callers."""
        if self.esc_quit_hold_frames <= 0:
            return 0.0
        return min(1.0, self.esc_quit_timer / self.esc_quit_hold_frames)

    def render_esc_quit_progress(self, surface):
        """Draw a small circular hold-progress indicator while ESC is held."""
        progress = self.esc_quit_progress()
        if progress <= 0:
            return

        radius = 28
        width = 6
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 155)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = center

        pygame.draw.circle(surface, WHITE, center, radius, 2)
        pygame.draw.arc(
            surface,
            MAIN_MENU_SELECTED_COLOR,
            rect,
            -math.pi / 2,
            -math.pi / 2 + math.tau * progress,
            width,
        )

    def _tick_esc_hold(self, frame_input):
        """Hold-ESC-to-navigate (#113, generalised #453): count frames while ESC is
        held; the value drives ``esc_hold_complete()``. The timer resets whenever
        ESC is released, or immediately when the setting is off (ESC is then inert —
        B / the menus still back out every screen).

        This method no longer decides a *destination*: it only maintains the timer.
        Each state's back-guard reads ``esc_hold_complete()`` to pop one level, and
        ``update()`` turns a completed hold at ``main_menu`` into an app quit.
        """
        from .settings import load

        if not load().get("esc_hold_to_navigate", True):
            self.esc_quit_timer = 0
            return
        if pygame.K_ESCAPE in frame_input.held:
            self.esc_quit_timer += 1
        else:
            self.esc_quit_timer = 0

    def esc_hold_complete(self):
        """True once ESC has been held for the full 2-second threshold (#453)."""
        return self.esc_quit_timer >= self.esc_quit_hold_frames

    # FSM Guard Functions
    def _guard_menu_to_char_select(self, ctx):
        """Check if should transition from main menu to character select."""
        if hasattr(self.main_menu, "action_requested") and self.main_menu.action_requested == "play":
            self.main_menu.action_requested = None
            return True
        elif hasattr(self.main_menu, "action_requested") and self.main_menu.action_requested == "quit":
            self.main_menu.action_requested = None
            self.should_quit = True
            return False
        return False

    def _guard_menu_to_options(self, ctx):
        """Enter the Options sub-menu when the main menu requests it."""
        if hasattr(self.main_menu, "action_requested") and self.main_menu.action_requested == "options":
            self.main_menu.action_requested = None
            return True
        return False

    def _guard_options_to_main_menu(self, ctx):
        """Return to the main menu when the Options sub-menu backs out (B / the
        ``back`` row) or ESC is held for 2s (#453)."""
        if hasattr(self.options_menu, "action_requested") and self.options_menu.action_requested == "back":
            self.options_menu.action_requested = None
            return True
        return self.esc_hold_complete()

    def _guard_char_select_to_playing(self, ctx):
        """Check if should transition from character select to playing."""
        frame_input = ctx["frame_input"]
        return self.char_selector.show_start_screen and self.char_selector.ready_to_start(frame_input.pressed)

    def _guard_char_select_to_main_menu(self, ctx):
        """Back to main menu from character select: hold-B for 1s (the existing
        char-select back) or hold-ESC for 2s (#453)."""
        return self.back_timer >= self.back_hold_frames or self.esc_hold_complete()

    def _guard_playing_to_pause(self, ctx):
        """Check if should transition from playing to pause."""
        frame_input = ctx["frame_input"]
        # Check if P key is pressed
        return pygame.K_p in frame_input.pressed

    def _guard_pause_to_playing(self, ctx):
        """Check if should transition from pause to playing."""
        # Check if pause menu has a resume action (only through menu selection now)
        if hasattr(self.pause_menu, "action_requested") and self.pause_menu.action_requested == "resume":
            # Clear the action so it doesn't get processed again
            self.pause_menu.action_requested = None
            return True
        return False

    def _guard_pause_to_stats(self, ctx):
        """Check if should transition from pause to stats (win screen for stats)."""
        if hasattr(self.pause_menu, "action_requested") and self.pause_menu.action_requested == "end_match":
            # Clear the action and trigger stats display
            self.pause_menu.action_requested = None
            # Set up win screen to show current stats without declaring a winner
            # We'll use a special mode where both players are alive but we show stats
            return True
        return False

    def _guard_playing_to_char_select(self, ctx):
        """Leave an active match to character select on a 2s ESC-hold (#453). The
        match is abandoned; char_select's entry/update resets the battle."""
        if self.esc_hold_complete():
            self.winner = None
            self.loser = None
            return True
        return False

    def _guard_pause_to_char_select(self, ctx):
        """Leave a paused match to character select — via the pause menu's
        ``return_to_char_select`` button (#453 #4) or a 2s ESC-hold. Abandons the
        match (winner/loser cleared; char_select resets the battle)."""
        if (
            hasattr(self.pause_menu, "action_requested") and self.pause_menu.action_requested == "return_to_char_select"
        ) or self.esc_hold_complete():
            self.pause_menu.action_requested = None
            self.winner = None
            self.loser = None
            return True
        return False

    def _guard_playing_to_win_screen(self, ctx):
        """Check if should transition from playing to win screen."""
        return self.winner is not None and self.loser is not None

    def _guard_win_screen_to_char_select(self, ctx):
        """Back to character select from the win/stats screen: both players confirm
        (the #10 gate) or a 2s ESC-hold bypasses it (#453 #3). Either way the match
        is cleared."""
        if self.win_screen_manager.ready_to_return() or self.esc_hold_complete():
            # Reset game state when transitioning back
            self.winner = None
            self.loser = None
            return True
        return False
