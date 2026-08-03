# Fixed-burst ledge invincibility — DEV plan (#552 spike)

> Scopes the code change for ratified decision **#543** (drop percent-scaled ledge invincibility →
> a fixed per-grab burst) so a DEV lands it in one pass. Produced by the #552 ARCH spike.
> Inputs already settled: **#543** (direction), **#671** (the datamined value), **#670/#656**
> (the separate 5-regrab cutoff — *not* this change).

## Q1 — the value: **flat 21 f** (recommended)

PM 3.6 `CliffCatch` (the ledge-grab catch action) is **fully intangible frames 1–21 (21 f)**,
**flat across every character checked** — datamined via rukaidata (runs brawllib_rs on PM 3.6):

| Character | Archetype | CliffCatch fully-intangible |
|---|---|---|
| Mario | all-rounder | 1–21 (21 f) |
| Kirby | floaty light | 1–21 (21 f) |
| Fox | fastfaller | 1–21 (21 f) |
| Bowser | superheavy | 1–21 (21 f) |
| Jigglypuff | floaty lightest | 1–21 (21 f) |
| Ganondorf | heavy | 1–21 (21 f) |

Six characters spanning the weight/fall spectrum all read **21 f** → the value is a **flat
constant, not per-character**. (Sourced in #671; first two chars there, four more added by this
spike.)

