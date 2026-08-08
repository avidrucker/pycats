# PM air-dodge tuning values — sourcing pass (#192 / #216)

> Sourcing pass for the air-dodge rows of `GUESSED_VALUES_TO_RESEARCH.md`, under the
> #192 umbrella. Records what each GUESS row could and could not be sourced to, and
> **why** — the headline being that the directional-boost magnitude is not obtainable
> from rukaidata the way #192's plan assumed.
>
> Method: targeted web research against the primary datamining sources named in
> `docs/research-120-smash-units-and-sources.md` (rukaidata PM3.6, SmashWiki, FightCore).
> Each numeric claim cross-checked against ≥2 sources. Date: 2026-06-29. Agent: DRAGONFRUIT.
> Area: `area:combat`. No code/sim change — pinning values is deferred (see #215).

## TL;DR

1. **Confirmed (primary):** the air-dodge **intangibility window** is frames **4–29 of a
   49-frame** air dodge; the **wavedash angle** is **17.1°**; **landing lag** is **10
   frames**; and a wavedash transfers **all** air-dodge momentum into the horizontal
   ground slide. The first corroborates a row that was previously a one-source guess;
   the latter three re-confirm values already FOUND and shipped in #202.
2. **Blocked:** `DODGE_AIR_SPEED` (the directional-boost magnitude) **cannot be sourced
   from rukaidata** — it is **engine-hardcoded**, not present in the datamined `.pac`
   subaction script. This invalidates the resolution path proposed in #192's comment for
   *this specific value* (it remains valid for hitbox sizes/positions). Filed as **#215**.

## Per-row outcome

| Row | Outcome | Evidence |
|---|---|---|
| Neutral air dodge → `(0,0)` halt | FOUND (qualitative) — unchanged | SmashWiki Air dodge: "halts momentum … hovering in place". |
| Directional air dodge → set (replace) | FOUND (qualitative) — unchanged | SmashWiki Air dodge: "small boost in the chosen direction"; #23. |
| `DODGE_AIR_SPEED` magnitude | **BLOCKED → #215** | rukaidata `EscapeAir` has no Self-Velocity command (engine-hardcoded); not on SmashWiki/FightCore. |
| Intangibility window 4–29 / 49f | **DIVERGENCE — canon now confirmed** | rukaidata PM3.6 `EscapeAir` (`IntangibleFlashing`@3 → `Normal`@29) + SmashWiki + FightCore agree; pycats keeps its 14f window by choice. |
| `DODGE_TIME` (14f vs Melee 49f) | DIVERGENCE (open feel decision) | rukaidata/FightCore: 49-frame air dodge total. pycats' 14f is its own scale. |
| Wavedash angle 17.1° | FOUND (re-confirmed) — shipped #202 | SmashWiki Wavedash. |
| Wavedash landing lag 10f | FOUND (re-confirmed) — shipped #202 | SmashWiki Wavedash. |
| Slide = momentum transfer | FOUND (mechanic) — validates #202 | SmashWiki Wavedash: "all of the momentum of the airdodge is transferred into horizontal (ground) movement". |

## Why rukaidata can't supply `DODGE_AIR_SPEED`

rukaidata (and its generator `brawllib_rs`) datamine the per-character `.pac` fighter
files and render each **subaction** as a script timeline: animation, hitbox commands,
GFX/SFX, and any **Self-Velocity** events. Spatial move data — hitbox *sizes* and
*positions* — lives in those scripts, which is exactly why `nalio_cat.py` could author
radii/positions as `round(units × PX_PER_UNIT≈5.4)` straight from rukaidata.

The **air dodge is different**: `EscapeAir` (subaction `0x46`) carries the animation and
the intangibility *flags*, but the **velocity it applies is set by the engine's hardcoded
air-dodge handler**, not by a scripted Self-Velocity event in the subaction. So the
subaction view exposes no magnitude — and neither would a `brawllib_rs` subaction dump.
Getting the true number means reading the engine's air-dodge code (the DOL / hardcoded
constants) or measuring it empirically. That is #215.

The community-standard Melee air-dodge speed is **≈ 3.1 units/frame** (× `PX_PER_UNIT`
≈ 5.4 ⇒ **≈ 17 px/frame**), but this pass could **not** corroborate the 3.1 against a
primary datamined source, so it is recorded only as a candidate — not pinned.

## What did NOT change

No constant was changed. `DODGE_AIR_SPEED` stays at the feel-tuned `14` until #215 lands
a primary value (or a playtest pins one). The umbrella #192 stays open: this pass resolved
the *sourceable* rows and converted the magnitude row from "derivable via rukaidata" to
"blocked on a binary datamine (#215)".

## Sources

- SmashWiki — [Air dodge](https://www.ssbwiki.com/Air_dodge),
  [Wavedash](https://www.ssbwiki.com/Wavedash).
- rukaidata — [PM3.6 Mario `EscapeAir`](https://rukaidata.com/PM3.6/Mario/subactions/EscapeAir.html),
  [PM3.6 Mario](https://rukaidata.com/PM3.6/Mario/); generator [rukai/rukaidata (`brawllib_rs`)](https://github.com/rukai/rukaidata).
- [FightCore](https://www.fightcore.gg/) — datamined Melee frame data (air dodge 49f total, active 4–29).
- pycats prior research: `docs/research/air-dodge-vertical-momentum-findings.md` (#23),
  `docs/research-120-smash-units-and-sources.md` (#120), `GUESSED_VALUES_TO_RESEARCH.md` (#192).
