# PM-parity marker audit — the ⚠ / 🔬 / ❓ sweep worklist (#454, Axis A / slice 1 of #408)

> Research / findings only. **No code markers applied in this slice** — this doc is
> the classified worklist the mechanical marking slices (2+) consume.
> Date: 2026-07-02. Agent: FIG. Design of record: #448. Tracker: #451.

## Legend (ratified 2026-07-02)

| Marker | U+ | Means | Grep answers |
|---|---|---|---|
| `⚠` | 26A0 | **guessed** — value present but unconfirmed vs Project M | "what's unpinned?" |
| `🔬` | 1F52C | **needs research** — queued for sourcing/derivation | "what's the research backlog?" |
| `❓` | 2753 | **open question** — undecided design/behaviour point | "what's undecided?" |

**Rules applied.** (1) `⚠` and `🔬` are orthogonal and **co-occur** (`⚠🔬`) on a guessed
value that is also queued for sourcing. (2) Markers flag only **unresolved** things — the
#233 *resolved* states (`FOUND` / `TUNED` / `DIVERGENCE`) get **no** marker. (3) An inline
`❓` references its `decision` ticket where one exists.

**Legend home (role split, ratified):** `RULES.md` carries the terse **dev / write-time
convention** (so new code marks at authoring time); **#452** carries the fuller
**human-facing key**. They cross-reference; neither duplicates the other. The RULES.md note
itself is written in a later marking slice, not here.

## Candidate universe (termination greps)

| Grep | Raw hits | Genuine open-work | Notes |
|---|---:|---:|---|
| `grep -rn '⚠'` | 53 | 53 (keep) | all correct; 15 also get `🔬` (below) |
| prose-only (`placeholder\|playtest\|approximat\|not sourced\|guess\|tbd\|unconfirmed`) minus `⚠` | ~48 | ~40 | 8 excluded (provenance.py machinery + descriptive) |
| `grep -rni 'decision'` | 7 | **0** | all false positives ("decision logic", docstrings) — see ❓ finding |

The inventory is complete: every line from the three greps is accounted for below as
`keep` / `add-marker` / `no-marker (reason)`.

---

## Q1 — prose-only: genuine open-work vs historical/explanatory

**Genuine open-work → ADD `⚠` (positions/values unpinned vs PM):**

