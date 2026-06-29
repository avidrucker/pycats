# Items — PM mechanics reference

> A concise survey of Project M's **item system** — pickups that spawn into the
> arena and alter the fight. The lightest doc in the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)): items are
> **off by default in competitive PM** and **out of scope for pycats**, so this is
> a reference survey, not a catalog. PM 3.6.

**Audience:** a contributor — human or agent — wanting a quick orientation on PM
items (e.g. if items are ever considered). Reference depth, not a tutorial.

## The item concept

An **item** is a world object that spawns onto the stage (randomly over time, or
from a container) and can be **picked up, held, thrown, or used** to alter the
fight. Items are a *casual/party* layer; **standard competitive PM turns items
off** (the Rules item toggle — see [menus-and-game-flow](./menus-and-game-flow.md)),
so a faithful 1v1 trainer needs none. That's a design fact about how PM is played,
not a missing feature.

## Categories

PM's item set largely inherits Brawl's. Broadly:

- **Battering** (beam sword, bat, …) — melee weapons that boost your attacks.
- **Throwing / shooting** (bob-omb, ray gun, …) — ranged/explosive damage.
- **Recovery / healing** (food, heart, Maxim tomato) — restore percent; **the one
  category with no analog elsewhere in the engine** (everything else reuses the
  standard hit model — see below).
- **Containers** (crate, capsule, barrel) — break to release other items.
- **Transforming / special** (Poké Ball / Assist-style, stat boosts) — summon or
  buff effects.

## Spawning & interaction

- **Spawning** is governed by the **item frequency + item set** in the Rules menu
  ([menus-and-game-flow](./menus-and-game-flow.md)); off for tournament play.
- **Interaction:** walk over to **pick up**, **hold** (you can still move/act),
  **throw** (a thrown item is an attack), or **use** (weapons modify your moves,
  consumables apply their effect).
- **Damage model:** an item's hit (thrown or swung) deals its own damage + knockback
  through the **standard hit-resolution model** — same knockback formula, hitstun,
  hitlag — see [combat-knockback-hitstun](./combat-knockback-hitstun.md) and
  [combat-hitboxes-priority](./combat-hitboxes-priority.md). So most of an item
  system is *content* (which objects exist), not new *mechanics* — except healing,
  which adds a percent-restore the engine otherwise never does.

> **Items vs projectiles:** a world *item* is distinct from a **projectile fired
> by a move** (Fireball, blaster) — those are part of a character's moveset
> ([moveset-and-frame-data](./moveset-and-frame-data.md)), not pickups.

## Brawl / Melee / PM deltas

- PM's item **roster** largely inherits Brawl's; Melee's set differs.
- Item *physics/behaviour* run on the same engine across the family.
- **Items-off** as the competitive norm is a ruleset convention, consistent
  Melee→PM.

## Sources

- SmashWiki — [Item](https://www.ssbwiki.com/Item).
- Item hit model: [combat-knockback-hitstun](./combat-knockback-hitstun.md); the items toggle: [menus-and-game-flow](./menus-and-game-flow.md); move-fired projectiles: [moveset-and-frame-data](./moveset-and-frame-data.md). Conventions: [00-overview](./00-overview.md).

## pycats status

**No item system — not planned / iceboxed.** pycats is a 1v1 trainer and items are
off in competitive PM, so none are needed for parity.

- The only projectile-adjacent hook is `Attack(disappear_on_hit=True)` in
  `pycats/entities/attack.py` (a commented example in `fighter_input.py`) — intended
  for a future **move-fired** ranged attack, **not** a world item.
- Broader "feel/polish" extras incl. ranged attacks are parked in the icebox
  proposal [#104](https://github.com/avidrucker/pycats/issues/104).

If items were ever added, most of it would reuse the existing hit model
([combat-knockback-hitstun](./combat-knockback-hitstun.md)); only **healing**
(percent restore) and the **pickup/hold/throw** entity lifecycle would be genuinely
new. Divergences: [#99](https://github.com/avidrucker/pycats/issues/99). Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
