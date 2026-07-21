# Pause-menu select-key ignores attack rebinds — source verification

**Ticket:** #836 (RESEARCH, child of menu-dedup #837, under refactoring epic #833).
**Date:** 2026-07-21 · **Agent:** APPLE · **Scope:** docs-only; no source change.
**Basis:** refactoring review findings `docs/research/2026-07-21-codebase-refactoring-review-findings.md` §1.

## Verdict: **CONFIRMED**

The review's §1 claim holds against source: `PauseMenuManager.update` decides "select"
against the **hardcoded** keycodes `pygame.K_SLASH` / `pygame.K_v`, whereas
`MainMenuManager.update` decides it against the **rebindable** `p1_controls["attack"]` /
`p2_controls["attack"]`. Both managers are handed the *same* live `Keymap` objects, so the
pause menu has the rebound key available and ignores it. After a player rebinds **attack**
away from its default (`v` for P1, `/` for P2), the pause menu's select stops responding to
that player's attack key — only the original `/` or `v` still selects.

## Evidence (verbatim, function + file)

### `pause_menu` — select is hardcoded

`PauseMenuManager.update` in `pycats/pause_menu.py` (navigation reads the rebindable
`p1_controls["up"]`/`["down"]`, but select does **not**):

```python
# Handle selection input from either player (/ or V keys only)
if (
    pygame.K_SLASH in pressed_keys  # P2's attack key
    or pygame.K_v in pressed_keys  # P1's attack key
):
    if self.selected_option == 0:  # Resume
        self.action_requested = "resume"
    ...
```

### `main_menu` — select follows the rebind

`MainMenuManager.update` in `pycats/main_menu.py`:

```python
# Handle selection input from either player
if self.p1_controls["attack"] in pressed_keys or self.p2_controls["attack"] in pressed_keys:
    self.action_requested = {
        "Play": "play",
        "Options": "options",
        "Quit": "quit",
    }.get(self.options[self.selected_option])
```

### The hardcoded values are exactly the *defaults* of the rebindable action

`P1_KEYS` / `P2_KEYS` in `pycats/app.py` — the factory defaults "reset to defaults" restores:

```python
P1_KEYS = Keymap(dict(... attack=pygame.K_v, ...))
P2_KEYS = Keymap(dict(... attack=pygame.K_SLASH, ...))
```

So with default binds the pause menu behaves identically to the main menu; the divergence
only surfaces once `attack` is rebound. This is why the bug is easy to miss.

### `attack` is genuinely rebindable, and the pause menu holds the live keymap

- `KeybindMenu.__init__` in `pycats/keybind_menu.py` makes *every* action rebindable —
  `self.actions = list(p1_keymap.keys())` — and `bind` calls
  `self.keymaps[self.player].rebind(self.action, keycode)`, mutating the `Keymap` in place.
- `ScreenStateManager.__init__` in `pycats/screen_manager.py` constructs **both** managers
  from the same objects:

  ```python
  self.main_menu = MainMenuManager(p1_controls, p2_controls)
  ...
  self.pause_menu = PauseMenuManager(p1_controls, p2_controls)
  ```

  `rebind` mutates that shared `Keymap`, so `self.p1_controls["attack"]` inside the pause
  menu *would* return the rebound key — the select branch simply never reads it.

## Player-facing impact

A player who opens the in-game keybind menu and rebinds their **attack** to any key other
than the default (`v` for P1, `/` for P2) will find that, in the pause menu:

- **Navigation still works** — up/down read the rebindable `["up"]`/`["down"]`.
- **Select is deaf to their rebound attack key** — pressing it does nothing. Only the
  literal `/` or `v` confirms a pause-menu choice.

It is a functional inconsistency within one screen (its own nav honors rebinds, its select
does not), and it contradicts the pause menu's own on-screen hint "Press V or / to select"
only in the narrow sense that a rebinding player expects their bound key to work. The menu
is not hard-locked: `/` and `v` still select, and Resume also remains reachable via the
pause toggle / ESC path, so the player is not stranded.

## Repro (spec, for a downstream DEV ticket)

1. Launch the game, enter Options → Keybinds, rebind **P1 attack** from `v` to some other
   key (e.g. `j`).
2. Start a match, open the pause menu.
3. Navigate with W/S — focus moves (nav honors the rebind).
4. Press the rebound attack key (`j`) — **no selection fires** (bug).
5. Press `v` — selection fires (the original hardcoded default still works).

Able-to-fail regression target for the fix: drive `PauseMenuManager.update` with a
`p1_controls` whose `attack` is rebound to a non-default keycode and `pressed_keys`
containing that keycode; assert `get_action()` returns the focused option's action. Red
against the hardcoded branch, green once select reads `p1_controls["attack"]` /
`p2_controls["attack"]`.

## Recommended severity for the follow-up DEV ticket: **`severity:low`**

It is a real defect (a rebind the UI offers is ignored on one screen), but narrow:

- It manifests **only** after a player actively rebinds attack away from `/`/`v`.
- Navigation still functions and the default keys still select, so the pause menu is never
  hard-locked — the player can always Resume.
- No effect on default-config play (the overwhelming common case).

A `severity:medium` argument exists (the rebound key is fully non-functional for select on
that screen, which is surprising); calling it `severity:low` reflects the narrow trigger and
the available fallback. Final label is the DEV ticket's call.

## Recommendation

File a follow-up DEV bug-fix ticket (`bug` + `severity:low`) to make `pause_menu` select
read `p1_controls["attack"]` / `p2_controls["attack"]` (matching `main_menu`), landing an
able-to-fail regression test in the same commit. Keep this **separate** from the menu-dedup
refactor #837, which stays behavior-preserving — #837 is held `blocked` on this thread so
the fix ships with its own test rather than as a construction side effect. Filing that DEV
ticket is downstream and awaits an explicit go-ahead.
