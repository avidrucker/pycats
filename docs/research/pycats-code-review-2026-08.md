# pycats — external code review (2026-08-01)

**Scope:** whole repo at `71bfbc9` (2026-07-31). Read-only. Static analysis + structural read.

**Frame:** you asked for organization / modularity / hexagonal / DDD, plus *other lenses*, with the goal of a lean codebase that is easy to accrete onto.

Prior work read first so this doesn't repeat it: `docs/research/architecture-review-2026-06b.md` (#252) and its predecessor (#56). The DDD/Hexagonal follow-ups from that pass (H-a Tail inversion, H-b rendering port, D1–D4) are **confirmed executed** — `Tail`, `Attack`, `Platform` no longer own Surfaces, and no `entities/` module imports the render layer anymore. This review therefore looks at what those two passes *didn't* cover.

---

## Headline

**The code is not messy. The topology is.**

| Measure | Value | Read |
|---|---|---|
| Logical lines of code (LLOC) | **7,339** | Small. A weekend-readable game. |
| Source lines (SLOC) | 10,939 | |
| Comment lines | 3,108 (26% of code) | High, but mostly good "why" |
| Issue-number references in source | **1,665** | ← see Finding 3 |
| Dead code (vulture ≥80%) | **0** | Clean |
| Test modules / test LOC | 258 / 28,803 | 2.6× the source |
| Doc files / words | 264 / **371,670** | ≈1,240 printed pages |
| Repo bytes: docs vs code | 3.2 MB vs 1.2 MB | Docs are 2.7× the code |
| Modules at package root | **31 of 105** | ← see Finding 1 |
| Import cycles | 6 | ← see Finding 5 |

Your instinct that it's "getting bigger and messier" is right, but the growth is **not in the logic** — 7.3k LLOC is genuinely lean for a fighting game with four archetypes, a statechart FSM, AI controllers, and a full menu stack. The growth is in **surface area you have to navigate before you can touch the logic**: 31 flat root modules, five packages that all mean "the model," 264 docs, and 1,665 ticket references embedded in the source.

The fix is mostly *moving and naming*, not rewriting. Below, roughly in leverage order.

---

## Finding 1 — The package root is a junk drawer (31 modules, ~4,400 lines)

`pycats/` has ten well-named sub-packages and then **31 loose modules at the root**, which import each other 46 times. Every new screen, menu, store, or shell object has landed there because there was no obvious folder — the classic accretion sink.

They cluster cleanly into four groups that already exist implicitly:

| Proposed home | Modules | ~lines |
|---|---|---|
| `pycats/screens/` | `char_select`, `options_menu`, `win_screen`, `main_menu`, `pause_menu`, `keybind_menu`, `keybind_sets_menu`, `battle_screen`, `screen_manager`, `screen_render`, `text_entry` | ~2,900 |
| `pycats/ui/` (reusable widgets) | `menu_widgets`, `menu_controller`, `menu_layout`, `esc_hold`, `text_utils`, `cat_faces`, `stats_print`, `input_history` | ~1,300 |
| `pycats/shell/` (the driving adapter) | `app`, `game`, `display`, `display_manager`, `input_poll`, `runtime_settings` | ~700 |
| `pycats/storage/` | `settings`, `keybind_store`, `profile_store`, `dev_log` | ~350 |
| delete | `render_battle` (shim) | 45 |

**Why this is the top item:** it's the single change with the best ratio of "reduces cognitive load" to "risk of breaking behavior." It is pure `git mv` + import rewrite, mechanically verifiable by a green suite, and it immediately makes the *next* 30 modules have obvious homes. It also fixes a real dependency smell for free: `render/hud.py` currently does `from ..input_history import _GLYPHS, INPUT_HISTORY_FRAMES, PRESSED` — a render module reaching across the root for a private name. Once `input_history` lives in `ui/`, that read is "render uses a UI primitive," which is fine.

Do it in slices (screens first — biggest, most self-contained), one PR each, `git mv` so blame survives. Add each moved path to `.git-blame-ignore-revs`, which you already have wired up.

