# PM ledge-grab intangibility — the sourced basis (audit) (#536)

> **Home-of-record** for what Project M's ledge-grab intangibility actually is, and
> whether pycats' percent-scaled `ledge_invuln_frames` has any PM basis. The #535
> register cites this; `docs/research/2026-06-30-ledge-recovery-mechanics.md` (#297)
> points here after its percent-scaling attribution was corrected.
>
> Origin: surfaced during #520's PM-parity pass (2026-07-05), audited under #536.
> Sources re-verified 2026-07-06 (independent of #536's filing).

## TL;DR — the verdict

- **PM ledge-grab intangibility = a *fixed per-grab burst* + a *5-regrab count cutoff*.**
  Neither is percent-scaled.
- **pycats' percent-scaling (`+0.3/% `, cap 60) has no PM basis.** It is a **pycats-original
  divergence** introduced in #311, sourced only to secondary community threads and
  mis-attributed to PM. It matches neither PM (fixed magnitude) nor Smash 4 / Ultimate
  (per-grab *decay* — the opposite direction).
- **The 5-regrab cutoff is the actually-primary-sourced PM anti-stall rule** — and pycats
  does **not** implement it.

## 1. What IS primary-sourced for PM

**PMDT — "3.5 Blogpost #6: Ledge Invincibility"** (Project M Dev Team official dev blog;
`projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility`, live site dead, recovered
via Wayback; text independently reproduced 2026-07-06). Verbatim:

> "After a character regrabs the ledge five times without touching the ground, that
> character no longer receives invulnerability for grabbing the ledge again (except for a
> few frames during the initial ledge snap) until he or she either lands on the stage or
> gets hit."

Tier: **PRIMARY** (PMDT). This is an **anti-stall count cutoff**, not a duration function:

- Grabs **1–5** (without touching the ground) grant the normal per-grab intangibility burst.
- Grab **6+** grants **no** grab-invulnerability — "except for a few frames during the
  initial ledge snap" — until the fighter **lands on the stage or gets hit** (which resets it).

**Per-grab burst magnitude** — a *fixed* window, Brawl-derived (PM is a Brawl mod). The Brawl
baseline is **~23 frames** (SmashWiki *Ledge*, secondary; recorded in #297 as
`LEDGE_INVULN_BASE_FRAMES = 23`, tagged **FOUND**). The **exact PM 3.6 frame value is not
pinned here** — that is #552's job (rukaidata PM 3.6 dump). Confidence on "fixed, not
percent-scaled": **inferred-strong** (positive evidence the %-effect is elsewhere + no source
for magnitude scaling).

## 2. What is NOT PM (the mis-attributions)

- **Percent-scaling of intangibility *duration*** — **no source, in any game.** SmashWiki
  *Edge recovery* verbatim: *"Prior to Smash 4, when the character has 100% damage or more,
  the action of climbing back to the stage is significantly slower."* That is climb-**speed**,
  not intangibility **duration**. The ≥100% effect makes recovery *harder*, the **opposite**
  of pycats' "higher % → longer invincibility."
- **Per-grab intangibility *decay*** — a **Smash 4 / Ultimate** mechanic, **explicitly not PM**.
  SmashWiki *Planking*, verbatim:
  - Smash 4: *"characters only have ledge intangibility on their first ledge grab; regrabbing
    the ledge without landing on the stage first … will result in the player grabbing the ledge
    with no intangibility at all."*
  - Ultimate: *"Ledge recovery options grant fewer intangibility frames with each regrab,
    granting no intangibility at all after the fourth ledge grab"* + *"a player can only grab the
    ledge a maximum of 6 times before having to land on stage."*
  - **Project M is not mentioned on the page at all.**

  PM's real anti-plank tool is the **count cutoff** in §1 (full burst for 5 grabs, then off),
  **not** a graded decay.

## 3. pycats today vs. the sourced basis

| Aspect | pycats (`ledge_invuln_frames`, #311) | Sourced PM | Classification |
|---|---|---|---|
| Per-grab magnitude | `23 + round(0.3·%)`, cap 60 — grows with damage | fixed burst (~23f Brawl-derived) | `LEDGE_INVULN_BASE_FRAMES=23` **FOUND**; `PER_PERCENT=0.3` + `MAX=60` **DIVERGENCE** |
| Percent-scaling of duration | yes (higher % → longer) | no source, any game | **pycats-original / mis-attributed** |
| Repeated-grab anti-stall | none | **5-regrab count cutoff** (PMDT primary) | **missing in pycats** |

The percent-scaling was believed FOUND at #311 (sourced to secondary Smashboards threads);
this audit **reclassifies it as a divergence** with no primary PM basis. #543 (ratified
2026-07-05) already decided to **drop** it → a fixed per-grab burst.

## 4. Recommendation (#536 paths a/b/c)

- **(a) Re-label the basis faithfully — DONE.** Percent-scaling is a divergence, not PM; #543
  ratified removing it (→ fixed burst, scoped by #552). This doc + the #297 correction complete
  the re-labeling. ✅
- **(b) Adopt PM's 5-regrab count cutoff — RECOMMENDED.** It is the primary-sourced PM anti-plank
  mechanic and pycats lacks it. Already scoped: **#656** (the cutoff sim mechanic), **#657**
  (grabs-left dots), **#658** (frame dots), under epic **#267**. *Needs a ratified `decision` to
  adopt* (RULES "Changing values" — a new mechanic needs a basis). **← the open decision (§5).**
- **(c) Keep percent-scaling — REJECTED.** No basis; superseded by #543.

## 5. The decision the human must make

#543 already settled the *magnitude* direction (drop percent-scaling → fixed burst). The
**still-open** decision this audit surfaces:

1. **Adopt PM's 5-regrab ledge-intangibility count cutoff in pycats? (yes / no.)** It is
   primary-sourced (§1) but is a **new sim mechanic**, so it needs a game-designer ruling to
   have a basis. A "yes" is the decision **#656** cites; a "no" drops #656–#658.
2. **If yes — post-cutoff behavior:** after the 5th regrab, grant **zero** grab-invuln, or model
   PMDT's residual **"few frames during the initial ledge snap"**? **→ RESOLVED by #671** — the
   primary keeps a **non-zero** residual (the CliffCatch snap intangibility); exact count is
   engine-hardcoded. See `2026-07-06-pm-post-ledge-cutoff-frames.md`.

Everything else (the exact fixed-burst frame value, edge-hog/AI blast radius) is already owned by
the #552 spike — not a decision for here.

## Sources

| Source | Tier | Used for |
|---|---|---|
| [PMDT — "3.5 Blogpost #6: Ledge Invincibility"](https://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility) (dead; Wayback / reproduced) | **PRIMARY (PMDT)** | the 5-regrab count cutoff (verbatim, §1) |
| [SmashWiki — Planking](https://www.ssbwiki.com/Planking) | secondary | per-grab decay = Smash 4 / Ultimate, **not PM** (verbatim, §2) |
| [SmashWiki — Edge recovery](https://www.ssbwiki.com/Edge_recovery) | secondary | ≥100% = slower climb *speed*, not intangibility duration (§2) |
| [SmashWiki — Ledge](https://www.ssbwiki.com/Ledge) | secondary | Brawl ~23f grab-intangibility baseline (via #297) |
| in-repo #297 `docs/research/2026-06-30-ledge-recovery-mechanics.md` | — | prior data (its percent-scaling PM attribution corrected by this audit) |

## Cross-refs

Audit **#536**; origin pass **#520**; percent-scaling origin **#311**; ratified magnitude
decision **#543**; fixed-burst spike **#552**; adoption chain **#656 / #657 / #658** under epic
**#267**; register **#535**; parity docs `docs/pm-reference/ledge-mechanics.md`,
`docs/project-m-rules-by-category.md`. PM canon = **Project M 3.6**.
