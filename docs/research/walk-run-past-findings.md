# Can fighters walk / run past (through) each other? — findings (#1038)

**Ticket:** #1038 (research · `area:entities`) · downstream of #594 (character collision),
#1015 (air jostle), ADR-0012 / #1020 (the shipped PM-faithful ground jostle).
**Questions:** (1) Can two fighters walk past / through each other in Melee / Brawl / PM 3.6 —
always, conditionally, or never; is there any **hard horizontal block**, or only the soft jostle
push? (2) Does **running / dashing** differ from walking? (3) Interaction with the shipped
ADR-0012 jostle — is pycats' "moving fighter passes through" canon? (4) Confirm the walk/run
hard-block is **Ultimate-only** (Melee / Brawl / PM 3.6 have none).
**Status:** all four answered from **primary sources** — the retail Melee decompilation
(`doldecomp/melee`) for the engine behavior, SmashWiki *Jostle* for the cross-game prose, with
meleelight as a secondary faithful-reimplementation cross-check. **Research only — reports the
option space; it does not decide the spec** (RULES → "research never produces the spec"). Any
change is a follow-on ARC/decision ticket with the human.

Confidence tiers: `[PRIMARY]` (retail Melee decomp / SmashWiki), `[SECONDARY]` (meleelight — a
faithful Melee reimplementation, not the ROM), `[INFERENCE]`, `[UNDOCUMENTED]`.

---

## TL;DR

**Fighters can walk and run straight through / past each other in Melee, Brawl, and PM 3.6.**
`[PRIMARY]` There is **no hard horizontal block and no minimum-separation clamp** — the only
char-vs-char positional interaction is the soft "player nudge" jostle, a **fixed-constant**
per-frame push added *on top of* the fighter's own locomotion. Because a walk or dash moves far
more per frame than the nudge, a determined mover overpowers it and crosses the opponent's body.
The walk/run **hard-block** ("can no longer walk or run past each other at all") is an **Ultimate
rework** and does **not** exist in Melee / Brawl / PM 3.6.

pycats matches this. The shipped ADR-0012 jostle nudges `JOSTLE_PUSH_PX = 2` px/frame while walk
(`MOVE_SPEED = 6`) and dash (`DASH_SPEED = 8`) move 6–8 px/frame — so a moving fighter nets
4–6 px/frame of closing and **passes through** a stationary opponent. That "pass-through" is
**canon-faithful**, not a bug. **Recommendation: keep as-is; do not add a horizontal block** —
one would be an Ultimate-only import that contradicts the primary source.

---

## Q1 — Can two fighters walk past / through each other? Any hard block?

**Answer: Yes — pass-through is allowed; there is NO hard horizontal block in Melee / Brawl /
PM 3.6.** The only char-vs-char positional interaction is the soft jostle nudge, which slows a
crossing but never prevents it. `[PRIMARY]`

### Primary — the retail Melee decomp: the nudge is additive, with no clamp

The char-vs-char push is the engine's **"player nudge"** (`Fighter.xF8_playerNudgeVel`), traced
in #1015 to `src/melee/ft/ftcommon.c` — driver `ftCommon_8007E0E4`, pairwise loop
`ftCommon_8007DD7C`. Provenance: `doldecomp/melee` @
`51890e0b4cf8915b895a60b97bc6c0298c97c85d` (master, 2026-08-02). `[PRIMARY]`

Two facts settle Q1 directly from the decomp:

1. **The nudge is a fixed constant, not a barrier.** In `ftCommon_8007DD7C` the horizontal push is

   ```c
   arg_ft->xF8_playerNudgeVel.x +=
       temp_f0 < 0 ? -p_ftCommonData->x450
                   : p_ftCommonData->x450;
   ```

   `x450` is a constant from common fighter data; the **direction** depends only on the sign of
   the relative horizontal position (`temp_f0`), and the **magnitude is fixed** — it does not
   scale with how far apart or how fast the fighters are moving.

2. **Nothing stops the fighter's own horizontal movement.** The nudge is **purely additive** —
   `xF8_playerNudgeVel` is accumulated and added to position alongside the fighter's own
   locomotion velocity. The one clamp in `ftCommon_8007E0E4` bounds the **nudge velocity itself**
   (prevents runaway accumulation), **not** the fighter's position or separation:

   ```c
   if (sp10.z + fp->xF8_playerNudgeVel.y > phi_f31) {
       fp->xF8_playerNudgeVel.y = phi_f31 - sp10.z;
   }
   ```

   There is **no hard block or minimum-separation enforcement** anywhere in the nudge code.
   `[PRIMARY]`

