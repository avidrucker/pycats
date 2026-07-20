# Intangibility vs invulnerability — ratified rename/remodel plan (#775)

> **ARCHITECT deliverable** for epic **#772**, child **iii**. Joins the two research
> findings into a single plan the DEV child **#776** executes **without re-deciding**
> vocabulary or classification. Design-only — no code changes here.
>
> **Inputs (both closed):**
> - Census (i, #773): `docs/research/2026-07-20-invuln-intangibility-usage-census.md`
> - Canon (ii, #774): `docs/research/2026-07-20-intangibility-vs-invulnerability-canon.md`
>
> **Companion artifact:** the forward-looking respawn ruling is split into a `decision:`
> issue (see §5) because it is a behavior/design call, not a rename.
>
> Ratified 2026-07-20. Canon = Project M 3.6.

## 1. Ratified vocabulary (human-decided 2026-07-20)

Three forks, decided by the project owner:

| Fork | Ruling |
|---|---|
| **Code symbols for the pass-through mechanic** | Full rename → **`intangible` / `intangibility`** (fields, flags, constants, functions, HUD, docs). Not a docs-only or neutral-flag half-measure. |
| **Term for the connect-for-zero mechanic** | **`invincibility`** — single spelling; the word `invuln`/`invulnerable` is **retired** repo-wide. |
| **HUD bar label** | **`INTANG`** (width-constrained bar; `INTANGIBLE` where space allows). User-visible → eyeball sign-off before #776 closes. |

**Rule of thumb for #776:** every current `invuln`/`invulnerable` symbol becomes
`intangible`/`intangibility`. The word `invincible`/`invincibility` is **reserved** —
it appears in **no** current mechanic; it is held for the respawn window if/when #506 lands (§5).

## 2. Why this is (almost) a pure rename — the two grounding facts

Read from the code, not recalled:

1. **One consumer, and it already models intangibility.** `systems/combat.py` `check_hits`
   skips the defender when `fighter.invulnerable` is true — no pairing, no hitlag, no damage.
   Per #774 that *is* intangibility behaviour. So for **every** live mechanic (ledge, dodge,
   getup) the model is already correct; only the word is wrong.
2. **No respawn immunity is implemented.** `Fighter.reset_to_spawn` only *clears* the flag;
   the sole `invulnerable = True` sites are ledge-grab (`player.py` grab branch), dodge
   (`_start_dodge`), and getup (`start_getup_roll` / getup-attack). "Respawn" appears only in
   **comments** naming a *future* source (#506). So there is no connect-for-zero behavior to
   change today.

**Consequence: #776 is golden-neutral.** Sim goldens serialize a positional `namedtuple`
(`PlayerSnap`, field order unchanged) and `defensive_status` already emits the string
`"intangible"`. Renaming Python attributes changes no serialized bytes. The only test impact
is the **render layer** (§4).

## 3. The correct-label table (census × canon → action)

Every census usage, marked **keep** / **rename** / **remodel**, with the target name.
Grouped by the census's mechanic buckets. All rows are **rename** (word only) except where noted.

### Bucket 1 — Ledge-grab / regrab burst  →  intangibility (keep behavior, rename)
| Current symbol | Action | New name |
|---|---|---|
| `config.LEDGE_INVULN_BASE_FRAMES` | rename | `LEDGE_INTANGIBLE_BASE_FRAMES` |
| `config.LEDGE_REGRAB_INVULN_CUTOFF` | rename | `LEDGE_REGRAB_INTANGIBLE_CUTOFF` |
| `entities/ledge.py::ledge_invuln_frames()` | rename | `ledge_intangible_frames()` |
| `entities/ledge.py::ledge_regrab_invuln_frames()` | rename | `ledge_regrab_intangible_frames()` |
| `Fighter.ledge_invuln_timer` | rename | `Fighter.ledge_intangible_timer` |
| `Fighter.ledge_invuln_granted` | rename | `Fighter.ledge_intangible_granted` |
| `combat/provenance.py` key `"LEDGE_INVULN_BASE_FRAMES"` | rename | `"LEDGE_INTANGIBLE_BASE_FRAMES"` (⚠ string key — grep tests/docs that read it by name) |
| comments in `fighter.py`/`player.py` (edge-hog, receive_hit) | rename | prose → "intangibility" |

### Bucket 2 — Air / spot / roll dodge  →  intangibility (keep, rename)
| Current symbol | Action | New name |
|---|---|---|
| `Fighter._start_dodge` sets `invulnerable = True` | rename | `intangible = True` |
| dodge-end branch `invulnerable = False` | rename | `intangible = False` |
| `player.py` dodge-tail `invulnerable = False` | rename | `intangible = False` |
| `sim/showcase.py` roll-dodge scene ("intangible … passes through") | keep | already correct |
| `systems/combat.py::check_hits` guard `defender.fighter.invulnerable` | rename | `.intangible` |

### Bucket 3 — Getup-roll / getup-attack  →  intangibility (keep, rename)
| Current symbol | Action | New name |
|---|---|---|
| `config.GETUP_ROLL_FRAMES` (+ comment) | keep const name (already neutral), keep `intangib` comment | — |
| `Fighter.getup_roll_timer` | keep | already neutral |
| `Fighter.start_getup_roll` (`invulnerable = True`, `invulnerable_timer=…`) | rename | `intangible = True`, `intangible_timer=…` |
| `player.py` getup-roll / getup-attack end `invulnerable = False` | rename | `intangible = False` |
| `combat/provenance.py` key `"GETUP_ROLL_FRAMES"` | keep | neutral key |
| `charts/fighter_chart.py` getup comments | rename | prose → "intangibility" |

### Bucket 4 — Respawn  →  **forward ruling (see §5)**; today: comment-only rename
| Current symbol | Action | New name / note |
|---|---|---|
| `Fighter.invulnerable_timer` init comment "post-respawn" | rename | `intangible_timer`; comment stays (respawn = future source) |
| `Fighter.invulnerable` init comment "respawn" | rename | `intangible`; comment stays |
| `reset_to_spawn` (`invulnerable* = 0/False`) | rename | `intangible* = 0/False` |
| `render_battle.py` "#506 respawn" bar-source comment | keep/rename prose | note: **if #506 grants immunity, it is invincibility (§5), not this flag** |

### Bucket 5 — HUD / render (the bar + dots)
| Current symbol | Action | New name |
|---|---|---|
| `render_battle.INVULN_BAR_COLOR` | rename | `INTANGIBLE_BAR_COLOR` |
| `render_battle.GRABS_LEFT_DOT_COLOR` (= INVULN color) | keep name, repoint | → `INTANGIBLE_BAR_COLOR` |
| `render_battle._invuln_remaining_max()` | rename | `_intangible_remaining_max()` |
| bar registry id `"ledge_invuln"` | rename | `"ledge_intangible"` |
| bar registry id `"invuln"` | rename | `"intangible"` |
| bar **labels** `"INVULN"` (×2) | rename | **`"INTANG"`** (user-visible — §4 sign-off) |
| grabs-left dots helper + LOCKOUT/INVULN docstring | rename | prose → intangibility |

### Bucket 6 — Defensive-status label  →  keep (already "intangible")
| Current symbol | Action | Note |
|---|---|---|
| `player.py::defensive_status` (`"intangible" if invulnerable else "vulnerable"`) | rename the **bool read** only | `if intangible` — the emitted **string is unchanged** |
| `fighter_chart.py` defensive_status region + `intangible` leaf | rename bool read | leaf id `"intangible"` unchanged |
| `state_engine.py` / `state_engine_sc.py` defensive_status | rename bool read | `in_state("intangible")` unchanged |

### Bucket 7 — Sim serialization
| Current symbol | Action | Note |
|---|---|---|
| `sim/runner.py` `PlayerSnap` field `invulnerable` | rename | `intangible` — **positional JSON, golden-neutral** |
| `PlayerSnap` field `invulnerable_timer` | rename | `intangible_timer` — golden-neutral |

**No `remodel` rows.** Every live usage is a pure rename; the only behavior question is the
respawn *future* ruling in §5, which changes no current code.

## 4. Test & golden strategy for #776

- **Sim goldens: no regen expected.** The rename is positional/string-neutral (§2). If any
  golden moves, that is a **red flag** the DEV mislabeled a value — stop and investigate, do
  not regen to green.
- **Render-parity test** (`tests/test_battle_screen_render.py`) and any test asserting the
  literal `"INVULN"` string (`test_ledge_invuln_bar.py`, `test_status_registry.py`,
  `test_status_timer_bar.py`, `test_grabs_left_dots.py`, `test_ledge_regrab_cutoff.py`,
  `test_ledge_hang.py`, `test_edge_hog.py`) **will** change: update the expected label to
  `INTANG`. These are the able-to-fail proof the rename reached the HUD.
- **Rename-coverage check** (able-to-fail for the rename itself): after #776,
  `grep -rn -i 'invuln' pycats/` should return **0** hits (the word is retired). That grep
  going to zero is the machine-verifiable done-condition.
- **String-key audit:** the provenance key rename (`"LEDGE_INVULN_BASE_FRAMES"`) and bar-id
  renames are string literals — grep `tests/` and `docs/` for each before renaming so no
  by-name lookup breaks.
- **Test-file renames** (`test_ledge_invuln_bar.py` → `…_intangible_bar.py`) are optional
  polish; the DEV may keep filenames to minimize churn, but the in-test label assertions must
  update regardless.

## 5. The one decision that is NOT a rename → `decision:` issue (item B)

**Finding (grounded):** pycats grants **no** respawn immunity today (§2). PM/Smash canon
(#774, *Revival platform*) gives the post-platform descent **invincibility** (attacks connect
for zero, 120f). So the open question is forward-looking:

> **If/when respawn immunity is implemented (#506), should it be modeled as *invincibility*
> (attack connects, attacker gets hitlag, zero damage — canon-faithful) or as the existing
> *intangibility* skip-the-hit path (simpler, but diverges from canon)?**

This is a **design/behavior decision** (it would need a new connect-for-zero code path the
current single gate cannot express, and it *would* move goldens *when built*), so per RULES →
"Changing values" it is filed as **`decision:` issue #784** (humans-only), not ratified in this
plan. #776 does **not** touch it; #506 is gated on the #784 ruling.

## 6. Execution order for #776 (suggested)

1. Rename the two `Fighter` fields (`invulnerable*` → `intangible*`) + the `combat.py` guard — the spine.
2. Rename config constants + `ledge.py` helpers + `provenance.py` string key (audit by-name reads first).
3. Rename `render_battle.py` symbols + bar ids; flip labels to `INTANG`.
4. Rename `PlayerSnap` fields; run goldens — **expect green** (if not, §4 red flag).
5. Update the render-parity + label-asserting tests to `INTANG`.
6. Sweep doc prose in the canonical homes (`glossary.md`, `pm-reference/*`); leave dated
   research-doc **filenames** as historical records, but update the glossary to define
   intangibility/invincibility and mark `invuln` retired.
7. `grep -rn -i 'invuln' pycats/` → 0. Eyeball sign-off on the `INTANG` HUD bar.

## Acceptance (against #775)

- ✅ A DEV can execute without re-deciding vocabulary (§1) or classification (§3).
- ✅ Every census usage maps to keep/rename/remodel with a reason (§3).
- ✅ Behavior-change items separated from pure renames — and the sole behavior call
  (respawn) is split into a `decision:` issue (§5), not asserted here.

## Refs

Epic **#772**; census **#773**; canon **#774**; DEV **#776**; respawn-immunity mechanic **#506**.
Origin **#754** / **#771**. Parity docs: `docs/pm-reference/defense-shield-dodge.md`,
`docs/pm-reference/ledge-regrab-invuln-and-display.md`.
