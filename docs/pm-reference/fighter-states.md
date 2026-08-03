# Fighter action states & transitions — PM mechanics reference

> The **action-state map**: the discrete states a fighter can be in, what enters
> and exits each, and which states override others. This doc ties the rest of the
> set together — it names the states; the *numbers* (shield HP, hitstun frames,
> throw data, ledge timings) live in the sibling docs it links to. Part of the
> [PM mechanics reference](./00-overview.md) ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6, Brawl/Melee deltas noted.

**Audience:** a contributor — human or agent — about to implement or modify the
fighter action FSM. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions (60 Hz integer frames).

## The model

PM (on Brawl's engine) gives every fighter exactly **one action state at a time** —
an enumerated *action* with a hex ID (`Wait = 0x0`, `Guard = 0x1B`,
`GuardDamage = 0x1D` shieldstun, … `Dead = 0xBD`). Each action drives an animation
(a *subaction* — a **separate ID namespace**) and gates what inputs do. There is a
public **list** of these IDs (OpenSA, rukaidata, BrawlHeaders `fighter.h`), but the
**transitions between them live in code**, not in any published table — so the map
below is assembled from behaviour, not copied from a spec.

Two things are *not* one-at-a-time and layer **over** the action state:
- **Attacks/specials** run as a sub-phase (startup → active → recovery) on top of
  the underlying ground/air state.
- **Tangibility** (vulnerable / intangible / armored) is an orthogonal flag set by
  the current state (dodges, ledge/respawn) — see [combat-hitboxes-priority](./combat-hitboxes-priority.md).

## State categories

**Grounded (actionable):** stand/wait · walk · dash → run · crouch (+ crouch→stand) · turn.
**Airborne:** jump (short hop / full hop) · double jump · fall · **helpless** (special-fall after up-B/airdodge, no actions until landing).
**Defense:** shield (GuardOn → Guard → GuardOff) · **shieldstun** (GuardDamage) · spot dodge · roll (fwd/back) · air dodge.
**Damage / disadvantage:** **hitstun** · **tumble** (high-knockback flailing, can be teched/DI'd) · **knockdown** (on the ground) · **getup** (neutral / roll / attack options) · **tech** (well-timed press → no knockdown) · shield-break **dizzy/stun**.
**Special:** ledge-hang (+ getup options) · grabbed / grabbing · pummel / thrown · respawn platform · KO/dead.

Mechanic *values* for these are owned by sibling docs: shield/dodge numbers →
[defense-shield-dodge](./00-overview.md); hitstun/tumble thresholds →
[combat-knockback-hitstun](./combat-knockback-hitstun.md); grab/throw →
[grabs-throws](./00-overview.md); ledge → [ledge-mechanics](./00-overview.md).

## Major transitions

- **Idle ⇄ movement:** stand → walk (tilt) / dash (tap) → run; run → skid/turn;
  hold down → crouch → (release) stand. All freely interruptible by jump, shield,
  attack, grab.
- **Ground → air:** jump squat → jump; walk/run off a ledge → fall; → ledge-hang
  if a grabbable edge is in range.
- **Air → ground:** fall → land (landing lag if mid-aerial; → helpless's landing
  if special-fall) → idle/run.
- **Into defense:** grounded + shield → Guard; Guard + direction → roll/spot dodge;
  airborne + dodge → air dodge → (often) helpless.
- **Into disadvantage:** any state + a clean hit → hitstun; enough knockback →
  tumble → (tech?) → knockdown → getup. Shield depleted → shield-break dizzy.
- **Exit:** each timed state (shieldstun, hitstun, dodge, dizzy, getup) returns to
  idle/fall when its frame timer expires.

## Interrupt / priority order

When several conditions are true on a frame, stronger states **override** weaker
ones. Roughly, highest first:

1. **KO / dead** (blast-zone or shield-break death) — overrides everything.
2. **Shield-break dizzy/stun** — locks all input.
3. **Hitstun / tumble** — a clean hit interrupts any action (incl. mid-attack);
   no acting until it ends (PM **removed hitstun cancelling**, so you can't airdodge
   out early).
4. **Grabbed** — locked until thrown / mash-released.
5. **Dodge / shieldstun** — committed for their window.
6. **Attack/special sub-phase** — occupies the fighter until recovery ends (or an
   interrupt above fires).
7. **Movement / idle** — the default, freely interruptible.

This ordering is why the implementation checks damage/stun timers *before*
movement input each frame.

## Brawl / Melee / PM deltas

- **Hitstun cancelling:** in Brawl, removed by **PM** (and absent in Melee) — a
  core reason PM combos feel Melee-like.
- **Teching / getup:** PM restores Melee-style tech windows and getup options that
  Brawl weakened.
- **Action vs subaction IDs:** two namespaces (e.g. GuardOn = action `0x1A` but
  subaction `0x3F`) — don't conflate when reading datamined dumps.
- **Helpless/special-fall** exists across the family; PM tunes air-dodge so it no
  longer always forces a free-fall the way Brawl did (movement-tech territory).

## Sources

- [`docs/research/brawl-projectm-fighter-states.md`](../research/brawl-projectm-fighter-states.md) — the enumerated state list, where it lives, and the shield-priority rule (deep-research, 107 agents / adversarially verified).
- OpenSA [`Actions (Brawl)`](http://opensa.dantarion.com/wiki/Actions_(Brawl)) / [`StatusIDs`](http://opensa.dantarion.com/wiki/StatusIDs); [BrawlHeaders `fighter.h`](https://github.com/Sammi-Husky/BrawlHeaders); rukaidata per-character action dumps.
- SmashWiki — [Hitstun](https://www.ssbwiki.com/Hitstun), [Tech](https://www.ssbwiki.com/Tech), [Helpless](https://www.ssbwiki.com/Helpless).

## pycats status

The action FSM runs as a swappable engine — a hand-rolled FSM (`legacy`) and a
hierarchical statechart (`statechart`), proven byte-identical — in
`pycats/charts/fighter_chart.py`, `pycats/systems/fighter_fsm.py`, driven by
`pycats/entities/player.py` + `pycats/entities/fighter.py`.

**States implemented:** `idle`, `run`, `jump`, `fall`, `shield`, `dodge`
(spot/roll/air), `crouch` ([#124](https://github.com/avidrucker/pycats/issues/124)),
`attacking` (startup/active/recovery → flat label `attack`), `hitstun` (`hurt`),
shield-break `stun`, `ko`, plus the orthogonal `defensive_status`
(`vulnerable`/`intangible`). The interrupt order above is enforced (damage/stun
timers gate input before movement) — incl. hitlag ([#138](https://github.com/avidrucker/pycats/issues/138)) and shieldstun ([#140](https://github.com/avidrucker/pycats/issues/140)).

**Deferred / not yet a state:**
- **walk** (only `run` exists today — no walk/dash/run split),
- **tumble / knockdown / getup / tech** (Phase 3),
- **helpless / special-fall**,
- **ledge-hang** ([#14](https://github.com/avidrucker/pycats/issues/14)), **prone/knockdown** ([#13](https://github.com/avidrucker/pycats/issues/13)),
- **grabbed / grabbing / thrown** (Phase 4).

Roadmap: `docs/research/pm-mechanics-implementation-analysis.md` (Phase 3 = defense
& hitstun states; Phase 4 = grabs). Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
