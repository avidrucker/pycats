# PM fall physics — weight vs gravity vs fall-speed (+ fast-fall); should Nalio (Mario) and Birky (Kirby) fall the same? (#528)

**Role:** RESEARCH (DRAGONFRUIT), 2026-07-04. Findings + a graded comparison to pycats;
**no code changes** — mechanics-fix follow-ups are *proposed*, not filed.

## TL;DR — the headline answer
**No — Nalio (Mario) and Birky (Kirby) should not fall at the same rate** — but the reason is
subtler than "Kirby is floaty, so he falls slower." In the Brawl engine PM inherits, their
**normal terminal fall speeds are close** (Mario ~1.28, Kirby ~1.2). They diverge on two *other*
independent axes:
- **Gravity (fall acceleration):** Mario 0.075 > Kirby 0.061 — Kirby accelerates toward fall
  speed more slowly (the floaty feel).
- **Fast-fall:** Mario has a strong fast-fall (~1.792); **Kirby is one of the few characters with
  essentially no fast-fall boost.** This is the single biggest practical difference — and pycats
  **cannot represent it** (no fast-fall mechanic exists).
- **Weight is NOT a fall attribute.** Mario 100 vs Kirby 70 changes *knockback taken*, not
  descent. (This is the conflation the ticket flagged; the data dispels it.)

pycats already differentiates the two on `gravity` + `max_fall_speed`, and — a pleasant surprise —
Birky's "#229 guess" **ratios** are close to canonical. The real gaps are (1) Nalio rides the
*unsourced engine default*, and (2) **fast-fall is missing**, which is exactly where Kirby and
Mario diverge most.

## The model — four *independent* attributes
| Attribute | What it does | pycats field |
|---|---|---|
| **Weight** | resists knockback (heavier = launched less) | `weight` — feeds `knockback()` (`combat/data.py:181`), **not** fall |
| **Gravity** | downward acceleration per frame (this *is* "fall acceleration" — not a separate thing) | `gravity` (`data.py:208`, default `GRAVITY=0.5`) |
| **Max fall speed** | terminal descent cap (normal) | `max_fall_speed` (`data.py:209`, default `MAX_FALL_SPEED=13`) |
| **Fast-fall speed** | a *second, higher* cap engaged by holding down while airborne | **absent** — no fast-fall mechanic |

Confirmed against PM/Brawl: these four are independent; **weight ≠ fall speed**. pycats' `gravity`
(accel) + `max_fall_speed` (cap) faithfully model "accelerate under gravity to a terminal
fall-speed cap," so **"fall-acceleration vs gravity" is one field, not two** — no model mismatch.
The only missing piece is fast-fall.

## Canonical values (Brawl engine, which PM3.6 inherits; PM tweaks noted)
| | weight | gravity | fall speed | fast-fall |
|---|---|---|---|---|
| **Mario** (SSBB → PM) | 100 | 0.075 | 1.28 | 1.792 (strong) |
| **Kirby** (SSBB → PM) | 70 (**PM: 74**) | 0.061 (**PM: possibly raised — see caveat**) | ~1.2 | ≈none (one of the few characters without the standard fast-fall boost) |

