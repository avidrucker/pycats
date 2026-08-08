# Research findings — does Project M use randomness, and where/how?

- **Ticket:** #144
- **Agent:** DRAGONFRUIT
- **Date:** 2026-06-26
- **Area:** combat
- **Question:** Does Project M use randomness (RNG) anywhere? If so, where and how —
  and what does it mean for pycats (which is deterministic by design)?

---

## Answer (short)

**Yes — but almost none of it touches the core fighting math, and the part that
does is opt-in or character-specific.** Project M is Melee-style physics on the
Brawl engine, and it **removed Brawl's most notorious RNG (random tripping)**.
What remains is the same RNG families as Melee:

1. **Core combat math is fully deterministic** — knockback, hitstun, shieldstun,
   hitlag, DI, and clank/priority have **no random spread**. Same inputs → same
   result, every time. (This is what makes Melee/PM replays and netplay possible.)
2. **Move-intrinsic RNG** exists on a handful of *specific characters* (Mr. Game &
   Watch's Judge, Peach's turnips/fsmash, Luigi's misfire, Kirby's copy-loss,
   etc.). This is deliberate per-move design, not engine-wide variance.
3. **Item / stage / Poké Ball / hazard RNG** exists but is **off in the standard
   competitive configuration** (items off, neutral/Final-Destination-type stages
   with no hazards) — which is the configuration pycats models.
4. **It's all one seeded PRNG stream.** Given the same seed, the whole sequence is
   reproducible — which is exactly why replays save *only the seed*, not the
   events.

**Bottom line for pycats:** PM's determinism where it matters (the fight math)
matches ours. The RNG PM *does* have lives in features pycats doesn't implement
(items, hazards) or in a few specific specials we haven't authored. So pycats'
"no RNG at all" is not a divergence in the parts that exist today — it's the same
behaviour by a stricter route.

---

## Catalogue of RNG surfaces (Melee/PM family)

Classification: **C** = cosmetic/selection · **G** = gameplay-affecting ·
**Comp** = present in the standard competitive config (items off, neutral stage).

### A. Core combat math — DETERMINISTIC (no RNG)