**Recommendation:** fixed burst = **21 f**, model = **flat constant**, provenance = **FOUND**
(basis: rukaidata PM 3.6 `CliffCatch`, #671). This is a **−2 f change** from the current
`LEDGE_INVULN_BASE_FRAMES = 23` (a Brawl baseline). PM canon is PM 3.6, so 21 is the faithful
value; #671 is the data citation that satisfies RULES "Changing values."
**Fallback:** keep **23** (already FOUND, Brawl-derived) if the owner prefers no behaviour change —
but 21 is the PM-3.6-sourced value.

pycats models the grab burst as a single `ledge_invuln_timer`, so PM's 21 f `CliffCatch` window
maps **directly** to it — no structural change.

## Q2 — edge-hog / AI test blast radius (small, localized)

Only **`tests/test_edge_hog.py` Piece 1** asserts the percent-scaling. Everything else survives.

**Breaks — must change (2 tests + 2 lines):**
- `test_ledge_invuln_frames_monotonic_and_bounded` — its premise (monotonic scaling between BASE
  and a cap) is gone. **Rewrite** to assert `ledge_invuln_frames()` returns the constant 21.
- `test_higher_percent_grants_longer_ledge_invuln_window` — asserts the *removed divergence*.
  **Delete**, or invert to `test_percent_does_not_change_ledge_invuln_window` (low % vs high % →
  equal).
- `ledge_invuln_frames(10_000) == LEDGE_INVULN_MAX_FRAMES` (in the monotonic test) and the
  `<= LEDGE_INVULN_MAX_FRAMES` bound (~L85) — **`MAX` is retired**, both references break; drop them.

**Survives — no change needed (verified):**
- `test_hog_denies_grab_while_occupant_invincible` / `test_hog_grab_succeeds_and_evicts_once_invuln_lapses`
  (Piece 2) set `percent = 100` only to get *some* invuln > 0 — a fixed 21 f still grants that, so
  the assertions hold. Only the stale `# long invuln burst` comment should be corrected. The
  `range(ledge_invuln_frames(0) + N)` count-down loops still work (see signature note).
- **All four AI tests** (`test_ai_edge_hog`, `test_ai_edge_hog_selfko`, `test_ai_recovery`,
  `test_ai_edge_guard`) are **golden-safe by design**: edge-hog is off in the level-less golden
  path ("passing ledges must never change its output"), and none assert on the window.
  `test_ai_edge_hog_selfko` only zeroes `ledge_invuln_timer` as setup.

**#311 hog timing still holds:** a hog is denied while `ledge_invuln_timer > 0` — gated on the
*presence* of the burst, not on it being percent-longer. A fixed 21 f window gates hog timing
identically (a constant duration instead of a percent-dependent one).

## Q3 — RESOLVED (out of scope)

The 5-regrab anti-plank mechanic is a **count cutoff**, ratified **#670**, filed **#656** (residual
pinned by #671). Not this change. **Coordination note:** #656 also edits the grab site in
`Player.update`, so sequence — **land this DEV first** (smaller, foundational: the fixed window),
then #656 builds the cutoff on top.

## Q4 — provenance-registry deltas

`ledge_invuln_frames` is percent-scaled today: `BASE + round(percent·PER_PERCENT)`, capped `MAX`.
Reducing to a constant retires two constants.

- **`pycats/config.py`** (`LEDGE_INVULN_*` block): `LEDGE_INVULN_BASE_FRAMES` `23 → 21`;
  **delete** `LEDGE_INVULN_PER_PERCENT` and `LEDGE_INVULN_MAX_FRAMES`.
- **`pycats/combat/provenance.py`**: update the `LEDGE_INVULN_BASE_FRAMES` `Provenance` row
  (value `21`, basis `"PM 3.6 CliffCatch intangibility 1–21, rukaidata (#671)"`, tag `FOUND`,
  issue `552`); **delete** the `LEDGE_INVULN_PER_PERCENT` + `LEDGE_INVULN_MAX_FRAMES` entries;
  **remove both names** from the `TUNING_CONSTANT_NAMES` enforced-names list.
- **`docs/project-m-rules-by-category.md`** (the #635 manifest gate): the `Ledge` row for
  `LEDGE_INVULN_BASE_FRAMES` shows `= 23` — update to `= 21`; and the **"Flagged discrepancy (→
  #536)" note** about the `PER_PERCENT`/`MAX` compound is now obsolete (those constants are gone) —
  remove/replace it.

**Gates that will red if a step is missed** (`tests/test_tuning_provenance.py`):
`test_no_drift_registry_value_matches_config` (value must match config), `test_no_orphans...`
(registry keyset must equal `TUNING_CONSTANT_NAMES` — remove from **both**),
`test_every_curated_constant_exists_in_config`, and `test_manifest_status_matches_registry`
(#635 — the manifest `Constant`/status must agree).

## Q5 — sim-golden scope

**No golden regen expected.** The window feeds no golden sim path — the AI edge-hog behaviour is
golden-safe/off (level-less controllers don't seek ledges), so no recorded match hangs on a
percent-dependent window. The DEV **runs the full suite** to confirm; any golden shift would be
cleanly attributable to the 23→21 length change. (Full suite is green as of this spike.)

## Q6 — consumer interaction (#658, not #531)

A fixed burst makes `ledge_invuln_frames()` a **constant**, so the per-grab `ledge_invuln_granted`
stored at the grab site (#531) is always that constant. For **#658** (the frame-dots ticket that
superseded #531's bar), the dots' denominator is a constant — simpler than the stored-per-grab
value #538 recommended for the divergent model. Note it there; no action in this DEV.

## Signature note

`ledge_invuln_frames(percent)` should **drop the `percent` param** (a constant needs none) →
`def ledge_invuln_frames() -> int: return config.LEDGE_INVULN_BASE_FRAMES`. Call sites to update:
`Player.update` grab (`pycats/entities/player.py`, drop `self.fighter.percent`) and the ~4 calls in
`tests/test_edge_hog.py`. (Optional cosmetic: rename `LEDGE_INVULN_BASE_FRAMES` → `LEDGE_INVULN_FRAMES`
since it is no longer a "base" — but that ripples into provenance + the manifest `Constant` column,
so it is a low-value nicety; keeping the name is fine.)

## Ordered DEV steps

1. `config.py` — `LEDGE_INVULN_BASE_FRAMES = 21`; delete `LEDGE_INVULN_PER_PERCENT`, `LEDGE_INVULN_MAX_FRAMES`.
2. `entities/ledge.py` — `ledge_invuln_frames()` returns the constant (drop the percent arg + scaling/cap).
3. `entities/player.py` — grab site → `ledge_invuln_frames()`.
4. `combat/provenance.py` — update the surviving `LEDGE_INVULN_BASE_FRAMES` row; delete 2 entries; remove 2 names from `TUNING_CONSTANT_NAMES`.
5. `docs/project-m-rules-by-category.md` — update the `= 23` → `= 21` cell; remove the obsolete percent-scaling discrepancy note.
6. `tests/test_edge_hog.py` — rewrite the 2 Piece-1 scaling tests; drop the `MAX` references; adapt the `ledge_invuln_frames(...)` call sites; fix the stale `# long invuln burst` comment.
7. Grep `LEDGE_INVULN_PER_PERCENT` / `LEDGE_INVULN_MAX_FRAMES` repo-wide (docs strays: `parity-status.md`, `ledge-mechanics.md`) and reconcile.
8. `ruff format` + full suite; confirm green + no golden regen.

## File list (DEV)
`pycats/config.py` · `pycats/entities/ledge.py` · `pycats/entities/player.py` ·
`pycats/combat/provenance.py` · `docs/project-m-rules-by-category.md` · `tests/test_edge_hog.py`
(+ doc strays per step 7).

## Split recommendation: **ONE DEV**
Single cohesive change (2 source modules + config + provenance + 1 manifest doc + 1 test file); no
independent deliverables to separate. **Sequence before #656** (both touch the `Player.update` grab
site). Estimate ~30–40m.

## Ready-to-file DEV (proposed)

- **Title:** `DEV(entities): drop percent-scaled ledge invincibility → flat 21f fixed burst (#543)`
- **Labels:** `enhancement, area:entities, v1`
- **Basis:** #543 (direction) + #671 / this plan (value 21f, FOUND). Cites this doc for the seam map.
- **Body:** the ordered steps + file list + acceptance (the 2 rewritten tests are able-to-fail;
  provenance gates green; full suite green; no golden regen) from this plan.

## Cross-refs
Spike **#552**; direction **#543**; value source **#671** (+ audit **#536**); cutoff **#670/#656**
(sequence before); consumer **#658**; divergence origin **#311**; provenance ADR-0003 + #233/#635;
parity docs `docs/pm-reference/ledge-mechanics.md`, `docs/project-m-rules-by-category.md`.
