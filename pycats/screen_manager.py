"""
Screen state management using FSM for the cat fighting game.

This module handles:
- Managing transitions between different game screens
- Screen state logic and timing
- Input handling for screen transitions
"""

import pygame  # type: ignore
from .systems.fsm import FSM, Transition
from .main_menu import MainMenuManager
from .char_select import CharacterSelector
from .win_screen import WinScreenManager
from .pause_menu import PauseMenuManager


class ScreenStateManager:
    """Manages screen states and transitions using FSM."""

    def __init__(self, p1_controls, p2_controls):
        # Player controls
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        # Screen managers
        self.main_menu = MainMenuManager(p1_controls, p2_controls)
        self.char_selector = CharacterSelector(p1_controls, p2_controls)
        self.win_screen_manager = WinScreenManager(p1_controls, p2_controls)
        self.pause_menu = PauseMenuManager(p1_controls, p2_controls)

        # Back to menu timer for character select
        self.back_timer = 0
        self.back_hold_frames = 60  # 1 second at 60 FPS

        # FSM setup
        self.fsm = FSM(
            state="main_menu",
            on_enter={
                "main_menu": self._on_enter_main_menu,
                "char_select": self._on_enter_char_select,
                "playing": self._on_enter_playing,
                "pause": self._on_enter_pause,
                "win_screen": self._on_enter_win_screen,
            },
            on_update={
                "main_menu": self._update_main_menu,
                "char_select": self._update_char_select,
                "playing": self._update_playing,
                "pause": self._update_pause,
                "win_screen": self._update_win_screen,
            },
            table={
                "main_menu": [
                    Transition("char_select", self._guard_menu_to_char_select),
                ],
                "char_select": [
                    Transition("playing", self._guard_char_select_to_playing),
                    Transition("main_menu", self._guard_char_select_to_main_menu),
                ],
                "playing": [
                    Transition("pause", self._guard_playing_to_pause),
                    Transition("win_screen", self._guard_playing_to_win_screen),
                ],
                "pause": [
                    Transition("playing", self._guard_pause_to_playing),
                    Transition("win_screen", self._guard_pause_to_stats),
                    Transition("main_menu", self._guard_pause_to_main_menu),
                ],
                "win_screen": [
                    Transition("char_select", self._guard_win_screen_to_char_select),
                ],
            },
        )

        # Game state data
        self.winner = None
        self.loser = None
        self.should_quit = False

    def update(self, frame_input):
        """Update the screen state manager."""
        # Update the FSM with input context
        self.fsm.update({"frame_input": frame_input, "screen_manager": self})

    def render(self, surface):
        """Render the current screen."""
        if self.fsm.state == "main_menu":
            self.main_menu.render(surface)
        elif self.fsm.state == "char_select":
            self.char_selector.render(surface)
        elif self.fsm.state == "win_screen":
            self.win_screen_manager.render(surface)
        elif self.fsm.state == "pause":
            # Pause menu rendering is handled by the main game loop
            pass
        # Note: "playing" state is handled by the main game loop

    def get_state(self):
        """Get the current state."""
        return self.fsm.state

    def set_winner(self, winner, loser):
        """Set the winner data for win screen."""
        self.winner = winner
        self.loser = loser

    def get_selected_characters(self):
        """Get the selected characters from character selection."""
        return self.char_selector.get_selected_characters()

    def set_stats_data(self, player1, player2):
        """Set stats data for viewing current match stats from pause."""
        # Set both players as winner/loser for stats display
        # The win screen will handle this appropriately
        self.win_screen_manager.set_match_data(player1, player2, from_pause=True)

    def get_pause_menu(self):
        """Get the pause menu manager."""
        return self.pause_menu

    def should_quit_game(self):
        """Check if the game should quit."""
        return self.should_quit

    def should_reset_game(self):
        """Check if the game should be reset (when returning from win screen)."""
        # Check if we just transitioned from win screen to char select
        return (
            self.fsm.state == "char_select"
            and self.winner is None
            and self.loser is None
        )

    # FSM State Enter Handlers
    def _on_enter_main_menu(self, fsm, ctx):
        """Called when entering main menu state."""
        self.main_menu.reset()

    def _on_enter_char_select(self, fsm, ctx):
        """Called when entering character select state."""
        # Reset character selector if coming from main menu
        if hasattr(self.char_selector, "reset"):
            self.char_selector.reset()
        self.back_timer = 0

    def _on_enter_playing(self, fsm, ctx):
        """Called when entering playing state."""
        # Game loop will handle this state
        pass

    def _on_enter_pause(self, fsm, ctx):
        """Called when entering pause state."""
        # Reset pause menu state
        self.pause_menu.reset()

    def _on_enter_win_screen(self, fsm, ctx):
        """Called when entering win screen state."""
        if self.winner and self.loser:
            # Normal win condition
            self.win_screen_manager.set_match_data(self.winner, self.loser)
        else:
            # Coming from pause menu - show stats for current match
            # We need to get the current players from the game context
            screen_manager = ctx.get("screen_manager", self)
            # The game.py will need to provide player data, for now just set dummy data
            # This will be handled by the game loop providing the current players

    # FSM State Update Handlers
    def _update_main_menu(self, fsm, ctx):
        """Update main menu state."""
        frame_input = ctx["frame_input"]
        self.main_menu.update(frame_input.pressed)

    def _update_char_select(self, fsm, ctx):
        """Update character select state."""
        frame_input = ctx["frame_input"]
        self.char_selector.update(frame_input.held, frame_input.pressed)

        # Handle back to menu timer
        if (
            self.p1_controls["special"] in frame_input.held
            or self.p2_controls["special"] in frame_input.held
        ):
            self.back_timer += 1
        else:
            self.back_timer = 0

    def _update_playing(self, fsm, ctx):
        """Update playing state."""
        # The main game loop handles this state
        pass

    def _update_pause(self, fsm, ctx):
        """Update pause state."""
        frame_input = ctx["frame_input"]
        self.pause_menu.update(frame_input.pressed)

    def _update_win_screen(self, fsm, ctx):
        """Update win screen state."""
        frame_input = ctx["frame_input"]
        self.win_screen_manager.update(frame_input.pressed)

    # FSM Guard Functions
    def _guard_menu_to_char_select(self, fsm, ctx):
        """Check if should transition from main menu to character select."""
        # Check if the main menu has a "play" action ready without consuming it
        # We'll peek at the action_requested without clearing it
        if (
            hasattr(self.main_menu, "action_requested")
            and self.main_menu.action_requested == "play"
        ):
            # Clear the action so it doesn't get processed again
            self.main_menu.action_requested = None
            return True
        elif (
            hasattr(self.main_menu, "action_requested")
            and self.main_menu.action_requested == "quit"
        ):
            # Handle quit action
            self.main_menu.action_requested = None
            self.should_quit = True
            return False
        return False

    def _guard_char_select_to_playing(self, fsm, ctx):
        """Check if should transition from character select to playing."""
        frame_input = ctx["frame_input"]
        return (
            self.char_selector.show_start_screen
            and self.char_selector.ready_to_start(frame_input.pressed)
        )

    def _guard_char_select_to_main_menu(self, fsm, ctx):
        """Check if should go back to main menu from character select."""
        return self.back_timer >= self.back_hold_frames

    def _guard_playing_to_pause(self, fsm, ctx):
        """Check if should transition from playing to pause."""
        frame_input = ctx["frame_input"]
        # Check if P key is pressed
        return pygame.K_p in frame_input.pressed

    def _guard_pause_to_playing(self, fsm, ctx):
        """Check if should transition from pause to playing."""
        # Check if pause menu has a resume action (only through menu selection now)
        if (
            hasattr(self.pause_menu, "action_requested")
            and self.pause_menu.action_requested == "resume"
        ):
            # Clear the action so it doesn't get processed again
            self.pause_menu.action_requested = None
            return True
        return False

    def _guard_pause_to_stats(self, fsm, ctx):
        """Check if should transition from pause to stats (win screen for stats)."""
        if (
            hasattr(self.pause_menu, "action_requested")
            and self.pause_menu.action_requested == "end_match"
        ):
            # Clear the action and trigger stats display
            self.pause_menu.action_requested = None
            # Set up win screen to show current stats without declaring a winner
            # We'll use a special mode where both players are alive but we show stats
            return True
        return False

    def _guard_pause_to_main_menu(self, fsm, ctx):
        """Check if should transition from pause to main menu."""
        if (
            hasattr(self.pause_menu, "action_requested")
            and self.pause_menu.action_requested == "return_to_menu"
        ):
            # Clear the action and reset game state
            self.pause_menu.action_requested = None
            # Reset winner/loser to clean state
            self.winner = None
            self.loser = None
            return True
        return False

    def _guard_playing_to_win_screen(self, fsm, ctx):
        """Check if should transition from playing to win screen."""
        return self.winner is not None and self.loser is not None

    def _guard_win_screen_to_char_select(self, fsm, ctx):
        """Check if should transition from win screen to character select."""
        if self.win_screen_manager.ready_to_return():
            # Reset game state when transitioning back
            self.winner = None
            self.loser = None
            return True
        return False
