# Air dodge & vertical momentum — is the cancel intended? (#23)

> Research findings for #23 (child of the Brawl/PM fighter-state umbrella **#24**):
> does pycats' air dodge cancel vertical momentum, and is that intended versus
> Project M?
>
> Method: source reading of the live air-dodge path on `main` +
> SmashWiki / Smashboards corroboration of Melee/Brawl/PM air-dodge mechanics.
> Date: 2026-06-29. Agent: DRAGONFRUIT. Area: `area:combat`.

## TL;DR

**The ticket's premise is stale: pycats air dodge does NOT zero vertical
momentum on current `main` — it _preserves_ it (Brawl-style).** So there is no
"momentum-cancel" defect to fix.

The more useful finding underneath the question: **Project M uses the
_Melee_-style air dodge, which deliberately _halts_ (replaces) all momentum** and
drops the fighter into a **helpless / special-fall** state afterward. pycats does
neither the halt nor the helpless — its air dodge is a **Brawl/Melee hybrid that
matches neither game cleanly**. The real gap is not "we wrongly zero Y" but "we
don't model PM's air dodge at all yet."

So the answer to the literal question is: **zeroing vertical momentum is not a
bug, but it is also not what `main` does.** For PM fidelity, momentum *should* be
replaced — but only as one piece of a larger Melee-style package, not as an
isolated `vel.y = 0`.

## What pycats actually does today (`main`)

Air dodge lives in `pycats/entities/fighter.py::_start_dodge` (velocity) and
`pycats/entities/fighter_input.py` (trigger), with physics in
`pycats/entities/fighter_physics.py`. (The ticket points at
`pycats/statecharts/fighter_chart.py` — stale path; the chart is now
`pycats/charts/fighter_chart.py`, but the velocity logic is in `fighter.py`, not
the chart. The chart only routes `dodge_timer > 0 → "dodge"` leaf and back to
`fall`.)

| Aspect | pycats behavior | Code |
| --- | --- | --- |
| **Vertical momentum** | **Preserved** — `_start_dodge` never touches `vel.y` for any air dodge | `fighter.py:333-355` |
| **Neutral air dodge** (no dir) | Velocity **unchanged** (both x and y kept) | `fighter.py:333-338` |
| **Directional air dodge** | **Additive** horizontal nudge `vel.x += dir_x * DODGE_SPEED` (14 px/f); `vel.y` kept | `fighter.py:352-354`, `fighter_input.py:146` |
| **Gravity during dodge** | Normal gravity keeps applying — Y keeps accelerating down | `fighter_physics.py:30-36` ("Air dodges should still have normal gravity") |
| **After dodge** | `dodge_timer` (14 frames) expires → `fall` leaf. **No helpless / special-fall state exists** | `fighter_chart.py:192` |
| **Per-airtime limit** | **Once** per jump/fall — `air_dodge_ok`, reset on land | `fighter.py:233,280`, `fighter_input.py:148-152` |
| **Invulnerability** | `invulnerable = True` for the 14-frame `DODGE_TIME` | `fighter.py:322-323` |

Net: pycats air dodge = **momentum-preserving** (Brawl) + **once-per-airtime**
(Melee) + a **horizontal additive nudge** (neither game) + **no helpless**
(Brawl). It is a hybrid.

`grep` for `helpless|special.?fall|freefall` across `pycats/` returns nothing —
pycats has **no helpless state**, so the defining consequence of a Melee/PM air
dodge is simply absent.

## What Melee / Brawl / Project M actually do

