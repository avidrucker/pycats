# Character-on-character collision ("jostling") — findings (#594)

**Ticket:** #594 (research · `area:entities` · `post-v1` · `deferred`).
**Question:** Does Project M bounce/push stacked or overlapping fighters, what are the
rules, and how does pycats' `resolve_player_push` compare?
**Status:** all five research questions answered — three from primary sources, two
returned **⚠ UNDOCUMENTED** with the search trail recorded. Keep-vs-change recommendation
stated at the end. **Research only — reports the option space; it does not decide the spec**
(RULES → "research never produces the spec"). Any change is a follow-on ARC/decision ticket
with the human.

## TL;DR

Melee/Brawl/PM character collision is **jostling**: two overlapping fighters are **slowly
pushed apart** — not a hard block, not free pass-through. It is **horizontal**, has **no
vertical resolution** between fighters (you don't platform on a head; overlap is tolerated),
and is a **gentle per-frame position nudge that never touches velocity**.

pycats' `resolve_player_push` **matches canon on the structural choices** (X-axis only, no
vertical lock, stacking tolerated) but **diverges on the push model**: it resolves the entire
overlap in a **single frame** and **rewrites `vel.x`** (zero / average / half). Canon does
neither. The velocity rewrite is the most un-canonical behavior.

The pycats constants are already provenance-classified **TUNED** ("deliberate design values,
not seeking canon"), so moving them toward canon is a reclassification that needs this doc as
its basis — a decision for the human, not this ticket.

---

## Q1 — Ground soft-collision / overlap

**Answer:** Two overlapping grounded fighters **softly push apart** — a slow separation, not
a hard block and not free pass-through. The mechanic is **jostling**. `[PRIMARY]`

SmashWiki, *Jostle* (lead) — https://www.ssbwiki.com/Jostle:

> "**Jostling** is a form of collision detection present throughout the *Super Smash Bros.*
> series. Typically, it is understood as the effect wherein two objects are overlapping, and
> as a result each object is slowly pushed away from each other. When multiple characters
> attempt to occupy the same space, they push away from each other."

SmashWiki, *Jostle* (Properties):

> "In *Super Smash Bros.*, only characters can jostle; items cannot… All characters will push
> each-other with equal strength. *Melee* would introduce the ability for items to partake in
> the effect. In *Super Smash Bros. Brawl*, while the effect itself is unchanged, enemies and
> bosses in the Subspace Emissary tend to use non-damaging and pushing hitboxes to amplify the
> effect."

**What governs the push.** No source names a distinct "pushbox" box type for Melee/Brawl/PM.
The **ECB (Environmental Collision Box) is a character-vs-*stage* box, not the char-vs-char
box** — doldecomp/melee `docs/glossary.md`
(https://raw.githubusercontent.com/doldecomp/melee/master/docs/glossary.md): `[PRIMARY]`

> "ECB: Stands for 'environmental collision box.'"

(The decomp models the ECB under map-collision — `src/melee/mp/mpcoll`, `mpColl_LoadECB` — and
reads it in stage/ground code, confirming it is the stage-collision box.) The only *named*
governing quantity, **"jostle strength"**, appears **only in the wiki's Ultimate paragraph**
and does **not** describe Melee/Brawl/PM; for the earlier games the wiki says only that all
characters push "with equal strength." `[Ultimate-only → out of scope]`

**Concrete Melee rule (faithful reimplementation).** meleelight (`schmooblidon/meleelight`
@ `27af171`, 2018-05-30), `src/physics/physics.js`, function `physics(i, input)`, the
grounded-player push block (findable by the comment "this pushing code needs to account for
players on slanted surfaces"): `[SECONDARY — faithful engine reimpl, not the retail ROM]`

```js
if (player[i].phys.grabbing !== j && player[i].phys.grabbedBy !== j) {
  const diff = Math.abs(player[i].phys.pos.x - player[j].phys.pos.x);
  if (diff < 6.5 && diff > 0) {
    player[j].phys.pos.x += Math.sign(player[i].phys.pos.x - player[j].phys.pos.x) * -0.3;
  } else if (diff === 0 && Math.abs(player[i].phys.cVel.x) > Math.abs(player[j].phys.cVel.x)) {
    player[j].phys.pos.x += Math.sign(player[i].phys.cVel.x) * -0.3;
  }
}
```

Reading it out:
- **Activation range:** horizontal centre-distance `< 6.5` internal units.
- **Push amount:** **`0.3` units/frame**, a direct **position** nudge away — *velocity is never
  touched*. (The block runs once per ordered pair per frame, so with both fighters grounded on
  the same surface the net separation is ≈ `0.6` units/frame.)
- **Exact-overlap tie-break** (`diff === 0`): the **faster-moving** fighter
  (`|cVel_i| > |cVel_j|`) nudges the slower one; equal speeds → no move that frame.

---

## Q2 — On-top / stacking (standing on another fighter's head)

**Answer:** **⚠ UNDOCUMENTED in primary prose.** No SmashWiki/decomp source states whether a
fighter can stand on another's head or whether char-vs-char collision has any vertical
resolution. `[UNDOCUMENTED]`

Search trail: fetched full *Jostle* wikitext (no stacking/vertical sentence), *Hitbox* §0
(hitbox/hurtbox only), decomp `glossary.md` (ECB only). No article titled "Pushbox" or
"Character collision" exists (SmashWiki search returned no dedicated page).

**Best available answer — from the Melee code, inference:** jostling is **horizontal-only with
no vertical component**. In meleelight the push modifies only `pos.x`, and it fires **only when
both fighters are grounded on the same surface** (see Q3). A fighter above another (airborne,
or on a different platform) satisfies neither condition, so **no push and no vertical
resolution occurs** — the fighters simply overlap. This matches the widely-observed behavior
that you cannot platform on a fighter's head; vertical overlap is tolerated rather than
resolved. `[INFERENCE from meleelight — not a primary-prose confirmation]`

---

## Q3 — Air vs ground

**Answer:** Jostling is **weaker or absent in the air**. The two sources disagree on the exact
edge and I flag the tension rather than resolve it. `[PRIMARY (brief) + SECONDARY]`

SmashWiki, *Jostle* (lead): `[PRIMARY]`

> "The effect tends to be stronger on the ground, particularly in *Ultimate* between two
> opposing fighters."

This phrasing implies the effect **exists in the air but is weaker**. The detailed airborne
behavior is not described. The Ultimate "can no longer walk or run past each other" hard-block
is an **Ultimate-only rework** and does **not** apply to Melee/Brawl/PM.

meleelight (Melee reimpl) is more categorical: the entire push block is **grounded-only** —
guarded by `if (player[i].phys.grounded)` and requiring `player[j].phys.grounded` plus the same
`onSurface`. Under that model there is **no airborne jostle at all**. `[SECONDARY]`

**Tension, left open:** wiki "weaker in air" vs meleelight "grounded-only." For a PM-parity port
the meleelight model (grounded + same-surface gate) is the more concrete and directly usable
rule; the wiki's "weaker in air" may reflect item/other-object jostle or a nuance meleelight
omits. Nailing this precisely would need the decomp collision routine (Q4 trail).

---

## Q4 — Values & determinism (engine-hardcoded vs scripted)

**Answer:** The push is **engine logic / an engine global, not per-character move-script data**
`[INFERENCE (strong)]`; the **exact retail Melee/Brawl/PM 3.6 magnitude is ⚠ UNDOCUMENTED**
in the sources reached `[UNDOCUMENTED]`; the best available literal is meleelight's **0.3
units/frame over a 6.5-unit range** `[SECONDARY]`.

- **Engine-hardcoded, not scripted.** In the Melee decomp, fighter *attack* collision
  (`src/melee/ft/ftcoll.c`) contains hitbox↔hurtbox/grab/shield logic but **no fighter-vs-
  fighter push**; ECB/stage collision lives in `src/melee/mp/mpcoll` + `src/melee/gr/*`. A
  char-vs-char push is therefore a **global engine routine**, exactly the class of value that
  per-move datamine tools (rukaidata, brawllib_rs) do **not** expose — cf. the air-dodge-force
  precedent (memory `rukaidata-engine-hardcoded-limit`, doc `pm-globals-dump-setup.md`).
- **No published numbers for Melee/Brawl/PM.** SmashWiki publishes a per-fighter "jostle
  strength" table for **Ultimate only**; there is no Melee/Brawl/PM table. Pre-Ultimate the
  wiki says only "equal strength."
- **Best literal available:** meleelight's `0.3` units/frame nudge, `6.5`-unit activation
  range, position-only (Q1). This is a faithful reimplementation, not the retail ROM.
- **Determinism:** the meleelight rule is fully deterministic — fixed 0.3/frame, fixed 6.5
  range, velocity-magnitude tie-break at exact overlap. pycats is likewise deterministic
  (fixed-timestep integer-pixel, #80).

**Search trail for the missing retail constant:** decomp searches `Push`/`ftColl`/`grColl`/
`pushback`/`ecb` (only ECB/stage hits); read `ftcoll.c`, `ftcoll.dox`, `glossary.md`; grep of
the local meleelight tree for `jostle`/`pushbox`/char-vs-char push. Pinning the retail number
would require tracing the un-named `ftColl_8007xxxx` collision functions in the decomp, or a
PMDT/OpenSA engine-global dump — not reached here (GitHub API rate-limited the decomp trace).

**Cross-era:** PM 3.6 runs on the **Brawl** engine, and the wiki states Brawl's jostle "effect
itself is unchanged" from Melee. So PM 3.6 is expected to inherit **Melee/Brawl jostle** —
gentle overlap-separation, pass-through allowed, no Ultimate hard-block. `[INFERENCE from the
wiki's era statements; no PM-specific PMDT jostle doc located]`

---

## Q5 — pycats gap: what `resolve_player_push` does, and where it diverges

`resolve_player_push(players)` lives in `pycats/core/physics.py` and is called every frame from
`pycats/sim/runner.py`. Behavior confirmed by source read **and** an executed headless probe:

- **Gates:** skips any fighter in `"dodge"` state; requires AABB `rect.colliderect`; then
  requires vertical overlap `≥ JOSTLE_MIN_VOVERLAP_FRAC (0.8)` of the shorter body — the #68
  flyover fix (probe: with 60px bodies the gate flips at v-overlap 48px, push suppressed below,
  active above).
- **Separation:** on the X axis only, **resolves the entire overlap in one frame** — each body
  moves `overlap // 2 + 1` px apart (probe: a 20px overlap → fighters fully clear, centres
  20→42px apart, no longer colliding, in a single call).
- **Velocity rewrite:** unlike canon, it **overwrites `vel.x`** — opposite directions → both
  `0`; one-sided → both at `COLLISION_PUSH_SPLIT (0.5)` × pusher; same direction → the average
  (probe confirmed 4.0-vs-0 → 2.0/2.0; 3.0-vs-−3.0 → 0/0; 2.0-vs-6.0 → 4.0/4.0).
- **No vertical resolution:** never touches `vel.y` or Y position; vertical overlap (standing
  on a head) is tolerated, then nudged off sideways (`test_player_push.py`).
- **Tie-break:** perfectly-stacked (`centerx` equal) fighters separate deterministically
  (leftward default), independent of velocity.

**Provenance status:** `JOSTLE_MIN_VOVERLAP_FRAC = 0.8` is classified **TUNED** in
`docs/research/2026-07-07-custom-mechanics-inventory.md` — "deliberate design values, **not
seeking canon**… vertical-overlap gate for the PM X-only push heuristic (#68)."
`COLLISION_PUSH_SPLIT = 0.5` is a local constant in `physics.py`. The whole jostle is a
self-declared **custom heuristic**, not a datamined PM value.

### Canon vs pycats

| Aspect | Melee/Brawl/PM (canon) | pycats `resolve_player_push` | |
|---|---|---|---|
| Axis | horizontal only | horizontal only | ✅ match |
| Vertical resolution | none (fighters overlap) | none (`vel.y`/Y untouched) | ✅ match |
| Stacking tolerated | yes | yes, nudged off sideways | ✅ match |
| Push model | gradual `~0.3` u/frame nudge | **entire overlap in 1 frame** | ❌ diverge |
| Velocity effect | **none** (position only) | **rewrites `vel.x`** (0 / avg / ½) | ❌ diverge |
| Air push | grounded-only (meleelight) / weaker (wiki) | **pushes in air too**, gated by 80% v-overlap | ❌ diverge |
| Same-surface gate | required | not checked | ❌ diverge |
| Grab exemption | yes | no (only `dodge`-exempt) | ⚠ minor |
| Activation region | centre-dist `< 6.5` u | AABB overlap + 80% v-overlap | different model |

---

## Keep-vs-change recommendation (opinion — the human decides at commit)

pycats already matches canon on the choices that matter most for feel — **X-only, no vertical
lock, stacking tolerated**. The divergences are the **push model** and the **velocity rewrite**.
My read of the option space:

1. **Keep as-is.** Defensible. The constants are provenance-**TUNED** (deliberate, not
   canon-seeking); the visible behavior (fighters separate, can't lock, can't platform on a
   head) already reads as jostle. `post-v1`/`deferred` fits — nothing here is a bug.
2. **Soften toward canon (recommended if any change is made).** The clearest fidelity win is
   dropping the **velocity rewrite** and replacing the **one-frame full separation** with a
   **gradual per-frame position nudge** (canon touches position only, never velocity). Optional
   further parity: a **grounded/same-surface gate** and **grab exemption**.
3. **Full port of the meleelight rule.** `0.3` u/frame over a `6.5`-u range, grounded-only.
   Blocked on two things: the retail PM 3.6 number is **⚠ UNDOCUMENTED** (meleelight is the best
   proxy, not the ROM), and porting a unit literal needs the unit→px conversion seam
   (ADR-0011 / `mod_factor`, memory `use-conversion-function-not-inline-multiply`) — a
   spec-time concern, not a bare `× PX_PER_UNIT`.

**Follow-on scope, if the human wants a change (file one at a time, downstream of this doc):**
an **ARC/decision ticket** to choose between options 1–3 and, if 2 or 3, reclassify the
constants off TUNED with this doc as the basis; then a **DEV ticket** to implement the chosen
model with a regression test. This ticket files neither — research reports options only.

---

## Sources

**Primary:**
- SmashWiki, *Jostle* — https://www.ssbwiki.com/Jostle (definition, Properties, era statements)
- doldecomp/melee `docs/glossary.md` — ECB = environmental (stage) collision box
- doldecomp/melee `src/melee/ft/ftcoll.c` — attack collision only, no char-vs-char push

**Secondary (faithful reimplementation):**
- meleelight `schmooblidon/meleelight` @ `27af171` — `src/physics/physics.js`, `physics(i, input)`
  grounded push block: `0.3` u/frame, `< 6.5` u range, position-only, grounded + same-surface,
  grab-exempt. Local clone: `~/Documents/Study/JavaScript/meleelight/` (#616).

**In-repo:**
- `pycats/core/physics.py` — `resolve_player_push`; `pycats/config/physics.py` —
  `JOSTLE_MIN_VOVERLAP_FRAC = 0.8`; `pycats/sim/runner.py` — per-frame call site.
- `docs/research/2026-07-07-custom-mechanics-inventory.md` — TUNED classification.
- `tests/test_player_push.py` — behavioral characterization (X-only, no Y lock, dodge-exempt).

**Ultimate-only (out of scope, recorded to prevent mis-citation):** the per-fighter "jostle
strength" attribute and its numeric table are an **Ultimate** rework; they do not describe
Melee/Brawl/PM.
