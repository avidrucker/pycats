# Ledge-recovery mechanics — frame data, intangibility, occupied-edge rules (#297)

> Research findings (#297, child of ledge epic #267). Fills the **quantitative** gaps
> the qualitative `docs/pm-reference/ledge-mechanics.md` left open: getup **frame
> data**, **intangibility** windows + decay, **hang duration**, and **occupied-edge
> collision/trump** rules. Grounds #267's DEV slices. **Findings only — no code.**
>
> PM is **Brawl-derived**; PM-exact numbers are per-character (use rukaidata PM 3.6).
> Mario is used as the **Nalio** archetype reference ([[cat-archetype-naming]]).
> Date: 2026-06-30. Agent: FIG. Area: `area:entities`.

## TL;DR
- **Intangibility on grab:** Brawl **23 frames** (+ a 23-frame grab animation); Melee 30
  (+7). pycats currently grants the **whole** `LEDGE_HANG_FRAMES` (120f) — *far* more
  than Brawl's ~23f burst. **Over-generous; should be a short burst.**
- **Hang time before auto-release:** Brawl **~6 s <100% / ~5 s ≥100%** (≈360/300f);
  Melee 11/8 s. pycats = **120f (2 s)** — shorter than Brawl.
- **Getup options have fast (<100%) and slow (≥100%) variants** — a core pre-Smash-4
  rule. pycats neutral getup is **instant** (no frame window) and has only neutral.
- **Occupied edge:** **one fighter per ledge.** **PM = edge-hogging** (grab denied;
  hog timing gated by the occupant's invincibility timer — a **fixed per-grab burst**, not
  percent-scaled: #536 reclassified the percent-scaling a divergence); **auto-ledge-trump
  is Smash-4+, NOT in PM** (confirmed). **pycats' one-occupant lockout already models
  PM edge-hogging** — so **#267's "ledge-trump" slice is removed** (not a PM mechanic).
- **The "2-frame":** exactly **2 frames** of vulnerability at grab before intangibility
  starts (Smash-4 framing of a window that exists across games). pycats grants
  intangibility immediately → no vuln window yet.

## Q1/Q2 — Getup frame data + intangibility

**Intangibility on a fresh grab** (SmashWiki *Ledge*):
| Game | Intangible frames | + grab animation |
|---|---|---|
| Melee | 30 | 7 |
| Brawl | 23 | 23 |
| PM | ~Brawl baseline (per-char) | — |

Intangibility **carries into a getup option's early frames** if the option begins
before it expires. PM **reduced/curbed** ledge intangibility vs Melee to limit
planking (the pycats doc's "decays with repeated grabs"); the **exact PM decay
schedule was not found** in a primary source → `gap`, playtest/patch-note needed.

**Fast vs slow by %:** *"all edge actions aside from letting go have two possible
animations"* — **fast/"fresh" <100%**, **slow/"tired" ≥100%** (SmashWiki). Applies to
neutral getup, roll, attack, jump.

**Ledge-attack frame data (PM 3.6, Smashboards "Ledge Option Frame Data"):**
| Char | <100% total / intang / hit | ≥100% total / intang / hit |
|---|---|---|
| **Mario** (→ Nalio ref) | 55f / 1–20 / 24–26 | 69f / 1–36 / 40–44 |
| Ness | 55f / 1–22 / 24–26 (6–8%) | 69f / 1–35 / 39–43 (10%) |
| Olimar | invuln 1–15 / hit 17–23 | invuln 1–43 / hit 39–43 |

So a representative PM ledge attack ≈ **55f <100%, 69f ≥100%**, intangible for the
first ~20 (<100%) / ~36 (≥100%) frames, hitbox ≈ frame 24 (<100%) / 40 (≥100%).
**Neutral getup / roll / jump per-frame counts** are per-character on the same
Smashboards thread (not all captured here) → pull Mario's at implementation; treat as
`⚠ playtest` until pinned.

## Q3 — Occupied-edge collisions (the headline question)

- **One fighter per ledge** — *"Multiple characters cannot hold onto an edge at the
  same time"* (Ice-Climbers exception irrelevant to pycats).
- **Grabbing an edge an opponent already holds:**
  - **Brawl / PM → edge-hogging:** the second grab is **denied** while the first
    fighter occupies the ledge (you can't grab it; you hog it to deny recovery).
  - **Smash 4 / Ultimate → ledge-trump:** the incoming grab **auto-removes** the
    occupant (*"gently remove them… then grab it"*), putting them in a brief
    can't-act vulnerable state — *"removing edge-hogging."* **No frame data** for the
    vulnerability window in the sources (`gap`).
  - ✅ **CONFIRMED: Project M does NOT have ledge-trump — it uses edge-hogging.**
    Ledge-trump (auto-removal of an occupant) is the **Smash-4/Ultimate** replacement
    for hogging; PM (a Brawl mod) kept **edge-hogging** and reworked its *timing*, not
    its kind. The PM community frames the two as opposites ("ledge hogging **or**
    ledge trumping" — PM = the former). **Correction to the reference doc:** it called
    trump *"first-class in the Brawl/PM family"* — that is **wrong**; remove trump as a
    PM mechanic. **pycats' one-occupant lockout already IS PM-faithful edge-hogging.**

    **How PM edge-hogging actually works** (the fidelity detail #267 should target):
    > ⚠ **CORRECTION (#536, 2026-07-05):** the "invincibility **scales with percent**" claim
    > below is a **DIVERGENCE, not PM.** No primary source scales ledge-intangibility *duration*
    > with damage (SmashWiki *Edge recovery*'s ≥100% effect is climb *speed*, and makes recovery
    > *harder* — the opposite). PM's real anti-stall rule is a **5-regrab count cutoff** (PMDT
    > dev-blog #6). Home-of-record: `docs/research/2026-07-05-pm-ledge-intangibility-basis.md`.
    - **Ledge invincibility is a fixed per-grab burst** (~23f Brawl-derived; exact PM 3.6 value
      = #552, ratified fixed by #543). Whether a hog succeeds is governed by the **occupant's
      invincibility timer**, so hog timing depends on **how recently the occupant grabbed** —
      too early and the recovering fighter takes the ledge from you. *(pycats #311's continuous
      "higher % → longer" is the reclassified divergence, not this.)*
    - A fighter **can act out of the grab sooner** than in Brawl, and while performing
      **any** getup (climb/jump/roll/attack) the ledge is **re-grabbable by others only
      after the animation is ~half done** — making edge-hopping/regrab faster.
    - **Tether** recoveries **ignore** edge-hoggers (latch on regardless, auto getup).
    None of this is auto-trump; it is hog-with-a-fixed-per-grab-invincibility-window
    (the percent-scaling is reclassified a divergence — #536).
- **Climbing up into an opponent standing at the lip** (the asked case): no source
  gives a *special* ledge rule for this. Mechanically it resolves as **normal**: the
  getup carries its own **intangibility** (early frames) and, for **ledge attack**, a
  **hitbox** that strikes a fighter standing in that space; once the fighter leaves
  the hang onto the stage it's an ordinary grounded body subject to the usual
  overlap/push. In pycats that's already handled by `resolve_player_push` — no
  ledge-specific collision code is needed beyond letting the getup's intangibility/
  hitbox apply.

## Q4 — Hang duration
Brawl auto-release ≈ **6 s (<100%) / 5 s (≥100%)** → ~360/300 frames; Melee 11/8 s.
pycats `LEDGE_HANG_FRAMES=120` (2 s) is **shorter** than Brawl. Whether to lengthen
toward Brawl or keep it short for pace is a `⚠ playtest` call (joins the #233 registry).

## Q5 — Recovery-to-ledge (up-B sweetspot)
Recovery moves are *designed to sweetspot* the ledge (snap when the catch region
overlaps the sweetspot, generally facing the stage, with a rising-grab limitation).
**Gated on specials existing** in pycats (no up-B yet) → this stays a #267 slice for
after the specials work; no new numbers needed until then.

## Q6 — pycats mapping & recommendations

| Mechanic | PM/Brawl source value | pycats today | Recommendation |
|---|---|---|---|
| Grab intangibility | ~23f burst (Brawl) | **whole 120f hang** | shorten to a ~23f burst (over-generous now) |
| Repeated-grab anti-stall | **5-regrab count cutoff** (PMDT primary) | none | add the count cutoff (#656). Per-grab *decay* is Smash-4/Ult, NOT PM — see #536 |
| Hang auto-release | ~360/300f (Brawl) | 120f | playtest (lengthen vs keep snappy) |
| Neutral getup | fast<100% / slow≥100%, real window | **instant, neutral only** | add a frame window + the %-variant |
| Ledge attack | ~55f/69f, intang 1–20/1–36, hit ~24/40 (Mario) | absent | implementable now (use Mario ref) |
| Ledge roll / jump | per-char (Smashboards) | absent | implementable; pull per-char frames |
| Occupied edge | **edge-hog (deny)** in Brawl/PM | **one-occupant lockout** | ✅ already PM-faithful — keep |
| "Ledge-trump" | **Smash-4+**, not PM | n/a | **re-scope #267's trump slice** (non-PM; confirm) |
| "2-frame" vuln | 2f at grab before intang | intang immediate | add the vuln window for edge-guard punish |

### Ordered #267 unblocking
1. **Getup options** (roll / attack / jump) with fast/slow %-variants + carried
   intangibility — frame data now available (Mario ref). *(biggest, ready)*
2. **Intangibility model fix** — short burst (not full hang) + decay-on-regrab.
3. **The "2-frame"** vulnerable window — enables edge-guard punish.
4. **Re-scope "ledge-trump"** — confirm PM = edge-hog (pycats already does it); add
   trump only as an explicit non-PM option, or drop it.
5. **Up-B sweetspot** — after specials exist.

## Caveats & gaps
> ⚠ **#536 correction:** this section originally framed the anti-stall rule as a percent/decay
> *schedule*. That is wrong — PM's rule is a **5-regrab count cutoff** (PMDT primary), and the
> exact fixed per-grab frame value is #552, not a percent schedule. See
> `docs/research/2026-07-05-pm-ledge-intangibility-basis.md`.
- **The trump-vulnerability frame count is a gap** (no primary source found); flagged as a
  playtest/patch-note item. (The "decay schedule" gap is retired — the mechanic is the count
  cutoff above.)
- Getup frame data is **per-character**; Mario is used as the Nalio reference — other
  cats want their own archetype's numbers (#117).
- The **trump-vs-edge-hog attribution is confirmed** (PM = edge-hog, no trump) via
  SmashWiki + PM community sources; what remains a `gap` is PM's **exact fixed per-grab
  intangibility frame value** (#552) — **not** a percent→frames schedule, which #536
  reclassified as a divergence.

## Sources
| Source | Quality | Gives |
|---|---|---|
| [SmashWiki — Ledge](https://www.ssbwiki.com/Ledge) | secondary | intangibility frames (Melee 30/Brawl 23), hang times, fast/slow ≥100%, one-occupant, 2-frame |
| [SmashWiki — Ledge trump](https://www.ssbwiki.com/Ledge_trump) | secondary | trump = Smash-4+; trumped = brief can't-act; buffer to escape |
| Smashboards — "Ledge Option Frame Data" (PM 3.6) | secondary (community data) | per-char ledge-attack frames (Mario/Ness/Olimar) |
| Smashboards — "Ledge Grab Limit for PM" + "ledge hogging or ledge trumping" + PM ledge-rework threads | secondary (PM community) | PM = edge-hogging (NOT trump); act-out-sooner; ~half-animation regrab; tethers ignore hoggers. ⚠ the "percent-scaled ledge invincibility" these threads implied is **reclassified a divergence** — #536 (primary = fixed burst + 5-regrab cutoff) |
| `docs/pm-reference/ledge-mechanics.md`, `pycats/config.py`, #14 spec/plan | primary (repo) | current pycats values + the trump mis-attribution this corrects |