| File | Lines | Target | Note |
|---|---|---|---|
| `characters/nalio_cat.py` | 37, 58, 70, 101, 128, 153, 155, 182, 216, 249, 281, 308–313, 356, 365, 393, 425 | `⚠` | hitbox **position** approximations (bones not modelled, per #120). #408 lists these as unpinned. |
| `characters/nalio_cat.py` | 338, 356 | `⚠🔬` | projectile / release-swing values explicitly "playtest (tracked #192 way)" → also research. |
| `characters/birky_cat.py` | 4, 44, 45, 65, 66, 87, 109, 134, 155, 182, 206, 227 | `⚠` | Kirby proportional-to-Mario approximations "pin/playtest" (#229 spike). |
| `characters/narz_cat.py` | 16, 289 | `⚠` | moves reusing the default-cat **placeholder** (unspecified → unpinned). |
| `characters/default_cat.py` | 75 | `⚠` | "Playtest starting point" (hitbox window). |
| `characters/roster.py` | 18 | `⚠` | OG-skin cosmetic palette, "playtest". Low priority, still unpinned. |
| `combat/data.py` | 127, 128 | `⚠🔬` | `projectile_speed` GUESS, "derive via rukaidata" → research. |
| `sim/controllers.py` | 44 | `⚠` | edge-guard projectile-mode "GUESS px". |

**Historical / explanatory / resolved → NO marker (excluded):**

| File | Lines | Why excluded |
|---|---|---|
| `combat/provenance.py` | 23, 24, 35, 36, 50, 51 | The provenance **registry's own machinery/docstring/data** — it *defines* GUESS/FOUND, and its rows already machine-track status (#233). Marking it would be marking the marker system. |
| `characters/default_cat.py` | 8, 26 | Module-doc **describing** the default cat as a deliberately-simple stand-in ("approximating today's basic attack") — a design description, not a PM-parity claim. |

---

## Q2 — which marker(s): the `🔬` (needs-research) subset

15 existing `⚠` sites explicitly say the value is queued for sourcing/derivation
("rukaidata-confirm", "derivation pending", "verify", "not sourced", "#192/#195") →
**upgrade to `⚠🔬`:**

- `config.py`: 169 (`HITSTUN_MULTIPLIER` "verify"), 170 (`HITSTUN_FLOOR` "not sourced"), 214 (getup speeds "not sourced").
- `characters/narz_cat.py`: 8, 28, 50, 69, 92, 134, 155, 177, 198, 220 (all "⚠ playtest / rukaidata-confirm").
- `characters/nalio_cat.py`: 337, 349 (`projectile_speed` "GUESS … #192/#195 derivation pending").

Plus the two prose-only `⚠🔬` adds from Q1 (`combat/data.py` 127/128, `nalio_cat` 338/356).

The remaining ~38 `⚠` are guesses **not** currently queued for a specific sourcing action
(playtest tuning) → stay plain `⚠`.

## Q3 — existing `⚠` that should LOSE the marker

**None.** All 53 `⚠` sites denote genuinely-unconfirmed values (playtest/GUESS), none has
since become a `FOUND`/`TUNED`/`DIVERGENCE` resolved state. (The #233 registry covers the
~34 `config.py` combat scalars; none of those flip to resolved here.)

## Q4 — `❓` open questions

**Finding: the termination grep-3 (`decision`) is the wrong lens** — all 7 hits are false
positives (AI "decision logic" in `sim/controllers.py`, "the decisions on expiry" in
`fighter.py` docstrings, module docstrings in `core/input.py`/`input_poll.py`). Genuine
undecided-design points live in `#### TODO:` comments, not the word "decision".

Confirmed `❓` site (undecided behaviour, no decision ticket yet):
- `entities/fighter_input.py:160` — `#### TODO: determine whether walking off a ledge "consumes" a jump` → `❓` (open behaviour question).

Other `#### TODO:` comments are **deferred implementation**, not undecided design → **not**
`❓` (a todo ≠ an open question). `❓` is genuinely sparse in this codebase. **Recommendation
for slices 2+:** seed `❓` from `#### TODO.*(determine|whether|should we|do we)`, not
`decision`; add `❓` opportunistically as undecided points are noticed, and reference a
`decision` ticket when one is filed.

---

## Marking plan (slices 2+, one file-group per slice, all comment-only / golden-safe)

- **Slice 2 — `characters/*.py`** (the bulk): apply `⚠` / `⚠🔬` per Q1+Q2 to
  `nalio_cat` (~19), `birky_cat` (~12), `narz_cat` (12 upgrades + 2 adds), `default_cat` (1),
  `roster` (1). ~47 sites.
- **Slice 3 — `entities/` + `combat/data.py` + `sim/controllers.py`**: the `⚠🔬` upgrades in
  `combat/data.py`, the `⚠` add in `controllers.py:44`, the `❓` in `fighter_input.py:160`,
  and confirm the existing `entities/attack.py` / `ledge.py` / `player.py` `⚠` sites.
- **Slice 4 — `config.py`** (3 `⚠→⚠🔬` upgrades) **+ the RULES.md dev-legend note** (the
  write-time convention; cross-ref #452). Cross-ref the `config.py` combat scalars to #233.
- Each marking slice: `git diff` shows only the target file(s), comments only →
  `tests/golden/` byte-identical, no regen.

## Acceptance check (this slice)

- [x] Every line from the three termination greps is triaged above (keep / add / no-marker+reason).
- [x] The 4 research questions are answered.
- [x] Per-file-group marking plan recorded (slices 2–4).
- [x] Legend split recorded as ratified (RULES.md dev-convention · #452 human-key).
- [x] Doc-only slice — no code markers applied; suite/goldens untouched.

## Cross-refs

Slice 1 of **#408** (Axis A of **#451**; design **#448**). Provenance registry **#233**;
guessed-values umbrella **#192** + `GUESSED_VALUES_TO_RESEARCH.md`; human legend **#452**;
anchor-citation hygiene **#337**.
