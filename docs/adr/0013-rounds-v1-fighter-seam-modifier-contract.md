# ADR-0013 — ROUNDS v1 fighter-seam modifier contract

- **Status:** Accepted  *(2026-08-02 — owner ruling on #1097, per-seam, in a wayfinder grilling session)*
- **Date:** 2026-08-02

## Context

ROUNDS Mode (#347) wraps a card-draft loop around a pycats stock match. The #1076 premortem
established the central hypothesis: pycats is a **richer modifier surface** than ROUNDS' single
gun — a card is literally a `FighterData` / `MoveData` patch — but the two disagree on the combat
model (ROUNDS is HP-attrition; pycats is knockback + blast-zone KO), so a ROUNDS "survivability"
card has no direct analog.

#1097 entered as **"survivability mapping — what an HP/defense card becomes under knockback."**
In the grilling session the owner **decomplected** that framing: rather than map ROUNDS *card
families* onto pycats, enumerate the **atomic, individually-scalable seams** pycats already
exposes and decide **each one's modifier shape on its own**. A "card" is a *later* composition
over these primitives; v1 just needs each primitive to have a working, tunable seam. This ADR
records that per-seam contract.

Two grounding facts drove the rulings:

1. **No modifier / apply layer exists yet.** Every seam below is *readable and scalable*
   (`FighterData` / `MoveData` fields, serialized in `characters/data/<cat>.json`), but nothing
   *applies a delta*. The apply-layer is genuinely new work — it is what the map's "modifier
   mechanism" thread was reaching at.
2. **Velocities/speeds are integer-contracted** despite `FighterData`'s `: float` annotations.
   The `config/physics.py` constants (`JUMP_VEL = -13`, `MOVE_SPEED = 6`, `DASH_SPEED = 8`,
   `MAX_FALL_SPEED = 13`) and the shipped JSON values are all integers, and `pygame.Rect`
   truncates fractions each frame (ADR-0011 §3). So a velocity seam must `round()` on apply.
   `gravity` (e.g. `0.42`) is the sole genuine float among the physics attrs.

## Decision

### Two default modifier patterns

- **Continuous magnitude → multiplicative percent** (`± %`), with `round()` iff the target
  field is int-typed. Stacks order-independently, reads like ROUNDS' "×1.3", proportional
  across cats of different base values.
- **Small integer count → additive `± N`**, with a floor. A `× %` of a 2–6 count is coarse
  and no-ops small values (`2 × 1.2 → 2`).

Apply through a **named modifier seam**, never inline multiplies (spirit of ADR-0011 / #962).

### Per-seam ledger

| # | Seam | Field(s) / where | Modifier | Notes |
|---|------|------------------|----------|-------|
| 1 | Weight | `FighterData.weight: int` → KB term `200/(w+100)` in `combat/knockback.py::knockback` | mult %, `round()`, floor `≥1` | Defensive only; survivability effect nonlinear + inverse (helps at low %, little near KO %) → tuning is the swinginess thread's problem, not a blocker. |
| 2 | Jump height | `FighterData.jump_vel` (int-contracted) | mult %, `round()` | Card % is **velocity-%**, not √-corrected height-%. Feeds the edgeguard axis (#578/#754). |
| 3 | Move / dash / run / fall speed | `move_speed` / `dash_speed` / `run_speed` / `max_fall_speed` (int) | mult %, `round()` | One family, identical ruling. |
| 4 | Gravity | `FighterData.gravity: float` | mult %, **no round** | Only genuine float in the physics attrs. |
| 5 | Jump count | `FighterData.max_jumps: int` (2–6) | **additive `±N`**, floor `1` | A count, not a velocity. Feeds the edgeguard axis. |
| 6 | Move damage | `Hitbox.damage: float` | mult %, no round | Plain-inherit. |
| 7 | Hitbox reach / size | `Hitbox.r`, `dx`/`dy` (int) | mult %, `round()` | Reach touches priority / clank / same-frame multi-hit (#829/#843). |
| 8 | Body / hurtbox size | `stand_size` / `hurtbox` (int) | mult %, `round()` | Bigger = easier to hit → a downside seam. |
| 9 | Knockback | `base_knockback` / `knockback_growth` (float) | mult % (`±`) | The premortem's **#1 swinginess hazard** — compounds the nonlinear KB curve. Tuning → swinginess thread. |
| 10 | Stocks | `fighter.lives: int` (match-level; read by `systems/win_condition.py::winner_index`) | **additive `±N`**, floor `1` | Changes match length. |
| 11 | Frame data | `startup` / `active` / `recovery` (int) | **DEFERRED (v1)** | No clear "faster" semantics for a long move with a single active frame; revisit post-v1. |
| 12 | Angle | `Hitbox.angle: int°` | **OUT (non-seam v1)** | Directional, not a magnitude buff/nerf. |
| 13 | Recovery distance | `grants_recovery: bool`, `recovery_vx`/`recovery_vy: float` | **DEFERRED (v1)** | Premortem §3 rates recovery cards **"Breaks"** — trivializes edgeguarding (#578/#754). Revisit post-v1. |
| 14 | Novel "%-per-second" | *none — new field + a per-tick hook* | **INCLUDE v1, shape TBD via research** | Regen / heal / lifesteal / DoT — the "±dmg% per second" family. No seam exists; how to build it (and how PM/Brawl/Melee/meleelight handle it) is a follow-up RESEARCH ticket. |

## Consequences

- **The modifier apply-layer is the next real design decision.** Every seam 1–10 is
  scalable but there is no place a card applies a delta. Designing that layer (where deltas
  apply — load-time vs per-tick — how they stack, how `round()`/floors are enforced through a
  named seam) is now the live thread on the map.
- **Two seams deferred, one cut for v1:** frame data (11) and recovery distance (13) are
  deferred; angle (12) is out. Recovery distance is deferred specifically because it lands on
  the edgeguard game the premortem flags as pycats' highest-blast-radius, most PM-specific
  system.
- **The novel %-per-second family is in scope but unbuilt** — it needs both a pycats
  implementation design and an engine survey; a follow-up RESEARCH ticket owns both, and its
  survey coordinates with the fighter-buff-mechanics catalog (#1106) to avoid duplicate work.
- **Swinginess hazards are named, not solved:** weight's nonlinear/inverse curve (1) and
  knockback's compounding (9) are tuning problems handed to the swinginess thread, not
  reasons to withhold the seams.
- **Ruled out for v1:** frame-data scaling, angle as a card seam, recovery-distance scaling.

### Follow-up (filed downstream of this ADR)

1. **RESEARCH — novel %-per-second family** (`research` + `area:combat`): (1) how to implement
   a %-per-second regen/heal/lifesteal/DoT seam in pycats (new field + per-tick hook), and
   (2) how PM 3.6 / Brawl / Melee / meleelight handle regen/lifesteal/DoT today — cross-ref
   #1106 to dedup the survey.
2. **The modifier apply-layer** graduates from the map's fog as the next decision thread.

### Relationships

Parent epic **#347** (Rounds Mode). Wayfinder map **#1096**; resolves grilling ticket
**#1097**. Grounded by the #1076 premortem (fit matrix §3) and the #1099 seeding-contract
findings. Balance flags: edgeguard #578/#754, same-frame multi-hit #829/#843. Engine survey
coordinates with #1106. Conversion / int-contract precedent: **ADR-0011** (#962).
