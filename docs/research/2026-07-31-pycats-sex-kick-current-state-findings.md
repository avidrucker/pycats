# Findings — what pycats currently implements for the sex-kick / lingering-aerial mechanic

> **Ticket:** #890 (RESEARCH, `area:combat`). **Date:** 2026-07-31. **Agent:** GRAPE.
> **Canon yardstick:** #889 findings
> ([`2026-07-31-sex-kick-clean-late-window-findings.md`](./2026-07-31-sex-kick-clean-late-window-findings.md)).
> **Hit-count authority:** #879
> ([`2026-07-28-same-move-window-rehit-findings.md`](./2026-07-28-same-move-window-rehit-findings.md))
> + the #883 ruling (B-full, deferred to #888). **Status:** audit — no code change.
> Feeds **#893** (the "no sex-kick mechanic in V1?" scope decision).

## Question

Given #889's canon spec (a lingering "sex kick" = one set overwritten early→late,
damage always drops, angle/knockback change per-move, one hit per target), what does
pycats **actually implement** today? Four facets: (1) inventory of two-window early/late
moves, (2) whether clean/late power falloff matches #889, (3) the hit-count state, and
(4) provenance — was this mechanic ever approved for V1?

## Answer (short)

**pycats reproduces the canon clean/late *power falloff* faithfully, and the two-window
early/late structure is far more pervasive than the three moves #890's ticket names.**
A programmatic sweep of every playable cat found **~15 moves** carrying an early/late
window pair; of these, **five are genuine lingering-aerial "sex kicks"** by #889's shape
(`nalio bair`, `nalio uair`, `birky nair`, `birky bair`, plus the borderline `birky uair`),
and several ground tilts/smashes carry the same contiguous damage-falloff shape.

For the two aerials that map directly onto #889's datamined exemplars, the falloff
matches **exactly**:

| pycats move | #889 canon exemplar | Clean → late | Match |
|---|---|---|---|
| `nalio bair` | Mario bair (+angle+KB) | dmg 11→9 · ang 28→361 · bkb 43→20 · kbg 65→100 | **exact** |
| `birky nair` | Kirby nair (+base-KB) | dmg 12→9 · ang 55 · bkb 15→0 · kbg 100 | **exact** |

The **damage-only** profile (canon Mario nair) also appears — `nalio uair` (11→10, all
else equal). So pycats faithfully implements #889's central finding that **falloff is
per-move, not a fixed constant** — each move authors its own clean/late values.

