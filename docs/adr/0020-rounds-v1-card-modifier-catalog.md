# ADR-0020 — ROUNDS v1 card-modifier catalog: file format + home

## Status

Accepted — 2026-08-04. Resolves the **ROUNDS Mode v1 wayfinder map** (#1096) decision
#1178 ("decide the card-modifier catalog file format + home for ROUNDS v1"). Downstream of
**ADR-0013** (per-seam modifier shapes), **ADR-0014** (the modifier apply-layer), and
**ADR-0019** (the Leech card family, which affirmed the "tweakable data file" direction but
left the file itself unspecified); epic #347.

## Context

ROUNDS v1's card modifiers must be **authored in a tweakable data file**, not hardcoded — a
direction affirmed in ADR-0019 and consistent with ADR-0014's apply-layer (which reads each
drafted card's bare `(seam, op, value)` deltas and patches `FighterData` once at
`build_fighter`). ADR-0019 deliberately left the *file itself* unspecified because it is a
**cross-card** concern spanning all 9+ starter cards (#1101), not the Leech family alone. This
ADR fixes the catalog's format + home by grilling the designer through #1178's five forks.

Grounding facts, read from source 2026-08-04:

- **Two JSON-data shapes already exist in the repo.** Per-entity fighter stats live one file
  per cat at `pycats/characters/data/<cat>.json` (`nalio`, `narz`, `birky`, `gnok`, `default`),
  loaded by `combat/data.py`. A **cross-cutting** concern instead lives in one shared file:
  `pycats/characters/palettes.json` (all palettes together). Cards are cross-cutting (one pool
  any fighter drafts), so they follow the `palettes.json` shape, not the per-cat shape.
- **The apply-layer is settled** (ADR-0014): a modifier is a bare `(seam, op, value)` record
  where `op` is one of ADR-0013's two fixed operations (`mult_pct` / `add_n`); active state is
  the drafted `list[Card]`; a pure `card → [Modifier]` function derives the deltas; effective
  stats are `apply(baseline_FighterData, all_derived_deltas) → new FighterData`, recomputed
  once per round at the `loadout/build_fighter.py::build_fighter` seam.
- **The Leech knobs are new `FighterData` fields** (ADR-0019): `lifesteal_fraction` (Vampire
  sets ~0.3) and `regen_rate` + its interval (Health Regen); the interval N and heal-chunk are
  "tunable config authored in the modifiers file."
- **The draw rule needs per-card stackability** (#1103): valid draw = *all stackable* ∪
  *unowned once-only*; all starter cards stack except **Metal**. Stacking *magnitude* / cap is
  deferred to #1156.

## Decision

### 1. Home — one shared file, `characters/data/cards.json`

The whole v1 card pool lives in **one** file, `pycats/characters/data/cards.json`, beside the
per-cat data files. Cards are a cross-cutting draft concept (not per-fighter entities), so they
follow the `palettes.json` precedent (one shared file), not the per-cat `<cat>.json` precedent.
Rejected: per-card files (cards aren't per-fighter entities — 9+ files, more churn, no locality
gain) and a Python module (loses the "tweakable data file" direction ADR-0019 affirmed).

### 2. Schema — one uniform card shape, Leech knobs are ordinary deltas

Every card, with no exceptions, is:

```json
{
  "id": "glass_cannon",
  "name": "Glass Cannon",
  "deltas": [
    {"seam": "damage", "op": "mult_pct", "value": 25},
    {"seam": "weight", "op": "add_n",    "value": -8}
  ],
  "stackable": true
}
```

- `id` — stable string key (draft + catalog lookups reference it, never the display `name`).
- `name` — human display label.
- `deltas` — a list of ADR-0014 modifiers: `seam` names an ADR-0013 seam, `op` is one of the
  two fixed ops (`mult_pct` / `add_n`), `value` is the magnitude. The apply-layer consumes this
  tuple verbatim — **zero new apply machinery**.
- `stackable` — see §5.

**The Leech knobs use the same delta shape — no rider block.** `lifesteal_fraction`,
`regen_rate`, and `regen_interval` are new `FighterData` fields defaulted off (0), so each is
set by an ordinary `add_n` delta off its default:

```json
{ "id": "vampire", "name": "Vampire",
  "deltas": [ {"seam": "lifesteal_fraction", "op": "add_n", "value": 0.3} ],
  "stackable": true }

{ "id": "health_regen", "name": "Health Regen",
  "deltas": [ {"seam": "regen_rate",     "op": "add_n", "value": 2},
              {"seam": "regen_interval", "op": "add_n", "value": 21} ],
  "stackable": true }
```

A card-specific `over_time` rider block (Option B) was rejected: it would fork the schema into
two shapes and force the apply-layer to special-case riders. One uniform shape honors the map's
**decomplect** preference — each atomic seam decided on its own; a card is a later composition.

### 3. Magnitudes — structure here, values by-feel at build

This ADR fixes only the file's **structure** (home, schema, keys, field names, load path,
stackability). The actual **numbers** — each `value`, `lifesteal_fraction`, `regen_rate`,
`regen_interval`, and the heal-chunk — are **picked by feel by the DEV who authors
`cards.json`** and re-tuned in the post-v1 balancing pass (#1156). The values shown above are
**illustrative, non-normative** — they make the format read concretely and fix nothing. Values
are not blocked on #1156; #1156 owns only revisiting them later.

### 4. Load path — read once into a cached catalog, at `loadout/cards.py`

- A **`load_cards()`** loader (new module **`loadout/cards.py`**, housing `load_cards()` + the
  `Card` dataclass) reads `characters/data/cards.json` **once** into an in-memory
  `dict[card_id → Card]`, cached like the existing JSON-data loads. Not re-read per round.
- The **draft** (#1103) draws / selects card **ids** against that catalog.
- The **`build_fighter` seam** (ADR-0014) runs the `card → [Modifier]` derivation on each
  drafted card's `deltas`; `apply(baseline, deltas)` patches `FighterData` once per round.
- **`over_time.py`** reads `regen_rate` / `regen_interval` off the patched `FighterData`.

**Module home rationale:** the data file lives in `characters/data/` for locality with the
other JSON, but the `Card` model + loader are a **loadout** concern (they feed the ADR-0014
apply-layer at `build_fighter`, already in `loadout/`), so the code sits in `loadout/cards.py`
beside its one consumer — the dependency arrow points one way (`loadout` reads
`characters/data/`). Rejected: folding into `combat/data.py` (that loads per-cat fighter
*stats*; cards are cross-cutting, not fighter data) and a `characters/`-side loader (cards
aren't a character).

**Determinism:** the file is static data read once — no RNG, no per-frame or per-round file
I/O. The draft's only randomness is the #1099 seeded draw stream (card *selection*), never the
catalog. The byte-identical ordinary-vs-seeded golden property holds.

### 5. Stackability — a single `stackable` boolean per card

Each card carries **one** `stackable` boolean in `cards.json`, next to its `deltas` (a card's
stackability is a static property of the card, so it lives with the card):

- `stackable: true` → drawable any number of times (the 8 others).
- `stackable: false` → drawable only while unowned — the "once-only" case (**Metal**).

Draw filter (#1103): a card is drawable iff **`stackable OR not owned`**. In v1, Metal is both
the sole non-stacker and the sole once-only card — the same card, so the same axis — so one
boolean captures it fully. Two independent flags (`stackable` + `once_only`) were rejected:
they invent contradictory states (`stackable:true, once_only:true`) for no v1 payoff. If a
post-v1 card ever needs once-only-*and*-stackable to come apart, the second field is added then
(YAGNI). Stacking **magnitude** / cap stays deferred to #1156 — this boolean answers only "may
I hold two?".

## Consequences

- The card-catalog DEV build + the ADR-0014 apply-layer implementation are unblocked: the DEV
  authors `characters/data/cards.json` (by-feel magnitudes), builds `loadout/cards.py`
  (`load_cards()` + `Card`), and wires `card → [Modifier]` at `build_fighter`.
- **Flagged complection — a DEV `/decomplect` checkpoint.** §2's uniform-delta choice puts
  `regen_rate` / `regen_interval` into `FighterData` as fields even though they are over-time
  *timing* config, not fighter *stats*. This is a deliberate uniformity-over-purity trade (one
  delta shape, zero apply-layer special cases), bounded to two fields. It is the seam most worth
  a decomplection lens — but that lens is far more useful against the **actual `over_time.py` +
  `FighterData` code** than against this schema, so the DEV ticket that builds `over_time.py`
  should run `/decomplect` on this seam and decide whether the timing knobs stay `FighterData`
  fields or move behind an over-time config object.
- No values are fixed here; a green suite after the DEV lands proves the format loads, not that
  the magnitudes feel right (that is #1156 + playtest).

## Follow-up

- Downstream DEV children (post-map, one at a time, under epic #347): author
  `characters/data/cards.json`; build `loadout/cards.py` (`load_cards()` + `Card`); wire the
  `card → [Modifier]` derivation at `build_fighter`; run `/decomplect` on the
  `regen`-fields-in-`FighterData` seam when `over_time.py` is built.
- Magnitudes / intervals / stacking-cap: **#1156** (post-v1 balancing).

## Relationships

- Resolves **#1178** (card-modifier catalog file format + home), a child of the **ROUNDS Mode
  v1 wayfinder map** (#1096), epic **#347**.
- Downstream of **ADR-0013** (per-seam modifier shapes), **ADR-0014** (the apply-layer that
  consumes the `deltas`), and **ADR-0019** (the Leech family that affirmed the tweakable-file
  direction and defines `lifesteal_fraction` / `regen_rate`).
- Serves the starter set **#1101** (the 9+ v1 cards this file holds) and the draft/draw rule
  **#1103** (which reads the `stackable` boolean).
- Coordinates with **#1156** (post-v1 balancing — the by-feel magnitudes this file's structure
  hosts) and the #1099 seeded draw stream (the draft's only randomness — the catalog is static).
- Grounded in: `characters/data/<cat>.json` + `characters/palettes.json` (the two JSON-data
  precedents), `combat/data.py` (the existing per-cat loader), `loadout/build_fighter.py` +
  `loadout/resolvers.py` (the apply seam), `entities/fighter.py` (seam caching + the Leech
  fields' home).
