# PM/Brawl hit/hurtbox model — how it works, what to replicate in pycats, and whether a box editor is warranted

**Ticket:** #782 (RESEARCH · `area:combat`). **Produces:** this findings doc. Follow-up
DEV/decision tickets are filed one-at-a-time downstream (none filed here).

**Grounding note.** PM/Brawl claims are cited to a primary source: `brawllib_rs` source
(the parsing crate rukaidata.com is built on) for the data model, SmashWiki for runtime
semantics, and my own `brawllib_rs` datamine run for the worked-example numbers.
Tool-derived and community-inferred facts are labelled as such; inference is called out
inline. In-repo facts are grounded in the code read for this ticket.

---

## TL;DR

- **pycats is already most of the way there.** It has a working, deterministic,
  circle-based hit/hurtbox system with the exact SmashWiki **knockback formula**, WDSK,
  Sakurai-angle resolution, hitstun, hitlag, clank, and multi-hit — and Nalio's
  **offensive** kit is transcribed from real PM 3.6 data. The ticket's "Nalio has only a
  coarse hurtbox" is true **only of the defensive hurtbox**; the hitboxes are datamined.
- **PM's model is a bone-anchored 3-D capsule system.** Hurtboxes and hitboxes are both
  capsules (two endpoints + one radius) hung off skeleton bones, resolved per animation
  frame; hitboxes are swept (previous→current frame) to prevent tunnelling; hit = hitbox
  capsule overlaps hurtbox capsule.
