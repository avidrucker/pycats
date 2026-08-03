# Move → source-subaction mapping audit — completeness across all playable cats

**Ticket:** #1149 (`wayfinder:research`, child of the datamined per-hitbox move data map #1147).
**Date:** 2026-08-02 · **Agent:** CHERRY · **Type:** read-only audit (no code change).

**Question:** For every playable cat, which defined moves are mapped to a source subaction
in the editor's `gif_map`, and which are unmapped — so the downstream datamine migration
knows what still needs a mapping before its per-hitbox data can be pulled.

## Sources read (all primary, local)

- Roster: `pycats/characters/roster.py` — `ARCHETYPE_ROSTER = ("nalio", "birky", "narz", "gnok")`
  (**four** playable cats, not five).
- Map data: `pycats-editor/src/pycats_editor/data/gif_map.json` + module docstring in
  `pycats-editor/src/pycats_editor/gif_map.py`.
- Source manifests: `docs/pm-reference/{mario,marth,kirby,dk}-gif-index.md`.
- Cat movesets: `pycats/characters/data/{nalio,birky,narz,gnok}.json` (`moves` object keys).

## Source-fighter mapping (from gif_map.json `source` field)

| cat | source fighter |
|-----|----------------|
| nalio | mario |
| narz | marth |
| birky | kirby |
| gnok | dk |

