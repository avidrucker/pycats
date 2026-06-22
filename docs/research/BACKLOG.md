# Research backlog

Open research threads to tackle later. Each links back to the findings doc that
spawned it.

## Brawl / Project M fighter states

Spawned by: [brawl-projectm-fighter-states.md](./brawl-projectm-fighter-states.md)

### a. State-to-state transition graph

Is there any published authoritative list of the actual **state-to-state
transition rules** (the directed state-machine graph: which action states can
legally transition to which), as opposed to just the enumerated list of
action-state IDs? If not published, can it be extracted from
[doldecomp/brawl](https://github.com/doldecomp/brawl) /
[BrawlHeaders](https://github.com/Sammi-Husky/BrawlHeaders)?

### b. Correct shield-pushback formulas

What are the correct Brawl shield-pushback formulas for **both defender and
attacker**? The previously-proposed formula
(`(damage×0.069+0.4)×shield` capped at 1.6) was **refuted** in verification.
Are the real formulas in the decompilation, or only datamined?

### c. Project M / Project+ deviations

How does **Project M / Project+ specifically deviate** from base Brawl in action
states, shield mechanics, and the addition of **powershield / parry** behavior?
Is there a PM-specific documented list distinct from base Brawl?

### (bonus) Collision-resolution algorithm

Does doldecomp/brawl or BrawlHeaders yet expose the concrete
**collision-resolution algorithm** (the order in which
shield/hitbox/hurtbox/grab collisions are tested and resolved each frame), or is
only the observer-interface scaffolding currently reconstructed?