From SmashWiki ([Air dodge](https://www.ssbwiki.com/Air_dodge)) and corroborating
Smashboards/SmashWiki PM coverage:

| | **Melee** | **Brawl** | **Project M** |
| --- | --- | --- | --- |
| Existing momentum | **Halted / replaced** | **Preserved** | **Halted / replaced** (Melee model) |
| Directional input | Small fixed **boost** in stick direction | No nudge | **Boost** (Melee model) |
| After dodge | **Helpless** (special-fall) until land | Actionable, no lag | **Helpless** (Melee model) |
| Uses per airtime | **Once** | **Unlimited** | **Once** |
| Wavedash | Yes (airdodge diagonally into ground) | No | **Yes — restored** |

Key SmashWiki quotes (Air dodge):

> "The air dodge **halts the character's momentum**; if the control stick is not
> tilted, it leaves the character hovering in place for most of its duration" …
> "if the control stick is tilted, it gives the character a **small boost in the
> chosen direction**." … "After air dodging, characters enter a **helpless
> state** and fall to the ground." *(Melee)*

> "In Brawl, the air dodge … no longer halts the character's momentum and no
> longer permits the user to nudge the character … it simply grants brief
> intangibility along the character's **current line of movement**." *(Brawl)*

Project M's whole identity here is **restoring the Melee air dodge** (and thus
wavedashing) over Brawl's momentum-preserving one — confirmed by SmashWiki's
Project M page and Smashboards tech guides ("Air dodging in Project M applies a
directional boost and causes helplessness … restoring the wavedash techniques
vital for most characters' metagames").

Melee frame reference: ~49-frame animation, intangible ~frames 4–29.

## So, is cancelling vertical momentum "intended"?

Three layers, because the question conflates them:

1. **Is it a bug that pycats zeroes Y on air dodge?** — Moot: **`main` doesn't
   zero it.** The premise doesn't reproduce. The code explicitly preserves Y
   (comment + behavior) and applies normal gravity through the dodge. No
   momentum-cancel defect exists to file.

2. **Would zeroing Y be PM-correct?** — Partly. PM/Melee air dodge **does replace
   momentum** (neutral → zero, hover in place). So a *momentum replacement* is the
   PM-faithful direction of travel. But a bare `vel.y = 0` in isolation would be
   *Melee-wrong the other way*: without the **helpless/special-fall** lockout, you
   would zero momentum and then immediately act — which is neither Brawl
   (preserve + actionable) nor Melee (halt + helpless). Don't ship the halt
   without the helpless.

3. **What's actually missing for PM?** — The full Melee-style air dodge package:
   - **Momentum replacement** (neutral → ~zero; directional → fixed-magnitude
     burst in stick direction, *set* not *added*).
   - A **helpless / special-fall** state entered after the dodge, locking normal
     actions until landing.
   - **Wavedash** falling out naturally once an air dodge into the ground cancels
     into a grounded slide governed by traction.
   - Keep the existing once-per-airtime + intangibility window.

## Recommendation

- **Close #23.** The literal question ("is air-dodge cancelling vertical momentum
  intended?") resolves to: *it isn't cancelling it on `main`, and a bare cancel
  is not the right fix anyway* — so there is **no DEV bug and no `wontfix`
  behavior to bless**; the premise is stale. This findings doc is the
  deliverable.
- **Follow-up is a feature, not a defect.** PM-faithful air dodge (momentum
  replacement + directional burst + **helpless state** + wavedash) is an
  `enhancement` under umbrella **#24**, not a `severity:*` bug. It is sizeable
  (introduces a new `helpless`/special-fall leaf to the fighter chart) and is
  natural to sequence **with the basic-attacks / movement-tech combat phases**,
  alongside DEV work like #135 — not before it. **Filed as #184**
  (`enhancement` + `area:combat` + `deferred`, under umbrella #24): PM-faithful
  air dodge — momentum replacement + directional fixed-burst + a new
  `helpless`/special-fall chart leaf + wavedash.

## Caveats & gaps

- Melee/PM mechanics here are **SmashWiki + Smashboards** community
  documentation (datamined/measured), reliable and cross-corroborated but
  secondary-tier — not decompilation output. Consistent with the umbrella #24
  source-quality caveats.
- **Exact PM air-dodge velocity magnitude** (the fixed directional-burst speed,
  and any per-character variation) was **not** pinned down here — it is a tuning
  input for the eventual feature, not needed to answer the yes/no question.
- pycats' current **horizontal additive nudge** on directional air dodge
  (`vel.x += …`) is itself non-canonical (Melee *sets* the vector; Brawl adds
  nothing). Flagged for the feature ticket, out of scope for this finding.

## Sources

| Source | Quality | What it gives |
| --- | --- | --- |
| [SmashWiki — Air dodge](https://www.ssbwiki.com/Air_dodge) | secondary (authoritative community) | Melee halts-momentum + boost + helpless; Brawl preserves-momentum; frame data |
| [SmashWiki — Project M](https://www.ssbwiki.com/Project_M) | secondary | PM restores Melee air dodge → directional boost + helplessness + wavedash |
| [SmashWiki — Wavedash](https://www.ssbwiki.com/Wavedash) | secondary | Air-dodge-into-ground = wavedash; traction-governed slide |
| [Smashboards — PM underused techniques](https://smashboards.com/threads/project-m-the-underused-techniques-youre-probably-not-using.354762/) | tertiary | PM air-dodge / wavedash in practice |
| `pycats/entities/fighter.py`, `fighter_input.py`, `fighter_physics.py`, `charts/fighter_chart.py` | primary (this repo) | Current air-dodge behavior on `main` |
