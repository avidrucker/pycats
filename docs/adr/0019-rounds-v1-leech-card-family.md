# ADR-0019 — ROUNDS v1 Leech card family: two heal cards (Vampire + Health Regen)

## Status

Accepted — 2026-08-04. Resolves the **ROUNDS Mode v1 wayfinder map** (#1096) decision
#1172 ("decide the Leech %-per-second card shape for ROUNDS v1"). Downstream of research
**#1111** (the novel %-per-second option space, findings-only) and **ADR-0014** (the
modifier apply-layer); epic #347.

## Context

The starter card set (#1101) slots a single **Leech** family as a "%-per-second" rider with
its shape deferred to research. Research #1111
(`docs/research/2026-08-04-rounds-novel-pct-per-second-findings.md`) mapped the pycats option
space and surveyed the Smash engines, deciding nothing: the family splits into three
mechanically-distinct shapes (flat regen/DoT · lifesteal = a fraction of damage dealt ·
on-absorb heal), each wanting a different field + hook, and pycats has **no timer-driven
`percent` mutator** today. This ADR picks the v1 shape by grilling #1111's nine open forks
with the designer.

Grounding facts, read from source 2026-08-04:

- **`percent` has a single mutator and a hard 0-floor.** `entities/fighter.py` sets
  `self._percent = max(0, value)` in the percent setter (the "S3 first guard"); there is no
  ceiling. `receive_hit` (`self.percent += atk.damage`) is the only place combat drives it up.
- **Knockback is super-linear in the victim's percent.** `combat/knockback.py::knockback`:
  `KB = (((((p/10)+(p*d/20))*(200/(w+100))*1.4)+18)*(KBG/100))+BKB`, where `p` is the victim's
  post-hit percent. Lower `p` → lower KB against that fighter.
- **`systems/` already houses frame-level game logic** — `systems/hit_resolution.py`
  (`process_hits`) and `systems/win_condition.py` are existing siblings; `systems/over_time.py`
  does not yet exist.
- **The apply-layer is settled** (ADR-0014): a card loadout rewrites `FighterData` **once** at
  the `build_fighter` seam via bare `(seam, op, value)` deltas, and `Fighter.__init__` caches
  each seam, so one patch feeds both the headless sim and the live game.
- **FPS is 60** (`config/screen.py`), so 1 s = 60 frames; the sim `snapshot` records
  `round(percent, 6)`.

## Decision

### 1. Shape — two cards, not one

The single "Leech" slot becomes **two named cards**, each an atomic seam (per the map's
decomplect note — a "card" is a later composition):

- **Vampire** — *lifesteal on-hit*: when the owner lands a melee hit, the owner heals a
  fraction of the damage dealt.
- **Health Regen** — *passive self-heal*: the owner heals a fixed chunk every N frames,
  combat-independent.

Both heal the **owner**. Neither is a DoT (no card in this family damages an opponent
over time in v1).

### 2. Field home — new `FighterData` fields, defaulted off

Two new `FighterData` fields carry the card knobs, both defaulted off so every existing cat
is unaffected:

- `lifesteal_fraction: float = 0.0` — Vampire sets it (e.g. `0.3`).
- `regen_rate` (+ its interval) — Health Regen sets it.

These are the **cached target** of ADR-0014's load-time patch: the card's delta rewrites the
field once at `build_fighter`, and `Fighter` reads it at `__init__`. Runtime fighter state was
rejected — it would need a second write path and break ADR-0014's "one patch feeds sim + live".

Card modifiers are **authored in a tweakable data file**, not hardcoded (direction affirmed).
The file's format + home (one file vs per-card, schema, location beside
`characters/data/<cat>.json`) is a **cross-card** concern larger than this ticket and is spun
into its own follow-up ARC ticket — see Follow-up.

### 3. Hook site — event-driven vs time-driven, kept separate

- **Vampire** hooks the existing **`systems/hit_resolution.py::process_hits`** — it is an
  event on landing a hit, and `process_hits` already knows the damage dealt.
- **Health Regen** gets a **new `systems/over_time.py`** (sibling of `win_condition.py`), a
  time-driven per-frame system the runner calls at a fixed point.

Two hooks for two cards is correct, not a smell: they trigger on fundamentally different things
(a hit event vs elapsed time). Forcing one mechanism to carry both would make Vampire poll
"did I hit this frame?" when `process_hits` already has the answer.

### 4. Accumulation — per-N-frame interval (Smash-faithful)

