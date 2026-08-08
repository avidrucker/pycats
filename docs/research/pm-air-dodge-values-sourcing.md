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

---

## 2026-08-07 — #1251 re-verify `DODGE_AIR_SPEED` against a PM/Melee primary (CHERRY)

> First concrete value of #638's "re-verify single-secondary / guessed values, one at a time"
> campaign (the motivating #215 example). Goal: replace the single-secondary-proxy citation with a
> **PM primary** read via the extraction capability, and route the provenance (confirm the 3.1-restored
> `FOUND`, or correct it). Method: direct read of `doldecomp/melee` (T1 Melee decompilation) via the
> GitHub API **at a pinned SHA** — the no-ISO technique #1249 established — cross-checked against the
> locally-cloned meleelight reimpl (#616). Area: `area:combat`. **No code/config change** (research ≠
> implementation; the registry edit is a downstream DEV).

### TL;DR

1. **The value is `17` px/f (= `round(3.1 × PX_PER_UNIT≈5.4)`), unchanged.** No primary contradicts it,
   and no PM-specific override was found. The number is not corrected — the **citation is**.
2. **Upgrade obtained (T1, no ISO):** the retail-Melee air-dodge **mechanic and the exact data field**
   are now read straight from `doldecomp/melee` — `ftCo_EscapeAir.c` sets
   `self_vel = escapeair_force × (cosθ, sinθ)` in the stick direction, deadzone → `(0,0)` halt; the
   magnitude lives in `struct ftCommonData.escapeair_force` (a `float` at **CommonFighterData +0x338**).
   This matches pycats' `fighter.py` air-dodge branch exactly (directional SET, neutral HALT).
3. **Ceiling hit (same as #1249):** the **numeric magnitude is not a source literal** anywhere in the
   decomp — `escapeair_force` appears only as a struct-field declaration + its use; its value is a
   **data-section float** in the DOL, which needs the ISO-gated read (**#1250**). So `doldecomp/melee`
   supplies the *formula + address*, not the *number*.
4. **Where `3.1` comes from, corrected:** the meleelight literal is in
   `characters/shared/moves/ESCAPEAIR.js` (`cVel = 3.1 * cos/sin(ang)`), **not** the animation-frame
   `animations/fox/ESCAPEAIR.js` the prior citation pointed at. meleelight is a Melee **reimpl** (T2
   proxy); its `3.1` is the reimpl author's extraction of the `+0x338` data-section value.
5. **Routing:** the status can **stay `FOUND`** under this file's own **`JOSTLE_TRIGGER_UNITS` precedent**
   (a meleelight literal kept `FOUND` *with an explicit "SECONDARY proxy … UNDOCUMENTED" caveat*) — but
   the **current source string overstates corroboration** (it credits `doldecomp/melee` with
   `escapeair_force=3.1u/f`, which the decomp does not carry) and must be corrected. A DEV follow-up
   should rewrite the citation (draft below). See the FOUND-vs-downgrade note before editing.

### What was read (T1 primary — `doldecomp/melee`)

Read at pinned SHA `7d4a30dcd79037ca771ebbb085f045c366b9960b` (default branch `master`), no local clone
— identical authoritative blobs, pinned SHA is the provenance anchor (same procedure #1249 used for the
`doldecomp/brawl` symbol map).

- **`src/melee/ft/chara/ftCommon/ftCo_EscapeAir.c`** — the air-dodge (Escape Air) handler. The entry
  `inlineA0(fp)` sets the burst:
  ```c
  float angle = ftCommon_8007D9D4(fp);            // stick angle
  fp->self_vel.x = p_ftCommonData->escapeair_force * cosf(angle);
  fp->self_vel.y = p_ftCommonData->escapeair_force * sinf(angle);
  ```
  with a deadzone short-circuit (`escapeair_deadzone`) → `self_vel = (0,0)`, a per-frame
  `escapeair_decay` multiply in `..._Phys`, and exit to `FallSpecial`. The magnitude is the struct
  field `escapeair_force`, **not** an immediate.
- **`src/melee/ft/types.h`** — `struct ftCommonData` field layout, offsets in the source comments:
  ```
  /* +32C */ Vec2  escapeair_deadzone;
  /* +338 */ float escapeair_force;     // ← the air-dodge burst magnitude
  /* +33C */ float escapeair_decay;
  ```
  A whole-repo search for `escapeair_force` returns exactly **two** hits: this declaration and the
  use in `ftCo_EscapeAir.c`. **No assignment / initializer with a numeric value exists** — confirming
  the magnitude is loaded from the DOL data section, not present in the decompiled C.

### The ceiling — why the number still needs #1250

This is the **same wall #1249 documented** for the smash charge-cap: `doldecomp` maps
*address ↔ name ↔ code*, but an engine value stored in the **data section** (here CommonFighterData
`+0x338`) is only recoverable as a *number* by reading the DOL/ISO bytes at that address. `doldecomp/melee`
is a far more complete decomp than `doldecomp/brawl` (the whole Escape Air routine *is* decompiled, where
Brawl's fighter engine was not — #1249), so it **does** yield the formula and the exact field address —
a true upgrade over the prior meleelight-only formula citation — but it **cannot** yield `3.1` itself.
That number remains a **T2 reimpl proxy** until a data-section read lands (#1250, live Dolphin RAM read,
ISO-gated; or a `PlCo.dat`/CommonFighterData `+0x338` dump).

### Corroboration — meleelight (T2) + a second lead

- **meleelight** @ `27af171` `src/characters/shared/moves/ESCAPEAIR.js` (locally cloned, #616):
  `cVel.x = 3.1 * Math.cos(ang)`, `cVel.y = 3.1 * Math.sin(ang)`; neutral → `(0,0)`; decay `*= 0.9`
  for the first 30 frames; interrupt to `FALLSPECIAL` at timer > 49. A faithful reimpl → its `3.1`
  and `0.9` are the author's extractions of Melee's `escapeair_force` / `escapeair_decay`. This is
  the **only source that carries the numeric `3.1`** here.
- **Second lead (not read this pass):** the #1239 source catalog lists **Magus "SSBM Data Sheet"
  `PlCo.dat` offsets** as an independent reader of the same CommonFighterData field. It reads the same
  `+0x338` region, so it is a candidate second corroboration for `3.1` without an ISO — worth a follow-up
  if the campaign wants two independent proxies before pinning. (A Google-Sheet source; tier is
  proxy/near-primary, not the retail ROM.)

### PM vs Melee

PM 3.6 **restored Melee's directional air dodge** (the whole point of PM movement tech — Brawl removed
it; #215). The sibling air-dodge values already `FOUND` — wavedash angle `17.1°` and landing lag `10f`
— match Melee exactly, consistent with a Melee-faithful restore. **No PM primary read this pass shows a
PM-specific magnitude override**, and none is documented. Whether PM 3.6 kept Melee's `escapeair_force`
byte-for-byte or retuned it is answerable only by reading PM 3.6's own data section (**#1250**); until
then, "PM = Melee's `3.1`" is the **most-supported reading but ⚠ primary-unconfirmed**, exactly as the
retail magnitude itself is.

### Routing recommendation (for the downstream DEV — do NOT edit provenance here)

- **Value:** keep `DODGE_AIR_SPEED = 17`, derivation `round(3.1 * PX_PER_UNIT)`. Unchanged.
- **Status:** **keep `FOUND`** — consistent with this file's `JOSTLE_TRIGGER_UNITS`, a meleelight
  literal kept `FOUND` with an explicit proxy caveat. (Do not silently keep the *old* citation, which
  reads as if a T1 confirms the number.)
- **Correct the source string** to stop crediting `doldecomp/melee` with the numeric value and to flag
  the proxy tier — mirroring the `JOSTLE_TRIGGER_UNITS` wording. Draft:
  > `"3.1 u/f: meleelight @27af171 characters/shared/moves/ESCAPEAIR.js cVel=3.1*(cos,sin)(ang) (SECONDARY proxy — retail Melee/PM escapeair_force @ CommonFighterData+0x338 is a data-section float, UNDOCUMENTED as a source literal, pending #1250); mechanic+field T1-confirmed doldecomp/melee @7d4a30d ftCo_EscapeAir.c + ft/types.h; SmashWiki:Air_dodge"`

  Keep the header comment in `provenance.py` / `config/physics.py` in sync (it currently says
  `doldecomp/melee (escapeair_force × (cosθ,sinθ)); PM restored Melee's air dodge` — the model claim is
  now T1-verified and correct; only the implication that the *number* came from the decomp needs fixing).

**FOUND-vs-downgrade note (decision for the human/DEV, not this research):** keeping `FOUND` is
*consistent with `JOSTLE`*. If the campaign instead decides a data-section value proxied only by a single
reimpl should not read `FOUND` (a stricter tiering than `JOSTLE` currently applies), then **both**
`DODGE_AIR_SPEED` and `JOSTLE_TRIGGER_UNITS` should move together for consistency — that is a
provenance-policy call above this one value, not a per-value edit.

### Campaign-level finding (#638)

The **first re-verify value confirms the shape of the whole engine-global campaign**: `doldecomp`
(brawl in #1249, melee here) reliably yields a hardcoded global's **formula + field address** with no
ISO, but **never the data-section number**. Every remaining engine-hardcoded re-verify candidate that
resolves to a CommonFighterData / attribute float (e.g. the #271 fireball speed, #243 waveland traction)
will hit the identical wall. **#1250 (live RAM read) is the shared unlock** for pinning any of them to a
primary number; the `doldecomp` route's role in the campaign is to nail the *mechanic + address* (so the
RAM read knows exactly which offset to sample) and to catch any value whose magnitude *is* an inline
immediate. Sequencing the campaign so #1250 lands before the engine-global batch avoids re-hitting this
ceiling one ticket at a time.

### Sources (this pass)

- **doldecomp/melee** @ `7d4a30dcd79037ca771ebbb085f045c366b9960b` (T1, retail Melee decompilation):
  [`ftCo_EscapeAir.c`](https://github.com/doldecomp/melee/blob/7d4a30dcd79037ca771ebbb085f045c366b9960b/src/melee/ft/chara/ftCommon/ftCo_EscapeAir.c),
  [`ft/types.h`](https://github.com/doldecomp/melee/blob/7d4a30dcd79037ca771ebbb085f045c366b9960b/src/melee/ft/types.h)
  (`escapeair_force` @ `+0x338`).
- **meleelight** @ `27af171` (T2 Melee reimpl, #616):
  `src/characters/shared/moves/ESCAPEAIR.js` (`3.1 * cos/sin(ang)`, decay `0.9`).
- **#1239 catalog lead** (not read): Magus "SSBM Data Sheet" `PlCo.dat` / CommonFighterData `+0x338`.
- Prior: **#215** (engine-hardcoded, not web-datamineable), **#1249** (`doldecomp/brawl` symbol-map
  route + the data-section ceiling), **#1250** (live RAM read — the ISO-gated unlock), ADR-0003
  (provenance registry), `docs/pm-reference/smash-charge-ramp-provenance.md` (#1249's parallel finding).
