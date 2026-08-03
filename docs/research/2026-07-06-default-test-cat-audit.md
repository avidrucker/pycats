# Default / test-cat usage audit — where it's used, and where it should be a named cat

**Ticket:** #647 (Child A of the disambiguation umbrella **#646**) · **Role:** RESEARCH · **Date:** 2026-07-06 (GRAPE)
**Status:** findings — feeds the #646 umbrella; gates #630.

## TL;DR

- The "default test cat" is **not one thing**. Three *independent* seams resolve a fighter, and they treat `"P1"`/`"P2"` and `"testcat"` differently:
  1. **Mechanics** — `load_fighter_data(key)` (`combat/data.py`): unknown/empty → the minimal `DEFAULT_FIGHTER_DATA`.
  2. **Cosmetics** — `palette_for(key)` (`characters/roster.py`): `"testcat"` → a distinct gray placeholder (#636); any *other* unknown key → `_NEUTRAL` light-gray.
  3. **Identity** — `char_name` (`"P1"`/`"P2"`): the win-attribution / HUD label; **stays fixed** regardless of data or palette.
- The minimal fixture as a **mechanics default** lives in essentially **one real place**: `build_players` / `run_battle` (`sim/runner.py`) — the sim + golden path — plus `watch.py`'s no-char default. The **live game already runs named cats** (char-select → `battle_screen.create_from_selection`), and the **demos are already named** (`nalio` vs `birky`).
- **#636 already shipped** the `testcat` gray placeholder look and locked the name to `testcat` — so the earlier "name it UNKNOWN/UNNAMED?" question is **moot**: the codebase chose `testcat` + an opaque mid-gray, gray-eyed placeholder.
- **#630 ruling (revise, don't drop):** confirm Nalio for the *sim/match default*, but **split off the genuine unknown-key fallback** → route it to the visible `testcat` placeholder, not silently to Nalio. See [The #630 ruling](#the-630-ruling).

Counts: **~7 non-test sites** (2 are the real mechanics-default), **~70 test files** across 6 buckets (only ~4 golden + ~20 generic-P1/P2 tests are actually touched by the flip).

---

## Background — the three seams

A fighter's on-screen presence is assembled from three keys that are resolved separately; conflating them is the root confusion this umbrella exists to fix.

| Seam | Resolver | `"P1"`/`"P2"` today | `"testcat"` today | Unknown key today |
|---|---|---|---|---|
| **Mechanics** (moves/hurtbox) | `load_fighter_data` (`combat/data.py`) | `DEFAULT_FIGHTER_DATA` (minimal 1-move) | `DEFAULT_FIGHTER_DATA` (same object, #591) | `DEFAULT_FIGHTER_DATA` |
| **Cosmetics** (body/stripe/eye) | `palette_for` (`roster.py`); sim uses `CAT_CHARACTERS` skins | sim: `calico`/`tabby` skins · live: `_NEUTRAL` | `_TESTCAT` gray (128/96/64, gray eyes) — #636 | `_NEUTRAL` light-gray (200, black eyes) |
| **Identity** (label) | `char_name` | `"P1"`/`"P2"` | `"testcat"` | as passed |

**Consequence for #630:** it edits *only* the mechanics seam. So "unknown → Nalio" would give an unknown key **Nalio mechanics + `_NEUTRAL` light-gray cosmetics** — an incoherent hybrid that looks like a generic gray blob but hits like Nalio. That's the crux of the ruling below.

---

## Per-site table — non-test

| Site (landmark) | What it is | Classification | Notes |
|---|---|---|---|
| `sim/runner.py` → `build_players` / `run_battle` (`p1_char`/`p2_char=None`) | The sim + **golden** default fighters | **SWAP → Nalio** (as the explicit match default) | THE golden source (`tests/golden/default.json` etc.). Colors come from `CAT_CHARACTERS["calico"]/["tabby"]`, not `palette_for`; `char_name` stays `"P1"`/`"P2"`. Regenerates under #630. Prefer an **explicit** `p1_char="nalio"` default over leaning on the fallback (see ruling). |
| `entities/player.py` → `self.fighter_data = fighter_data or load_fighter_data(char_name)` | The **resolution seam** (mechanism, not a "use") | mechanism | This is where `char_name="P1"` becomes the default cat. #630 changes `load_fighter_data`'s fallback, not this line. |
| `battle_screen.py` → `create_from_selection(p1_char, p2_char)` | Live match after char-select | **already NAMED** | Char-select forces an `ARCHETYPE_ROSTER` pick, so live play never uses the fixture — *unless* handed an unknown key (defensive). Passes `palette_for(key)` into Player. |
| `watch.py` → `--p1-char` / `--p2-char` default `None` | Dev CLI default | **SWAP → Nalio** (align with `run_battle`) | `watch.py` with no char args runs fixture-vs-fixture. Should track whatever the sim default becomes. Low stakes (dev tool). |
| `sim/demo.py` → `DEMOS` (`Demo.p1_char`/`p2_char`) | In-game / CLI demos | **already NAMED** | The registered demo names `p1_char="nalio"`, `p2_char="birky"`. `p1_char`/`p2_char` default `None`, so a *future* demo that omits them would fall to the default — cheap guard: default demos to a named cat. |
| `bench.py` / `bench_render.py` → `build_players("statechart")` | Perf benchmark | **KEEP** (or SWAP; low stakes) | A benchmark wants a stable, representative fighter; the fixture or Nalio both work. No golden, no user-facing surface. |
| `characters/roster.py` → `palette_for` (`_TESTCAT` / `_NEUTRAL`) | Cosmetics seam | **KEEP — done (#636)** | `"testcat"` → distinct gray placeholder; other unknown → `_NEUTRAL`. Separate axis from mechanics. |

## Per-site table — tests (~70 files, bucketed)

| Bucket | ~n | Representatives | Classification / effect of the flip |
|---|---|---|---|
| **Named-cat data tests** | ~30 | `test_nalio_*`, `test_birky_*`, `test_narz_*`, `test_fsmash_angle`, `test_smash_charge*`, `test_move_select`, `test_reach_aware` | Load named cats — **unaffected** by the flip. Their `DEFAULT_FIGHTER_DATA`/`"P1"` golden-safety pins were migrated to `"testcat"` in #591. |
| **Minimal-kit assertion tests** | ~8 | `test_combat_data`, `test_up_b_recovery`, the #591-migrated smash-golden-safety pins | **KEEP → load `"testcat"` by name** (mostly done in #591). These *want* the 1-move kit; they must not follow the flip to Nalio. |
| **Golden tests** | 4 | `test_golden`, `test_golden_summary`, `test_full_match`, `test_battle_screen_render` | **Regenerate under #630.** `tests/golden/default.json` is the fixture-vs-fixture golden that becomes Nalio-vs-Nalio. |
| **Generic P1/P2 mechanics tests** | ~20 | `test_player_move`/`push`/`seam`, `test_crouch`, `test_prone`, `test_dash`, `test_hitlag`, `test_shieldstun`, `test_shield_break_stun`, `test_respawn_*`, `test_jump_over_flush_adjacent`, `test_stun_no_drop_through`, `test_ground_air_split`, `test_thick_platform_*` | **The #630/child-2 fix surface.** After `"P1"`/`"P2"` → Nalio, re-run: kit-agnostic movement/shield/platform tests pass unchanged; any that assert the *default jab* (dmg 10 / angle 0) or "only `attack` exists" via `"P1"`/`"P2"` must migrate to `"testcat"`. Child 2 fixes exactly what breaks; child 3 sweeps the rest. |
| **Identity / label tests** | ~10 | `test_player_nickname`, `test_render_nickname`, `test_name_label_clears_ears`, `test_win_screen_*`, `test_stats_console_header`, `test_battle_log`, `test_watch_log`, `test_dev_log` | **Unaffected** — assert `char_name`/nickname as a *label*, not fighter data. |
| **Cosmetic / roster tests** | ~3 | `test_testcat_placeholder_palette` (#636), `test_sprite_tint_consolidated`, `test_archetype_selectability` | **KEEP — done.** Pin the placeholder look / roster; independent of the mechanics flip. |

*(Bucket membership is by name + known role; the "generic P1/P2" bucket is where per-file classification actually matters, and it is precisely the child-2/3 work — this audit maps it, it doesn't pre-resolve every file.)*

---

## The #630 ruling

**Confirm the swap, but revise its scope: split "the match default" from "the unknown-key fallback."**

The current #630 spec — *"`load_fighter_data` returns Nalio for any unknown/empty key"* — conflates two cases the audit shows are different:

1. **The explicit sim/match default** (`build_players` with no char). A real match should run a real cat → **Nalio**. ✔ Keep this. Implement it as an **explicit** default (`p1_char = p1_char or "nalio"`) rather than by deleting the fallback, so the intent is legible at the call site and the goldens regenerate for a clear reason.

2. **A genuine unknown / mis-keyed character** (`load_fighter_data("Nailo")`, a typo). Under #630-as-written this **silently becomes Nalio** — and, because cosmetics resolve separately, renders as the `_NEUTRAL` light-gray blob. That hides load failures. The umbrella's whole motivation (and the user's original instinct — "color the unknown cat so there's no confusion") points the other way: **route the unknown-key fallback to `"testcat"`** so a mis-key is *visibly* the gray, gray-eyed placeholder (#636), coherent in both mechanics and cosmetics.

So the revised loader contract:

| Key | Mechanics (`load_fighter_data`) | Rationale |
|---|---|---|
| `"nalio"`/`"birky"`/`"narz"` | that archetype | unchanged |
| `"testcat"` | minimal fixture | unchanged (#591) |
| **empty / explicit default** (sim/match) | **Nalio** | a real match runs a real cat |
| **unknown / unrecognized** (typo, bad key) | **`testcat` placeholder** (visible gray) | catch mis-keys instead of masquerading as Nalio |

This keeps #630's golden regeneration (the sim default flips minimal → Nalio) while turning the fallback into a debugging asset rather than a silent coercion. **#630 should be rescoped to this contract** before it resumes; #634 (constant rename + narration sweep) is unaffected in spirit.

> If the game-designer prefers the simpler *"unknown → Nalio, full stop"* (accepting silent coercion of mis-keys), that's a legitimate call — but it should be made knowingly, given the cosmetics-incoherence and lost-debugging-signal above. Flagging for the human; not deciding it here.

---

## Recommended sequencing (downstream of this doc — NOT filed here)

1. **Rescope + resume #630** to the split contract above (explicit default → Nalio; unknown → `testcat`), regenerating `tests/golden/default.json` et al. with an author≠reviewer digest.
2. **#634** — rename `DEFAULT_FIGHTER_DATA` → a `testcat`-aligned name; sweep stale "default cat = sim path" narration.
3. **Small guards** (optional, low priority): default `watch.py` and any char-less `Demo` to a named cat so no *new* fixture-as-default sites appear.

The appearance work (**#636**) and the naming (**`testcat`**) are **already done** — no downstream slice needed for either.

## Refs

Umbrella **#646**; #586 + #591 (testcat name) / #630 (the flip — to be rescoped) / #634 (sweep); **#636** (the shipped `testcat` gray placeholder). Code: `load_fighter_data` + `DEFAULT_FIGHTER_DATA` fallback (`combat/data.py`); `build_players`/`run_battle` (`sim/runner.py`); `create_from_selection` (`battle_screen.py`); `palette_for` + `_TESTCAT`/`_NEUTRAL` (`characters/roster.py`); `fighter_data or load_fighter_data(char_name)` (`entities/player.py`); `DEMOS` (`sim/demo.py`); `tests/golden/default.json`.