- **Knockback** is a fixed formula of damage, weight, base knockback, and
  knockback growth — **no random spread** ([SmashWiki: Knockback]). Hitstun,
  shieldstun, hitlag, and **clank/priority** (the 9% rule, see #141) are likewise
  deterministic.
- **DI / SDI** are *player-controlled* trajectory influence from stick input —
  not random.
- → This is the part pycats cares about, and it is RNG-free in both games.

### B. Move-intrinsic RNG — G, **Comp** (these are live in tournament play)

| Character / move | Random element | Notes |
|---|---|---|
| **Mr. Game & Watch — Judge** | Number 1–9, each a different attack | **Not uniform**: cannot repeat either of the last two numbers, so each valid number is **1/7**; first two uses seeded to exclude 1 then 2. (9 = ~32% dmg KO move; 7 drops food.) ([SmashWiki: Judge]) |
| **Mr. Game & Watch — Chef** | Food projectiles travel at random angles | trajectory RNG |
| **Peach — Vegetable (down-B)** | Turnip face = power; rare item pulls | stitched-face (strongest) **1/58**; small chance of Beam Sword / Bob-omb / Mr. Saturn |
| **Peach — Forward Smash** | One of 3 weapons (pan/club/racket) | equal chance, **no repeat twice in a row** |
| **Luigi — Green Missile** | Misfire | **1/8** chance; 50% to stick in walls above a speed |
| **Kirby — Copy Ability** | Loses copy when hit | **1/32** per hit |
| **King Dedede — Waddle Dee Toss** (Brawl-derived) | Waddle Dee 71.4% / Doo 20.4% / Gordo 8.2% | PM retuned Dedede; the toss-type RNG family persists |

These are **deliberate character design**, intentionally injecting variance into a
few specials. They do **not** generalise to the rest of the cast.

### C. Items / Poké Balls / Assist-type — G, **NOT Comp** (off by default)

- **Container contents** random from the enabled item set; chance to be explosive.
- **Item-drop-from-damage**: formula `damage/60` (Melee) guarantees a drop at
  ≥60% — gameplay, but only when items are on.
- **Poké Ball spawns**: each Pokémon weighted; rares (Mew/Celebi/Jirachi) 1/151.
- **Food**: which food appears is random (the healing amount varies).
- → All gated behind items being ON; the competitive/pycats config has them off.

### D. Stage hazards / transformations — G, **NOT Comp** (neutral stages only)

- Pokémon Stadium transformation order is randomised; Big Blue track layout random;
  Brinstar acid timing random from preset patterns. → Only on hazard stages; the
  neutral/FD-type stage pycats models has none.

### E. Cosmetic / selection — C

- Random character / random stage **select** (menu convenience).
- Crowd cheers, announcer, particle variance — purely presentational.

### F. CPU AI — G (weighted, not "pure" random)

- SmashWiki: "the higher the computer's level, the more likely it is to do a
  specified action" — i.e. **weighted/probabilistic** action selection, plus
  reaction delay. Relevant to #141: this is part of what desyncs two CPUs out of a
  perfect mirror (pycats bots are deterministic, so they can't self-desync).

### G. Removed in Project M

- **Random tripping** (Brawl's 1% dash / 1.25% run-turn / ~13.5% knockback-trip)
  was **removed** in PM. Only *forced* tripping from specific causes (e.g. banana)
  remains, and it can be teched. ([SmashWiki: Project M], [SmashWiki: Tripping])

---

## How the RNG works mechanically

Melee/PM use a **single pseudo-random number generator (PRNG)** advanced from a
seed. SmashWiki: *"If a computer were to start out with a certain seed, one could
predict the entire sequence of pseudorandom numbers… It is believed this is how
Replays are saved; the system only saves the seed instead of all random events."*

Implication: PM's randomness is itself **deterministic given the seed** — every
"random" event (a Judge roll, a turnip face) is a draw from one reproducible
stream. This is the foundation of both **replay** fidelity and **netplay** sync:
both clients share a seed and advance the same stream in lockstep.

---

## What this means for pycats

| PM RNG surface | pycats today | Verdict |
|---|---|---|
| Core combat math (knockback/hitstun/clank/DI) | deterministic, RNG-free | **Match** — same behaviour, stricter route |
| Move-intrinsic RNG (Judge, turnips, misfire…) | none of these moves authored | **N/A today** — would need a *seeded* RNG seam if ever added |
| Items / Poké Balls | not modelled | **N/A** — off in our config anyway |
| Stage hazards / transformations | single neutral stage | **N/A** |
| Random tripping | not modelled | **Aligned** — PM removed it too |
| CPU AI weighting | deterministic flowchart controllers | **Divergence** — our bots can't desync a mirror (see #141 → #61's timer cap) |

**Key design takeaway:** pycats is deterministic with **no PRNG at all**. PM is
deterministic *given a seed* with **one PRNG stream**. For everything pycats
currently implements, "no RNG" reproduces PM's competitive-config behaviour
exactly. The only place the difference bites is **emergent symmetry-breaking**:
PM's seeded RNG (DI quirks, CPU weighting) naturally desyncs a mirror match,
whereas pycats cannot — which is why #61 added an explicit match-length cap as the
deterministic analog of PM's match timer.

**If pycats ever wants PM-faithful move-intrinsic RNG** (e.g. an authored Judge or
turnip pull), introduce **one seeded PRNG** threaded through the sim (seed in the
match config / snapshot), advanced in a fixed order per frame — so replays and
goldens stay reproducible by pinning the seed. Do **not** reach for Python's global
`random`; a seam-injected, snapshot-seeded stream is what keeps determinism.

---

## Outcome / recommendation

- **Question answered:** PM uses RNG, but the **core fight math is deterministic**;
  RNG is confined to (a) a few character specials, (b) items, (c) stage hazards,
  (d) CPU weighting — and PM **removed** Brawl's random tripping. It is all one
  seeded PRNG stream (deterministic given seed).
- **No engine change warranted now** — none of the RNG-bearing features exist in
  pycats, and our determinism matches PM's competitive config.
- **Future seam (file only when needed):** if a move-intrinsic-RNG character is
  authored, add a single **seeded** PRNG to the sim (config/snapshot-seeded) rather
  than ad-hoc randomness, to preserve replay/golden determinism. Cross-ref #141
  (clank determinism + mirror-loop), #61 (match-length cap as the timer analog).

## Sources

- [SmashWiki: Randomness](https://www.ssbwiki.com/Randomness)
- [SmashWiki: Judge](https://www.ssbwiki.com/Judge)
- [SmashWiki: Knockback](https://www.ssbwiki.com/Knockback)
- [SmashWiki: Tripping](https://www.ssbwiki.com/Tripping)
- [SmashWiki: Project M](https://www.ssbwiki.com/Project_M)
