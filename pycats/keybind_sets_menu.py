# pycats/keybind_sets_menu.py
#
# Save / load / rename / delete UI controller for named keybinding schemes (#463).
# Pure logic over `keybind_store` (#440), a `TextEntry` (#471) for names, and a
# set-list cursor. A sub-mode of the Options keybinding screen (#455): the pygame
# `pressed`-set read + rendering are a thin adapter in options_menu.py that calls
# `move` / `select` / `back` and renders this state. Locked design: spike #464
# (docs/research/2026-07-02-keybinding-set-ui-scope-464.md).
from __future__ import annotations

from . import keybind_store
from .text_entry import TextEntry

# Max characters in a saved-scheme name (the on-screen grid is uppercase, #471).
NAME_MAXLEN = 12


class KeybindSetsMenu:
    # Top-level actions, in display order. Trailing "…" flags the ones that open a
    # sub-view (text entry or the set list); "Back" leaves the sets sub-mode.
    MENU = ["Save current...", "Load...", "Rename...", "Delete...", "Back"]

    def __init__(self, keymaps):
        # keymaps[player] is the live Keymap the save/load acts on (shared with the
        # KeybindMenu so an in-memory remap is what gets saved).
        self.keymaps = keymaps
        self.player = 0
        self.view = "menu"          # "menu" | "list" | "text" | "confirm"
        self.menu_index = 0
        self.sets = []
        self.list_index = 0
        self.list_action = None     # "load" | "rename" | "delete" — what the list picks for
        self.entry = None           # a TextEntry while view == "text"
        self.entry_action = None    # "save" | "rename"
        self.rename_from = None     # the old name while renaming
        self.confirm_name = None    # the name pending delete-confirmation
        self.message = ""
        self.done = False           # set when the sub-mode should hand back to the keybind screen

    # ---- entry / exit ----
    def open(self, player):
        """Enter the sets menu focused on `player` (the keybind screen's active player)."""
        self.player = player
        self.view = "menu"
        self.menu_index = 0
        self.message = ""
        self.done = False
        self._refresh()

    def _refresh(self):
        self.sets = keybind_store.list_sets()

    # ---- navigation ----
    def move(self, dx, dy):
        """Move the active cursor. In the menu/list dy steps the vertical cursor; in
        text-entry both axes drive the character grid; confirm ignores movement."""
        if self.view == "menu":
            self.menu_index = (self.menu_index + dy) % len(self.MENU)
        elif self.view == "list":
            if self.sets:
                self.list_index = (self.list_index + dy) % len(self.sets)
        elif self.view == "text":
            self.entry.nav(dx, dy)

    # ---- activation ----
    def select(self):
        if self.view == "menu":
            self._select_menu()
        elif self.view == "list":
            self._select_list()
        elif self.view == "text":
            self._select_text()
        elif self.view == "confirm":
            self._do_delete(self.confirm_name)

    def _select_menu(self):
        action = self.MENU[self.menu_index]
        if action == "Save current...":
            self._begin_text("save")
        elif action == "Load...":
            self._begin_list("load")
        elif action == "Rename...":
            self._begin_list("rename")
        elif action == "Delete...":
            self._begin_list("delete")
        elif action == "Back":
            self.done = True

    def _begin_list(self, list_action):
        self._refresh()
        if not self.sets:
            self.message = "no saved schemes"
            return
        self.list_action = list_action
        self.list_index = 0
        self.view = "list"

    def _begin_text(self, entry_action, initial=""):
        self.entry = TextEntry(NAME_MAXLEN)
        self.entry_action = entry_action
        self.view = "text"

    def _select_list(self):
        name = self.sets[self.list_index]
        if self.list_action == "load":
            keybind_store.load_set(name, self.keymaps[self.player])
            self.message = f"loaded {name}"
            self.view = "menu"
        elif self.list_action == "rename":
            self.rename_from = name
            self._begin_text("rename")
        elif self.list_action == "delete":
            self.confirm_name = name
            self.view = "confirm"

    def _select_text(self):
        self.entry.select()
        if not self.entry.confirmed:
            return
        name = self.entry.text.strip()
        if not name:                      # DONE on an empty buffer — stay and prompt
            self.entry.confirmed = False
            self.message = "name required"
            return
        if self.entry_action == "save":
            keybind_store.save_set(name, self.keymaps[self.player])
            self.message = f"saved {name}"
        elif self.entry_action == "rename":
            keybind_store.save_set(name, self.keymaps[self.player])
            if name != self.rename_from:
                keybind_store.delete_set(self.rename_from)
            self.message = f"renamed to {name}"
        self._refresh()
        self.view = "menu"

    def _do_delete(self, name):
        keybind_store.delete_set(name)
        self.message = f"deleted {name}"
        self._refresh()
        self.view = "menu"

    # ---- back ----
    def back(self):
        """B / special: back out one level — a sub-view returns to the menu; the menu
        signals `done` so the adapter hands input back to the keybind screen."""
        if self.view == "menu":
            self.done = True
        else:
            self.view = "menu"