**Sourcing caveat.** PM3.6-*exact* per-attribute numbers are not cleanly published; PM inherits
the Brawl engine and is documented to buff a few Kirby attributes (heavier **70 → 74**, faster air
**0.78 → 1.00**). The Kirby (PM) page also lists a gravity near **0.08** — if accurate, PM raised
Kirby's gravity well above Brawl's 0.061 (de-floatifying him, consistent with the weight/air
buffs), which would make gravity a *weaker* differentiator than Brawl suggests. Treat the exact PM
gravity as **⚠ unconfirmed — pin from a rukaidata/decomp dump later** (same posture as #120/#229).
The headline answer is robust to this: even if PM raised Kirby's gravity, the **fast-fall** gap
(Kirby ≈none vs Mario strong) and **weight** gap remain, and Kirby's floaty identity is
well-attested ("lightweight with slow fast-fall speed").

## pycats today vs canonical
| | pycats gravity | pycats max_fall | pycats weight |
|---|---|---|---|
| **Nalio** (Mario) | 0.5 — the **generic engine default**, *not sourced as Mario's* (`nalio_cat.py` overrides only `weight`) | 13 (default) | 100 ✓ (Mario) |
| **Birky** (Kirby) | 0.42 (#229 "proportional guess, pin later") | 12 (#229 guess) | 70 ✓ (Kirby, Brawl) |

pycats runs its own unit scale (px/frame² and px/frame), so compare **ratios**, not absolutes:

| ratio (Kirby ÷ Mario) | gravity | fall speed |
|---|---|---|
| Brawl canonical | 0.061/0.075 = **0.81** | 1.2/1.28 = **0.94** |
| pycats (Birky ÷ Nalio) | 0.42/0.5 = **0.84** | 12/13 = **0.92** |

**Birky/Nalio ratios land within ~0.03 of the Brawl Kirby/Mario ratios** — the #229 "guess" is
actually near-faithful, not a wild number. And **weight is correct and correctly separated**
(feeds knockback, not fall). The conflation is dispelled: pycats already models weight and fall as
distinct, with the right values.

## Gaps (what is actually off)
1. **Nalio's fall values are the generic engine default (`0.5`/`13`), never sourced as Mario's.**
   They *serve* as the baseline but carry no citation — RULES → "Changing values" wants a basis.
   Pin + document them as the Mario reference (or adjust if the intended baseline differs).
2. **Fast-fall is absent** — the attribute where Kirby (≈none) and Mario (strong) diverge *most*.
   Without it, pycats structurally cannot express the biggest felt difference between the two. A
   shared engine mechanic, already tracked as a Birky prereq (#261/#229).
3. **Minor:** Birky's weight 70 is the *Brawl* value; PM buffed Kirby to **74** — a candidate pin
   if we target PM3.6 over Brawl (a small game-designer call).

## Proposed follow-ups (listed, NOT filed — one at a time)
1. **DEV — source + pin the fall values.** Document Nalio's `gravity`/`max_fall_speed` as the
   Mario baseline (cite Brawl 0.075/1.28 → the pycats scale) and re-pin Birky's with the ratio
   citation (0.81/0.94) so #229's guess is grounded. Weight already correct. *(Per RULES →
   "Changing values"; note the DEV-vs-ARCHITECT classification question is #530.)*
2. **ARC → DEV — fast-fall mechanic.** Hold-down while airborne → a second, faster fall cap
   (`fast_fall_speed` per fighter). ARC decides the model (a second cap vs a gravity multiplier;
   Kirby's near-absent boost is a special case), then DEV wires it + per-character values. The
   shared engine prereq #261/#229 — and the highest-fidelity payoff (it's where Kirby vs Mario
   diverge most).
3. **(optional) decision — Brawl vs PM3.6-exact target** for Kirby (weight 70 vs 74; gravity
   0.061 vs the PM page's ~0.08). A small game-designer call that also unblocks pinning gap #1's
   Birky numbers to PM rather than Brawl.

## Method / limits
- Grounded in the code (`data.py:181/207-209`, `config.py:31-32`, `nalio_cat.py`, `birky_cat.py`)
  + SmashWiki attribute data (Mario SSBB, Kirby SSBB, Kirby PM, Falling speed / Fast fall).
- **Not** a rukaidata/decomp dump of PM3.6-exact attributes — those aren't cleanly published, so
  the PM-vs-Brawl gravity for Kirby is left ⚠ unconfirmed (follow-up decision #3).
- Sources: SmashWiki — [Kirby (PM)](https://www.ssbwiki.com/Kirby_(PM)), [Kirby (SSBB)](https://www.ssbwiki.com/Kirby_(SSBB)), [Mario (SSBB)](https://www.ssbwiki.com/Mario_(SSBB)), [Falling speed](https://www.ssbwiki.com/Falling_speed), [Fast fall](https://www.ssbwiki.com/Fast_fall).
