# Default routing — `default.json`, the `"default"` key, and loud errors for unknown keys

> **RESEARCH findings for #861** (child of #792 via SCOPE #826). Design basis: #809 §2.4
> (migration order), #844 (R4 reader precedence). **Findings only — no decision, no code.**
> The ruling and the DEV flip are separate downstream children, filed one at a time.

## TL;DR

- `load_fighter_data(character)` (`pycats/combat/data.py`) resolves a
  `CHARACTER_DATA_DIR/<character>.json` mirror first (#844), else a Python `if`-switch
  ending in a catch-all that returns `DEFAULT_FIGHTER_DATA` for **every** unmatched key.
- **The requester's steer** — prefer a loud/obvious raised error over resolving an
  unexpected key to a default with no notification — is *cheaper and safer than the ticket
  framing implies*, because of a finding the ticket didn't have: **the live game and sim
  paths never hand a raw typo to `load_fighter_data`.** The #672 domain layer
  (`registry.py` / `placeholder.py`) already absorbs unknown keys into
  `PLACEHOLDER_CHARACTER` (whose `.key` is `"testcat"`) and renders a typo as a **visible
  gray placeholder** — "never silently as a real cat." So on the live path the catch-all
  only ever sees a real archetype key or `"testcat"`.
- That reframes Q3: a raise at `load_fighter_data` is **defense-in-depth for the data
  seam** (catches a *programming* error — a caller that bypassed the domain resolver and
  passed a raw string), not a user-facing typo guard (already handled upstream). It cannot
  fire on the live/sim/golden path, so **golden-safety for a raise is a non-issue on
  production paths** — the only fallout is in tests that call the seam directly.
- The population that *does* rely on the silent catch-all is **entirely tests**: ~14 sites
  pass `"default"` as a "the default cat" comparison oracle, and `test_combat_data.py`
  passes `"calico"`/`"ghost"`/`"unknown_character_xyz"` specifically to assert the current
  silent-default behavior. Any raise option must migrate those.

---

## Current behavior (as read from source, worktree of #861)

`load_fighter_data` in `pycats/combat/data.py` (`load_fighter_data`, `CHARACTER_DATA_DIR`):

```
path = CHARACTER_DATA_DIR / f"{character}.json"
if path.exists():           # R4 JSON branch (#844)
    return _fighter_from_json(...)
if character == "nalio":  return NALIO_FIGHTER_DATA
if character == "birky":  return BIRKY_FIGHTER_DATA
if character == "narz":   return NARZ_FIGHTER_DATA
if character == "gnok":   return GNOK_FIGHTER_DATA
if character == "testcat":return DEFAULT_FIGHTER_DATA   # named fixture handle (#591)
return DEFAULT_FIGHTER_DATA                              # catch-all: "default", "P1", "P2", typos, …
```

Facts established while writing this doc:

1. **All four flipped cats already ship JSON** — `nalio/birky/narz/gnok.json` exist in
   `CHARACTER_DATA_DIR`, so the R4 branch *does* fire for them today. (The module comment
   near `CHARACTER_DATA_DIR` still reads "NO `<character>.json` ships today" — stale since
   the flips; noted, out of scope to fix here.)
2. **No `default.json` ships** — `"default"` currently falls through the switch to the
   catch-all → `DEFAULT_FIGHTER_DATA` (Python `default_cat.py`).
3. **`"testcat"` and the catch-all return the same object** — both `return
   DEFAULT_FIGHTER_DATA`. `test_combat_data.py::test_load_fighter_data_testcat_is_the_default_cat_object`
   pins `load_fighter_data("testcat") is DEFAULT_FIGHTER_DATA`.
4. **The domain layer already routes unknowns to a placeholder, loudly-ish.**
   `pycats/domain/registry.py::character_for` returns `PLACEHOLDER_CHARACTER` for an
   unknown/None key; `PLACEHOLDER_CHARACTER.key == "testcat"`
   (`pycats/domain/placeholder.py`). `resolve_selection` routes a typo to the **gray
   placeholder skin in both halves** so "a typo renders *visibly* … never silently as a
   real cat." This is the existing, ratified answer to "what happens to an unknown key" on
   the user-facing path — a **visible placeholder**, chosen over a raise.

### Consequence: what actually reaches the catch-all on each path

| Path | How the key is produced | Does a raw typo reach `load_fighter_data`'s catch-all? |
|---|---|---|
| **Live game** (`battle_screen.py::create_from_selection`) | `build_fighter(sel)` → `fighter_data_of(character)` → `load_fighter_data(character.key)`; `character` came from `character_for`/`resolve_selection` | **No** — unknown already became `PLACEHOLDER_CHARACTER.key == "testcat"`. `fighter_data` is injected into `Player`, so `char_name="P1"/"P2"` never reaches the loader either. |
| **Sim / goldens** (`sim/runner.py::build_players`) | same domain resolver; `fighter_data=built.fighter_data` injected into `Player` | **No** — same as above. `"P1"/"P2"` are labels only; the key is a real archetype or `"testcat"`. |
| **`Player(char_name=...)` with no `fighter_data`** (`entities/player.py:116`, `fighter_data or load_fighter_data(char_name)`) | bare `Player("P1")` fixtures | **Yes** — `char_name` (`"P1"`, `"nalio"`, `"TestCat"`, …) hits the loader directly. **Test-only construction** (~20 fixtures); no production site builds a bare `Player`. |
| **Direct `load_fighter_data("…")` calls** | tests | **Yes** — see census below. |

**Net:** the silent catch-all is a **test-facing seam**, not a live-path behavior. This is
the single most decision-relevant finding.

---

## Caller census

Every call site that passes a key that is **not** a shipped archetype
(`nalio/birky/narz/gnok`), grouped by what it expects the catch-all to do. (Archetype-key
calls — the bulk of `grep load_fighter_data(` — are omitted; they hit their own arms.)

### A. `"testcat"` — legitimate fixture handle (#591); **must stay resolvable**
The minimal one-move kit, loaded by name. Also the `.key` of `PLACEHOLDER_CHARACTER`, so
the whole live/sim unknown-key path funnels through it.
- `tests/test_nalio_cat.py:18`, `tests/test_nalio_smashes.py:17`, `tests/test_narz_smashes.py:15`,
  `tests/test_birky_smashes.py:16`, `tests/test_smash_charge.py:22`, `tests/test_up_b_recovery.py:25`,
  `tests/test_birky_crouch_geometry.py:12` — module-level `_TESTCAT = load_fighter_data("testcat")`.
- `tests/test_combat_data.py:57,68` — asserts testcat = minimal kit and `is DEFAULT_FIGHTER_DATA`.
- `tests/test_domain_model.py:112` — `bf.fighter_data is load_fighter_data("testcat")` (domain build resolves unknown → testcat).

### B. `"default"` — used as a "the default cat" comparison oracle
These read `"default"` as *the name of the default fighter*, comparing an archetype's field
against it. They rely on `"default"` → `DEFAULT_FIGHTER_DATA`.
- `tests/test_dash.py:26`, `tests/test_narz_jab.py:11`, `tests/test_reach_aware.py:31`
- `tests/test_birky_data.py:30,58,69,126`, `tests/test_gnok_data.py:31,42,70,87`,
  `tests/test_narz_data.py:22,33,43`
- (`test_birky_data.py:58` even comments `# any non-archetype key -> default cat`.)

### C. `"calico"` / `"ghost"` / `"unknown_character_xyz"` — assert the silent-default contract
`test_combat_data.py` **only**. These exist to pin "any string maps to the same default"
(`test_load_fighter_data_unknown_char_returns_fighter_data`: *"Phase 0: any string maps to
the same default."*). Note `calico`/`ghost` are **skin keys** (`SHARED_SKIN_KEYS` in
`domain/skin_assignment.py`), used here as stand-in unknowns, not character keys.
- `tests/test_combat_data.py:32,37,43,85,90,101,106,112,119,126,133,139,145,151,157,234`.

### D. Production — the `"P1"`/`"P2"` catch-all is **not reached** on live/sim paths
`entities/player.py:116` is the only production site that *could* pass an unresolved key,
and only for a bare `Player(char_name=...)` with `fighter_data=None`. Both real
constructors (`battle_screen.py:87/98`, `sim/runner.py:120/131`) inject `fighter_data`, so
this never fires outside tests. **No production caller depends on the silent catch-all.**

---

## Q1 — Does `default` flip to JSON, and how is the fallback SSOT kept from drifting?

The other four flips are safe because the Python literal became a *pure fallback nothing on
the live path reaches* (the JSON wins, the `.py` is dead unless the file is deleted).
`default` is different: `default_cat.py::DEFAULT_FIGHTER_DATA` is the **one fighter the
engine must always load** — it backs `"testcat"`, the domain placeholder, and every
test-facing catch-all. Flipping it introduces a second source for the load-bearing
fallback.

| Option | What it is | Loud-error steer | Golden-safety | Drift risk | Notes |
|---|---|---|---|---|---|
| **Q1-a** ship `default.json`, thin `default_cat.py` to a generated fallback | JSON is SSOT; `.py` regenerated from it | neutral | must prove round-trip byte-equal (R5) | low once generated, but the generator becomes load-bearing | inverts today's direction (Python = truth) |
| **Q1-b** ship `default.json`, keep `default_cat.py` as oracle + R7-style drift-guard | two sources, a test asserts equality | neutral | round-trip + drift-guard both green | low (guarded) but **two sources to edit** | most machinery for the least-changing fighter |
| **Q1-c** do **not** flip default — keep Python-only canonical fallback ⭐ | `default_cat.py` stays the sole source; no `default.json` | neutral | zero movement (nothing changes) | **none** (one source) | the engine's guaranteed-loadable fighter stays a code constant, not a file that can be absent/corrupt |

**Reading (not a decision):** Q1-c is the low-risk default. The reason the other four flips
were worth it — authoring real per-fighter box data through the editor — **does not apply
to the default cat**, which is a fixed minimal kit no one authors against a Mario
reference. A `default.json` would add a second source and a drift-guard for a fighter that
never changes. Q1-a/b earn their cost only if a later decision wants *zero* Python fighter
literals (uniformity); that is a separate architectural call. The R6/R7 interaction: a
drift-guard (Q1-b) is the same pattern #863 built, but there is no provenance to collapse
for default, so it would be a plain byte-equality test, not a `collapse()` recompile.

## Q2 — What serves `"P1"`/`"P2"` and unmatched-but-intended keys?

The premise "the sim/golden path loads the Python `DEFAULT_FIGHTER_DATA` for `"P1"`/`"P2"`"
is **only true for bare-`Player` test fixtures** (finding D). The live and sim paths inject
`fighter_data` resolved from a real key, so they are already off the catch-all.

| Option | Catch-all / `"P1"`/`"P2"` source | Golden-path risk | Notes |
|---|---|---|---|
| **Q2-a** keep catch-all on Python `DEFAULT_FIGHTER_DATA` ⭐ | unchanged | **none** — live/sim inject `fighter_data`; only bare-`Player` test fixtures read it, and they get the same object as today | pairs naturally with Q1-c |
| **Q2-b** if `default.json` ships (Q1-a/b), route catch-all through it too | `_fighter_from_json(default.json)` | must show `_fighter_from_json(default.json) == DEFAULT_FIGHTER_DATA` (equal; the four flips proved JSON loads are *equal, not identical* — see #870/JSON-flip note) | **`is DEFAULT_FIGHTER_DATA` identity assertions break** (`test_combat_data.py:68`, `test_domain_model.py:112`) — JSON hydrate returns a fresh instance; those must relax `is` → `==` |

**Golden-path statement (required by AC):** No Q2 option moves the *live* `"P1"`/`"P2"`
render off its current data, because those seats never resolve through the catch-all. The
only observable change is object *identity* for bare-`Player` fixtures and testcat identity
asserts under Q2-b.

## Q3 — Unknown keys and `"testcat"`, given the loud-error steer

`"testcat"` must stay resolvable (it is both the #591 fixture and the placeholder key).
The question is the **catch-all**.

| Option | Behavior on an unmatched key | Loud-error steer | Breaks (from census) | Notes |
|---|---|---|---|---|
| **Q3-a** raise on unknown (`ValueError` naming the bad key + listing valid keys) | `load_fighter_data("naio")` → error | **strongest** | all of census B + C (~30 sites) + the bare-`Player` typo path | cannot fire on live/sim (already placeholder-resolved) → pure data-seam guard |
| **Q3-b** raise on unknown, but keep an explicit allow-list of intended-default keys (`"default"`, `"P1"`, `"P2"`, `"testcat"`) ⭐ | listed keys → default; anything else → error | **strong**, honors the steer while sparing legitimate defaults | census C (`calico`/`ghost`/`unknown_character_xyz`) — the tests asserting *unknown*→default; census B (`"default"`) **survives** (allow-listed) | smallest test migration that still makes a *typo* raise; matches the domain layer's intent (typo = loud) while keeping the fixture keys |
| **Q3-c** log-and-default | default + a log line | **weakest** — the steer explicitly disprefers "resolve to a default with notification"; a log line is not "loud and obvious" | none | documented per AC as the option that least honors the steer |

**Reading (not a decision):** Q3-b fits the requester's steer with the least collateral: a
real typo raises, while the four intended-default keys (`default`/`P1`/`P2`/`testcat`) stay
resolvable, so census B (the `"default"` oracles) and census A (`testcat`) keep passing.
Only census C — the `test_combat_data.py` cases whose *whole point* is "unknown → silent
default" — must migrate, and those tests are precisely the assertion of the behavior the
steer wants to reverse, so rewriting them (to assert *raises*) is the intended change, not
collateral damage. Q3-a is simplest to implement but forces ~14 extra edits to the
`"default"` oracles for no steer benefit (a deliberate `"default"` is not a typo). Note the
interaction with the domain layer: since `resolve_selection` already turns a user typo into
the gray placeholder, a Q3 raise never degrades the *player* experience — it fires only
when code passes a raw unresolved string to the data seam, i.e. a bug.

---

## Coupling between the three questions

- **Q1-c + Q2-a + Q3-b** is the internally-consistent low-risk set: default stays a Python
  constant (one source, no drift-guard, no golden movement), the catch-all keeps serving
  the intended-default keys, and a typo raises loudly at the seam. It changes only the
  `test_combat_data.py` unknown→default assertions.
- **Q1-a/b** (ship `default.json`) only makes sense if a later architectural decision wants
  zero Python fighter literals; it then forces Q2-b's identity-assertion relaxations and a
  default drift-guard. That is a *uniformity* argument, orthogonal to the loud-error steer.
- The loud-error steer (Q3) is **independent of whether default flips** — it can land on
  today's Python-only default without any `default.json`.

## Open questions for the downstream DECISION child (human-gated)

1. Does the project want **zero Python fighter literals** (flip default, Q1-a/b) or is a
   guaranteed-loadable Python fallback (Q1-c) preferred? — the only real fork in Q1/Q2.
2. Raise scope: **allow-list** the four intended-default keys (Q3-b) or raise on everything
   including `"default"` (Q3-a) and migrate the `"default"` oracle tests too?
3. Error type + message contract: `ValueError` vs `KeyError`; should the message enumerate
   valid archetype keys (helpful, but couples the message to the roster)?
4. Should the `test_combat_data.py` unknown-key tests be **rewritten to assert the raise**
   (making them the regression guard for the new behavior) as part of the DEV flip?

## Refs

- Tickets: #792 (tracker) · #826 (SCOPE) · #844 (R4 reader precedence) · #851/#856/#858/#860
  (the four completed flips) · #862 (R6 collapse) · #863 (R7 drift-guard) · #591 (testcat
  fixture) · #672 (domain placeholder / `resolve_selection`) · #809 §2.4 (migration order).
- Code (worktree of #861): `pycats/combat/data.py` (`load_fighter_data`, `CHARACTER_DATA_DIR`)
  · `pycats/characters/default_cat.py` (`DEFAULT_FIGHTER_DATA`) · `pycats/domain/registry.py`
  (`character_for`, `resolve_selection`) · `pycats/domain/placeholder.py`
  (`PLACEHOLDER_CHARACTER`) · `pycats/sim/runner.py` (`build_players`) ·
  `pycats/battle_screen.py` (`create_from_selection`) · `pycats/entities/player.py`
  (the `fighter_data or load_fighter_data(char_name)` seam) · `tests/test_combat_data.py`
  (the unknown→default assertions).
