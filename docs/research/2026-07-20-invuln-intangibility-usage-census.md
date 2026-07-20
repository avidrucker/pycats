# Intangibility / invulnerability usage census (child i of #772)

**Role:** RESEARCH (inventory only). **Child of #772**, strand **(i)**. Companion: the
canon-mapping strand **(ii)**, #774.

**What this is:** a map of *where* every `invuln` / `invulnerable` / `intangib` usage lives
in `pycats/` today and *what each one currently governs*. It records the present state of the
code; it makes **no** judgment on whether a given usage *should* be intangibility or
invulnerability, and proposes **no** renames. Those verdicts are child (ii) #774 and the
architect child #775.

## How to re-derive this census

Run from the repo root. As of the census date the counts below were produced by:

```bash
grep -rn -i 'invuln'    pycats/     # ~115 line-hits
grep -rn -i 'intangib'  pycats/     #  ~65 line-hits
grep -rli -E 'invuln|intangib' docs/   # 49 files
grep -rli -E 'invuln|intangib' tests/  # 28 files
```

Census taken **2026-07-20** against the worktree branch for #773 (base `main` @ `e4b8e27`).
Line numbers are as-of hints only; the census is keyed on **file + symbol** (named landmark)
per the repo's referencing rule.

## The core distinction the code does NOT yet make

Today the code carries **one** boolean, `Fighter.invulnerable`, and **one** frame timer,
`Fighter.invulnerable_timer`, that every defensive mechanic below shares. Comments and
docstrings use the words `invuln`/`invulnerable` and `intangib`/`intangible`
interchangeably to describe that single flag — e.g. `fighter.py` initializes
`self.invulnerable` with the comment "dodging / post-hit / respawn / ledge-grab
invulnerability", while `player.py` and `fighter_chart.py` describe the *same* flag as
granting "intangibility". Whether each usage is behaviorally intangibility (hurtbox off) or
invulnerability (hurtbox on, zero damage) is exactly what child (ii) decides — this doc only
notes which flag/timer each site reads or writes.

---

## Mechanic bucket 1 — Ledge-grab / regrab intangibility burst

