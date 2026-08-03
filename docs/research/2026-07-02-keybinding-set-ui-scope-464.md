# Spike #464 — scope the keybinding-set UI (#463) + the shared text-entry mechanism

**Agent:** ELDERBERRY · **Date:** 2026-07-02 · **Parent:** #463 · Epic #438. **Scope-only — no production code.**

## Current state
- Persistence exists: `keybind_store` (#440) — `save_set` / `list_sets` / `load_set` / `delete_set` over `profiles/keybindings.json`.
- In-memory rebinding exists: `OptionsMenu`'s keybind sub-mode + `KeybindMenu` (#455).
- **No UI calls the store**, and **no text-entry mechanism exists** in the screen system.

## The crux — text entry
Naming a saved scheme (and #441's nickname) needs typed input. Two facts decide the approach:
- Screens receive only **`frame_input.pressed`** (a derived keycode set) via `screen_manager.update(frame_input, …)` (`screen_manager.py:106`) — **raw events are NOT threaded to screens** (`game.py:356-358` keeps the event list in the top loop).
- The menu layer is pure-logic + thin-render and unit-tested headless (`menu_layout.py`, `menu_widgets.focus_label`).

| Option | Verdict |
|---|---|
| **On-screen keyboard grid** (letter grid navigated by the existing pressed-nav; attack=select-char, special=backspace/done) | **RECOMMENDED** — no new event plumbing, controller-friendly, headless-testable (pure buffer logic), reusable by #463 + #441. |
| `pygame.TEXTINPUT` field | Rejected — keyboard-only (no gamepad), and requires threading raw text events through `screen_manager.update` (new plumbing), harder to test headless. |
| Letter-cycle (A→B→C per slot) | Rejected — tolerable for a ≤4-char nickname but tedious for arbitrary set names; the keyboard grid subsumes it. |

## Decisions (locked)
1. **Shared on-screen text-entry widget** — a pure `TextEntry` model: a char grid + cursor + buffer + `maxlen`; methods `nav(dx, dy)`, `select()` (append focused char), `backspace()`, `done()`; exposes `text` + cursor for a thin render. **#463 uses it for set names; #441 (#465) reuses it for nicknames (`maxlen=4`).** This is the foundational piece — file it once, both consume it.
2. **Placement:** extend the `OptionsMenu` keybind sub-mode (#455) with "Save scheme…" / "Load scheme…" actions, rather than a new `ScreenStateManager` screen — reuses the existing `update(pressed)` / render / input-cooldown, stays headless-testable.
3. **Flow (per the current keybind-screen player):**
   - **Save:** "Save scheme…" → text-entry (name) → `save_set(name, keymaps[player])`.
   - **Load:** "Load scheme…" → navigable set-list from `list_sets()` → `load_set(name, keymaps[player])`.
   - **Rename:** pick from list → text-entry → save under new name + `delete_set(old)`. **Delete:** pick from list → confirm → `delete_set(name)`.
4. **Set-list render:** reuse `menu_layout` (grid/scroll) + `menu_widgets.draw_menu_button` + the `CharacterSelector` cursor-nav pattern (`char_select.py:154`, cooldown-gated pressed nav).

## Key code sites
- `pycats/keybind_store.py` (#440) — the store the UI drives.
- `pycats/options_menu.py` (#455 keybind sub-mode) — host the save/load actions + the set-list sub-view.
- `pycats/menu_layout.py` / `pycats/menu_widgets.py` — pure layout + button widget to reuse for the keyboard + list.
- `pycats/char_select.py:154` — `CharacterSelector` selection-nav precedent.

## Perceived ROI
**High** — unblocks the entire profiles/keybindings UI chain, and the shared text-entry widget serves both #463 and #441 (one build, two consumers).

## Recommendation — decompose
- [x] **Decompose:** file **1 new shared DEV** — the reusable on-screen text-entry widget (child of #438) — which **blocks #463 and #441**. #463 then stays a single DEV (set-list + save/load/rename/delete wired to `keybind_store`, using the widget), gaining a `blocked-by` the widget + the locked design above. #465 (the #441 spike) reuses the widget decision (no second text-entry design).