Consequence: a walking/running fighter advances by (own velocity) each frame while the nudge
subtracts only a small fixed amount. Own velocity ≫ nudge, so the mover keeps closing and
**crosses through** the opponent — the nudge merely slows the crossing. The jostle is the **only**
char-vs-char positional routine (attack collision is hitbox/hurtbox — `ftcoll.c`; ECB is
fighter-vs-stage — `mpcoll`; #594/#1015 decomp searches found no other), so there is nothing else
to block the crossing. `[PRIMARY for "nudge is the only routine" + INFERENCE(strong) for
"therefore pass-through"]`

### Primary (prose) — SmashWiki confirms the block is Ultimate-only

SmashWiki, *Jostle* — https://www.ssbwiki.com/Jostle: `[PRIMARY]`

> "In *Super Smash Bros. Ultimate*, jostling on the ground has been heavily reworked. Characters
> on the ground who are not teammates can no longer walk or run past each other at all, outside
> certain actions such as dodges."

The hard-block ("can no longer … at all") is stated **for Ultimate**, framed as a *rework*, and
"the article does not mention similar restrictions in Melee or Brawl." For the pre-Ultimate games
the only char-vs-char effect the article describes is the soft push. `[PRIMARY]`

### Secondary — meleelight agrees

meleelight (`schmooblidon/meleelight` @ `27af171`, `src/physics/physics.js`, grounded push block)
nudges `pos.x += sign(...) * -0.3` for `diff < 6.5` and otherwise leaves the fighter's own
velocity untouched — a fixed 0.3 u/frame position offset with no clamp, no barrier. A mover's own
velocity carries it through. `[SECONDARY, agrees with PRIMARY]`

**Verdict:** walk-past / run-through is **allowed (conditionally: the soft nudge is overpowered
by any real locomotion speed)**. There is **no hard horizontal block** in Melee / Brawl / PM 3.6.

---

## Q2 — Does running / dashing differ from walking?

**Answer: The per-frame nudge magnitude is speed-independent (a fixed constant); what differs is
that a faster mover's own locomotion overpowers the fixed nudge more decisively. Neither walk nor
run is ever hard-stopped at the opponent's body in Melee / Brawl / PM 3.6.** `[PRIMARY]`

There is an apparent tension between two primary sources; it resolves cleanly:

- **Decomp (PRIMARY):** the nudge push is a **fixed constant** `x450`, independent of either
  fighter's velocity (Q1). The only place velocity enters meleelight's port is the **exact-overlap
  tie-break** (`diff === 0` → the fighter with the larger `|cVel.x|` pushes the other) — a
  direction rule, not a magnitude scale. `[PRIMARY + SECONDARY]`

- **SmashWiki (PRIMARY):** "The speed of a fighter's walk or dash determines the rate at which
  they can apply the force of their push in a direction, faster movement allowing players to apply
  force at a fittingly faster rate."

These are consistent, not contradictory. The wiki is describing the **aggregate** shoving outcome,
not the per-frame nudge constant: a fighter's **own walk/dash velocity** is what accumulates
position against the opponent, so faster movement wins the shoving contest and crosses faster —
exactly the decomp's "fixed nudge + own locomotion added on top" model. Running does **not**
strengthen the nudge; it means the runner's larger own velocity dominates the fixed nudge sooner.

Crucially, **no run/dash hard-stop exists** in Melee / Brawl / PM 3.6 — the "can no longer walk or
run past each other" block is **Ultimate-only** (Q4). So both walking and running pass through; run
just does it faster. `[PRIMARY]`

---

## Q3 — Interaction with the shipped ground jostle (ADR-0012)

**Answer: pycats' "moving fighter passes through a stationary one" is canon-faithful. The shipped
jostle correctly *nudges* without *blocking*.** `[PRIMARY basis for canon + in-repo for pycats]`

The shipped `resolve_player_push` (`pycats/core/physics.py`, ADR-0012 / #1020) is a literal port
of meleelight: a gradual, position-only nudge of `JOSTLE_PUSH_PX = 2` px/frame per fighter, gated
on both grounded + same platform, triggered within `JOSTLE_TRIGGER_PX = 35` px centre-distance,
**velocity never touched**. Against the locomotion layer (`pycats/config/physics.py`):

| Interaction | px/frame | Net effect |
|---|---|---|
| Jostle nudge (per fighter) | 2 | separates the pair ~4 px/frame when both idle |
| Walk (`MOVE_SPEED`) | 6 | mover nets **6 − 2 = 4 px/frame** closing → **passes through** |
| Dash (`DASH_SPEED`) | 8 | mover nets **8 − 2 = 6 px/frame** closing → **passes through faster** |

This is the **same structure as canon**: a small fixed nudge added on top of much larger own
locomotion, with no hard block → the moving fighter crosses the stationary one. Walk vs dash
differ exactly as canon predicts (faster own speed → faster crossing), and pycats has **no**
horizontal barrier — matching Melee / Brawl / PM 3.6, not Ultimate. `[INFERENCE(strong) from the
primary canon model + confirmed pycats constants]`

**Assessment:** the pass-through is **intended and faithful**. The jostle's job is to gently
separate two fighters who are *standing* in the same spot (both idle → they drift apart), not to
wall off a fighter who is *walking* into another. pycats does exactly that.

---

## Q4 — Confirm the walk/run hard-block is Ultimate-only

**Answer: Confirmed. The walk/run hard-block and the per-fighter "jostle strength" table are
Ultimate-only; Melee / Brawl / PM 3.6 have neither — fighters pass through freely.** `[PRIMARY]`

SmashWiki, *Jostle*: `[PRIMARY]`

- Hard-block: "In *Super Smash Bros. Ultimate*, jostling on the ground has been **heavily
  reworked**. Characters on the ground who are not teammates **can no longer walk or run past each
  other at all**, outside certain actions such as dodges." — stated for **Ultimate**; the article
  states no such restriction for Melee or Brawl.
- Jostle strength: "How strongly one character can push another … is determined by their **jostle
  strength** …" — accompanied by a per-fighter table published **exclusively for Ultimate**. For
  Melee/Brawl the article says only that characters push "with equal strength" and that Brawl's
  "effect itself is unchanged" from Melee (#594).

Cross-era: **PM 3.6 runs on the Brawl engine**, and the wiki states Brawl's jostle is "unchanged"
from Melee. So PM 3.6 inherits the **Melee/Brawl** model — soft nudge, pass-through allowed, **no**
Ultimate hard-block. `[INFERENCE from the wiki's era statements + the Brawl-engine base; no
PM-specific PMDT jostle doc located — consistent with #594/#1015]`

This confirms #594's and #1015's out-of-scope framing of the Ultimate rework: it is a distinct
mechanic that must **not** be cited as Melee/Brawl/PM behavior.

---

## Keep-vs-change recommendation (opinion — the human decides at commit)

**Keep pycats as-is. Do not add a horizontal block or minimum-separation clamp.** `[recommended]`

1. **Keep (recommended).** pycats already matches the primary canon model: a soft fixed nudge with
   no hard block, so walk/run overpowers it and fighters pass through. Adding a walk/run block
   would import an **Ultimate-only** mechanic the primary source explicitly ties to Ultimate — an
   unsourced divergence from PM 3.6. Nothing here is a bug; the pass-through is the intended
   behavior.

2. **(Only if a future design goal wants it) an Ultimate-style hard-block** would be a **TUNED
   design decision**, not a canon-seeking one, and must be labelled TUNED — the primary source says
   Melee/Brawl/PM have no such block. That is a separate design direction, not a parity fix.

**Follow-on scope:** this ticket recommends **no** change on current evidence, so it files **no**
downstream ticket. If the human later wants an Ultimate-style block anyway, the faithful path is a
fresh ARC/decision ticket citing this doc, and any block ships **labelled TUNED**. Research reports
options only.

---

## Sources

**Primary:**
- `doldecomp/melee` @ `51890e0b4cf8915b895a60b97bc6c0298c97c85d` (master, 2026-08-02) —
  `src/melee/ft/ftcommon.c`: `ftCommon_8007DD7C` computes `xF8_playerNudgeVel.x` as a **fixed
  constant** (`±p_ftCommonData->x450`), direction by relative position only, **no** velocity/distance
  scaling; `ftCommon_8007E0E4` clamps the **nudge velocity**, not the fighter's position/separation.
  **No hard block or minimum-separation enforcement** — the nudge is additive over the fighter's own
  locomotion. (Routine first traced in #1015.)
- SmashWiki, *Jostle* — https://www.ssbwiki.com/Jostle: walk/dash speed sets the **rate** a fighter
  applies push force ("faster movement … at a fittingly faster rate"); the "**can no longer walk or
  run past each other at all**" hard-block is **Ultimate** ("heavily reworked"), with **no** such
  restriction stated for Melee/Brawl; "**jostle strength**" attribute + table are **Ultimate-only**.

**Secondary (faithful reimplementation):**
- meleelight `schmooblidon/meleelight` @ `27af171` — `src/physics/physics.js` grounded push block:
  fixed `pos.x += sign(...) * -0.3` for `diff < 6.5`, velocity used only for the `diff === 0`
  direction tie-break, no clamp/barrier → own velocity carries a mover through. Local clone:
  `~/Documents/Study/JavaScript/meleelight/` (#616).

**In-repo:**
- `pycats/core/physics.py` — `resolve_player_push` (ADR-0012 port); `JOSTLE_PUSH_PX = 2`,
  `JOSTLE_TRIGGER_PX = 35`.
- `pycats/config/physics.py` — `MOVE_SPEED = 6` (walk), `DASH_SPEED = 8` (dash): both ≫ the 2 px/f
  nudge, so a mover passes through.
- `docs/adr/0012-pm-faithful-character-jostling.md` — the ratified V1 ground jostle.
- `docs/research/character-collision-push-findings.md` (#594) — the ground model + pass-through
  framing this ticket pins for the horizontal-crossing axis.
- `docs/research/air-jostle-vertical-overlap-findings.md` (#1015) — the retail-decomp trace of the
  player-nudge routine, reused here.

**Ultimate-only (out of scope, recorded to prevent mis-citation):** the walk/run hard-block and the
per-fighter "jostle strength" attribute/table are Ultimate reworks; they do **not** describe
Melee / Brawl / PM 3.6.