All four cats have a `gif_map` entry; none is deferred. The `gif_map.py` docstring's mention
of "gnok, deferred" in `source_for` is stale prose — gnok IS mapped (per #1006), and the JSON
confirms it.

---

## 1. Per-cat coverage tables

### nalio → mario (moves from nalio.json)

| move key | mapped subaction(s) | note |
|----------|--------------------|------|
| wait   | Wait1                       | ✓ |
| jab    | Attack11, Attack12, Attack13 (3-hit combo) | ✓ |
| attack | AttackLw3 (`attack.name` = "down tilt" → IS dtilt) | ✓ |
| ftilt  | AttackS3S                   | ✓ |
| utilt  | AttackHi3                   | ✓ |
| fsmash | AttackS4S                   | ✓ |
| usmash | AttackHi4                   | ✓ |
| dsmash | AttackLw4                   | ✓ |
| nair   | AttackAirN                  | ✓ |
| fair   | AttackAirF                  | ✓ |
| bair   | AttackAirB                  | ✓ |
| uair   | AttackAirHi                 | ✓ |
| dair   | AttackAirLw                 | ✓ |
| neutral_b | SpecialN                 | ✓ |
| up_b   | SpecialHi                   | ✓ |

**nalio: 15 of 15 mapped.** No unmapped moves.

### narz → marth (moves from narz.json)

| move key | mapped subaction(s) | note |
|----------|--------------------|------|
| wait   | Wait1        | ✓ |
| jab    | Attack11, Attack12 (2-hit — Marth jab, no Attack13) | ✓ |
| ftilt  | AttackS3S    | ✓ |
| utilt  | AttackHi3    | ✓ |
| dtilt  | AttackLw3    | ✓ (narz has a distinct dtilt key) |
| fsmash | AttackS4S    | ✓ |
| usmash | AttackHi4    | ✓ |
| dsmash | AttackLw4    | ✓ |
| nair   | AttackAirN   | ✓ |
| fair   | AttackAirF   | ✓ |
| bair   | AttackAirB   | ✓ |
| uair   | AttackAirHi  | ✓ |
| dair   | AttackAirLw  | ✓ |
| **attack** | **UNMAPPED** | `attack.name` = "attack" (non-standard Smash move); left unmapped by design, not guessed onto a Marth subaction |

**narz: 13 of 14 mapped.** Unmapped: `attack`.

### birky → kirby (moves from birky.json)

| move key | mapped subaction(s) | note |
|----------|--------------------|------|
| wait   | Wait1        | ✓ |
| jab    | Attack11, Attack12 (2-hit — Kirby jab) | ✓ |
| ftilt  | AttackS3S    | ✓ |
| utilt  | AttackHi3    | ✓ |
| attack | AttackLw3    | ✓ (`attack.name` = "dtilt" → attack IS dtilt, like nalio) |
| fsmash | AttackS4S    | ✓ |
| usmash | AttackHi4    | ✓ |
| dsmash | AttackLw4    | ✓ |
| nair   | AttackAirN   | ✓ |
| fair   | AttackAirF   | ✓ |
| bair   | AttackAirB   | ✓ |
| uair   | AttackAirHi  | ✓ |
| dair   | AttackAirLw  | ✓ |
| up_b   | SpecialAirHi | ✓ (Final Cutter; Kirby has no non-empty ground SpecialHi, so mapped to the aerial start) |

**birky: 14 of 14 mapped.** No unmapped moves. (birky defines no `neutral_b`.)

### gnok → dk (moves from gnok.json)

| move key | mapped subaction(s) | note |
|----------|--------------------|------|
| wait   | Wait1        | ✓ |
| jab    | Attack11, Attack12 (2-hit — DK jab, no Attack13) | ✓ |
| ftilt  | AttackS3S    | ✓ |
| utilt  | AttackHi3    | ✓ |
| dtilt  | AttackLw3    | ✓ (gnok has a distinct dtilt key) |
| fsmash | AttackS4S    | ✓ |
| usmash | AttackHi4    | ✓ |
| dsmash | AttackLw4    | ✓ |
| nair   | AttackAirN   | ✓ |
| fair   | AttackAirF   | ✓ |
| bair   | AttackAirB   | ✓ |
| uair   | AttackAirHi  | ✓ |
| dair   | AttackAirLw  | ✓ |
| **attack** | **UNMAPPED** | `attack.name` = "attack" (non-standard); left unmapped by design, mirroring narz. gnok defines no specials (no neutral_b / up_b) |

**gnok: 13 of 14 mapped.** Unmapped: `attack`.

---

## 2. Summary count per cat

| cat | source | mapped / total |
|-----|--------|----------------|
| nalio | mario | 15 / 15 |
| narz  | marth | 13 / 14 |
| birky | kirby | 14 / 14 |
| gnok  | dk    | 13 / 14 |
| **total** | | **55 / 57** |

## 3. Unmapped moves (what the datamine migration still needs a mapping for)

Only two, and both are intentional non-mappings, not gaps:

- **narz `attack`** — the `attack` MoveData whose `name` == "attack" (not a standard Smash
  move; narz already has a separate `dtilt`). Left unmapped by design (`gif_map.py` docstring).
- **gnok `attack`** — same case (`name` == "attack", separate `dtilt`). Left unmapped,
  mirroring narz (docstring, #1006).

There are **no accidental gaps**: every standard move each cat defines is mapped. The two
unmapped keys are the deliberately-unmapped `attack` placeholder that only narz and gnok
carry. (This directly feeds the "drop the legacy `attack` move-key alias" decision #1155.)

## 4. Quirks / mismatches

- **Multi-hit jab differs by source.** nalio/mario jab = 3-hit (`Attack11/12/13`);
  narz/marth, birky/kirby, gnok/dk jabs = 2-hit (`Attack11/12`, no `Attack13`). Confirmed
  against each manifest (mario has Attack13; marth/kirby/dk do not).
- **"attack IS dtilt" vs "attack is a separate placeholder."** Two distinct patterns:
  - nalio & birky have NO separate `dtilt`; their `attack` key IS the down-tilt
    (`attack.name` = "down tilt" / "dtilt") → mapped to `AttackLw3`.
  - narz & gnok have a distinct `dtilt` key (→ `AttackLw3`) PLUS an `attack` key whose
    `name` == "attack" → left unmapped.
- **Kirby Final Cutter (birky `up_b`).** Mapped to `SpecialAirHi`, not `SpecialHi` — per the
  docstring, Kirby's only non-empty Final Cutter animation in the manifest is the aerial
  start. (nalio/mario `up_b` uses the ground `SpecialHi`.)
- **Specials coverage varies.** nalio maps both `neutral_b` (SpecialN) and `up_b` (SpecialHi).
  birky maps only `up_b` (no neutral_b defined). narz and gnok define/map NO specials at all.
- **No orphan map entries.** Every move key present in each cat's `gif_map` block also exists
  in that cat's JSON `moves` — no `gif_map` entry references a move the cat doesn't define.
- **Stale docstring note.** `gif_map.py::source_for` docstring says the `None` case is
  "e.g. gnok, deferred" — gnok is no longer deferred (mapped in #1006, present in JSON).
  Cosmetic only; the code path is unaffected.
- **All mapped subactions are present in their source manifest** (string-presence check
  against `{mario,marth,kirby,dk}-gif-index.md`). The stronger "non-empty animation"
  grounding is enforced by the editor's own
  `test_e10_gif_map.py::test_every_mapped_subaction_is_a_real_manifest_animation`.
