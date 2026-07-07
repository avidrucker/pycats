# Hold-to-act hint discoverability — are the holds findable *before* the hold?

**Ticket:** #549 (research · `area:screens`) · parent #544 · from the #346 audit, finding #8
**Date:** 2026-07-06 · **Agent:** DRAGONFRUIT · time-boxed ~30m
**Question:** For each screen carrying a hold-to-act affordance (hold-ESC-to-quit #113,
hold-B-to-menu #20), is a **resting hint** — text telling the player to hold, visible
*before* they start holding — present, or is the hold only findable by accident?

Audit only. Any recommended hint is a follow-up `enhancement`, **not filed here** (per the
ticket's Out-of-scope + Termination clauses).

---

## Background — what the holds are, and what's shown *during* the hold

Both affordances have grown into one generalised mechanic since they were filed:

- **hold-ESC (#113, generalised by #453):** a **2-second** ESC hold pops one level up the
  screen ladder; at `main_menu` (the top) it **quits the app**. Owned by
  `screen_manager.py :: ScreenStateManager._tick_esc_hold` / `esc_hold_complete`
  (threshold `esc_quit_hold_frames = 120`). Per-state back-guards
  (`_check_*_back` / `should_exit`) read `esc_hold_complete()`.
- **hold-B (#20):** a **1-second** B hold on **char-select** returns to the main menu
  (`screen_manager.py` `back_timer` / `back_hold_frames = 60`).

**Progress feedback during the hold exists** and is not in question:
`screen_manager.py :: ScreenStateManager.render_esc_quit_progress` →
`esc_hold.draw_esc_hold_arc` draws a circular arc as ESC is held. That is *mid-hold*
feedback — it appears only **after** the player has already discovered the hold. This
research is strictly about the **pre-hold resting hint**.

---

## Per-screen findings

### 1. `char_select` — hold-B-to-menu (#20) → **DISCOVERABLE**

A resting hint is drawn unconditionally whenever the char-select screen is shown:

> `screen_render.py :: render_active_screen` (`char_select` branch) —
> `back_text = "Hold B for 1 second to return to main menu"`

The hint names the key (B), the action (hold), the duration (1 second), and the result.
**No action needed.** (The 2s ESC-hold alternative is not separately hinted here, but it
reaches the same destination, so the *action* is discoverable via the B hint.)

### 2. `main_menu` — hold-ESC-to-quit (#113) → **hold not hinted; action covered by a menu item**

No resting hint mentions the ESC-hold. `main_menu.py :: MainMenu.render` draws only:
`"Use W/S or ↑/↓ to navigate"`, `"Press A (/ or V) to select"`, and `"F11: Toggle Fullscreen"`.

**However**, the quit *action* is fully discoverable by other means:
`main_menu.py :: MainMenu.__init__` lists `options = ["Play", "Options", "Quit"]` — a
focusable **"Quit"** button drawn by `render`. So on the main menu the ESC-hold is a
redundant/hidden shortcut, not the only way out; the discoverable path (the Quit button)
already exists. Verdict: the **hold** is not discoverable, but this is **low-value to fix**
because the visible Quit button covers the same intent.

### 3. `playing` (in-match) — hold-ESC-2s → char-select (#453) → **NOT DISCOVERABLE (hold); action covered by Pause**

The playing-state chrome carries **no resting hint** for the ESC-hold-to-leave-match:
- `render_battle.py :: draw_pause_hint` → `"P: Pause Game"` (a *different* affordance — P
  opens the pause menu).
- `render_battle.py :: draw_shell_chrome` → FPS, the debug input line, and the fullscreen
  hint (`"F11: Toggle Fullscreen | F10: … | ESC: Exit Fullscreen"`). None of these mention
  holding ESC to leave the match.

The leave-match *action* is still reachable discoverably via **P → pause menu**:
`pause_menu.py :: PauseMenu.__init__` lists `options = ["Resume", "End Match", "Return to
Character Select"]`. So a player who presses P finds the exit; a player who never presses P
has no on-screen cue that a 2s ESC-hold also leaves.

**⚠ ESC ambiguity to flag:** in fullscreen, `draw_shell_chrome` shows `"ESC: Exit Fullscreen"`
(an ESC **tap**), while an ESC **hold (2s)** leaves the match. Same key, two behaviours by
hold-duration, only one of them captioned — a discoverability *and* a mislead risk.

Verdict: the ESC-hold shortcut is **not discoverable** pre-hold. This is the strongest
candidate for a small resting-hint enhancement (see Recommendations).

### 4. `options` — the ESC-hold *is* documented, but only here and only on focus

`options_menu.py` carries a caption for the `esc_quit` toggle row:
> `"Hold ESC 2s to go back one level (or quit from the main menu)."`

This is the one place the ESC-hold mechanic is spelled out in words — but it is shown only
when the player **focuses that specific Options row**, i.e. it documents the feature rather
than surfacing it on the screens where a player would actually reach for it. Options also
offers `"A to toggle, B to go back"` (tap-B navigation, distinct from the char-select
hold-B). Not a hold-to-act screen itself; recorded here as the existing source of truth for
the ESC-hold wording (useful if a hint is later authored).

---

## Summary

| Screen | Hold affordance | Pre-hold resting hint? | Citation | Verdict |
|---|---|---|---|---|
| `char_select` | hold-B 1s → menu (#20) | **Yes** | `screen_render.py :: render_active_screen` (`char_select`) | Discoverable — no action |
| `main_menu` | hold-ESC 2s → quit (#113) | No (but "Quit" button exists) | `main_menu.py :: MainMenu.render` / `__init__` | Hold hidden; action covered by Quit button — low priority |
| `playing` | hold-ESC 2s → char-select (#453) | **No** | `render_battle.py :: draw_shell_chrome` / `draw_pause_hint`; `pause_menu.py :: PauseMenu.__init__` | Not discoverable; action covered by P→pause — **best hint candidate** |
| `options` | (documents ESC-hold) | Caption on focus only | `options_menu.py` `esc_quit` row caption | Feature documented, but buried in Options |

**One-line answer:** hold-**B** on char-select is discoverable (explicit resting hint);
hold-**ESC** is **not** discoverable on any screen where you'd use it — it's only progress-
drawn mid-hold and word-documented inside an Options row. On every screen the underlying
*action* (quit / leave match / back to menu) has a discoverable alternative (Quit button,
Pause menu, hold-B hint), so no player is *stranded* — but the ESC-hold shortcut itself is
effectively an undocumented power-user gesture.

---

## Recommendations (proposed follow-ups — NOT filed, per ticket scope)

1. **`enhancement` (highest value):** add a resting hint on **`playing`** for the ESC-hold
   leave-match shortcut, and disambiguate it from `ESC: Exit Fullscreen` (e.g.
   `"Hold ESC to leave match"` vs the tap-to-exit-fullscreen caption). Draw site:
   `render_battle.py :: draw_shell_chrome`.
2. **`enhancement` (optional, low priority):** a small `"Hold ESC to quit"` hint on
   `main_menu` — redundant with the visible Quit button, so cosmetic only.
3. **No change** for `char_select` (already hinted) or `options` (documentation only).

## Open questions

- Is the ESC-hold *meant* to be a discoverable feature or a deliberate hidden safety gesture
  (hold-to-confirm to avoid accidental match-exit)? If intentional-hidden, item 1 becomes a
  design call rather than a plain hint add — a `decision:` may precede the `enhancement`.
- The `controls` Options toggle ("Show the on-screen control hints during battle") gates the
  battle HUD hints; whether a new ESC-hold hint should sit under that same toggle is a design
  detail for the follow-up, not resolved here.
