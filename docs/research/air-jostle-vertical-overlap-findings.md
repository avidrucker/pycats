# Air jostle & vertical-overlap ("ratchet") behavior — findings (#1015)

**Ticket:** #1015 (research · `area:entities`) · downstream of #1003 / ADR-0012.
**Questions:** (1) Does character jostling exist in the **air** in Melee / Brawl / PM 3.6, and
how strong? (2) What is the "ratchet" / flyover behavior — does canon char-vs-char collision have
any **vertical** component or overlap-tolerance rule, and how do the engines avoid the sideways
ratchet? Picks up the two trails #594 left open (Q3 air tension; Q2 stacking ⚠ UNDOCUMENTED).
**Status:** both questions answered, and **upgraded from #594's inference to PRIMARY** by tracing
the retail Melee decompilation (`doldecomp/melee`) to the actual char-vs-char push routine —
which #594 could not reach (rate-limited). **Research only — reports the option space; it does
not decide the spec** (RULES → "research never produces the spec"). Any change is a follow-on
ARC/decision ticket with the human, then a DEV ticket.

Confidence tiers used: `[PRIMARY]` (retail Melee decomp / SmashWiki), `[SECONDARY]` (meleelight, a
faithful Melee reimplementation — not the ROM), `[INFERENCE]`, `[UNDOCUMENTED]`.

---

## TL;DR

1. **Air jostle does not exist in Melee.** `[PRIMARY]` The retail char-vs-char push (the engine's
   **"player nudge"**, `Fighter.xF8_playerNudgeVel`, in `src/melee/ft/ftcommon.c`) is gated on
   **both** fighters being grounded (`ground_or_air == GA_Ground`) on the same/adjacent floor
   line. An airborne fighter **neither pushes nor is pushed.** meleelight (secondary proxy) is
   identically grounded-only. Brawl/PM 3.6 inherit this — the wiki states Brawl's jostle "effect
   itself is unchanged" from Melee `[PRIMARY-for-Melee → INFERENCE-for-PM, strong]`. The wiki's
   "stronger on the ground, particularly in *Ultimate*" line publishes **no air magnitude** for
   the pre-Ultimate games. **Two airborne fighters therefore pass through / overlap each other —
   no collision resolution applies.** **Recommendation: keep pycats grounded-only (the ADR-0012
   V1 model); do not add an air push** — it would be an unsourced invention that contradicts the
   retail gate.

