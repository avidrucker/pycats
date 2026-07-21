"""Shared navigation/selection controller for the option-list menu screens (#837).

`MainMenuManager` and `PauseMenuManager` had byte-identical `__init__` / `reset` /
`update` / `get_action` bodies — the only differences were the `options` list and
what a confirmed selection maps to. This base carries the shared state and the
nav/select loop; subclasses supply `options` and `on_select(index)` and keep only
their own `render`.

Behaviour is preserved exactly, including the original loop's quirks: up and down
are independent `if`s (both fire in a frame that presses both, a net no-op that
still arms the cooldown), and the select check does not re-read the cooldown, so a
nav+attack frame both moves focus and confirms — same as before the extraction.

Select reads the rebindable `p1/p2_controls["attack"]` for both players (the #842
fix, now shared here), so an attack rebind is honoured on every menu.
"""

from .config import MENU_NAV_COOLDOWN, MENU_SELECT_COOLDOWN
from .menu_widgets import PRESS_PULSE_FRAMES


class MenuController:
    """Base for the two-player option-list menus. Subclasses define `options` and
    `on_select(index)`; this owns navigation, selection, cooldown, and the press
    pulse."""

    def __init__(self, p1_controls, p2_controls):
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        self.options = []
        self.selected_option = 0  # Index of currently selected option

        # Input debouncing
        self.input_cooldown = 0

        # Press-feedback flash: frames remaining on the focused button's pulse (#332).
        self.press_pulse = 0

        # Action results
        self.action_requested = None

    def on_select(self, index):
        """Return the action string for confirming `options[index]` (or None).

        Subclass hook — called when an attack key is pressed on a focused row."""
        raise NotImplementedError

    def reset(self):
        """Reset the menu state."""
        self.selected_option = 0
        self.input_cooldown = 0
        self.press_pulse = 0
        self.action_requested = None

    def _pressed_by_either(self, action, pressed_keys):
        """True if either player's binding for `action` is down this frame."""
        return self.p1_controls[action] in pressed_keys or self.p2_controls[action] in pressed_keys

    def update(self, pressed_keys):
        """Update menu based on player input."""
        # Decay the press-flash every frame, before the cooldown early-return, so it
        # still ticks down while input is debounced (#332).
        if self.press_pulse > 0:
            self.press_pulse -= 1

        # Decrease input cooldown
        if self.input_cooldown > 0:
            self.input_cooldown -= 1

        # Don't process input during cooldown
        if self.input_cooldown > 0:
            return

        # Handle navigation input from either player (wraps over N options)
        if self._pressed_by_either("up", pressed_keys):
            self.selected_option = (self.selected_option - 1) % len(self.options)
            self.input_cooldown = MENU_NAV_COOLDOWN  # Prevent rapid navigation
            self.press_pulse = PRESS_PULSE_FRAMES  # flash the newly-focused row

        if self._pressed_by_either("down", pressed_keys):
            self.selected_option = (self.selected_option + 1) % len(self.options)
            self.input_cooldown = MENU_NAV_COOLDOWN  # Prevent rapid navigation
            self.press_pulse = PRESS_PULSE_FRAMES  # flash the newly-focused row

        # Handle selection from either player's ATTACK key. Reads the rebindable
        # p1/p2_controls["attack"] (#842) so an attack rebind is honoured here.
        if self._pressed_by_either("attack", pressed_keys):
            self.action_requested = self.on_select(self.selected_option)
            self.input_cooldown = MENU_SELECT_COOLDOWN  # Prevent rapid selection
            self.press_pulse = PRESS_PULSE_FRAMES  # flash the confirmed row

    def get_action(self):
        """Get the requested action and clear it."""
        action = self.action_requested
        self.action_requested = None
        return action