**Delete `render_battle.py`.** It is a pure `from pycats.render import *` shim from #900. Shims are accretion debt with a half-life: every month it survives, more new code imports the old path. Grep, rewrite the ~15 call sites, delete. Same question for the four dead archetype arms in `combat/data.py::load_fighter_data` — your own comment says they're unreachable and kept only as drift-guard oracles. If they're oracles, they belong in `tests/` or `combat/provenance.py`, not in a live dispatch function where a reader has to work out they're dead.

---

## Finding 2 — Five packages all mean "the model" (sliced by kind, not by subdomain)

This is the DDD finding the previous reviews didn't surface, because they scored the *model quality* rather than the *package boundaries*.

Where does a mechanic live? Right now you have to guess among:

- `domain/` — skin, character, selection, registry, resolvers, placeholder, player_identity
- `entities/` — fighter, player, attack, tail, ledge, platform, stages
- `combat/` — data, knockback, shield, collapse, charge, geometry, move_clock, tangibility
- `systems/` — combat, movement, match_engine, win_condition, status_model, state_engine
- `core/` — physics, input, keymap

Those are **layers-by-technical-kind** (entities / services / value objects / infrastructure), which is exactly the packaging DDD warns against — it maximizes the number of packages a single behavior change has to touch. Adding one mechanic (say, grabs) means touching `combat/`, `systems/`, `entities/`, `charts/`, and `render/`.

Two specific naming problems make it worse:

1. **`domain/` doesn't hold the domain.** Every file in it is about roster / skin / selection. Meanwhile `entities/fighter.py`'s own docstring calls `Fighter` "the domain aggregate." A newcomer reading `CONTEXT.md` and then `ls pycats/domain/` gets a wrong mental model in under a minute. Rename it to what it is: **`roster/`** (or `casting/`).
2. **`systems/combat.py` and `combat/` are different things.** `systems/combat.py::process_hits` is the per-frame hit-resolution service; `combat/` is the rules and value objects. Two modules named "combat" in different packages, both about combat, is a coin-flip every time you reach for one.

**The lens to apply here is vertical slicing / bounded contexts.** Group by *what changes together*:

```
pycats/
  fighting/     hit resolution, knockback, hitstun, shield, clank, tangibility, move_clock
  movement/     physics, platforms, ledges, stages, takeoff/landing
  roster/       characters, skins, palettes, selection, registry   (today's domain/ + characters/)
  match/        stocks, win condition, blast zones, match_engine
  fighter/      Fighter aggregate, statechart, FighterInput, timers
  present/      render/, screens/, ui/, shell/
```

I'd treat this as a **direction, not a task**. It's a bigger, riskier move than Finding 1 and it's not urgent — the model quality is already good (the 8.5/10 in the June review is fair). But when a package next needs to split, split it toward this shape rather than adding a sixth kind-based package. And do the two renames now: they're cheap and they remove the two worst wrong-turns.

---

## Finding 3 — The source is carrying its own changelog

**1,665 issue references (`#NNN`) live in the source comments** — about one per seven lines of code. `sim/controllers.py` has 185 of them across 666 code lines; `entities/fighter.py` has 134.

Sample, from `entities/fighter_input.py::handle_actions`:

