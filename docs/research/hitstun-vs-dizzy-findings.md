# Hitstun vs shield-break dizzy in Project M — are they equivalent? (#615)

> Compares **hitstun** (`hurt` / `hurt_timer`) and **shield-break dizzy** (`stun` /
> `stun_timer`) in Project M / Melee, beyond how they are triggered and how long
> they last. pycats models both as leaves under one `hitstun` compound state
> (`pycats/charts/fighter_chart.py`); this asks whether that shared treatment is
> faithful. Follows #610.
>
> Inputs:
> - Primary: SmashWiki [Hitstun](https://www.ssbwiki.com/Hitstun), [Stun](https://www.ssbwiki.com/Stun), [Tech](https://www.ssbwiki.com/Tech)
> - Prior finding: `docs/research/stun-actionability-findings.md` (#610)
> - Canonical reference: Project M 3.6 (the project's fidelity target)
> - Date: 2026-07-05
>
> **Bottom line: NOT functionally equivalent.** Apart from trigger + duration,
> hitstun and dizzy differ on nearly every axis — DI, mashing, airborne
> existence, teching, re-hit behaviour, wake-up, and internal identity. They are
> separate mechanics (internally `DamageFrame` vs `FuraFura`), not one mechanic
> parameterised two ways. See §2.

## 1. Framing

Both states are **non-actionable** (established in #610: a fighter can take no
normal action during either). The question here is the *complement* — given both
lock out actions, do they otherwise behave the same? The axes below are sourced
Melee behaviour; PM applicability is discussed in §4 (labeled inference).

## 2. Per-axis comparison

| Axis | Hitstun (`hurt`) | Shield-break dizzy (`stun`) | Same? |
| --- | --- | --- | --- |
| Stick influence | **DI + SDI + teching** allowed | **No** actions/influence at all | **Different** |
| Button-mash to shorten | **No** (Melee/PM: no hitstun canceling) | **Yes** (~3 frames/input) | **Different** |
| Exists airborne | **Yes** (tumble/knockback) | **No** — grounded-only; airborne cancels it | **Different** |
| Teching | **Yes** (tech out of tumble/reel) | **No** (grounded stand, not tumbling) | **Different** |
| Vulnerable / punishable | Yes — the basis of combos | Yes — but a re-stun is **flinchless & non-extending** | Both punishable; dizzy has a quirk |
| Ending / follow-up | Resumes to actionable | Distinct **wake-up** animation (`FuraFuraEnd`) then actionable | **Different** |
| Internal identity | `DamageFrame` | `FuraFura` | **Separate systems** |

## 3. Per-axis detail (primary quotes)

### 3a. Stick influence — hitstun has DI, dizzy has none
> "a period of time after being hit by an attack that a character is unable to
> act outside of directional influence or teching" — [Hitstun](https://www.ssbwiki.com/Hitstun)

> "A stunned character is dazed for a few seconds and can't perform any actions
> until the condition ends." — [Stun](https://www.ssbwiki.com/Stun)

Hitstun's whole point is that DI/SDI let the victim bend their knockback
trajectory. Dizzy is a grounded daze with no trajectory to influence and "can't
perform any actions" — no stick influence.

### 3b. Mashing — dizzy is mashable, Melee/PM hitstun is not
> "Button mashing reduces the duration of shield break stun by … 3 frames per
> input in later games." — [Stun](https://www.ssbwiki.com/Stun)

> Melee: no hitstun canceling exists; hitstun runs its full duration. (Brawl adds
> air-dodge/aerial canceling after 13/25 frames — but that is Brawl; PM restores
> Melee hitstun.) — [Hitstun](https://www.ssbwiki.com/Hitstun)

So dizzy shortens with mashing; Melee/PM hitstun runs its full knockback-derived
duration regardless of inputs. (Melee *momentum canceling* reduces knockback
*distance*, not hitstun *frames* — not a counterexample.)

### 3c. Airborne — dizzy is grounded-only
> "It is impossible to be stunned while airborne. Possibly as a result, any
> airborne state induced upon a stunned character will cancel the stunned state
> immediately." — [Stun](https://www.ssbwiki.com/Stun)

Hitstun by contrast exists freely in the air (tumbling). This is the #613 parity
gap for pycats.

### 3d. Teching — a hitstun/tumble exception dizzy lacks
> "A tech … is an action that can be performed when the player's character hits
> the ground, a wall, or a ceiling while tumbling (or reeling)." — [Tech](https://www.ssbwiki.com/Tech)

> For wall techs: "the character must be in hitstun for it to work." — [Tech](https://www.ssbwiki.com/Tech)

Teching is gated to tumbling/reeling (i.e. hitstun). A grounded dizzy fighter is
not tumbling, so dizzy cannot be teched.

### 3e. Re-hit — both punishable, dizzy has a flinchless quirk
> Hitstun is "an essential component of combos, as the basis of a combo is to
> have enemies trapped in hitstun while constantly being attacked." — [Hitstun](https://www.ssbwiki.com/Hitstun)

> "While a character is stunned … hitting them with a stunning move does not
> extend the duration, instead simply causing flinchless damage." — [Stun](https://www.ssbwiki.com/Stun)

Both can be hit. The dizzy-specific rule: a further stunning hit does not extend
the daze and deals flinchless damage — a nuance hitstun does not share.

### 3f. Ending — dizzy has a wake-up animation
> "From Brawl onward … every character has an animation for regaining
> consciousness after their stun ends (known internally as FuraFuraEnd)." — [Stun](https://www.ssbwiki.com/Stun)

Hitstun simply resumes to an actionable state; dizzy ends through a distinct
regain-consciousness animation. (In Melee/PM a fighter can act immediately once
the timer ends — see #610 — but the state identity + wake-up framing still
differ.)

### 3g. Internal identity — separate states
Dizzy is `FuraFura` (per the `FuraFuraEnd` wake-up animation); hitstun is
`DamageFrame` ([Hitstun](https://www.ssbwiki.com/Hitstun)). They are distinct
internal states, not one shared mechanic with two parameter sets.

## 4. Project M applicability — labeled inference

Sources document **Melee**. "These hold in PM" is **inference** (PM restores Melee
hitstun — removing Brawl's hitstun canceling — and dizzy is Melee-identical), not
a PM-specific primary quote; flagged per the project's PM-parity sourcing
discipline (cite primary; label inference). No PM source contradicts the Melee
behaviour above.

## 5. pycats implications (observations — no fixes here)

pycats treating `hurt` and `stun` as sibling leaves under one `hitstun` compound
is a reasonable *shared-lockout* abstraction, but the two are **not**
interchangeable. Divergences worth their own tickets (file one-at-a-time; do not
bundle):

- **Airborne persistence** — dizzy stays in-air in pycats; already filed as **#613**.
- **Mashing** — confirm whether pycats lets a player mash to shorten dizzy (~3
  frames/input). If not modelled, that is a candidate DEV ticket; hitstun should
  *not* be mashable (Melee/PM), so the two must not share a mash path.
- **DI/SDI** — pycats hitstun bleeds launch velocity but models no DI/SDI input
  at all; a broader feature, likely its own scope rather than a defect.
- **Wake-up (`FuraFuraEnd`)** — pycats exits dizzy straight to `idle`/`fall` with
  no regain-consciousness beat; cosmetic, low priority.
- **Flinchless re-stun** — confirm pycats handling of a stunning hit landing on an
  already-dizzy fighter (should not extend; flinchless).

These are **noted, not filed** — surface to a human before creating work.

## Sources

- SmashWiki — [Hitstun](https://www.ssbwiki.com/Hitstun)
- SmashWiki — [Stun](https://www.ssbwiki.com/Stun)
- SmashWiki — [Tech](https://www.ssbwiki.com/Tech)