**The one divergence is hit count, and it is the already-known #879/#883 issue.** Every
*contiguous* two-window move double-hits a stationary target (clean **and** late both
land), because the resolution model (#204) spawns a separate `Attack` per window with no
per-target hit-ID shared across them. This is grounded below by live simulation. The fix
is **B-full**, ruled in #883 and deferred to **#888** — not re-litigated here.

**One finding that widens the picture: the divergence footprint is broader than #879's
DIVERGENCE table recorded.** #879 named `_BIRKY_NAIR`, `_BIRKY_UTILT`, `_NALIO_BAIR`.
The sweep shows the same contiguous-window double-hit also affects `_BIRKY_BAIR`,
`_NALIO_UAIR`, and the contiguous ground smashes/tilts — a dozen moves, not three. #888's
scope should account for all of them.

## Method (how this was audited — execution-grounded, not memory)

1. **Inventory** — loaded each playable archetype via `load_fighter_data(<cat>)` and
   introspected every `MoveData.hitboxes`, grouping by `(active_start, active_end)` to
   count temporal windows and read per-window damage / angle / bkb / kbg / set_knockback.
   This is the live data (JSON-backed cats deserialize through the same path), not a
   reading of the `.py` literals.
2. **Falloff match** — compared each two-window aerial's clean/late values against #889's
   datamined table.
3. **Hit count** — read the resolution model (`pycats/systems/combat.py` `process_hits`,
   `pycats/combat/move_clock.py`) to confirm the per-window `Attack` spawn + per-`Attack`
   dedup, then **drove five moves through the real `Player.update` + `process_hits` loop**
   against a stationary defender and counted percent applications.
4. **Provenance** — searched the issue tracker (`gh issue list --search "sex kick"`) and
   read the authoring comments in `birky_cat.py` / `nalio_cat.py`.

## Facet 1 — Inventory (canon → pycats)

Every playable-cat move with an early/late window pair (or an explicit `rehit_rate`).
"Contiguous" = the late window starts on the frame after the clean window ends (the
sex-kick overwrite shape); "gapped" = a frame gap between windows (two distinct hits).

| Cat.move | Air? | Windows | Clean → late (dmg · ang · bkb · kbg) | Shape | Class |
|---|---|---|---|---|---|
| `nalio.bair` | air | f6-8 / f9-17 | 11·28·43·65 → 9·**361**·20·100 | contiguous | **sex kick** (+angle+KB) |
| `nalio.uair` | air | f4-5 / f6-9 | 11·55·0·100 → 10·55·0·100 | contiguous | **sex kick** (damage-only) |
| `birky.nair` | air | f3-6 / f7-29 | 12·55·15·100 → 9·55·**0**·100 | contiguous | **sex kick** (+base-KB) |
| `birky.bair` | air | f6-8 / f9-20 | 14·361·10·100 → 10·361·**0**·100 | contiguous | **sex kick** (+base-KB) |
| `birky.uair` | air | f10-12 / f13-15 | 15·75·5·115 → 12·30·**10**·90 | contiguous | juggle (dmg falls, bkb **rises**) — borderline |
| `birky.utilt` | grnd | f4-5 / f6-10 | 8·92·40 → 6·88·40 | contiguous | ground clean/late (dmg+angle) |
| `birky.fsmash` | grnd | f8-14 / f15-17 | 15·38·40 → 13·73·25 | contiguous | ground clean/late |
| `birky.usmash` | grnd | f6-8 / f9-13 | 15·88·30 → 13·70·12 | contiguous | ground clean/late |
| `birky.dsmash` | grnd | f4-10 / f11-18 | 14·… → 10-12·… | contiguous | ground clean/late (front+back) |
| `nalio.usmash` | grnd | f3-4 / f5-6 | 15·83·32 → **16**·259·35 | contiguous | two-part smash (dmg **rises**) — not a sex kick |
| `nalio.dsmash` | grnd | f3-4 / f12-13 | 16·361 → 10-12·361 | **gapped** | two-hit dsmash (front+back) |
| `narz.dsmash` | grnd | f6-7 / f13-14 | 12-15·361 → 10-13·361 | **gapped** | two-hit dsmash |
| `gnok.jab` | grnd | f3-6 / f10-14 | 4·65·1 → 6·75·40 | **gapped** | jab1/jab2 (separate hits) — correct multihit |
| `nalio.fair` | air | f16-17 / f18-22 | 16-17·60 → 15·**280** | contiguous | two-part fair (hit + down-angle finisher) |
| `nalio.dair` | air | rehit_rate 4 | 3 → 2 (WDSK drag) | looping | intentional multihit — correct |
| `birky.fair` | air | f7-8 / f14-15 / f22-24 | 5·drag / 5·drag / 7·361 | **gapped** ×3 | intentional multihit — correct |
| `birky.dair` | air | rehit_rate 3 | 3·270 (loop) | looping | intentional multihit — correct |

**Verdict — inventory.** The mechanic is **implemented and widespread**, not confined to
the three moves the ticket lists. Genuine lingering-aerial sex kicks: `nalio bair`,
`nalio uair`, `birky nair`, `birky bair` (+ borderline `birky uair`). The gapped and
`rehit_rate` moves are **intentional multihits** and are correct (they match #879's
"separate subactions / explicit rehit" category).

## Facet 2 — Power falloff vs #889 (does pycats match canon?)

**Yes, and per-move as #889 requires.** Damage always drops in every sex-kick-classed
move (12→9, 11→9, 14→10, 11→10). Angle/knockback vary per move exactly as #889 found:

- **`nalio bair` ≡ canon Mario bair** — the full launcher→poke transition: clean is a
  28° KO angle with high base knockback (bkb 43, kbg 65), late collapses to the Sakurai
  angle (361) weak poke (bkb 20, kbg 100). Values match #889's datamined table field for
  field. This is #879's `_NALIO_BAIR` exemplar.
- **`birky nair` ≡ canon Kirby nair** — angle held (55°), base knockback zeroed late
  (15→0), damage 12→9. Matches #889.
- **`nalio uair`** — the **damage-only** profile (#889's canon Mario-nair shape): 11→10,
  angle/bkb/kbg identical across windows.
- **`birky bair`** — its own profile (damage 14→10 + base-KB 10→0, Sakurai both windows),
  sourced from rukaidata Kirby AttackAirB per its authoring comment. Not one of #889's
  three datamined exemplars, but structurally a valid sex kick.

**Verdict — falloff:** **IMPLEMENTED / canon-faithful.** pycats reproduces #889's core
finding (falloff is per-move; damage always drops; angle/KB change for some moves and not
others). The two moves that map to #889 exemplars match exactly.

## Facet 3 — Hit count (the known divergence; grounded, not re-litigated)

**pycats double-hits a stationary target on every contiguous two-window move.** This is
the #204 model: `MoveClock` emits one spawn per temporal window (`test_temporal_windows.py`
`test_two_windows_become_two_separate_attacks_via_player_update`), and `process_hits`
dedups **per `Attack`** only — an `Attack` sets `active = False` after its one hit
(`pycats/systems/combat.py`, `process_hits`, the `# only one hit allowed` branch), with
no per-target hit-ID shared across a move's windows. So clean and late are two independent
`Attack`s and both land.

Grounded by driving each move through the real update + `process_hits` loop against a
stationary defender (script in "How this was produced"):

```
birky.nair : 2 hit(s)  [(f3, 12), (f16, 9)]   total 21%   ← clean 12 + late 9
nalio.bair : 2 hit(s)  [(f6, 11), (f18, 9)]   total 20%   ← clean 11 + late 9
birky.bair : 2 hit(s)  [(f6, 14), (f19, 10)]  total 24%
nalio.uair : 2 hit(s)  [(f4, 11), (f15, 10)]  total 21%
birky.utilt: 2 hit(s)  [(f4,  8), (f14,  6)]  total 14%
```

Canon (#889 + #879) is **one** hit per target — clean *or* late, never both. The
per-window damage that lands (12 then 9, etc.) confirms the authored falloff is intact;
it is only the **count** that diverges.

**Verdict — hit count:** **DIVERGENT (known).** Model = B-full, ruled #883, deferred
post-V1 to **#888**. Not re-litigated here — but see the footprint note.

### Footprint note (new to this audit)

#879's DIVERGENCE table named three moves (`_BIRKY_NAIR`, `_BIRKY_UTILT`, `_NALIO_BAIR`).
The sweep shows the *same* contiguous-window double-hit also affects **`_BIRKY_BAIR`,
`_NALIO_UAIR`, `_BIRKY_UAIR`, `_BIRKY_FSMASH`, `_BIRKY_USMASH`, `_BIRKY_DSMASH`** (and
`_NALIO_USMASH`, though that move's damage *rises* clean→late so it reads more like a
two-part smash than a sex kick). #888's B-full change touches all contiguous two-window
moves, so its scope and its regression tests should enumerate the full ~dozen, not three.

## Facet 4 — Provenance (was the mechanic approved for V1?)

**No mechanic-level design/decision ticket exists.** The sex-kick clean/late falloff rode
in through individual DEV **move slices**, each sourcing its own values from rukaidata and
approximating per #120, with no decision that "pycats has a sex-kick mechanic":

- `nalio bair` — DEV **#209** ("Nalio b-air … clean→Sakurai late sex-kick"), under the
  Nalio moveset slices (#123 family). The authoring comment literally calls it a sex kick.
- `birky nair` / `birky utilt` / `birky bair` — DEV slices **#255 / #249 / #258** under
  the Birky archetype umbrella **#228**.

The only *decision* tickets in this area are **#883** (hit-count authoring model only —
B-full) and the pending **#893** (scope). #889 supplied the canon spec after the fact.
So: the *falloff* mechanic is unratified-but-canon-faithful; only its *hit-count* half was
ever put to a decision.

**Verdict — provenance:** the mechanic is **live in V1 without a mechanic-level ruling.**
Surfaced for the human (#893) to decide whether that V1 state is intended.

## Verdict summary (canon #889 → pycats)

| Facet | Verdict | Note |
|---|---|---|
| Two-window structure | **IMPLEMENTED** | ~15 moves; 5 genuine lingering-aerial sex kicks |
| Clean/late power falloff | **IMPLEMENTED / faithful** | per-move; `nalio bair` & `birky nair` match #889 exactly |
| Hit count (one per target) | **DIVERGENT (known)** | double-hits; B-full → #888; footprint wider than #879's 3 |
| Provenance / approval | **UNRATIFIED** | rode in via slices #209/#255/#249/#258 (#228); no mechanic decision |

## Key input for #893 (the scope decision)

**The two-window structure is load-bearing for *parity*, and the divergence is separable
from it.** The structure does two independent jobs:

1. It carries the **canon-faithful clean/late power falloff** (damage/angle/KB) — which
   #889 shows is exactly how PM 3.6 authors these moves. This is correct and worth keeping.
2. It currently also produces the **double-hit** (#879) — a defect in the *resolution*
   model (#204), which #888's B-full fixes **without removing the two-window authoring**.

So #893's "simplify the affected aerials to drop the sex kick" option would trade away
canon-faithful falloff (a parity asset) to avoid a bug that #888 already fixes on its own.
The two are not coupled: you can keep the sex-kick falloff and fix the hit count. If #893
still rules "no sex kick in V1" for scope reasons, note that the simplification is a
**larger** change than #879 implied — it touches ~5 aerials (+ ground analogues), and it
means intentionally shipping *less* PM-faithful damage/angle/KB profiles on those moves.

## How this was produced (repeatable)

```bash
REPO=/home/avi/Documents/Study/Python/pycats
PY="$REPO/.venv/bin/python"
cd "$REPO/.claude/worktrees/wt-grape-pycats-890"   # or any checkout with the venv

# Inventory sweep — per-cat, per-move window/damage/angle/bkb/kbg:
SDL_VIDEODRIVER=dummy "$PY" - <<'PY'
from pycats.combat.data import load_fighter_data
from collections import defaultdict
for cat in ("nalio","birky","narz","gnok"):
    fd = load_fighter_data(cat)
    for mkey, mv in fd.moves.items():
        w = defaultdict(list)
        for hb in mv.hitboxes: w[(hb.active_start, hb.active_end)].append(hb)
        if len(w) < 2 and not getattr(mv,"rehit_rate",None): continue
        print(cat, mkey, "windows", len(w), "rehit", getattr(mv,"rehit_rate",None))
        for k in sorted(w):
            print("  ", k, sorted({h.damage for h in w[k]}), sorted({h.angle for h in w[k]}),
                  sorted({h.base_knockback for h in w[k]}))
PY

# Hit-count grounding — drive a move vs a stationary defender through the real
# Player.update + process_hits loop and count percent applications (full script in
# the #890 session transcript; five moves each show 2 hits).
```

## Next steps (filed one at a time, downstream of this doc)

- **#893** (ARCHITECT, unblocked by this + #889) — rule on whether V1 ships the sex-kick
  mechanic. This audit is its input; the "structure is load-bearing, divergence is
  separable" finding above is the key consideration.
- **#888** (DEV, B-full) — when scoped, enumerate the **full** contiguous-two-window set
  (this doc's Facet-3 footprint note), not just #879's three.

## Cross-references

- Canon spec: **#889** · Hit-count authority: **#879** · Hit-count decision: **#883**
- Resolution model: `pycats/systems/combat.py` `process_hits`, `pycats/combat/move_clock.py`,
  `tests/test_temporal_windows.py`
- Move data: `pycats/characters/birky_cat.py`, `nalio_cat.py` (+ JSON mirrors under
  `pycats/characters/data/`)