Health Regen heals a fixed chunk **every N frames**, matching the Smash engine idiom
(Flower/Lip's-Stick DoT ticks 1% every 21 frames; Curry similarly). This needs a **per-fighter
frame counter** (transient runtime state, like the existing `tick_timers`). The interval N and
the heal-chunk are **tunable config** authored in the modifiers file (by-feel; #1156), not
fixed here.

Per-frame-fraction and per-second-batch were considered and rejected for v1 in favor of the
engine-faithful interval.

### 5. Tick order — carved out to research #1173

Where `over_time` slots in the frame loop relative to `process_hits` and `snapshot`, and
whether pycats's existing frame order matches PM 3.6 / Brawl / Melee, is deferred to
**RESEARCH #1173** ("pycats frame/tick order faithfulness for the ROUNDS over_time system").
The DEV build waits on #1173 for the slot; the *shape* above does not.

### 6. Duration — permanent-for-the-match

Both cards are **always-on while owned**; no countdown, no expiry, no second decrement field.
A drafted card is a standing property of the fighter (recomputed each round from the immutable
baseline per ADR-0014), unlike the timed item pickups (Curry 13 s, Flower cap) the survey found.

### 7. KB coupling — no v1 mitigation

The #1111 percent→KB swinginess hazard is a **DoT** concern: a DoT inflates the victim's
percent, and because KB is super-linear in percent, it inflates everyone's KB against that
victim (snowball, handed to #1076). v1's Leech family is **heal-only**, so it runs the opposite
direction — lower percent → **lower** KB against the owner. That is the survivability the cards
sell, and it self-limits (healing near 0% barely moves KB; it matters most pulling the owner
back from the KO zone). No cap, no exemption. **The #1076 hazard only bites if a DoT card is
added post-v1** — that is when the swinginess thread must revisit. Stalling (a heavy healer
hard to KO) is a *balance* concern, explicitly v1-out-of-scope / emergent (#1156).

### 8. Clamping / KO — the existing 0-floor, nothing more

Both cards only *reduce* percent, so the existing `max(0, value)` floor catches the bottom:
they **heal up to a maximum of 0%**. No new clamp, no ceiling. Neither can KO — KO in pycats is
blast-zone only, never a percent threshold, and a heal cannot send anyone anywhere.

**v1 assumption flagged:** the global `max(0, value)` floor is *not* a permanent invariant.
Future cards are planned that drive percent **negative**; whoever builds those must lift or
make-conditional the hardcoded floor (a per-effect clamp, or a per-fighter min-percent). That
is out of scope here and recorded as map fog.

### 9. Determinism — fully deterministic, no RNG

Both cards are deterministic and touch **no** #166 seeded stream: Vampire's heal is a fixed
fraction of the damage dealt (computed at hit time); Health Regen's is a fixed chunk on a fixed
interval. The byte-identical ordinary-vs-seeded golden property holds. The only thing that would
force an RNG draw is a *probabilistic* tick, which neither card is.

## Consequences

- pycats gains its **first time-driven `percent` mutator** (`systems/over_time.py`) and its
  first on-hit self-heal (in `process_hits`) — both new seams, both deterministic, both
  golden-safe.
- Two new `FighterData` fields default off, so existing cats and their JSON are unchanged
  (dataclass defaults tolerate the missing keys).
- The exact heal magnitudes, the interval N, and same-card stacking are **not** fixed here —
  by-feel at build time (#1156), authored in the modifiers file.
- The DEV build is **blocked on #1173** (tick-order slot) before `over_time` can be wired into
  the runner.

## Follow-up

- **File an ARC ticket** for the card-modifier catalog **file format + home** (cross-card;
  affects all 9+ starter cards) — the "tweakable data file" whose *direction* this ADR affirms
  but whose schema it does not fix.
- **RESEARCH #1173** resolves the `over_time` frame-loop slot + Smash tick-order faithfulness.
- Downstream DEV children (post-map, one at a time): Vampire in `process_hits`; Health Regen +
  `systems/over_time.py` (after #1173); the two `FighterData` fields + their apply-layer deltas.
- Map fog: **future negative-% cards must revisit the `Fighter` `max(0, value)` floor.**

## Relationships

- Resolves **#1172** (Leech card shape), a child of the **ROUNDS Mode v1 wayfinder map**
  (#1096), epic **#347**.
- Downstream of research **#1111** (novel %-per-second option space + engine survey) and
  **ADR-0014** (the apply-layer that carries the two new fields).
- Surfaces **#1173** (frame/tick-order faithfulness) as a blocker of the DEV build.
- Refines the starter set **#1101** (one "Leech" family → the two named cards Vampire +
  Health Regen).
- Coordinates with **#1076** (swinginess premortem — the DoT-inflates-KB hazard this family
  sidesteps by being heal-only) and **#1156** (post-v1 balancing — magnitudes, intervals,
  stacking).
- Grounded in: `entities/fighter.py` (the `percent` setter's 0-floor + seam caching),
  `combat/knockback.py::knockback` (the super-linear percent→KB term), `systems/hit_resolution.py`
  (Vampire's hook), `systems/win_condition.py` (the `over_time.py` sibling pattern),
  `config/screen.py` (FPS = 60).
