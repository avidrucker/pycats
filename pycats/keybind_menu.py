# pycats/keybind_menu.py
#
# Capture-flow controller for the Options keybinding screen (#447). Pure logic over
# two per-player `Keymap`s (#439): which player/action is focused, the "press a key
# to bind" capture, conflict handling, and reset. The pygame KEYDOWN read + rendering
# are a thin layer that call `capture_key` / `reset_player` and render this state.
from __future__ import annotations

from .core.keymap import KeyBindingConflict


class KeybindMenu:
    def __init__(self, p1_keymap, p2_keymap):
        self.keymaps = [p1_keymap, p2_keymap]
        # The rebindable actions, in the keymap's own order (both players share them).
        self.actions = list(p1_keymap.keys())
        self.player = 0
        self.action_index = 0
        self.capturing = False
        self.message = ""

    @property
    def action(self):
        return self.actions[self.action_index]

    def focus(self, player, action):
        self.player = player
        self.action_index = self.actions.index(action)

    def nav(self, delta):
        """Move the focused action by `delta` rows (wraps)."""
        self.action_index = (self.action_index + delta) % len(self.actions)

    def switch_player(self):
        self.player = 1 - self.player

    def activate(self):
        """Enter capture on the focused action (press a key to bind next)."""
        self.begin_capture()

    def begin_capture(self):
        self.capturing = True
        self.message = ""

    def cancel_capture(self):
        self.capturing = False

    def reset_player(self, player):
        """Restore `player`'s factory keymap (leaves the other player untouched)."""
        self.keymaps[player].reset()
        self.message = "reset to defaults"

    def capture_key(self, keycode):
        """Bind the focused action to `keycode`. Ends capture either way; returns
        True on success, False on a conflict (binding untouched, `message` names it)."""
        self.capturing = False
        try:
            self.keymaps[self.player].rebind(self.action, keycode)
            self.message = f"{self.action} bound"
            return True
        except KeyBindingConflict as conflict:
            self.message = f"already used by {conflict.action}"
            return False

    def binding(self, player, action):
        return self.keymaps[player][action]
