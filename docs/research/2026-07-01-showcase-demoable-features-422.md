# Research #422 — which implemented features could the showcase demonstrate next?

**Agent:** ELDERBERRY · **Date:** 2026-07-01 · **Parent:** #421 (showcase expansion) · Epic #308. **No code — a prioritized candidate-beat list.**

## Method
Inventoried the moveset (`characters/nalio_cat.py`, `birky_cat.py`), the input→move seam (`combat/move_select.py`, `entities/fighter_input.py`), the fighter states (`entities/player.py`), and the systems (`combat/`, `config.py`). Classified each candidate by whether a **deterministic fixed-input demo can trigger it** — the same constraint that shaped #395/#398. Spot-checked aerials / air-dodge / spot-dodge by scripting them headless (all fired).

## The governing constraint: what a demo can input
A demo drives fighters through `InputSpan`s whose action is one of **`left, right, up, down, attack, shield`** (`input_script.py:13`). Move selection (`move_select.py`) maps `(direction × ground/air × A/B/smash)` to a move key. So from those six inputs a demo reaches:
- **Ground normals** — `attack` + direction: jab (neutral), ftilt (forward), utilt (up), dtilt (down).
- **Aerials** — jump, then `attack` + direction airborne: nair/fair/bair/uair/dair.
- **Dodges** — `shield` + direction (roll), `shield` + down (spot-dodge), `shield` airborne (air-dodge).
- **Movement/utility** — walk, jump, double-jump, ledge hang/getup, thin-platform drop (`down`).

But **`special` and `smash` are separate input keys** the demo model does NOT expose (`fighter_input` reads `_pressed(held, "special")` and a `"smash"` key with charge; `ACTIONS` omits both). **So specials (the fireball) and smashes cannot be scripted without extending the input model** — the single biggest enabler below.

Nalio's kit is fuller than the old "Phase 2 gated" comment implies — `moves` = jab, attack(dtilt), ftilt, utilt, nair, fair, bair, uair, dair, **neutral_b (fireball)**, fsmash, usmash, dsmash.

## Candidate beats by feasibility

### Tier 1 — scriptable now (high confidence)
| Feature | How to stage | Value | Notes |
|---|---|---|---|
| **Aerials** (nair/fair/bair/uair/dair) | jump → `attack`+dir airborne | **High** | Nalio has all 5; ✓ confirmed one fires. 1–2 beats (e.g. "fair off a jump", "dair spike"). |
| **Grounded tilts** (ftilt/utilt) | `attack`+forward / +up, grounded | Med | dtilt is the current "attack" slot; jab already shown. |
| **Air-dodge** | jump → `shield` airborne | Med | ✓ confirmed. Distinct from the roll already shown. |
| **Spot-dodge** | `shield`+down, grounded | Med | ✓ confirmed. Rounds out the defensive trio (roll shown, spot + air new). |
| **Ledge-getup variants** (roll / attack / jump) | from `ledge_hang`, add dir/attack/jump | Low–Med | Builds on #421's neutral getup. |
| **Thin-platform drop-through** | `down` on a thin platform | Med | Needs a fighter positioned on a thin platform first. |
| **Clank / priority** (#141) | both fighters `attack` with overlapping hitboxes same frame | Med | Distinctive; scriptable via Birky's spans + timing. |

### Tier 2 — scriptable but harder / needs careful two-fighter timing
| Feature | Why harder |
|---|---|
| **Edge-hog** (#311) | Needs one fighter hanging the ledge to deny the other's recovery — a 2-fighter contest; deterministic but fiddly to time. |
| **Hitstun / DI** | Happens during hits (already visible in the combo); a dedicated DI beat is subtle and low-legibility. |
| **Prone / knockdown + getup-roll** (#146) | Requires a knockdown hit (specific knockback to the floor) — hard to land deterministically with jabs. |

### Tier 3 — blocked by the input model (unlock first)
| Feature | Blocker |
|---|---|
| **Fireball / specials** (neutral_b, side/up/down_b) | No `special` action in the demo input model. **High value** (flashy, recognizable). |
| **Smashes** (fsmash/usmash/dsmash) | No `smash` action + charge in the demo input model. |

### Tier 4 — infeasible as-is / not implemented (not candidates)
- **Real KO** — jab-only cats can't launch; only a walk-off self-destruct (#395).
- **Shield-break stun** — jab whiffs on the shield bubble (#395).
- **Run / dash** — not implemented; pycats has walk only (#373).
- **Fast-fall** — not modelled (single global fall speed; provenance DIVERGENCE, #120).
- **Crouch** — unverified: `attack`/`down` crouch didn't trigger in a quick test (Nalio may lack `crouch_size`); confirm before proposing.

## Recommendation — decompose into DEV children of #421 / #308 (pending go-ahead)
Priority order (value ÷ effort):
1. **Aerials beat(s)** — Tier 1, highest value, five moves already implemented. Start here.
2. **Extend the demo input model with a `special` action** (a small tooling DEV) → then a **Fireball beat**. This is the highest-leverage enabler: it unlocks the flashiest feature and later the smashes. File the input-model extension first, the fireball beat as its child.
3. **Defensive-options beat** — spot-dodge + air-dodge (complements the shown roll).
4. **Grounded tilts beat** (ftilt/utilt).
5. **Ledge-getup variants** — builds directly on #421.
6. **Clank / priority** — distinctive, Tier 1.
7. Later, after the input-model work: **smashes** (needs `smash` + charge), **edge-hog**.

Each beat must keep the invariants this thread established: window-bound assertion (#397), dwell-on-payoff (#412), and one caption active per frame (#419).

## Key code sites
- `pycats/sim/input_script.py:13` — `ACTIONS` (the six scriptable inputs; extend here for special/smash).
- `pycats/combat/move_select.py` — input-context → move key (what each `attack`+dir reaches).
- `pycats/entities/fighter_input.py` — reads `special` / `smash` keys + smash charge (why they're not scriptable today).
- `pycats/characters/nalio_cat.py:482-486` — Nalio's full `moves` dict.
- `pycats/sim/showcase.py` — where new beats land.

Refs #421 #308 #398 #395 #397 #412 #419 #311 #141 #146 #373
