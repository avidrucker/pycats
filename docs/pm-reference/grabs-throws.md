# Grabs & throws — PM mechanics reference

> The **grab game**: seizing an opponent who can't be hit while shielding, then
> pummeling or throwing them. This doc owns the grab/throw model; the
> **grabbed/grabbing states** are named in [fighter-states](./fighter-states.md),
> shield/OOS context in [defense-shield-dodge](./defense-shield-dodge.md), and throw
> **knockback** uses the formula in [combat-knockback-hitstun](./combat-knockback-hitstun.md)
> — linked, not restated. Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6.
>
> **Note on values:** grab/throw *mechanics* are well-established and described
> qualitatively here; PM-specific *numbers* (per-throw damage/frames) are
> per-character and should be taken from a PM source (rukaidata / SmashWiki PM
> pages) at authoring time, not memorised.

**Audience:** a contributor — human or agent — about to implement or modify
grabs/throws. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames).

Grabs are the answer to shielding: a shield blocks attacks but **not** grabs, so
the grab/attack/shield triangle (attack beats shield-via-shieldstun-pressure,
grab beats shield, shield beats attack, spacing/movement beats grab) is the core
neutral-game rock-paper-scissors.

## The grab

- **Standing grab** — from idle; short range, fast.
- **Dash grab** — while running; longer range, more endlag.
- **Pivot grab** — a turnaround grab covering the space behind a dash.
- **Out-of-shield (OOS) grab** — the dedicated grab from shield (no GuardOff
  needed); a primary punish for an attack you just blocked (see
  [defense-shield-dodge](./defense-shield-dodge.md)).

A whiffed grab has significant **endlag** (the risk side of the RPS): grabbing air
is heavily punishable, which is why spacing/movement beats grab.

## Grab hold

A successful grab puts the attacker in **grabbing** and the victim in **grabbed**
(held, unable to act except to mash — below). The hold has a **maximum duration
that scales inversely with the grabbed fighter's damage**: a low-% opponent is held
longer; a high-% opponent slips out sooner. This bounds how long you can pummel and
forces a throw decision.

## Pummel

While holding, the attacker can **pummel** — repeated taps that each deal **minor
damage** to the held opponent. Pummeling trades hold-time for chip damage; pummel
too long at high % and the opponent escapes before you throw.

## Throws

From the hold, a direction commits a **throw** — each its own move with its own
damage and launch angle:

- **Forward / back throw** — reposition or send toward the ledge; common KO or
  edgeguard-setup throws.
- **Up throw** — launches upward; combo starter at low %, KO throw at high %.
- **Down throw** — plants the opponent low; the classic **combo-starter** (often
  into aerials).

Throw knockback uses the standard launch model
([combat-knockback-hitstun](./combat-knockback-hitstun.md)) with the throw's BKB/KBG/
angle; some throws also deal hits to **nearby** opponents (the throw's collateral
hitbox), distinct from the thrown victim's damage.

## Release & mash-out

- **Grab release** — if neither a throw nor pummel resolves, the grab **releases**.
  A **ground release** vs **air release** (the victim's state at release) leads to
  different follow-up windows — some characters have guaranteed release punishes,
  a known mixup layer.
- **Mash-out** — the grabbed fighter **mashes inputs** (stick/buttons) to shorten
  the hold and escape sooner; combined with the damage-scaling above, this means a
  high-% mashing opponent is very hard to hold.

## Brawl / Melee / PM deltas

- **Grab mechanics differ across the family** — Melee grabs are shorter-range/faster;
  Brawl added more grab range + the *grab-release* game; PM tunes grab range, release
  behaviour, and throw combo utility toward its competitive balance.
- **Throw values are PM-specific** — use PM 3.6 data, not Melee/Brawl, where they
  differ.
- **Pummel/mash rates** vary by game; the *direction* of the rule (more damage →
  shorter hold; mashing shortens it) is consistent.

## Sources

- SmashWiki — [Grab](https://www.ssbwiki.com/Grab), [Throw](https://www.ssbwiki.com/Throw), [Pummel](https://www.ssbwiki.com/Pummel), [Grab release](https://www.ssbwiki.com/Grab_release), [Mashing](https://www.ssbwiki.com/Mashing), [Out of shield](https://www.ssbwiki.com/Out_of_shield).
- PM-specific per-character throw data: [rukaidata PM 3.6](https://rukaidata.com/PM3.6/) / SmashWiki PM character pages.
- State names: [fighter-states](./fighter-states.md); shield/OOS: [defense-shield-dodge](./defense-shield-dodge.md); throw KB: [combat-knockback-hitstun](./combat-knockback-hitstun.md). Conventions: [00-overview](./00-overview.md).

## pycats status

**Not implemented — deferred to Phase 4** (Grabs & throws) on the roadmap
`docs/research/pm-mechanics-implementation-analysis.md`. There is no grab, grabbed,
grabbing, pummel, throw, or grab-escape behaviour today.

The intent is captured as source TODOs:
- `pycats/entities/player.py` — `#### TODO: implement grabbed state` / `grabbing state`; "grabs which are combo regular-attack + shield … put the opponent into a grabbed state … then throw … or follow-up"; "make player shielding ineffective against grabs". **Note:** the "grab = attack + shield combo" is **pycats design intent** from these TODOs, not the PM input itself.
- `pycats/entities/attack.py` — `#### TODO`: implement grabbing (hold duration scales inversely with defender %), throw attacks (forward/back/up/down), pummel (minor damage), and grab-escape (mash to escape sooner).

When built, the grabbed/grabbing **states** belong in the fighter chart
([fighter-states](./fighter-states.md)), throws reuse the knockback formula
([combat-knockback-hitstun](./combat-knockback-hitstun.md)), and grab beats shield
per the RPS above. Ledge *grabbing* is a separate concern → `ledge-mechanics.md`
([#14](https://github.com/avidrucker/pycats/issues/14)).

Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