> A fresh Up + A resolves the ATTACK, not a jump (#878 / #865 Option D): let the frame fall through to the Attack/Special seam below, where up + A becomes the up-tilt (grounded) / up-air (airborne). One guard fixes both the grounded and airborne cases because this branch is not `on_ground`-gated. Bare Up (no A) still jumps / double-jumps. Scope is A (`attack`) only — Up + B (`wants_up_special`) is unchanged. Shield is excluded so the frame keeps jumping out of shield…

That is a well-written **PR description**. It explains a *change* — what used to happen, what now happens, what was considered and rejected, what the scope boundary was. It is genuinely valuable. It is also the single largest contributor to "the codebase feels big," because a reader who wants to know *what the code does today* has to parse a paragraph of *how it got here*.

This is the direct cost of an agent-driven workflow: every ticket leaves a sediment layer, and nothing ever removes one. Under `RULES.md`'s own "work tracking is GitHub issues, not markdown TODO files" principle, this is the same violation in a different file type — narrative work-history stored in the source. (Relatedly: **46 `TODO`/`FIXME`/`DONE` markers remain in the source**, 18 of them in `entities/player.py`, including a `#### DONE:` block in `handle_actions`. Those should be issues or deleted.)

**Suggested rule — "present tense in code, past tense in git":**

- A comment may state *what is true now* and *why this constraint exists*.
- A comment may carry **one** issue ref, as a pointer to the rationale.
- A comment may not narrate what the behavior used to be, what alternatives were rejected, or what slice of what epic it came from. That goes in the commit body and the ticket, where `git log -S` and `git blame` will find it.

Rough target: get `sim/controllers.py` from 363 comment lines to ~120. You will not lose the knowledge — it's already in the tickets and the commits. What you gain is a file you can read in one sitting.

A cheap way to make this land: add a line to `CLAUDE.md` under the banned-words rule, and check comment density in review. It's the highest-yield doc edit available to you, because it changes what *every future agent* produces rather than fixing what past ones wrote.

---

## Finding 4 — Adding a character is shotgun surgery across parallel registries

The accretion test you actually care about: **what does it cost to add the fifth cat?** Today, seven source files, four of which are registration lists that must be edited in lockstep:

- `characters/<name>_cat.py` + `characters/data/<name>.json` — the real content
- `characters/roster.py` — **four parallel structures keyed on the same string**: `ARCHETYPE_ROSTER`, `ARCHETYPE_DEFAULT_SKIN`, `ARCHETYPE_EXTRA_SKINS`, `ARCHETYPE_NAME`
- `characters/palettes.json`
- `combat/data.py` — the `if character == "..."` dispatch chain (which, per its own comment, is dead)
- `config/menu.py`

Four dicts keyed by the same key is a **connascence-of-position** problem: nothing stops you adding a cat to three of the four, and the failure shows up as a missing name in the menu, not as an error.

**Fix:** one record per archetype, one tuple of records.

```python
@dataclass(frozen=True)
class Archetype:
    key: str
    display_name: str
    default_skin: str
    extra_skins: tuple[str, ...]

ARCHETYPES = (Nalio, Birky, Narz, Gnok)
```

Derive `ARCHETYPE_ROSTER`, `ARCHETYPE_NAME`, etc. as comprehensions over it so existing call sites keep working during the transition. Then adding a cat is: one JSON file, one palette entry, one line in `ARCHETYPES` — three edits instead of seven, and the type system catches an incomplete one.

Worth adding a guard test in the same commit: `test_every_archetype_has_a_palette_and_json` iterating `ARCHETYPES`. That converts the invariant from "remember to" into "the suite fails."

---

## Finding 5 — Complexity is concentrated in four priority ladders

`radon cc` on the source (only functions rated C or worse shown; full list in the appendix):

| Function | Complexity |
|---|---|
| `entities/fighter_input.py::FighterInput.handle_actions` | **F (71)** |
| `sim/controllers.py::AttackerController._decide_engage` | **F (70)** |
| `charts/fighter_chart.py::build_fighter_chart` | **F (61)** |
| `sim/controllers.py::AttackerController._decide_combat` | **F (44)** |
| `char_select.py::CharacterSelector.update` | **E (40)** |
| `entities/fighter_physics.py::step_physics` | D (27) |
| `systems/combat.py::process_hits` | D (25) |
| `sim/runner.py::run_battle` | D (25) |
| `entities/tail.py::Tail.update` | D (23) |
| `options_menu.py::OptionsMenu._row_label` | D (21) |

`sim/controllers.py` is the worst file in the repo by maintainability index (B/13.35 — everything else is A). `AttackerController` is a 630-line class whose whole behavior is a cascade: `decide` → `_decide_recovery` → `_decide_combat` → `_decide_engage` → `_apply_anti_stall`.

**The top three all have the same shape, and one refactor fixes all of them: the priority ladder is encoded in statement order and early returns rather than in data.**

`handle_actions` is: smash-charge wins → then double-tap dash → then jump → then dodge → then shield → then attack → then special. That ordering *is* the design. It's the thing you tune, the thing that breaks, and the thing a new contributor most needs to see. Right now it is only visible by reading 250 lines top to bottom and tracking which branches `return`.

Make it a list:

```python
# Highest priority first. Each rule returns an Intent or None.
ACTION_RULES = (
    resolve_smash_charge,   # rooted; consumes the frame
    resolve_double_tap_dash,# never consumes the frame
    resolve_up_special,
    resolve_jump,
    resolve_dodge,
    resolve_shield,
    resolve_attack,
)

def handle_actions(self, frame, attack_group):
    for rule in ACTION_RULES:
        intent = rule(self._p, frame)
        if intent is not None:
            return intent.apply(self._p, attack_group)
    return NO_ACTION
```

What you get:
- Each rule is a small pure-ish function, unit-testable in isolation without constructing a frame that reaches the right branch of a 250-line function.
- The priority order becomes a **seven-line diff** in code review instead of an inference.
- Adding a mechanic is inserting one line at the right position — the accretion property you asked for.
- The Up+A-beats-jump paragraph from Finding 3 collapses to `resolve_attack` sitting above `resolve_jump`, plus a test named `test_up_plus_a_produces_up_tilt_not_jump`.

Same treatment for `AttackerController`: the cascade becomes an ordered tuple of behaviors (`recover`, `edge_hog`, `punish_whiff`, `engage`, `anti_stall`), each a small class or function with a `decide()`. That is a behavior tree, which is the standard shape for game AI precisely because it makes the priority visible and each node testable. It also makes difficulty levels composable — a level is a subset/reordering of the tuple, rather than more branches inside `_decide_engage`.

`build_fighter_chart` at F(61) is a different case: it's a builder producing a declarative artifact, so high branch count is less alarming. Still worth splitting per state-group (`_ground_states`, `_air_states`, `_hitstun_states`) so a change to ledge handling doesn't require scrolling a 300-line function.

---

## Finding 6 — Import cycles (6), all avoidable

```
combat.data  ->  characters.birky_cat  ->  combat.data
combat.data  ->  characters.gnok_cat   ->  combat.data
combat.data  ->  characters.narz_cat   ->  combat.data
combat.data  ->  characters.nalio_cat  ->  combat.data
combat.data  ->  characters.gnok_cat   ->  characters.default_cat -> combat.data
sim.demo     ->  sim.showcase          ->  sim.demo
```

Five of the six are the same one: `combat/data.py` imports each character module (inside the dispatch function, to break the cycle at import time) while each character module imports `combat/data.py` for its value types. The function-local imports are a workaround for a dependency that points the wrong way — data definitions should depend on the value types, never the reverse.

**This dissolves for free with Finding 1's fix to `load_fighter_data`.** Once the dead archetype arms are deleted, `combat/data.py` only needs the JSON loader and the roster keys, and the cycle is gone. The remaining `sim.demo ↔ sim.showcase` cycle is a genuine bidirectional dependency — one of them should own the shared piece, or it should move to a third module.

The layer matrix is otherwise healthy. Nothing in `entities/`, `combat/`, `characters/`, or `core/` imports the render layer anymore — the June H2 inversion is genuinely fixed. The one boundary blur left is that `sim/` mixes a pure core (`controllers`, `runner`, `input_script`) with adapters (`presenters` imports `render_battle` and `imageio`; `demo`, `showcase`). Worth a `sim/pure/` vs `sim/present/` split, or moving the presenters to `present/`, so `CONTEXT.md`'s determinism contract can name a whole package rather than individual modules.

---

## Finding 7 — Still no CI, and the reason no longer holds

`.pre-commit-config.yaml` says it plainly: *"Enforcement model is pre-commit + on-demand, NOT a CI gate (there is no CI)."* There is no `.github/` directory.

I raised this in a prior review and it's still open, so let me put the case differently. Pre-commit is a **local, opt-in, per-clone** gate (`.venv/bin/pre-commit install` — one-time, per clone, easy to skip). You are running a **fleet** of agents (`.claude/orchestrate.json`) on worktrees, merging to `main` via `pmtools close`. That is precisely the setup where "everyone remembered to run the suite" is not a control. The repo is at issue #969; the odds that every one of those merges ran a green suite locally are not 100%, and nothing in the repo can tell you which ones didn't.

Minimum viable: one `.github/workflows/ci.yml` running `ruff check` + `ruff format --check` + `SDL_VIDEODRIVER=dummy pytest -q` on push and PR, plus a branch protection rule on `main`. This is ~25 lines and it converts your excellent suite from a convention into a guarantee. It also gives you a place to hang the two guard tests worth automating: the banned-words check (currently enforced by prose in `CLAUDE.md` and human attention) and a lightweight import-layering assertion.

**Related idea — architecture fitness functions.** You already have guard #339 for the pygame boundary. Generalize it: a single test that parses the import graph and asserts the allowed edges.

```python
FORBIDDEN = {("entities", "render"), ("combat", "render"), ("combat", "characters"), ...}
def test_no_forbidden_layer_imports():
    assert violations(import_graph("pycats")) == set()
```

Roughly 40 lines. It makes every rule in `CONTEXT.md` § "Determinism / headless contract" executable instead of aspirational, and it means the layering can't regress silently between architecture reviews. Given that reviews #56 and #252 both had to *re-derive* the layer map by hand, this pays for itself the first time.

---

## Finding 8 — The doc corpus has outgrown its index

371,670 words across 264 files. `docs/research/` alone is 121 files; `docs/learnings/` is 58 "today-i-learned-<date>-<fruit>.md" files.

The `docs/mechanics-index.md` router and `CLAUDE.md`'s "Start here" are the right instinct, and `CONTEXT.md` is a genuinely good orientation doc — short, stable, linked-not-duplicated. But at this volume there are two costs:

1. **Retrieval cost.** Neither a human nor an agent can hold 264 docs in view. Anything not reachable from the router in two hops is effectively write-only.
2. **Drift.** `CONTEXT.md` still describes `statecharts/` as a package (it's `charts/`), and the June review flagged the "`systems/` imports no pygame" wording as inaccurate — still unfixed (`systems/movement.py` imports pygame for `Vector2`). Small, but it's the doc newcomers read first.

Suggestions, in order of yield:

- **Give `docs/learnings/` a lifecycle.** 58 dated TIL files is a journal, not a knowledge base. Either fold the durable lessons into the relevant permanent doc (glossary, ADR, RULES) and delete the dated file, or move the whole directory to `docs/archive/learnings/` so it's clearly historical. A "TIL is a draft; it either graduates or expires in 90 days" rule keeps this from being a recurring problem.
- **Mark research docs closed.** `docs/research/` is where finished spikes go; add a `Status: CLOSED — superseded by X` header line so a reader knows in one line whether a doc is live guidance or a historical artifact. The architecture reviews already do this well; extend it.
- **`RULES.md` is 6,389 words** — it is the file you most need agents to actually follow, and it is at the length where they start skimming. Consider splitting into `RULES.md` (the ~15 hard gates, one line each) and `docs/rules-rationale.md` (the reasoning). The gates are what need to be read every session; the reasoning needs to be read once.
- Fix the two `CONTEXT.md` drifts.

---

## Other lenses worth applying

You asked what other lenses would be effective. Ranked by what I'd expect them to find *in this codebase specifically*:

**1. Connascence.** The most useful lens for your stated goal, because it grades coupling by *how expensive it is to change*, which is exactly the property you're optimizing. Ranked weakest to strongest: name → type → meaning → position → algorithm → timing → value → identity. The rule is *minimize the strength of connascence, and keep strong connascence local*. Your four parallel archetype dicts (Finding 4) are connascence-of-position across modules — the worst quadrant. `handle_actions`'s implicit priority ordering (Finding 5) is connascence-of-execution-order, also non-local. Both become weak, local, name-based connascence under the proposed fixes. This lens will find things DDD misses because DDD asks "is the model right?" and connascence asks "what breaks when I change this?"

**2. Change-cost / shotgun-surgery audit.** Empirical, cheap, and directly answers your question. Pick your five most likely next features (fifth cat, a grab mechanic, a new stage, online lobby stub, a new menu screen). For each, list the files you'd touch. Any feature touching >4 files is telling you where a seam is missing. Finding 4 is what this produced for "add a cat." Run it on the other four.

**3. Functional core / imperative shell.** You are already ~80% here and it's your biggest existing asset — the frame-counter timing, no-ambient-RNG, headless-by-default contract is what makes the golden suite possible. The lens's remaining question: *is the core reachable without the shell?* Right now, partially — `core/input.py` still binds the pure `InputFrame` port to the pygame `poll()` adapter in one module (open decision #9 from June), and `sim/presenters` drags `imageio` into `sim/`. Finishing this means `pip install pycats-core` could ship without pygame, which is the real test.

**4. Deletability.** Ask of each module: *if this feature were cancelled, how many files would I edit?* It's the inverse of the accretion question and it finds different things. `render_battle.py`, the dead dispatch arms, and `docs/learnings/` all surfaced from this angle. A codebase that's easy to accrete onto is one where features have clean removal boundaries, because that's the same boundary.

**5. Cognitive load / onboarding path.** Sit a new contributor (or a fresh agent with no `CLAUDE.md`) in front of the repo and ask: "where does knockback live?" Time it. Finding 2 exists because I ran this on myself and had to check three packages. This is the cheapest lens on the list and it directly measures the thing you said you want ("accessible").

**6. Data-vs-behavior separation.** You've already moved character data to JSON (`characters/data/*.json`) with the Python literals as drift oracles — good instinct, half-finished. The general form: anything a designer tunes should be data with a provenance record (which ADR-0003 already specifies), and anything a programmer changes should be code. The 104 remaining `⚠`/GUESS markers in source are the visible edge of the unfinished half.

**Lenses I would *not* prioritize here:** SOLID (too coarse to tell you anything you don't already know), formal hexagonal port/adapter re-scoring (you've done it twice; the remaining items are the two open decisions, not new discoveries), and test-coverage percentage (your suite's quality is well above what a coverage number would reflect).

---

## Suggested sequence

Ordered by leverage ÷ risk. Each is independently shippable and suite-verifiable.

| # | Action | Size | Why here |
|---|---|---|---|
| 1 | Add `.github/workflows/ci.yml` (ruff + pytest) + branch protection | S | Every later change is safer with it. Do it first. |
| 2 | Add the comment-hygiene rule to `CLAUDE.md` (present tense in code, history in git) | XS | Changes what every future agent writes. Highest yield per byte in the repo. |
| 3 | Delete `render_battle.py` shim + dead dispatch arms in `combat/data.py` | S | Kills 5 of 6 import cycles as a side effect. |
| 4 | Collapse the four archetype dicts into one `Archetype` record + guard test | S | Cuts "add a cat" from 7 files to 3. |
| 5 | `git mv` root modules into `screens/`, `ui/`, `shell/`, `storage/` (one PR per group) | M | The big cognitive-load win. Mechanical, low risk. |
| 6 | Rename `domain/` → `roster/`; disambiguate `systems/combat.py` | S | Removes the two worst wrong-turns for a newcomer. |
| 7 | Import-layering fitness test | S | Freezes the gains from 3/5/6 so they can't regress. |
| 8 | Refactor `handle_actions` to an ordered rule chain | M | Biggest single complexity drop; sets the pattern. |
| 9 | Same treatment for `AttackerController` (behavior tree) | M | Worst file in the repo by MI. |
| 10 | `docs/learnings/` lifecycle + `RULES.md` split + `CONTEXT.md` drift fixes | M | Do once the code side is settled. |

Items 1–4 are a weekend. 5–7 are the structural pass. 8–9 are the only ones that touch hot logic and should each get their own ticket, golden run, and eyeball-OK.

---

## What's working — protect it

Listing these because a review that only names problems gives a distorted picture, and because these are the things a refactor could accidentally damage:

- **Zero dead code** at 80% confidence. For a 105-module hobby project with 969 issues, that's rare.
- **The determinism/headless contract** (`CONTEXT.md`) is the load-bearing architectural idea and it's correct. Frame-counter timing, injected RNG, no display dependency in the core.
- **The golden suite's segmentation + summary digests** (#S4). Pairing a 125 KB opaque snapshot with a 0.6 KB reviewable semantic digest, and asserting the digest *first*, is a better answer to the rubber-stamp problem than most production teams manage.
- **Docstrings that explain why.** `display_manager.py`, `screen_render.py`, and `settings.py` each open with a paragraph explaining what problem the module exists to solve. Keep these. Finding 3 is about inline change-narration, not about these.
- **Test naming.** `test_hitstun_never_below_floor`, `test_crouch_lowers_hurtbox_high_attack_whiffs` — behavioral, specific, no vague names. The suite is a readable spec.
- **ADRs with real decisions in them**, including ones that decline to decide (ADR-0004 sanctioning `pygame.math` value types rather than churning geometry).

---

## Appendix — full complexity listing (radon, C and worse)

```
char_select.py          CharacterSelector.update              E (40)
char_select.py          CharacterSelector.render              C (11)
options_menu.py         OptionsMenu._row_label                D (21)
options_menu.py         OptionsMenu._update_keybind           C (19)
options_menu.py         OptionsMenu._activate                 C (15)
options_menu.py         OptionsMenu.update                    C (13)
options_menu.py         OptionsMenu._update_sets              C (11)
win_screen.py           WinScreenManager.update               C (14)
text_utils.py           TextRenderer.render_unicode_char      C (17)
text_utils.py           TextRenderer._compose_mixed           C (14)
text_utils.py           TextRenderer._can_font_render_char    C (12)
text_utils.py           TextRenderer._find_unicode_font       C (11)
app.py                  App.step                              C (12)
combat/collapse.py      collapse                              C (16)
systems/status_model.py timer_bar_specs                       C (11)
systems/combat.py       process_hits                          D (25)
systems/combat.py       _resolve_clanks                       C (13)
sim/runner.py           run_battle                            D (25)
sim/battle_log.py       events_from_snaps                     C (14)
sim/controllers.py      AttackerController._decide_engage     F (70)
sim/controllers.py      AttackerController._decide_combat     F (44)
sim/controllers.py      AttackerController                    C (14)
sim/controllers.py      AttackerController._apply_anti_stall  C (14)
sim/controllers.py      AttackerController._threat_incoming   C (13)
sim/controllers.py      AttackerController._decide_recovery   C (13)
sim/controllers.py      FollowerController.decide             C (11)
render/battle.py        render_battle                         C (19)
entities/fighter_input.py FighterInput.handle_actions         F (71)
entities/fighter_input.py FighterInput                        C (16)
entities/fighter_input.py FighterInput._maybe_start_dash      C (11)
entities/tail.py        Tail.update                           D (23)
entities/attack.py      Projectile.update                     C (12)
entities/fighter_physics.py step_physics                      D (27)
entities/player.py      Player._tick_timers_and_getup         C (16)
entities/player.py      Player._try_ledge_grab                C (11)
core/physics.py         solve_vertical                        C (20)
core/physics.py         resolve_player_push                   C (18)
charts/fighter_chart.py build_fighter_chart                   F (61)
```

Everything not listed is rated A or B.

**Method:** shallow clone at `71bfbc9`; `radon cc/mi/raw`, `vulture --min-confidence 80`, and a custom AST import-graph walker for the layer matrix and cycle detection. No code was executed; the test suite was not run in this environment.
