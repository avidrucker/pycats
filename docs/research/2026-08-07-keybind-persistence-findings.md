# Keybinding-change persistence — auto-saved on edit / on exit / neither, and is it tested?

> **Agent:** APPLE · **Authored:** 2026-08-07 · **Ticket:** #1302

## Question

When a player rebinds a control in the Options menu, is that change persisted — and
if so, *when* (auto-saved on each edit, saved on program exit, or never)? Does a
changed binding survive a program restart? And is the save/load path tested?

## Answer (short)

**Neither auto-on-edit nor on-exit.** A rebind lives only in an in-memory `Keymap`
and is **lost on restart**. There is exactly one on-disk writer for bindings, and it
fires only when the user manually saves a *named scheme* ("Save current…"). There is
**no loader at boot**: the game always starts from hardcoded factory defaults, and
even a saved scheme is not auto-restored — the user must re-enter Options and "Load…"
it each session. The manual named-scheme save/load path is well tested; the three
"auto" behaviors the ticket asks about are absent in code and therefore untested (an
absence, not a gap in coverage).

## Findings

### 1. Where bindings live at runtime, and what a rebind does

- Runtime store: `pycats/core/keymap.py` → `class Keymap(dict)`. An action→keycode
  map seeded from factory defaults; `reset()` restores this instance's defaults,
  `rebind(action, key)` repoints one action (raising `KeyBindingConflict` if the key
  is held by another action).
- Live instances: `pycats/shell/app.py` → module-level `P1_KEYS` / `P2_KEYS`, each a
  hardcoded `Keymap(dict(left=pygame.K_a, …))`. The same instances are handed to
  `BattleScreen(P1_KEYS, P2_KEYS)` and `ScreenStateManager(P1_KEYS, P2_KEYS, …)`, so a
  rebind takes effect live in-battle.
- Edit UI: `pycats/screens/keybind_menu.py` → `KeybindMenu.capture_key`, driven by
  `pycats/screens/options_menu.py` → `OptionsMenu._update_keybind`. `capture_key`
  calls `Keymap.rebind` and does **zero** file I/O.

`Keymap.rebind` in full — no writer on the edit path:

```python
def rebind(self, action, key):
    if self.get(action) == key:
        return
    holder = next((a for a, k in self.items() if k == key), None)
    if holder is not None:
        raise KeyBindingConflict(holder)
    self[action] = key
```

### 2. The only writer, and when it fires — (c) never automatic

`pycats/storage/keybind_store.py` → `save_set` / `_write` is the **only** code that
writes bindings to disk:

```python
def save_set(name, keymap):
    """Save `keymap`'s bindings under `name` as key names (overwrites an existing name)."""
    data = _read()
    data[name] = {action: pygame.key.name(code) for action, code in keymap.items()}
    _write(data)
```

Bindings serialize as key **names** (`pygame.key.name`), into
`<config>/profiles/keybindings.json` (`settings._config_dir()`), keyed by a
user-chosen scheme name.

`save_set` has exactly one non-test caller: `pycats/screens/keybind_sets_menu.py` →
`KeybindSetsMenu._select_text`, reached only when the user navigates to the "Schemes…"
sub-menu, picks "Save current…", types a name, and confirms. There is **no**
`atexit`/`pygame.QUIT`/quit-handler that saves bindings — the exit path
(`pycats/game.py` → `main()` ending in `pygame.quit(); sys.exit()`) writes nothing.
`App.save_prefs` *is* an on-change persister, but only for **display** prefs
(`windowed_scale`, `fullscreen`) — it never touches keymaps.

Callers of the store (grep, non-test): `save_set`/`load_set`/`delete_set`/`list_sets`
appear only in `keybind_sets_menu.py`. `keybind_store` is imported nowhere in
`app.py` or `game.py`.

### 3. No loader at boot — restart drops the change

Bindings are always the hardcoded defaults at startup:

- `pycats/shell/app.py` builds `P1_KEYS`/`P2_KEYS` from literal `Keymap(dict(…))` at
  module scope.
- `pycats/game.py` → `main()` calls only `prefs = settings.load()` +
  `runtime_settings.seed(prefs)` — **display** prefs. It never calls
  `keybind_store.load_set`.
- `keybind_store.load_set` exists but is called only from the UI
  (`keybind_sets_menu.py`, manual "Load…"), never at startup.
