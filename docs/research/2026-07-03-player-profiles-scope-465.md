# Spike #465 — scope player profiles (#441): schema + text-entry + select-UI + render seam

**Agent:** ELDERBERRY · **Date:** 2026-07-03 · **Parent:** #441 · Epic #438. **Scope-only — no production code.**

## Current state
- Fighters are labelled by `draw_player_name` (`render_battle.py:218-231`), which draws `p.char_name` and **picks its colour from `char_name == "P1"`**.
- `char_name` is **identity, not just display** — `battle_screen.py:65`: *"char_name stays 'P1'/'P2' so win-attribution [works]"*. `BattleScreen` builds players with `char_name="P1"/"P2"` (`battle_screen.py:73,79`).
- Character selection lives in `CharacterSelector` (`char_select.py`): `p1_selected`/`p2_selected`, `both_confirmed()` → start handoff. Cooldown-gated `update(held_keys, pressed_keys)`.
- Persistence precedents: `keybind_store` (#440) under `profiles/keybindings.json`; `settings.py` (#95) JSON + `PYCATS_CONFIG_DIR`.
- Shared text-entry widget: **#471** (`TextEntry(maxlen)`), scoped by #464.

## Gap (what #441 asks for)
A player profile = a **nickname** (≤4 chars) shown above the fighter (instead of "P1"/"P2") + an **associated keybinding set**, persisted under `profiles/`, selectable per player.

## Decisions (locked)

### 1. Schema
`profiles/profiles.json` (one file, mirrors #440's `keybindings.json`, same `profiles/` dir):
```json
{ "<NICK>": { "keybinding_set": "<set name or null>", "stats": { } } }
```
- **Nickname is the identity** (≤4 uppercase chars; the dict key).
- **Keybindings are referenced by name, not inlined** — a profile points at a saved set in #440's `keybindings.json`. One keybinding store, no duplication; a missing/deleted reference → factory defaults (`keybind_store.load_set` already falls back per-action).
- **`stats` is reserved now** (an empty object) so #442 (post-v1) extends the schema without reworking it.

### 2. Text entry — reuse #471, do NOT build a second one
Nickname entry is `TextEntry(maxlen=4)` (#471), uppercase A–Z (its default grid). #471 owns the widget; #441 just hosts it with `maxlen=4`.

### 3. Select-UI placement + flow
Host in **`CharacterSelector`** (`char_select.py`) — the player already picks a character there; picking/creating a profile alongside it is natural and reuses its cooldown-gated nav + start handoff.
- **Create:** a "New profile" action → `TextEntry(4)` for the nickname → optionally pick a saved keybinding set (`keybind_store.list_sets()`) → `profile_store.save`.
- **Select:** a per-player profile list (from `profile_store.list()`), navigated like the character grid; the chosen profile binds to that player's slot.
- **On start (`both_confirmed`):** apply each selected profile — set the player's nickname + `keybind_store.load_set(profile.keybinding_set, keymap)` onto that player's `Keymap`.

### 4. Above-fighter render seam (golden-safe)
- Add a **separate `Player.nickname`** field (default `None`) — do **not** overwrite `char_name` (breaks win-attribution + the colour test).
- `draw_player_name` shows `p.nickname or p.char_name`, and **colours by player slot** (P1 vs P2), not by `char_name` string. Nickname `None` → renders "P1"/"P2" in the same colour as today → byte-identical default, and the sim/golden path never renders. Live-only.

## Key code sites
- `pycats/render_battle.py:218-231` — `draw_player_name` (nickname field + slot-colour fix).
- `pycats/entities/player.py` — add `Player.nickname`.
- `pycats/char_select.py` — profile create/select UI (host #471; list from `profile_store`).
- `pycats/battle_screen.py:65-79` — where selected identity + keymaps flow into the players (apply profile on start).
- `pycats/profile_store.py` — **new**: profiles persistence (mirror `keybind_store` #440).
- `pycats/keybind_store.py` (#440) — the referenced keybinding sets.

## Open questions (minor, decide at implementation)
- Does the profile-select list live per-player next to each character cursor, or a shared list picked into a slot? (Recommend per-player, mirroring the P1/P2 cursors.)
- Colour for a nicknamed P1/P2 — keep the existing `P1_UI_COLOR`/`P2_UI_COLOR` by slot (recommended), so a nickname doesn't change the team colour.

## Perceived ROI
**High** — unblocks the profiles line (#441 → #442) and gives the game player identity. The schema's reserved `stats` key means #442 lands without a migration.

## Recommendation — decompose #441 into 2 DEV slices
- [x] **Decompose.**
  1. **Profile data + render seam (DEV):** `profile_store.py` (save/load/list/delete `{nickname: {keybinding_set, stats}}`, TDD'd like #440) + `Player.nickname` + `draw_player_name` (nickname-or-`char_name`, slot-colour). No profile-creation UI yet; render verified by screenshot; golden-safe. **Not blocked.**
  2. **Profile create/select UI (DEV):** in `CharacterSelector` — create (nickname via #471 + pick a keybinding set) + per-player select; on start apply the profile (nickname + `load_set` onto the keymap). **Blocked by #471** (text entry) + slice 1.
