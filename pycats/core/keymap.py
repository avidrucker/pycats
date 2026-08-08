# pycats/core/keymap.py
#
# Per-player rebindable keymap (#439). A `Keymap` is a mutable action->keycode map
# seeded from factory defaults. Pygame-free (keys are ints) so it lives in the `core`
# port; it subclasses `dict` so it drops into the existing `controls["attack"]` /
# `controls.get(name)` reads unchanged.
from __future__ import annotations


class KeyBindingConflict(ValueError):
    """Raised when rebinding to a key already bound to a different action.

    `.action` names that other action, so the UI can flag the conflict."""

    def __init__(self, action):
        super().__init__(f"key already bound to action {action!r}")
        self.action = action


class Keymap(dict):
    def __init__(self, defaults):
        super().__init__(defaults)
        self._factory = dict(defaults)  # immutable snapshot to reset to (per instance)

    def reset(self):
        """Restore this player's factory defaults (leaves other keymaps untouched)."""
        self.clear()
        self.update(self._factory)

    def rebind(self, action, key):
        """Point `action` at `key`. No-op if `key` is already this action's key;
        raises `KeyBindingConflict` (map untouched) if another action holds it."""
        if self.get(action) == key:
            return
        holder = next((a for a, k in self.items() if k == key), None)
        if holder is not None:
            raise KeyBindingConflict(holder)
        self[action] = key