- Player profiles don't rescue this either: `pycats/storage/profile_store.py` is not
  imported by `app.py` or `game.py`, so no profile-driven scheme is auto-applied at
  boot.

Net round-trip answer to the ticket's repro (change a binding → quit → relaunch):
**the change does not survive.** Even a manually-saved scheme is not auto-restored;
the user must re-open Options → Schemes… → "Load…" every session.

### 4. Test coverage

The **named-scheme** save/load/round-trip path is well covered:

- `tests/test_keybind_store.py` — direct store round-trips:
  `test_round_trip_restores_the_exact_keymap` (save then load restores
  `dict(loaded) == dict(km)`), `test_save_set_then_list_sets_returns_the_name`,
  `test_format_serializes_key_names_not_codes` (on-disk value is `"v"`, not `118`),
  `test_named_sets_coexist_delete_and_overwrite`,
  `test_missing_file_lists_no_sets` / `test_corrupt_file_degrades_to_no_sets`,
  `test_unknown_action_or_unparseable_name_falls_back_to_factory_default`,
  `test_wholesale_replace_allows_a_key_swap_without_conflict`.
- `tests/test_options_keybind_sets.py` →
  `test_saving_through_the_ui_captures_the_live_rebound_keymap` — sets a live rebind,
  drives the UI save, asserts the loaded set carries it. Proves the UI saves the
  *live* keymap **when the save is manually driven**.
- `tests/test_keybind_sets_menu.py` — menu-controller round-trips (save/rename/delete).
- `tests/test_keybind_menu.py`, `tests/test_keymap.py` — in-memory rebind / conflict /
  reset only (no persistence).

**Absence for the crux:** no test asserts (a) a rebind auto-writes to disk, (b)
bindings save on exit, or (c) bindings load at boot — consistent with the code, where
the edit path (`Keymap.rebind`) has no writer, the boot path (`game.py:main` /
`app.py`) has no `load_set` call, and the sole writer is reachable only via the manual
"Save current…" UI action. These are untested because they do not exist, not because a
present behavior lacks a test.

## What a regression test would assert (only if the behavior is adopted)

The current behavior — no auto-persist — is the design as built (#439 rebind, #440
named schemes). If a future decision adds auto-persistence of the *live* bindings
(distinct from named schemes), a regression test would:

- **On-edit / on-exit auto-save:** after a `rebind` (or on the `main()` teardown),
  assert `keybindings.json` gained an entry reflecting the new binding without any
  manual "Save current…" step.
- **Auto-load at boot:** with a persisted live-binding file present, assert
  `App.__init__` (or `game.main`) seeds `P1_KEYS`/`P2_KEYS` from it rather than the
  literal defaults — the round-trip the ticket's repro describes.

Absent such a decision, no regression test is warranted: asserting the *absence* of
auto-persist would pin a non-behavior.

## Follow-ups (optional, file one-at-a-time downstream if desired)

- A `decision:`/design ticket on whether rebound controls should persist across
  restarts by default (auto-save live bindings + auto-load at boot), vs. keeping the
  explicit named-scheme model as the only persistence. This is a product/design call,
  not a bug — the code does what #439/#440 specified.

## Sources

- `pycats/core/keymap.py` — `Keymap`, `rebind`, `reset`, `KeyBindingConflict`
- `pycats/storage/keybind_store.py` — `save_set`, `load_set`, `_write`, `_read`, `_store_path`
- `pycats/screens/keybind_menu.py` — `KeybindMenu.capture_key`
- `pycats/screens/options_menu.py` — `OptionsMenu._update_keybind`
- `pycats/screens/keybind_sets_menu.py` — `KeybindSetsMenu._select_text` / `_select_list`
- `pycats/shell/app.py` — `P1_KEYS` / `P2_KEYS`, `App.__init__`, `App.save_prefs`
- `pycats/game.py` — `main()`
- `pycats/storage/settings.py` — `_config_dir`
- `pycats/storage/profile_store.py` — not imported at boot
- Tests: `tests/test_keybind_store.py`, `tests/test_options_keybind_sets.py`,
  `tests/test_keybind_sets_menu.py`, `tests/test_keybind_menu.py`, `tests/test_keymap.py`

### Related docs

- `docs/research/2026-07-02-keybinding-set-ui-scope-464.md` — the named-scheme UI scope (#464)
- `docs/research/persist-display-preferences-findings.md` — the *display*-prefs
  persistence path (the on-change persister keymaps deliberately don't use)