The ledge burst has its **own dedicated fields** (`ledge_invuln_timer` /
`ledge_invuln_granted`), separate from the shared `invulnerable_timer`, plus its own config
constants and its own HUD bar.

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `config.py` :: `LEDGE_INVULN_BASE_FRAMES` | `invuln` (const) / `intangib` (comment) | Ledge-grab intangibility burst length = 21f (PM 3.6 CliffCatch 1-21). |
| `config.py` :: `LEDGE_REGRAB_INVULN_CUTOFF` | `invuln` (const) | Grabs 1..5 grant the full burst; grab 6+ grant only the residual (PM anti-plank cutoff). |
| `config.py` header comment (above `LEDGE_INVULN_BASE_FRAMES`) | `invuln` + `intangib` | Rationale: burst decays over time; the old 120f full-hang value is retired. |
| `entities/ledge.py` :: `ledge_invuln_frames()` | `invuln` / `intangib` | Returns the flat per-grab burst (`LEDGE_INVULN_BASE_FRAMES`). |
| `entities/ledge.py` :: `ledge_regrab_invuln_frames(regrab_count)` | `invuln` / `intangib` | Burst granted for the Nth consecutive grab; 0 past the cutoff. |
| `entities/fighter.py` :: `Fighter.ledge_invuln_timer` (init) | `invuln` / `intangib` | Percent-scaled → now fixed ledge-grab burst countdown (#311). |
| `entities/fighter.py` :: `Fighter.ledge_invuln_granted` (init) | `invuln` | The burst's length at grab; used as the INVULN bar denominator (#531). |
| `entities/fighter.py` :: `Fighter.reset_to_spawn` (ledge_invuln_timer = 0) | `invuln` | Clears the burst on respawn. |
| `entities/fighter.py` :: `Fighter.receive_hit` comment | `intangib` | A hit only lands past the ledge-grab intangibility burst (combat skips invulnerable defenders). |
| `entities/player.py` :: `ledge_regrab_invuln_frames` (import) | `invuln` | Player pulls the regrab-burst helper. |
| `entities/player.py` :: `Player.update` ledge-hang branch | `invuln` / `intangib` | Ticks `ledge_invuln_timer` down; sets `invulnerable = (ledge_invuln_timer > 0)`. |
| `entities/player.py` :: `Player.update` grab branch | `invuln` / `intangib` | On a fresh grab, sets `ledge_invuln_timer`/`ledge_invuln_granted = granted` and `invulnerable = True`. |
| `entities/player.py` :: edge-hog knock-off comment | `intangib` | Occupant still intangible → hog denied (`ledge_invuln_timer > 0`). |
| `combat/provenance.py` :: `"LEDGE_INVULN_BASE_FRAMES"` Provenance + register list | `invuln` / `intangib` | Sourcing record: 21f = PM 3.6 CliffCatch (FOUND, #683). |

## Mechanic bucket 2 — Air-dodge / spot-dodge / roll-dodge

These share the generic `invulnerable` flag + `dodge_timer` (no dedicated timer of their own;
the flag is dropped when `dodge_timer` hits 0).

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `entities/fighter.py` :: `Fighter._start_dodge` | `invulnerable` | Arms `dodge_timer = DODGE_TIME` and sets `invulnerable = True` for spot/roll/air dodge. |
| `entities/fighter.py` :: dodge-end branch (`dodge_timer == 0` → `invulnerable = False`) | `invulnerable` | Drops the flag and zeroes `dodge_timer` when the dodge ends. |
| `entities/player.py` :: `Player.update` dodge tail (`invulnerable = False # reset invulnerability after dodge ends`) | `invulnerable` | Player-side clear of the dodge flag. |
| `sim/showcase.py` :: roll-dodge scene (module docstring + scene label) | `intangible` | Narration: "a dodge is intangible and passes through" — P1 rolls clean through Birky. |
| `systems/combat.py` :: `check_hits` defender guard | `invulnerable` | A hit is skipped when `defender.fighter.invulnerable` — the consumer of every bucket's flag. |
| `config.py` :: `DODGE_FRAMES` | (neither term) | Dodge window length; the flag rides `dodge_timer`, noted here for completeness. |

## Mechanic bucket 3 — Getup-roll & getup-attack (knockdown / prone recovery)

Getup recovery reuses the **shared** `invulnerable` + `invulnerable_timer` machinery, plus its
own `getup_roll_timer` for duration.

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `config.py` :: `GETUP_ROLL_FRAMES` (+ header comment) | `intangib` | Roll lasts `GETUP_ROLL_FRAMES` (16) = its intangibility window. |
| `entities/fighter.py` :: `Fighter.getup_roll_timer` (init) | `intangib` | Getup-roll duration + intangibility window (#146). |
| `entities/fighter.py` :: `Fighter.start_getup_roll` | `invulnerable` / `intangib` | Sets `getup_roll_timer`, `invulnerable = True`, `invulnerable_timer = GETUP_ROLL_FRAMES`; "reuses the same invulnerable/timer machinery as the dodge". |
| `entities/player.py` :: `Player.update` getup-roll branch (`invulnerable = True # getup intangibility`) | `invulnerable` / `intangib` | Grants the flag for the roll; playtest caveat noted inline. |
| `entities/player.py` :: getup-roll end (`invulnerable = False # intangibility ends with the roll`) | `invulnerable` / `intangib` | Drops the flag when `getup_roll_timer` hits 0. |
| `entities/player.py` :: getup-attack end (`invulnerable = False # intangibility ends with the swing`) | `invulnerable` / `intangib` | Drops the flag when the getup-attack swing completes. |
| `combat/provenance.py` :: `"GETUP_ROLL_FRAMES"` Provenance + register list | `intangib` | Sourcing record: getup-roll duration = its intangibility window; DIVERGENCE from Melee noted (GUESS/tracked #65). |
| `charts/fighter_chart.py` :: getup-roll region comments | `intangib` | "Intangibility (invulnerable) is dropped … by player.update when getup_roll_timer hits 0." |

## Mechanic bucket 4 — Respawn

Respawn reuses the shared flag/timer; the census notes the field lifecycle (set on spawn,
cleared on reset).

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `entities/fighter.py` :: `Fighter.invulnerable_timer` (init comment: "post-respawn") | `invuln` | The shared timer; comment names respawn as one source. |
| `entities/fighter.py` :: `Fighter.invulnerable` (init comment: "respawn") | `invuln` | The shared bool; comment names respawn as one source. |
| `entities/fighter.py` :: `reset_to_spawn` (`invulnerable_timer = 0`, `invulnerable = False`) | `invulnerable` | Clears both fields on respawn so no state leaks into the next life. |
| `render_battle.py` :: bar-source comment ("#506 respawn") | `invuln` | Respawn is called out as a future INVULN-bar source folded into `_invuln_remaining_max`. |

## Mechanic bucket 5 — HUD / render (the `INVULN` bar + grabs-left dots)

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `render_battle.py` :: `LEDGE_REGRAB_INVULN_CUTOFF` (import) | `invuln` | Pulled in for the grabs-left dot budget. |
| `render_battle.py` :: `INVULN_BAR_COLOR` | `invuln` / `intangib` | Green bar color for the intangibility window (#358). |
| `render_battle.py` :: `GRABS_LEFT_DOT_COLOR` | `invuln` | Grabs-left dots share the INVULN green family. |
| `render_battle.py` :: `_invuln_remaining_max(p)` | `invuln` / `intangib` | Per-source resolve of the active window `(remaining, max)`; gated on `fighter.invulnerable`, suppressed while `ledge_hang`. |
| `render_battle.py` :: `ledge_invuln` bar spec (in the bar registry) | `invuln` / `intangib` | The fixed ledge-grab burst's own overlay bar; `active` on `ledge_invuln_timer > 0`, label `"INVULN"`. |
| `render_battle.py` :: `invuln` bar spec (in the bar registry) | `invuln` / `intangib` | The dodge / getup-roll / getup-attack window bar; `active` on `_invuln_remaining_max is not None`, label `"INVULN"`. |
| `render_battle.py` :: grabs-left dots helper (`LEDGE_REGRAB_INVULN_CUTOFF + 1 - count`) | `invuln` / `intangib` | Above-head dot count = remaining full-burst ledge grabs before the cutoff. |
| `render_battle.py` :: LOCKOUT/INVULN overview docstring | `invuln` / `intangib` | Describes the INVULN bar as the intangibility window (#358). |

## Mechanic bucket 6 — Defensive-status label ("intangible" vs "vulnerable")

The statechart / engines expose a string region label derived from the shared flag.

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `entities/player.py` :: `Player.defensive_status` (`"intangible" if fighter.invulnerable else "vulnerable"`) | `intangib` | The engine-free label computed straight off the `invulnerable` bool. |
| `charts/fighter_chart.py` :: defensive_status region (`_tick(... p.fighter.invulnerable, "intangible")` / `"vulnerable"`) | `invulnerable` / `intangib` | Chart region flips intangible/vulnerable off the same bool; "Intangibility reuses `invulnerable`". |
| `charts/fighter_chart.py` :: state tree comment (`└── intangible (leaf)`) + `{"id": "intangible"}` | `intangib` | The intangible leaf node in the defensive-status region. |
| `systems/state_engine.py` :: defensive-status comment ("directly from Player.invulnerable") | `invulnerable` | Legacy engine derives the label from the bool. |
| `systems/state_engine_sc.py` :: `defensive_status` (`in_state("intangible")`) | `intangib` | Statechart-session engine derives the label from the `intangible` state. |

## Mechanic bucket 7 — Sim serialization (debug/replay fields)

| File + symbol | Term used | What it currently governs |
|---|---|---|
| `sim/runner.py` :: frame-record field list (`… invulnerable_timer … invulnerable defensive_status …`) | `invulnerable` | Serializes the shared timer + bool + label into the per-frame sim record. |
| `sim/runner.py` :: record population (`p.fighter.invulnerable_timer`, `p.fighter.invulnerable`) | `invulnerable` | Reads both shared fields into the frame tuple. |

---

## Cross-cutting observations (facts, not verdicts)

1. **Two storage mechanisms, not one.** The ledge burst has dedicated fields
   (`ledge_invuln_timer` / `ledge_invuln_granted`); every other bucket (dodge, getup,
   respawn) shares the single `invulnerable` bool and `invulnerable_timer`. The HUD renders
   them as **two** separate `INVULN` bars (`ledge_invuln` and `invuln`), mutually suppressed
   during a hang.
2. **One consumer.** Exactly one place *acts* on immunity: `systems/combat.py`
   `check_hits` skips a defender when `fighter.invulnerable` is true. Every bucket's effect
   flows through that single gate. (Whether "skip the hit" models intangibility or
   invulnerability is the child-(ii) question.)
3. **Vocabulary is already mixed at every site.** The same `invulnerable` flag is described
   as "invulnerability" in `fighter.py` and as "intangibility" in `player.py`,
   `fighter_chart.py`, and the `defensive_status` label — so the term at a site does **not**
   currently indicate the mechanic. The census keys on the field read/written, not the word.
4. **Provenance registry coverage.** Only two immunity constants carry a `Provenance`
   record: `LEDGE_INVULN_BASE_FRAMES` (FOUND, #683) and `GETUP_ROLL_FRAMES` (GUESS, #65).
   `DODGE_FRAMES`, `LEDGE_REGRAB_INVULN_CUTOFF`, and the respawn window are not registered
   under these terms here.

## Docs & tests (noted separately — not part of the code census)

Per the ticket, doc/test usages are recorded as an aggregate, not row-by-row:

- **Docs:** 49 files under `docs/` mention `invuln`/`intangib`. Primary homes are
  `docs/glossary.md`, `docs/pm-reference/ledge-regrab-intangible-and-display.md`,
  `docs/pm-reference/ledge-mechanics.md`, `docs/pm-reference/defense-shield-dodge.md`,
  `docs/research/2026-07-04-invuln-timer-state-model.md`,
  `docs/research/2026-07-05-pm-ledge-intangibility-basis.md`, and
  `docs/research/2026-07-07-custom-mechanics-inventory.md`; the rest are learnings/plans/specs.
- **Tests:** 28 files under `tests/` reference the terms. The ones named directly for a
  bucket above: `test_ledge_invuln_bar.py`, `test_ledge_regrab_cutoff.py`,
  `test_ledge_hang.py`, `test_dodge_mechanics.py`, `test_air_dodge_helpless.py`,
  `test_air_dodge_shield_physics.py`, `test_spot_dodge_input_order.py`, `test_prone.py`,
  `test_respawn_timers.py`, `test_respawn_clears_damaged_state.py`, `test_status_registry.py`,
  `test_status_timer_bar.py`, `test_grabs_left_dots.py`, `test_fighter_chart.py`,
  `test_edge_hog.py`, `test_ai_edge_hog_selfko.py`.

## What this census deliberately does NOT do

- **No** verdict on which usages should be intangibility vs invulnerability → child (ii) #774.
- **No** proposed renames or remodel → architect child #775.
- **No** code change → DEV child #776.

## Refs

Child of #772. Companion: canon-mapping child (ii) #774. Origin: #754 / #771.