2. **Canon has no vertical resolution — the ratchet is impossible in the canon model.**
   `[PRIMARY]` The retail nudge is applied as `cur_pos.x += nudge.x` (horizontal) and
   `cur_pos.y += 0` — the **height axis is explicitly zeroed** (the decomp author annotates "Why
   is there no vertical component?"); the only non-horizontal term is a 2.5D depth nudge
   (`cur_pos.z`), irrelevant to pycats' 2D plane. Because activation is gated on **grounded-state**,
   not geometric overlap, a fighter passing *over* another is airborne, fails the gate, and
   triggers no push — so the sideways **ratchet cannot occur.** The pycats #68 ratchet was an
   artifact of activating on *any* AABB `rect.colliderect` overlap; ADR-0012's grounded +
   same-surface gate removes it **by construction** (#68's own validation comment confirms the
   grounded gate resolves the same bug). There is **no overlap-tolerance rule** in canon — the
   removed `JOSTLE_MIN_VOVERLAP_FRAC = 0.8` was a pycats-only workaround for the wrong activation
   model, now obsolete.

---

## Q1 — Does air jostle exist in Melee / Brawl / PM 3.6, and how strong?

**Answer:** **No air jostle in retail Melee** `[PRIMARY]`; Brawl/PM 3.6 inherit the grounded-only
model `[INFERENCE, strong]`. The wiki publishes no air magnitude for these games; the question of
"how strong in the air" is **moot — there is no air push to measure.**

### Primary: the retail Melee decomp

The Melee char-vs-char push is the engine's **"player nudge."** It is **not** in any `*coll*` file
(those are attack collision and fighter-vs-stage ECB — confirming #594); it lives in the fighter
common-think. Provenance: `doldecomp/melee` @ `51890e0b4cf8915b895a60b97bc6c0298c97c85d` (master,
2026-08-02). `[PRIMARY]`

Driver — `ftCommon_8007E0E4(Fighter_GObj*)` in `src/melee/ft/ftcommon.c` — zeroes the nudge, then
gates the **entire** computation on the pushing fighter being grounded:

```c
fp->xF8_playerNudgeVel.y = 0;
fp->xF8_playerNudgeVel.x = 0;
if (!fp->x2219_b1 && !fp->x2219_b5 && fp->ground_or_air == GA_Ground) {   // GATE: pusher grounded
    ...
    ftCommon_8007DD7C(gobj, &sp10);   // pairwise loop over other fighters
```

Pairwise loop — `ftCommon_8007DD7C` — **skips any other fighter that is not grounded**, and
requires both on the same **or adjacent** floor line:

```c
if (cur_ft->x221F_b3 || cur_ft->ground_or_air != GA_Ground ||   // OTHER must be grounded
    cur_ft->victim_gobj != NULL || cur_ft->x221F_b4) {
    continue;
}
arg_gnd = arg_ft->coll_data.floor.index;
cur_gnd = cur_ft->coll_data.floor.index;
if (arg_gnd == cur_gnd || cur_gnd == mpLineGetNext(arg_gnd) ||   // same OR adjacent floor line
    cur_gnd == mpLineGetPrev(arg_gnd)) {
    ... arg_ft->xF8_playerNudgeVel.x += ...; arg_ft->xF8_playerNudgeVel.y += ...;
```

**Both** the pusher and the pushed must be `GA_Ground`. **An airborne fighter neither pushes nor
is pushed — the jostle is grounded-only in retail Melee.** This is a **PRIMARY** confirmation of
what #594 could only infer from meleelight.

> **Nuance vs ADR-0012's gate (recorded for the future air/overlap ARC — not a V1 concern):**
> retail Melee jostles across the **same _or adjacent_ floor line** (`mpLineGetNext/Prev`), whereas
> ADR-0012 (following meleelight's exact `onSurface` type+index match) requires the **same**
> surface. Retail is thus marginally more permissive at floor-segment boundaries. This does **not**
> re-open the ADR-0012 ground model (settled); it is a fidelity footnote for any later refinement.

### Secondary: meleelight agrees (categorical)

meleelight (`schmooblidon/meleelight` @ `27af171`, `src/physics/physics.js`) nests its entire push
under `if (player[i].phys.grounded)` and additionally requires the other fighter grounded on the
**same** `onSurface` (type + index) — no air push whatsoever. `[SECONDARY]`

### Primary (prose): the wiki adds nothing for the air

SmashWiki, *Jostle* (lead) — https://www.ssbwiki.com/Jostle: `[PRIMARY, but ambiguous]`

> "The effect tends to be stronger on the ground, particularly in *Super Smash Bros. Ultimate*
> between two opposing fighters."

This does **not** establish a Melee/Brawl/PM air push: the pronounced ground/air asymmetry is
pinned to **Ultimate**, and "stronger on the ground" is fully compatible with "grounded-only"
(air strength = 0 is the limiting case). The numeric **"jostle strength"** attribute the wiki
attaches to the effect is **Ultimate-only** (#594). For Melee/Brawl the wiki says only "equal
strength" and that Brawl's "effect itself is unchanged." A direct fetch of the full article
surfaced **no** airborne or vertical sentence.

### Resolving the #594 tension

#594 left open: wiki "weaker in air" vs meleelight "grounded-only." **The decomp settles it in
favour of grounded-only** — the retail gate requires both fighters `GA_Ground`. The wiki's
"stronger on the ground" line is weaker evidence than #594 implied for a Melee/Brawl/PM air push
and is best read as Ultimate-weighted. **Confidence: HIGH that Melee/Brawl/PM 3.6 have no air
jostle** (PRIMARY for Melee; strong inference for Brawl/PM via the wiki's era statements).

---

## Q2 — Ratchet / flyover & vertical-overlap behavior

**Answer:** Canon char-vs-char collision is **horizontal-only with no vertical resolution and no
overlap-tolerance rule.** `[PRIMARY]` The push is gated on **grounded-state**, so a flyover
(airborne passer) never triggers it — the sideways ratchet is **impossible in the canon model.**
The pycats #68 ratchet was a defect of the pycats activation model, not a canon mechanic.

### The canon model has no vertical axis — primary confirmation

The retail nudge is applied in `fighter.c` (`Fighter_8006A360`) as:

```c
// add some horizontal+depth offset to the position? Why is there no
// vertical component?                        ← decomp author's own annotation
fp->cur_pos.x += fp->xF8_playerNudgeVel.x;   // horizontal (left/right)
fp->cur_pos.y += 0;                          // vertical/HEIGHT — explicitly ZERO
fp->cur_pos.z += fp->xF8_playerNudgeVel.y;   // depth (into/out of screen — 2.5D only)
```

The `Vec2` nudge's `.x` drives horizontal separation; its `.y` field is applied to **depth
(`cur_pos.z`)**, not height. The **height axis (`cur_pos.y`) is explicitly `+= 0`.** `[PRIMARY]`
For pycats' 2D gameplay plane this is **horizontal-only, no vertical resolution** — you cannot
stand on a fighter's head (no upward resolution), and a fighter above another is simply not pushed
(gate failure). meleelight matches (`pos.x` only). `[SECONDARY, agrees]`

Because the gate is **fighter grounded-state**, not a **geometric vertical-overlap threshold**,
canon needs no "overlap tolerance" tuning. The question "how much vertical overlap before the push
activates?" is a **category error against the canon model** — canon never asks about vertical
overlap; it asks whether both fighters stand on the same/adjacent floor.

### The pycats #68 ratchet, explained by the model mismatch

pycats #68 ("jumping over a flush-adjacent character shoves the stationary character sideways"):
an airborne fighter A rising over a grounded fighter B re-overlapped B's AABB each rising frame,
and `resolve_player_push` — which activated on **any** `rect.colliderect` overlap — ratcheted B
**~35 px** over ~12 frames until A cleared B vertically. `[in-repo, #68]`

Root cause (from #68): the push activated on geometric AABB overlap with no grounded/vertical
gate. Two candidate fixes were validated in #68's thread:
- **v-overlap gate** (`JOSTLE_MIN_VOVERLAP_FRAC = 0.8` of the shorter body) — the fix that shipped;
  a pycats-only geometric heuristic with **no canon basis** (classified **TUNED** in
  `docs/research/2026-07-07-custom-mechanics-inventory.md`).
- **grounded gate** (`a.on_ground and b.on_ground`) — the **canon-faithful** gate.

> #68 comment (verbatim): "gating the fighter-fighter push on `a.on_ground and b.on_ground` makes
> the bug-case test xpass (P2 displacement → 0) while the straight-up-jump guard stays green — so
> it resolves the shove without breaking the no-overlap case."

**ADR-0012 adopts the grounded + same-surface gate**, which removes the ratchet **by
construction** (the airborne flyover fails the grounded gate → no push → no sideways drift). This
is why #1003 removed `JOSTLE_MIN_VOVERLAP_FRAC`: with the canon gate, the geometric v-overlap
heuristic is **redundant**, not merely replaced — there is no flyover to guard against once
verticality is out of the activation condition. `[INFERENCE from ADR-0012 + #68 + the primary gate,
strong]`

### Two airborne fighters — they pass through each other

**Two airborne fighters overlap / pass through each other; no collision resolution applies.**
The grounded gate fails for both (neither is `GA_Ground`), so the nudge produces zero separation
force, and the jostle is the **only** char-vs-char positional interaction in the engine (attack
collision is hitbox/hurtbox — `ftcoll.c`; ECB is fighter-vs-stage — `mpcoll`; the decomp search
found no other char-vs-char push). With no push and no other routine, airborne fighters occupy
the same space freely — they do **not** collide. `[PRIMARY for "no air push" + HIGH-confidence
inference for "therefore pass-through", resting on the negative that the nudge is the only such
routine — a broad decomp search, not an absolute proof]`

### Stacking / standing on a head

**No vertical resolution exists** in canon (`cur_pos.y += 0`, PRIMARY). Fighters overlapping
vertically are tolerated; the only interaction is the horizontal grounded push. This **closes #594
Q2** ("on-top / stacking"), which returned ⚠ UNDOCUMENTED in primary *prose* — the decomp shows
the model has no vertical branch, so there is nothing to stack-resolve. `[PRIMARY, upgrades #594
inference]`

---

## Keep-vs-change recommendation (opinion — the human decides at commit)

1. **Air jostle — keep grounded-only (recommended, now on PRIMARY basis).** The retail Melee
   engine gates the push on both fighters grounded; there is no air push to port. Adding one would
   contradict the primary source and be an **unsourced invention**. Declined absent new primary
   evidence. If the human wants an air feel regardless, that is a **TUNED design decision**, not a
   canon-seeking one, and must be labelled TUNED (not FOUND).

2. **Vertical / ratchet — no further work needed.** ADR-0012's grounded + same-surface gate is
   canon-faithful (PRIMARY: `cur_pos.y += 0`, grounded gate) and removes the ratchet by
   construction. The `JOSTLE_MIN_VOVERLAP_FRAC` heuristic is correctly slated for removal in the
   DEV ticket (#1020); introduce **no** replacement overlap-tolerance rule — canon has none.

3. **Optional future fidelity (low priority, feeds a later ARC — not filed here):** retail Melee
   jostles across the same **or adjacent** floor line, whereas ADR-0012 requires the exact same
   surface. A refinement to `same-or-adjacent` would be marginally more faithful at floor-segment
   boundaries. Not a V1 concern; recorded so the trail isn't lost.

**Follow-on scope:** this ticket recommends **no** air-jostle enhancement on current evidence, so
it files **no** downstream ticket. If the human still wants to pursue air jostle or the
adjacent-floor refinement, the honest path is a fresh ARC/decision ticket citing this doc — and
any air push ships **labelled TUNED**, since the primary source says there is none. Research
reports options only.

---

## Sources

**Primary:**
- `doldecomp/melee` @ `51890e0b4cf8915b895a60b97bc6c0298c97c85d` (master, 2026-08-02) —
  `src/melee/ft/ftcommon.c` (`ftCommon_8007E0E4` driver + grounded gate; `ftCommon_8007DD7C`
  pairwise loop, other-fighter grounded skip + same/adjacent floor-line check); `src/melee/ft/
  fighter.c` (`Fighter_8006A360` — nudge applied `cur_pos.x += .x`, `cur_pos.y += 0`,
  `cur_pos.z += .y`); `src/melee/ft/types.h` (`Vec2 xF8_playerNudgeVel`). Char-vs-char push is
  **grounded-gated and has no height component.**
- SmashWiki, *Jostle* — https://www.ssbwiki.com/Jostle (lead "stronger on the ground, particularly
  in *Ultimate*"; Melee/Brawl "equal strength" / "effect unchanged"; no airborne or vertical
  statement; "jostle strength" attribute Ultimate-only).

**Secondary (faithful reimplementation):**
- meleelight `schmooblidon/meleelight` @ `27af171` — `src/physics/physics.js`, push region nested
  under `if (player[i].phys.grounded)` requiring the other fighter grounded on the same
  `onSurface`: `pos.x`-only, no vertical branch, no air push. Local clone:
  `~/Documents/Study/JavaScript/meleelight/` (#616).

**In-repo:**
- `docs/adr/0012-pm-faithful-character-jostling.md` — the ratified V1 grounded + same-surface gate.
- pycats #68 — the flyover-ratchet bug, its root cause (AABB-overlap activation), and the
  validation that the grounded gate resolves it.
- `docs/research/character-collision-push-findings.md` (#594) — the ground model + the Q2/Q3 trails
  this ticket picks up and upgrades to PRIMARY.
- `docs/research/2026-07-07-custom-mechanics-inventory.md` — `JOSTLE_MIN_VOVERLAP_FRAC` TUNED
  classification.

**Ultimate-only (out of scope, recorded to prevent mis-citation):** the per-fighter "jostle
strength" attribute/table is an Ultimate rework; it does not describe Melee/Brawl/PM, and its
"stronger on the ground" phrasing must not be cited as a Melee/Brawl/PM air magnitude.