- **The parity ceiling is already documented (#310) and it is the crux of (iii):**
  combat **scalars** (damage/angle/KBG/BKB/weight/frames) transfer **exactly** and are
  datamineable; **positions** (`dx`/`dy`) **cannot** be made pixel-faithful because pycats
  has no skeleton and there is no fixed unit→pixel scale. Positions are a "feel" quantity.
- **(iii) recommendation — do not build the in-game editor yet.** The highest-value, lowest-
  risk path is **(a) finish transcribing datamined scalars** (mechanical, exact, cheap) and
  **(b) hand-author positions against the #777 GIF reference** as feel values. An in-game
  editor is a real option and the *right* tool for the positional/feel layer specifically,
  but it is a sizable build whose payoff only lands once you are iterating on box *positions*
  heavily — which isn't the current bottleneck. Revisit it when hand-authoring becomes the
  measured pain point. Full reasoning in §(iii).

---

## What pycats already has (reframing the ticket premise)

Read before the parity discussion — it changes what "implement your own version" means.

| Layer | Status in pycats today | Landmark |
|---|---|---|
| Hit/hurtbox **geometry** | Circle-based (`Circle(dx,dy,r)`), pure/pygame-free | `pycats/combat/data.py`, `pycats/combat/geometry.py` |
| **Hit resolution** | `process_hits` — overlap test, priority order, clank | `pycats/systems/combat.py` |
| **Knockback formula** | Exact SmashWiki equation + WDSK + decay | `pycats/combat/knockback.py` |
| **Sakurai angle (361)** | Sentinel resolved (grounded linear ramp / airborne fixed) | `knockback.sakurai_angle` |
| **Hitstun / hitlag** | SmashWiki-sourced, per-frame | `knockback.hitstun_frames` / `hitlag_frames` |
| **Per-hitbox active window** | `active_start`/`active_end` (#204) | `combat/data.py` `Hitbox` |
| **Multi-hit / rehit rate** | `rehit_rate` looping (#213) | `combat/data.py` `MoveData` |
| **Projectiles** | `projectile_speed`/`lifetime` moving `Attack` | `pycats/entities/attack.py` |
| **Nalio offensive kit** | jab/tilts/aerials/smashes/fireball — **datamined PM 3.6 scalars** | `pycats/characters/nalio_cat.py` |
| **Nalio hurtbox** | **coarse** — reuses the generic 2-circle 40×60 body stack | `nalio_cat.py` `_HURTBOX` |
| **Skeleton / bones** | none — fighters are rectangles with drawn features | (by design) |
| **Hitbox interpolation (sweep)** | none — instantaneous circle each frame | (gap) |

So the real question this doc answers is not "how do we build a box system" — it exists —
but **"how much closer to PM-faithful should the existing system get, and by what
authoring path (transcribe / hand-author / editor)?"**

---

## (i) How hit/hurtboxes work in Project M / Brawl

PM is a Brawl mod; the **hit/hurtbox geometry engine is Brawl's**, so the model below is the
Brawl model. PM's documented differences are all in the *reaction* layer (§(i).7).

### (i).1 — Hurtboxes: bone-anchored capsules with a state

A hurtbox is a **capsule** (two endpoints + one radius) anchored to a skeleton bone. Verbatim
from the parser (`brawllib_rs/src/sakurai/fighter_data/misc_section.rs`):

```rust
pub struct HurtBox {
    pub offset: Vector3<f32>,
    pub stretch: Vector3<f32>,
    pub radius: f32,
    pub enabled: bool,
    pub zone: HurtBoxZone,       // Low | Middle | High
    pub grabbable: bool,
    pub trap_item_hittable: bool,
    pub bone_index: u16,
}
```

`offset` and `stretch` are the two capsule endpoints in **bone-local** space; `radius` is
swept between them; `bone_index` picks the bone it rides. The renderer confirms the capsule
shape — it draws both endpoints as a cylinder (`draw.rs`: `draw_cylinder(prev, next,
radius…)`), and the source even annotates that `offset`+`stretch` are *"less of an offset +
stretch and more like two separate independent offsets"* — i.e. two endpoints, not an
origin+extent. A character has an ordered **list** of these, one or more per bone.

SmashWiki corroborates the runtime meaning ([Hurtbox](https://www.ssbwiki.com/Hurtbox)):
hurtboxes are *"spheres and sphere-like structures known as capsules (cylinders with spheres
on the ends),"* attached to bones so they track the animation. Per-frame each hurtbox has a
**state**, verbatim from `brawllib_rs/src/script_ast/mod.rs`:

```rust
pub enum HurtBoxState {
    Normal, Invincible,
    IntangibleFlashing, IntangibleNoFlashing, IntangibleQuickFlashing,
    Unknown(i32),
}
```

SmashWiki definitions ([Hurtbox](https://www.ssbwiki.com/Hurtbox)):
- **Normal (yellow):** takes damage/knockback.
- **Invincible (green):** *"can be hit … but do not take any damage or knockback"* — the hit
  registers, effects are nullified.
- **Intangible (blue):** *"cannot be hit"* — no collision; the hitbox passes through.

The resolved per-frame form (`high_level_fighter.rs`) wraps the raw box with the bone's world
matrix for that frame and the state:

```rust
pub struct HighLevelHurtBox {
    pub bone_matrix: Matrix4<f32>,
    pub hurt_box: HurtBox,
    pub state: HurtBoxState,
}
```

### (i).2 — Hitboxes: bone-anchored capsules with ~50 parameters

A hitbox is spawned by a script event during a move and carries a large parameter set. The
fully-resolved value struct (`high_level_fighter.rs`, `HitBoxValues`) — abridged to the
load-bearing fields:

```rust
pub struct HitBoxValues {
    pub hitbox_id: u8,        // intra-move priority: lowest id wins a same-frame tie
    pub set_id: u8,           // "set" grouping (rehit / interpolation identity)
    pub damage: f32,
    pub trajectory: i32,      // launch angle in degrees (or a special code, §(i).5)
    pub wdsk: i16,            // weight-dependent set knockback
    pub kbg: i16,             // knockback growth
    pub bkb: i16,             // base knockback
    pub shield_damage: i16,
    pub size: f32,            // radius
    pub tripping_rate: f32,
    pub hitlag_mult: f32,
    pub sdi_mult: f32,
    pub effect: HitBoxEffect, // element (Normal, Flame, Electric, …)
    pub ground: bool, pub aerial: bool,   // can-hit gating
    pub clang: bool,          // participates in clank/priority
    pub direct: bool,         // direct (body) vs indirect (article/projectile)
    pub rehit_rate: i32,
    pub angle_flipping: AngleFlip,
    pub stretches_to_bone: bool,
    // + can_hit1..13 target-class flags, can_be_shielded/reflected/absorbed,
    //   ignore_invincibility, freeze_frame_disable, flinchless, …
}
```

Position lives alongside the values, not inside them: the low-level event
(`HitBoxArguments`) carries `bone_index` + `x_offset`/`y_offset`/`z_offset` (bone-local), and
`gen_hit_boxes` computes the world position as **`bone_matrix × offset`** each frame. So a
hitbox is "radius `size`, `offset` from bone `N`, live on the frames the script has it
spawned."

SmashWiki parameter semantics ([Hitbox](https://www.ssbwiki.com/Hitbox)):
- **Bone:** *"A bone of 0 or 'top' only follows the character's position, while other values
  correspond to different bones … and follow their movement."*
- **X/Y/Z offset:** *"displacement relative to the attached bone."*
- **Size:** *"specified as a radius measured in distance units."*
- **Hitbox ID (intra-move priority):** *"If multiple hitboxes of an attack connect within
  the same frame, the hitbox with the lowest ID value registers the hit."*

### (i).3 — Containment and the active-frame window

`HighLevelFighter → subactions → frames → { hit_boxes, hurt_boxes }`
(`high_level_fighter.rs`). Each `HighLevelFrame` is one animation frame and holds the boxes
live on that frame. There is **no stored start/end frame** — a hitbox appears in
`frame.hit_boxes` for exactly the frames between its `CreateHitBox` script event and the
matching `DeleteHitBox`/`DeleteAllHitBoxes` (or subaction end). Hurtboxes differ: they come
from the fighter's static list **every** frame; only their `HurtBoxState` changes.

### (i).4 — Hitbox interpolation (the swept capsule); hurtboxes are NOT swept

This is the subtlety most reimplementations miss. SmashWiki ([Hitbox](https://www.ssbwiki.com/Hitbox),
verbatim): a hitbox occupies *"not only the space where they currently are, but also the
space where they were one frame ago, as well as all the space in between (in a straight line
…)."* Purpose: *"prevents fast projectiles from passing through characters undetected"*
(anti-tunnelling). So a radius-`r` hitbox moving from center A to center B is tested as a
**capsule swept A→B**, not two discrete circles.

`brawllib_rs` encodes exactly this — each resolved hitbox stores both endpoints:

```rust
pub struct HighLevelHitBox {
    pub hitbox_id: u8,
    pub prev_pos: Option<Point3<f32>>, pub prev_size: Option<f32>,   // previous frame
    pub next_pos: Point3<f32>,         pub next_size: f32,            // this frame
    // …values…
}
```

`prev_pos` is `None` on the first active frame (degenerates to a sphere). Interpolation is
kept only across frames with the **same `set_id`**. The separate `stretches_to_bone` flag
reuses the same two-endpoint machinery to make a long fixed capsule from the hitbox out to
its bone.

**Asymmetry (verbatim, [Hurtbox](https://www.ssbwiki.com/Hurtbox)):** *"hurtboxes do not
interpolate across frames like hitboxes do, potentially allowing fast-moving characters to
pass through stationary hitboxes without damage."* Only the hitbox side is swept.

### (i).5 — Hit resolution → damage → knockback → angle

1. **Overlap:** *"when an attack's hitbox overlaps with a hurtbox, the attack is considered a
   hit"* ([Hurtbox](https://www.ssbwiki.com/Hurtbox)) — capsule-vs-capsule, gated by
   hurtbox state and the hitbox can-hit flags. Same-frame ties resolve to the lowest hitbox
   id.
2. **Damage** adds to the victim's percent.
3. **Knockback** ([SmashWiki — Knockback](https://www.ssbwiki.com/Knockback), verbatim):

   ```
   KB = ((((( p/10 + p×d/20 ) × 200/(w+100) × 1.4 ) + 18 ) × s ) + b ) × r
   ```

   `p` = victim percent **after** the hit, `d` = damage, `w` = weight, `s` = KBG/100,
   `b` = BKB, `r` = situational ratios (1 for a plain hit). **pycats implements this exactly**
   (`combat/knockback.py`, same SmashWiki citation).
   - **Set / WDSK** ([Set knockback](https://www.ssbwiki.com/Set_knockback)): a set-knockback
     hit ignores victim percent — `d` is replaced by the WDSK value and `p` is fixed at 10;
     weight (and KBG/BKB) still apply. *(The "d replaced, p=10" internal mechanic reads as
     community reverse-engineering on the wiki, not a cited disassembly — labelled inference.)*
     pycats matches: `set_knockback(wdsk,…) = knockback(10, wdsk, …)`.
   - **Brawl deltas from Melee** (verbatim): Brawl adds a gravity-based adjustment on top, and
     the `d` term *"includes the staleness or the freshness bonus"* — so a staled move loses
     both damage and knockback. pycats models neither gravity-term nor staleness (out of scope).
4. **Angle** ([Angle](https://www.ssbwiki.com/Angle)): integer degrees, `0` = away, `90` = up,
   `180` = toward, `270` = down. Special codes:
   - **361 = Sakurai angle** ([Sakurai angle](https://www.ssbwiki.com/Sakurai_angle),
     Brawl values, verbatim): grounded low-KB `0°`, grounded high-KB `37°`, **airborne `45°`**,
     scaling linearly between KB `<60` (stays 0°) and `≥88` (reaches 37°). pycats' `sakurai_angle`
     implements this shape (config-driven low/high/max).
   - **363–368 = autolink angles** (Brawl+): match knockback to attacker movement to link
     multi-hits (365 = 50% of attacker momentum; 366 = 5-frame vortex pull; 367 = momentum +
     20% of hitbox↔victim offset). pycats does not model autolink.
   - **362 = flipper** (Melee-only, toward hurtbox center) — not in Brawl.
5. **Angle flipping** (`brawllib_rs` `AngleFlip`, verbatim doc): the stored angle assumes the
   attacker faces right; a per-hitbox modifier decides when to mirror across Y — e.g.
   `AttackerPosition` = flip if attacker is left of defender; `AttackerDir`, `MovementDir`,
   `HitboxPosition`, etc. pycats mirrors by facing (a simplification of this).
6. **Hitstun** = `KB × 0.4` in Brawl (*"Brawl has the same hitstun multiplier Melee has,"*
   [Hitstun](https://www.ssbwiki.com/Hitstun)); pycats has a config multiplier.
7. **Hitlag** (freeze frames, [Hitlag](https://www.ssbwiki.com/Hitlag)): per-hitbox
   `hitlag_mult` (default 1×); **Electric** multiplies hitlag ×1.5. *(The closed-form
   `0.65·d+6` constant on the wiki is quoted for Ultimate, not Brawl — do not assume it for a
   Brawl model.)*

### (i).6 — Clank / priority, rehit, effects, trip

- **Clank / priority** ([Priority](https://www.ssbwiki.com/Priority), verbatim): if the
  stronger hitbox deals *"more than 9% … more than the weaker hitbox, the stronger move will
  continue … and the weaker move will end … in rebound. If both hitboxes deal within 9% of
  each other, both moves will end and both … go into rebound."* **Transcendent** hitboxes
  can't clank at all (most aerials, many projectiles). pycats has clank (`_resolve_clanks`,
  #38).
- **Rehit rate:** a persistent hitbox re-strikes the same victim only every N frames.
  *(Documented on the Hitbox page but captured via search summary, not a fetched verbatim
  sentence — confirm the exact Brawl field before hard-coding; labelled inference.)* pycats
  has `rehit_rate` (#213).
- **Effects / elements** ([Effect](https://www.ssbwiki.com/Effect)): mostly cosmetic;
  mechanically load-bearing ones are **Electric** (+50% hitlag), **Flame** (detonates
  explosives), and the status effects (Freeze, Bury, Sleep, Stun, Flower, Paralyze, Slip/Stop).
- **Trip** ([Trip](https://www.ssbwiki.com/Trip)): any hit >55 KB at a non-launching angle has
  a **13.5%** trip chance in Brawl, plus any hitbox-specific added chance; the **Slip** effect
  is a guaranteed trip. pycats does not model trip.
- **Shield damage** ([Shield damage](https://www.ssbwiki.com/Shield_damage)): an **additive**
  per-hitbox bonus to shield damage.
- **SDI multiplier:** per-hitbox scalar on SDI distance during hitlag. *(Only found in PM
  Smashboards frame-data threads, not a dedicated SmashWiki page — community-inferred.)*

### (i).7 — Project M vs vanilla Brawl (reaction layer only)

The geometry model is unchanged; PM's differences ([Project M](https://www.ssbwiki.com/Project_M))
are in reactions: **hitstun canceling removed** (longer combos), **successive-hit knockback**
re-combines when re-hit within 10 frames (vs Brawl's relative-strength compare), **DI restored
on non-tumble hits**, **air-dodge unusable during tumble**, a shared **16-frame meteor-cancel**
window (only 260–280° cancelable), and **Melee shieldstun**. No documented change to the KB
formula constants, the 9% clank threshold, the swept-capsule rule, or hurtbox states.

### (i).8 — Worked example: real Mario numbers (my datamine)

Run with `brawllib_rs` `high_level_frame_data` against PM 3.6 (`-d` vanilla Brawl, `-m`
pm36-sd; the #614 datamine recipe). Sizes are in world units; `pycats` maps units→px via
`PX_PER_UNIT ≈ 5.4` (`u(3.52) ≈ 19px`).

**Jab — `Attack11`** (16 frames; hitboxes active frames **2–3**, 1-based):

| id | dmg | angle | KBG | BKB | WDSK | size (u) | effect | flags |
|---|---|---|---|---|---|---|---|---|
| 0 | 3.0 | 83 | 100 | 0 | 20 | 3.52 | Normal | ground+aerial, clang, direct |
| 1 | 3.0 | 83 | 100 | 0 | 20 | 2.34 | Normal | " |
| 2 | 3.0 | 85 | 100 | 0 | 20 | 2.73 | Normal | " |

→ a set-knockback jab (WDSK 20, BKB 0). **pycats' Nalio `_JAB` already encodes these exactly**
(`damage=3.0, angle=83/83/85, set_knockback=20, KBG=100`) — direct cross-validation that the
transcription path works.

**Forward smash — `AttackS4S`** (45 frames; active frames **8–12**):

| id | dmg | angle | KBG | BKB | WDSK | size (u) | effect |
|---|---|---|---|---|---|---|---|
| 0 | 14.0 | 361 (Sakurai) | 96 | 25 | 0 | 3.52 | Normal |
| 1 | 19.0 | 361 | 97 | 30 | 0 | 3.94 | **Flame** (sweetspot fist) |
| 2 | 10.0 | 361 | 96 | 25 | 0 | 1.95 | Normal |

→ normal percent-scaling knockback (BKB/KBG, WDSK 0), Sakurai angle, a Flame sweetspot.

**Interpolation confirmed:** on frames 2–3 (jab) and 8–12 (f-smash) each hitbox carries a
`prev_pos = Some(...)` — the swept-capsule endpoints from §(i).4.

**Fireball — `SpecialN`** (49 frames): **`hit_boxes: []` on all 49 frames.** The fireball's
damage box is not on Mario's body — it is a **separate article/projectile** spawned by a
script event, whose hitbox lives in article data the fighter-subaction view does not carry.
*(Inference from the empty `hit_boxes` + the known fireball-is-a-projectile fact; the datamine
simply doesn't surface article hitboxes at this level.)* This is why **pycats hand-authors
the fireball** as a `projectile_speed` `MoveData` with a FOUND hitbox (`nalio_cat.py`
`_FIREBALL`, sourced from Smashboards/SmashWiki, not the subaction dump).

---

## (ii) What you must know to implement a faithful version in pycats

### (ii).1 — The parity ceiling (already ratified in #310)

`docs/research/parity-notes-regarding-hurtbox-values.md` (#310) is the governing decision and
it maps cleanly onto the model above:

- **Scalars are exact and datamineable** — damage, angle, KBG, BKB, WDSK, weight, frame
  timings, the knockback *formula* itself. *"A scalar like `KBG = 100` means the same thing in
  any reimplementation, so it transfers losslessly."*
- **Positions (`dx`/`dy`) cannot be made pixel-faithful**, for two structural reasons the doc
  calls out: **(1) no skeleton** — PM boxes are `bone_matrix × offset`, and pycats fighters
  are rectangles with no bones to attach to; **(2) no fixed unit→pixel scale** — #120
  established Brawl positions are abstract units with a dynamically-zooming camera and sizes
  *"based on feel."* The reachable ceiling is **proportional** parity (same body-relative zone,
  same relative reach ordering), which #309's `zone_dy` fraction scheme already encodes.

Consequence for anyone implementing: **treat scalars and positions as two different
provenance categories.** Scalars are a lookup (datamine → copy). Positions are a feel-tune
(author against a visual reference → playtest). This split drives all of (iii).

### (ii).2 — PM concept → pycats: in-scope / simplify / out

| PM/Brawl concept | Faithful-minimum for pycats | pycats today | Verdict |
|---|---|---|---|
| Knockback formula (`p,d,w,s,b`) | copy exactly | exact | **done — keep** |
| WDSK / set knockback | copy exactly | exact | **done** |
| Sakurai angle (361) | grounded ramp + airborne fixed | modeled | **done** |
| Hitstun / hitlag | KB×0.4 / per-hit + electric | modeled (config) | **done, minor gaps** |
| Damage / angle / KBG / BKB per hitbox | datamine → copy | Nalio done; roster partial | **finish transcribing** |
| Active-frame windows | per-hitbox start/end | modeled (#204) | **done** |
| Box **geometry** (capsule) | AABB or circle is fine | circle | **simplify — circle OK** |
| Box **position** (`dx`/`dy`) | feel-tuned vs GIF | eyeballed | **feel — see (iii)** |
| Multiple hurtbox parts | 2–4 circles per body | 2-circle coarse | **refine (cheap win)** |
| Hurtbox **states** (invinc./intang.) | needed for dodges/ledge | partial? | **scope per-move** |
| Hitbox **interpolation** (sweep) | matters only at high speed | none | **mostly out — see note** |
| Clank / priority | lowest-id + 9% clank | has clank | **done-ish** |
| Rehit rate | every-N-frames | modeled (#213) | **done** |
| Autolink angles (363–368) | multi-hit linking | none | **out (niche)** |
| Elements (Flame/Electric/…) | Electric hitlag ×1.5 is the only mechanical must | cosmetic-agnostic | **out mostly; Electric optional** |
| Trip / shield-damage field / SDI mult | balance polish | none | **out for now** |
| DI / directional influence | player-facing depth | none | **out (bigger feature)** |
| Staleness / gravity KB term | Brawl-specific | none | **out** |

**Circle vs capsule/AABB.** pycats' single-circle-per-box is a legitimate simplification: a
PM box is a sphere (capsule when swept), and a 2-D circle is the honest projection of a sphere.
The only fidelity lost is (a) the swept sweep and (b) fine shape. Neither is the current
bottleneck.

**The interpolation gap, precisely.** pycats tests an instantaneous circle each frame with no
A→B sweep. This only matters when a box moves more than ~its own radius per frame (fast
projectiles, whipping smashes) — then a fast body can tunnel through, exactly the case the PM
sweep exists to fix. For pycats' current speeds and single-hit boxes it is rarely observable;
worth a labelled ticket, not a priority.

### (ii).3 — Options for closing the remaining gaps (menu, not a mandate)

1. **Finish scalar transcription across the roster** (Narz/Birky to Nalio's standard). Pure
   datamine → copy; exact; the highest fidelity-per-effort.
2. **Refine hurtboxes from 2 circles to 3–4 body-relative circles** (head/torso/legs) using
   `zone_dy` fractions. Cheap, improves hit feel, and is the one place the ticket's "coarse
   hurtbox" is literally true. Sim-affecting (changes connect/whiff) — needs a reviewed golden
   regen.
3. **Add hitbox sweep (A→B capsule)** for fast/projectile boxes only. Localized change to
   `geometry.py`/`combat.py`; sim-affecting; do it when tunnelling is observed.
4. **Model hurtbox states** (intangible on dodge/ledge, invincible on respawn) — larger, ties
   into the state machine, not box-authoring.
5. **The in-game editor** — a tool for authoring #2/positions faster. See (iii).

---

## (iii) Is an in-game dev-mode box editor recommended?

**The question restated with the (ii) framing:** an editor does not help the *scalar* layer at
all (that's a datamine → copy pipeline, and exact). Its entire value is the *positional/feel*
layer — placing/dragging `Circle(dx,dy,r)` per move against a visual reference and seeing the
result live. So "is the editor worth it?" = "is authoring box **positions** the current
bottleneck, and is a live editor the cheapest way to do it well?"

### The three authoring paths (the ticket's a/b/c)

**(a) Transcribe datamined PM values.** Run `brawllib_rs`, copy scalars into `*_cat.py`.
- *Fidelity:* exact for scalars; **gives you nothing for positions** (bone-relative, no
  skeleton — §(ii).1).
- *Effort:* low, mechanical, already proven (Nalio jab matches the datamine byte-for-byte).
- *Sim/golden:* changing a scalar that a golden scenario exercises forces a reviewed regen.
- **Recommendation: keep doing this — it is the scalar SSOT.** Not an alternative to an editor;
  they cover disjoint layers.

**(b) Hand-author positions in the static data file against the #777 GIF reference.**
Eyeball `dx/dy/r` from the hurtbox-capsule GIFs, tune by playtest.
- *Fidelity:* proportional (the #310 ceiling) — the best positions *can* be, by construction.
- *Effort:* moderate per move; the #777 GIF set is exactly the reference substrate for it, and
  `zone_dy` gives body-relative anchoring for free.
- *Sim/golden:* a position edit that changes a hit's connect/whiff in a recorded scenario is
  sim-affecting (#768 — moving a hitbox/hurtbox perturbs the sim); a hitbox position is even
  **directly serialized** into the golden (`snapshot()` writes `hit_cx/hit_cy/hit_r`), so *any*
  spawned-hitbox move edited during a golden scenario changes the golden byte-for-byte. Both
  route through the reviewed `PYCATS_UPDATE_GOLDENS` regen.
- **Recommendation: this is the primary positional path today.** Low ceremony, uses assets you
  already built (#777), and keeps box data in version control as plain reviewable code.

**(c) In-game dev-mode box editor** (place/drag boxes per frame, live, save to data).
- *Fidelity:* same **proportional** ceiling as (b) — an editor cannot beat the #310 wall; it
  just makes reaching that ceiling faster and more visual.
- *Effort:* **high.** It needs: a frame-scrubber, box-picking/drag UI, a coordinate mapping
  back to `Circle(dx,dy,r)`, per-move/per-frame state, and a serializer that writes data the
  frozen-dataclass loader can consume — plus its own tests. It's a mini-app.
- *Sim/golden interaction (the sharp edge):* the editor must **write data, then let the normal
  deterministic sim run** — it must never become a live-mutation path that edits boxes inside a
  running match, or it breaks the frozen-dataclass/determinism contract the goldens depend on.
  The safe design is edit → serialize → reload → replay, with the same reviewed golden regen as
  (b). An editor that mutates sim state in place is a determinism footgun.
- *When it wins:* once you are iterating on positions **heavily** — many characters × many
  moves × repeated feel passes — a live editor's tighter loop (drag, see, adjust) pays back its
  build cost. Below that volume, (b) is faster end-to-end because you skip building the tool.

### Recommendation

**Do not build the in-game editor yet. Sequence it third, behind the two cheaper paths.**

1. **Now:** finish **(a)** scalar transcription (exact, mechanical) and use **(b)** hand-authoring
   against the #777 GIFs for positions and the hurtbox refinement. This closes the biggest real
   gaps (coarse hurtbox, un-transcribed roster) at the lowest cost and highest fidelity-per-hour.
2. **Trigger to revisit (c):** when hand-authoring positions becomes the **measured** bottleneck
   — i.e. you're doing repeated multi-character feel passes and the edit→run→eyeball loop in (b)
   is the thing slowing you down. That is the point where the editor's build cost amortizes.
3. **If/when you build it:** scope it as an **offline authoring tool that emits static data**
   (edit → serialize → reload → replay), *not* a live in-match mutator — to preserve the
   deterministic-sim/golden contract. It also pairs naturally with the #778 side-by-side sandbox
   (the #777 GIF on one side, the pycats move on the other) as the visual backdrop for placement.

**Rationale in one line:** the editor is the right tool for the *one* layer that can't be
datamined (positions/feel), but that layer isn't today's bottleneck and the ceiling it reaches
is identical to cheap hand-authoring — so its cost only justifies itself once positional
iteration volume is high. Build the cheap path first; let the pain, not the appeal, trigger the
tool.

*This is the research recommendation; the outward build decision remains human-gated.*

### Post-research decision (human / game-designer)

The game-designer reviewed this and **decided to prioritize the editor** — diverging from
the "defer" research recommendation above, with reason. The intended workflow is to compare
**every** Mario animation against **every** Nalio move/attack/animation and verify each has
roughly the **same duration** and roughly the **same hit/hurtbox placement** (against the
#777 Mario GIF reference). That is a very high volume of rect/circle placements, and
hand-authoring positions at that scale is too slow — a WYSIWYG editor is judged the only
practical way to do it quickly. The "trigger" this doc set for revisiting the editor
(positional iteration becoming the bottleneck) is considered already met by that intended
scale of work. The determinism-safe framing still holds: build it as an **offline,
data-emitting** tool (edit → serialize → reload → replay), not a live in-match mutator.

This is carried forward by the umbrella tracker **#792** (research → decision → design →
scope → build), which files its child threads one at a time downstream of this doc.

---

## Suggested follow-ups (not filed — one-at-a-time downstream, per RULES)

- **DEV:** refine Nalio's hurtbox from the 2-circle coarse stack to 3–4 body-relative circles
  via `zone_dy` (the literal "coarse hurtbox" gap). Sim-affecting → reviewed golden regen.
- **DEV:** finish scalar transcription for the rest of the roster to Nalio's datamined standard.
- **RESEARCH/DEV:** hitbox A→B sweep for fast/projectile boxes (anti-tunnelling), if/when
  tunnelling is observed.
- **DECISION (human-gated):** whether/when to build the offline box editor — gate on positional-
  iteration volume becoming the bottleneck; scope as data-emitting, not live-mutating.

## Sources

**Primary — `brawllib_rs`** (`~/Documents/Study/Rust/brawllib_rs`): `src/sakurai/fighter_data/misc_section.rs`
(HurtBox), `src/script_ast/mod.rs` (HitBoxArguments, HurtBoxState, AngleFlip),
`src/high_level_fighter.rs` (HitBoxValues, HighLevelHitBox/HurtBox, containment, interpolation),
`src/renderer/draw.rs` (capsule render). **Datamine:** `high_level_frame_data` vs PM 3.6
(recipe: `docs/tooling-brawllib-rs-datamine-recipe.md`, #614).

**Primary — SmashWiki:** [Knockback](https://www.ssbwiki.com/Knockback),
[Set knockback](https://www.ssbwiki.com/Set_knockback), [Angle](https://www.ssbwiki.com/Angle),
[Sakurai angle](https://www.ssbwiki.com/Sakurai_angle), [Autolink angle](https://www.ssbwiki.com/Autolink_angle),
[Priority](https://www.ssbwiki.com/Priority), [Hitbox](https://www.ssbwiki.com/Hitbox),
[Hurtbox](https://www.ssbwiki.com/Hurtbox), [Effect](https://www.ssbwiki.com/Effect),
[Hitlag](https://www.ssbwiki.com/Hitlag), [Shield damage](https://www.ssbwiki.com/Shield_damage),
[Trip](https://www.ssbwiki.com/Trip), [Hitstun](https://www.ssbwiki.com/Hitstun),
[Project M](https://www.ssbwiki.com/Project_M).

**Tool/community-inferred (flagged inline):** [rukaidata writeup](https://github.com/rukai/rukaidata/blob/main/docs/writeup.md);
SDI multiplier + rehit-rate exact semantics + set-KB internal mechanic (Smashboards / wiki
reverse-engineering); Brawl hitlag closed-form constants (wiki quotes Ultimate). OpenSA/PSA:
a live standalone OpenSA doc site was not located this pass — PSA-level facts are corroborated
via SmashWiki + `brawllib_rs` instead.

**In-repo cross-refs:** `docs/research/parity-notes-regarding-hurtbox-values.md` (#310, the
parity ceiling), `docs/research-120-smash-units-and-sources.md` (#120, units/scale),
`pycats/combat/{data,geometry,knockback}.py`, `pycats/systems/combat.py`,
`pycats/entities/attack.py`, `pycats/characters/nalio_cat.py`, `pycats/characters/body_zones.py`
(#309, `zone_dy`), `docs/pm-reference/mario-gif-index.md` (#777, the GIF reference set),
`docs/tooling-brawllib-rs-gif-recipe.md` (#758). Golden coupling: `pycats/sim/runner.py`
`snapshot()`, `tests/test_golden.py`.
