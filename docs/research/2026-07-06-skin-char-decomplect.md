# Decomplect the cat identity / cosmetic / character-data model (DDD + hexagonal)

**Ticket:** #673 (Child 1 of the epic **#672**) · **Role:** RESEARCH · **Date:** 2026-07-06 (GRAPE)
**Status:** findings — feeds the #672 design/refactor children. Produced by a `/decomplect` + `/grill-me` session.
**Precursor:** the #647 seam audit ([`2026-07-06-default-test-cat-audit.md`](./2026-07-06-default-test-cat-audit.md)).

## TL;DR

- The cat **cosmetic + identity + character-data** model has accreted several *braided* concerns (Hickey "complected" = independent things you can't change/test/reason about apart). That tangle is why the "default cat / testcat / P1-vs-P2" work (#586/#646/#630/#647) kept fighting the goldens.
- **Root braid:** `char_name` on `Player` is one string doing **four** unrelated jobs — character-DATA key, display label, win-attribution identity, and team-accent selector.
- **Second braid:** cosmetics resolve **two different ways** (live `roster.palette_for` vs headless-sim `CAT_CHARACTERS`), and `palette_for(key)` overloads one string across `testcat` / archetype / OG-skin / unknown namespaces.
- **Target:** a DDD **ubiquitous language** (Skin / Character / Selection / a 3-seam Player) behind a **hexagonal** port — `build_fighter(Selection)` — that both the sim and live adapters share, with the placeholder as a *normal* non-selectable `(Character, Skin)` rather than two `if key == "testcat"` special-cases.
- **Sequencing:** three phases — (1) hexagonal refactor, golden-*neutral*; (2) migrate sims to named Selections, golden-*flipping*; (3) phase out the shim + cleanup.
- **Disposition:** this epic **subsumes** #586 / #646 / #630 / #634 into #672 (close as superseded, carry the ratified decisions forward); **#636** (the shipped `testcat` gray look) is kept as input.

---

## The root braid (why this is worth doing)

`char_name` (on `Player`) is one string doing **four** unrelated jobs, and it doubles as a fifth:

- `Player.__init__` does `self.fighter_data = fighter_data or load_fighter_data(char_name)` → **char_name is a character-DATA key** when data isn't injected. This is why `"P1"`/`"P2"` are "unknown character keys" that fall through to the default cat — the entire origin of the #630/#647 mess.
- It is also the **display label** (`render_battle.draw_player_name`, `stats_print`, `sim/presenters`), the **win-attribution** identity (`stats_print.format_stats_data` — `if winner.char_name == "P1"`), and the **team-accent selector** (`render_battle.slot_accent_color` → `P1_UI_COLOR`/`P2_UI_COLOR`).

Plus a second braid: **cosmetics resolve two different ways** — live via `roster.palette_for`, headless sim via `CAT_CHARACTERS["calico"/"tabby"]` (which *is* `OG_SKINS` re-exported, a misnomer), with `char_select` calling `load_palettes()` a third time. And `palette_for(key)` itself overloads one string across `testcat`/archetype/OG-skin/unknown namespaces.

### Braids against the decomplect catalog

| # | Braid | Concerns entangled (X ⊗ Y) | Change-cost | Unbraiding | Confidence |
|---|---|---|---|---|---|
| 1 | `char_name` is a data key **and** label **and** win-id **and** accent selector | identity ⊗ mechanics ⊗ presentation | can't rename a seat, relabel a HUD, or key data without touching the others; forces `"P1"`/`"P2"` to be "unknown cats" | split into 3 Player seams + a Selection (below) | high |
| 6 | placeholder cat = two disconnected `if key == "testcat"` special-cases (mechanics in `load_fighter_data`, cosmetics in `palette_for`) | dispatch ⊗ dispatch, in two closed places | adding/altering the placeholder edits two files that don't know about each other | make it a normal non-selectable `(Character, Skin)` | high |
| 12 | two cosmetic-resolution paths kept in sync by hand (sim `CAT_CHARACTERS` vs live `palette_for`) | cosmetics-resolution ⊗ cosmetics-resolution | a palette change must be mirrored in both or they silently drift | one `Skin` concept behind one resolver | high |
| 6/7 | `palette_for(key)` overloads one string across `testcat`/archetype/OG-skin/unknown | 4 key-namespaces ⊗ one param | a call site can't say *which kind* of key it holds; typos fall through silently | typed `Skin`/`Character` refs, not bare strings | medium |
| 14 | `ARCHETYPE_PALETTE` pre-braids archetype identity with a cosmetic palette in a derived map | identity ⊗ cosmetics | the map must be rederived whenever either side moves | derive at the seam, drop the map | medium |

All five are **incidental** (construct/tool choices), i.e. worth decomplecting — none are inherent to the domain.

---

## Ubiquitous language (ratified in the grill)

| Term | Meaning | Notes |
|---|---|---|
| **Skin** | a cosmetic value object `{name, color, stripe_color, eye_color, description}` | the OG skins are Skins; the placeholder is a Skin |
| **Character** | fighter *identity + mechanics* | a mechanics-key + display name + a default-Skin **reference**; today's "archetype" |
| **Selection** | `(Character, Skin)` | what a player commits; already half-exists as char_select's `p*_selected` + `p*_palette` |
| **Player** (Match context) | a seat, decomposed into 3 independent seams + a Selection | see below |
| **PlaceholderSkin** | the flat-gray non-selectable Skin | `_TESTCAT`, no longer special-cased |

**The `Player` identity splits into three independent seams** (today all fused in `char_name`):

| Seam | v1 default | Later (NOT built in v1) |
|---|---|---|
| **PlayerNumberSlot** | `1` / `2` | up to ~4 (2 human + 2 CPU) |
| **PlayerTeamColor** | red / blue | + green / yellow |
| **PlayerName** | `"P1"` / `"P2"` (defaults from number) | custom nicknames (post-v1); absorbs today's `nickname` #478 |

Number is primary; color and name *default from* it (composition, not braid) and stay independently overridable. HUD side is derived from number by the render adapter (not a 4th seam).

---

## Target architecture (hexagonal)

- **Domain (pure — no pygame / sim / UI):**
  - Values: `Skin`, `Character` (mechanics-key + name + default-skin ref), `Selection = (Character, Skin)`, `PlaceholderCharacter` (degenerate) + `PlaceholderSkin`.
  - **Two independent resolvers** (kept separate — skin-cycling proves mechanics and cosmetics don't depend on each other):
    - `fighter_data_of(Character) → FighterData` (today's `load_fighter_data`, un-overloaded)
    - `palette_of(Skin) → palette` (near-identity)
- **Application port (the one seam both sim & live call):**
  - `build_fighter(Selection) → (FighterData, Skin)` — composes the two resolvers. Always returns a Skin (headless runs ignore it). Replaces the two parallel constructors.
- **Adapters:**
  - Driving (produce a `Selection` + `Player` seams): `char_select`, `sim/runner`, `watch`, `bench*`, the ~8 script/repro `Player()` sites.
  - Driven (consume the built fighter): `battle_screen` / `render_battle`.
  - The `Player` seat (number/color/name) is assigned by the **Match/battle adapter**, never the domain, never `build_fighter`.

Placeholder is a **normal** `(PlaceholderCharacter, PlaceholderSkin)` that is simply **absent from the selectable rosters** — "doesn't use the regular palette" = not a member of the OG-skin cycle, *not* a render bypass. This removes the two disconnected `if key == "testcat"` special-cases.

---

## Seam map — what the refactor touches (grounded)

- **The port replaces:** `sim/runner.build_players`, `battle_screen.create_from_selection`, and normalizes the ~8 `Player()` sites in `scripts/` + `repros/`.
- **Cosmetic unification:** fold `CAT_CHARACTERS`/`OG_SKINS` + `roster.palette_for` + `ARCHETYPE_PALETTE` into the one `Skin` concept; **rename `CAT_CHARACTERS → SKINS`** (config.py re-export); drop `ARCHETYPE_PALETTE` (derived from `ARCHETYPE_DEFAULT_SKIN`) and eventually `_NEUTRAL` (placeholder handles unknowns).
- **Identity split:** `char_name` → `PlayerNumberSlot` + `PlayerTeamColor` + `PlayerName`. Consumers to repoint: `render_battle.slot_accent_color` (→ team color, not name), `render_battle.draw_player_name` (→ PlayerName), `stats_print.format_stats_data` / `format_winner_announcement` (→ win-attribution by slot, label by name), `sim/presenters` HUD lines, `sim/runner.snapshot` (records `char_name`).
- **Already-separated (keep as the migration-readiness layer):** `nickname` (#478) and the tests written to anticipate names — `test_player_nickname`, `test_render_nickname` (None-nickname byte-identical), `test_stats_console_header` (labels sourced from data). `palettes.py` / `palettes.json` (validate-on-load, presentation-only) is already clean — keep.

---

## Sequencing — three phases (load-bearing)

**Phase 1 — hexagonal refactor, golden-*neutral*.** Introduce the domain (`Skin`/`Character`/`Selection`/`build_fighter`) + the 3 Player seams, and rewire `build_players` + `create_from_selection` to go *through* the port — but keep today's *selections* (sim = calico/tabby skins + default-cat data + `"P1"`/`"P2"`; live = selected archetype+skin + `"P1"`/`"P2"`) so **every Player is byte-identical**. Do **not** change the snapshot schema. Existing goldens + `test_battle_screen_render` (inline byte-equality) are the regression proof — **no regen**.

**Phase 2 — migrate sims to named Selections, golden-*flipping*.** Point the sim/e2e Selections at real `Character`s (start with `default`/`full_match`/`two_npc`; `combat` already uses Nalio/Birky data), regenerate goldens per `tests/golden/REGEN_PROTOCOL.md` (+ the provenance interlock) with **author ≠ reviewer**, one scenario at a time. The `testcat` shim is the safety net so nothing breaks mid-migration. **Keep `PlayerName` = the stable slot (`"P1"`/`"P2"`) as the snapshot row-key**; add `Character` as a *separate* snapshot field so goldens reflect the real fighter without breaking `summarize()`'s name-keying or the `p[0] == "P2"` row filters (repoint those to the slot field). Golden change = *mechanics* (real movesets), intended and reviewable.

**Phase 3 — phase out the shim + cleanup.** Once sims name real Characters, `testcat` recedes to its end-state (only a genuine unknown/mis-key → the gray PlaceholderSkin). Land the `CAT_CHARACTERS → SKINS` rename, remove `ARCHETYPE_PALETTE`/`_NEUTRAL`, and retire stale "default cat" narration.

---

## Ticket disposition

- **Close as superseded-by-#672:** #586 (epic), #646 (umbrella), #630 (its flip becomes Phase 2, done through the port), #634 (folds into Phase 3).
- **Keep as input:** #636 (shipped `testcat` gray look — becomes the `PlaceholderSkin` value), #591 (the `testcat` name), #647 (this audit's precursor).
- **#672** = the epic; **#673** = this spike (this doc). File downstream one at a time: a **design/spec child** (formalize the model + the placeholder exact values), then **Phase-1/2/3 refactor children**.

---

## Verification (per phase, for the refactor children)

- **Phase 1:** `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q` fully green with **zero golden diff** (`git diff tests/golden/` empty); `test_battle_screen_render` byte-equality green; `ruff check` / `ruff format --check` clean on `pycats/`. Sanity-run the game.
- **Phase 2 (per scenario):** regenerate via `PYCATS_UPDATE_GOLDENS=1 SDL_VIDEODRIVER=dummy … pytest`; review the `.summary.json` sidecar diff field-by-field per `REGEN_PROTOCOL.md`; author ≠ reviewer sign-off; suite green.
- **Phase 3:** grep shows no `CAT_CHARACTERS` / `ARCHETYPE_PALETTE` / anonymous-default references; `testcat` reachable only via genuine unknowns; suite green.

---

## Open questions (for the design/spec child — not blocking this findings doc)

1. **PlaceholderSkin exact values** — "flat pure gray" may revise #636's mid-gray body + gray stripe + gray eyes toward a single uniform gray. Values detail, not model.
2. **Snapshot identity field** — confirmed direction: row-key stays the slot (`"P1"`/`"P2"`), `Character` added as a separate field in Phase 2. Confirm the exact `PlayerSnap` field addition + `summarize()` shape with the golden reviewer.
3. **`Character` naming collision** — `CAT_CHARACTERS` currently *means skins*; the rename (`→ SKINS`) is a Phase-3 hazard to sweep carefully.
