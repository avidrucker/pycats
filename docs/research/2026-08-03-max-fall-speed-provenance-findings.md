# MAX_FALL_SPEED — provenance + is a global fall-speed cap even a real engine concept? — findings (#1118)

**Ticket:** #1118 (research · `area:combat` / `combat:physics`) · child of the fast-fall V1 epic
**#1068**; spun out of the fast-fall findings (`docs/research/2026-08-02-fast-fall-mechanics-findings.md`, #1069).
**Questions:** (1) provenance of pycats' `MAX_FALL_SPEED = 13` — sourced or guessed? (2) does
**Melee** have a global fall-speed cap, or per-fighter terminal + fast-fall only? (3) **Brawl / PM 3.6**
— same. (4) does **meleelight** have any global `MAX_FALL_SPEED`, or only per-char `terminalV` /
`fastFallV`? (5) recommendation / option space for pycats.
**Status:** all five answered. Q1 settled from in-repo history (`[IN-REPO]`). Q2/Q4 settled from a
faithful Melee reimplementation (meleelight, `[SECONDARY]`). Q3 is `[INFERENCE]` (PM inherits the
Brawl per-fighter attribute model) backed by `[TIER-3]` SmashWiki. **Tier-1 (retail decomp / DOL·.rel
disasm) was NOT gathered** — no local Melee decomp is reachable (see *Blocked / deferred source*);
Tier-1 confirmation stays deferred to **#988**, exactly as the fast-fall findings deferred it.
**Research only** — reports findings + the option space for the ARC/decision child; it does **not**
decide the spec (RULES → "research never produces the spec"). Any change is a follow-on ARC/decision
ticket with the human.

Confidence tiers used below:
- `[IN-REPO]` — current pycats source / git history (the baseline an ARC child would change).
- `[SECONDARY]` — meleelight (`~/Documents/Study/JavaScript/meleelight`), a faithful Melee
  reimplementation in JS. Not the ROM; the ticket's **Tier-2**.
- `[TIER-3]` — SmashWiki prose / attribute tables (the ticket's **Tier-3**).
- `[INFERENCE]` — PM inheritance / reasoning, explicitly labelled, **not** confirmation.
- `[TIER-1 PENDING #988]` — would need retail decomp / DOL·.rel disasm; not gathered here.

---

## Per-question answer table

| # | Question | Answer (short) | Strongest evidence |
|---|----------|----------------|--------------------|
| 1 | Provenance of `MAX_FALL_SPEED = 13` | **Guessed / tuned default.** The literal `13` entered in the **init commit**, before any PM sourcing pass. The #120/#384 calibration re-derived `GRAVITY`/`MOVE_SPEED`/`JUMP_VEL` (all `FOUND`) but **left `13` untouched** and classified it `DIVERGENCE`, not `FOUND`. Post-hoc it happens to sit at ≈ PM-Mario **fast-fall** (2.3 u/f × 5.4 ≈ 12.4). | `[IN-REPO]` git blame + `provenance.py` |
| 2 | Does **Melee** have a global fall cap? | **No.** Falling is per-fighter: each character has its own gravity, terminal velocity ("fall speed"), and a distinct fast-fall speed. No engine-wide maximum. | `[SECONDARY]` meleelight (no global constant; every clamp is per-char `terminalV`) + `[TIER-3]` |
| 3 | **Brawl / PM 3.6** — same? | **Per-fighter, no global cap (inference).** Brawl and PM inherit the per-fighter attribute-table model; PM 3.6 does not introduce an engine-global fall cap. PM Mario base 1.7 / fast-fall 2.3 u/f. | `[INFERENCE]` + `[TIER-3]` SmashWiki; Tier-1 deferred #988 |
| 4 | Does **meleelight** have a global `MAX_FALL_SPEED`? | **No.** No global fall-cap constant exists anywhere in the source. Every fall clamp is `min` against `player[p].charAttributes.terminalV`; fast-fall sets `cVel.y = -charAttributes.fastFallV`. Both are per-character. | `[SECONDARY]` grep + call-site census |
| 5 | Recommendation / option space | pycats **already models a per-fighter terminal cap** (`FighterData.max_fall_speed`, #126) — the global `13` is only the *default*. The real gap is the **base-vs-fast-fall split** (a 2nd per-fighter value + the fast-fall trigger). Three options below; each perturbs goldens, `KNOCKDOWN_VY_THRESHOLD`, and knockback descent. | `[IN-REPO]` |

---

## Q1 — Provenance of `MAX_FALL_SPEED = 13`

**Answer: guessed / tuned default, never sourced; later rationalized as ≈ PM-Mario fast-fall and
classified a `DIVERGENCE`. `[IN-REPO]`**

- **Origin.** `git log --reverse -S MAX_FALL_SPEED` puts the constant in the **`init commit`** (with
  the first physics/movement extraction), i.e. it predates every PM-sourcing pass. It was an initial
  play-feel number, not a derived one.
- **Not re-derived during PM calibration.** The base-movement block in `combat/provenance.py`
  ("calibrated to PM Mario via PX_PER_UNIT, #120/#384") re-derived its neighbours and marked them
  `FOUND`:
  - `GRAVITY = 0.5` — `FOUND`, "PM Mario gravity 0.095 u/f² (SmashWiki:Mario_(PM); #120)" (0.095 × 5.4 ≈ 0.51).
  - `MOVE_SPEED = 6` — `FOUND`, "PM Mario walk 1.1 u/f" (1.1 × 5.4 ≈ 6).
  - `JUMP_VEL = -13` — `FOUND`, calibrated to PM Mario full-hop 30.19 u.
  - **`MAX_FALL_SPEED = 13` — `DIVERGENCE`**, basis `#384`, note: *"pycats uses a single global fall
    speed ~= PM Mario fast-fall 2.3 u/f; the Melee/PM base 1.7 / fast-fall 2.3 split is not modelled
    (SmashWiki:Mario_(PM); #120)."* It was flagged as a divergence and kept, not sourced.
- **Corroborating comment (#785)** in `config/physics.py`: *"these velocity/physics defaults are
  GAME-TUNED px, not faithful rukaidata × PX_PER_UNIT — e.g. `MAX_FALL_SPEED 13` is well above Mario's
  real term vel (1.7 × 5.4 ≈ 9.2)."*
- **Reading of the coincidence.** `13` ≈ PM Mario **fast-fall** (2.3 × 5.4 ≈ 12.4), **not** base fall
  (1.7 × 5.4 ≈ 9.2). So the single cap pycats calls "max fall speed" is numerically the *fast-fall*
  terminal — which is exactly why the fast-fall findings noted a faithful split must **lower the base**
  rather than raise the peak.

**Verdict: GUESSED (initial tuning value), later annotated `DIVERGENCE` — not `FOUND`.**

## Q2 — Does Melee have a global fall-speed cap?

**Answer: no — falling is per-fighter (gravity + terminal + fast-fall), no engine-wide cap. `[SECONDARY]` + `[TIER-3]`**

- **meleelight has no global fall constant.** A repo-wide search for `maxfall` / `max_fall` /
  `fall-speed cap` / any global terminal returns nothing. The only fall clamps are per-character
  (Q4). meleelight is a faithful Melee reimplementation, so its architecture is strong secondary
  evidence for the retail engine's model: **fall speed lives in each fighter's attribute table**.
- **SmashWiki "Falling speed" `[TIER-3]`** (verbatim): *"Falling speed is measured in units per
  frame."* … *"A character's falling speed can greatly impact the fighting style — for instance, Fox,
  a fast-faller…"* … *"All characters can also fast fall at any time during a descent to increase
  falling speed, so long as they are not in tumble."* The article lists a **per-character value for
  every fighter** — i.e. a per-fighter property, not one game-wide maximum.
- **Fast-fall is a distinct per-char value, not one universal multiplier.** meleelight's fast-fall
  ratios differ per character (marth 2.2→2.5 = ×1.14; fox 2.8→3.4 = ×1.21), consistent with the
  fast-fall findings' Q2 result ("swap to a distinct `fastFallV`, not a fixed multiply").
- `[TIER-1 PENDING #988]` — retail-decomp confirmation of "no global cap" is not gathered here.

## Q3 — Brawl / PM 3.6

**Answer: per-fighter, no global cap — `[INFERENCE]` from the Brawl attribute model, `[TIER-3]` values.**

- Brawl and PM 3.6 inherit the same per-fighter attribute-table model (each fighter carries gravity,
  terminal/fall speed, and fast-fall speed); nothing in the lineage introduces an engine-wide fall
  cap. **Labelled inference** — not Tier-1-confirmed.
- **PM Mario numbers `[TIER-3]`** (via the fast-fall findings #1069, which cited SmashWiki:Mario_(PM)):
  base fall **1.7 u/f**, fast-fall **2.3 u/f**. At `PX_PER_UNIT ≈ 5.4` that is ≈ **9.2 px/f base**,
  **≈ 12.4 px/f fast-fall** — bracketing pycats' single `13`.
- **Flag:** PM-specific confirmation that no global cap exists (vs. per-fighter attributes only) is
  `[INFERENCE]`; the Tier-1 spike **#988** is where a `.rel`/DOL read would settle it.

## Q4 — meleelight

**Answer: no global `MAX_FALL_SPEED`; only per-char `terminalV` / `fastFallV`. `[SECONDARY]`**

- **No global constant.** Confirmed by search (Q2).
- **Normal fall clamp** (`src/physics/actionStateShortcuts.js`, the non-fast-fall branch):
  ```js
  if (!player[p].phys.fastfalled){
    player[p].phys.cVel.y -= player[p].charAttributes.gravity;
    if (player[p].phys.cVel.y < -player[p].charAttributes.terminalV) {
      player[p].phys.cVel.y = -player[p].charAttributes.terminalV;   // per-CHAR terminal
    }
    // down-flick → fastfalled = true; cVel.y = -charAttributes.fastFallV
  }
  ```
  Every other fall clamp across the cast (`DAMAGEN2`, `DAMAGEFLYN`, `PASS`, `WALLDAMAGE`, per-char
  specials…) also clamps to `charAttributes.terminalV`. There is no shared maximum.
- **Per-character attribute table** (gravity / terminalV / fastFallV), sampled from
  `src/characters/*/…Attributes.js`:

  | char | gravity | terminalV | fastFallV |
  |------|---------|-----------|-----------|
  | fox    | 0.23  | 2.8 | 3.4 |
  | falco  | 0.17  | 3.1 | 3.5 |
  | falcon | 0.13  | 2.9 | 3.5 |
  | marth  | 0.085 | 2.2 | 2.5 |
  | puff   | 0.064 | 1.3 | 1.6 |

  Both terminal and fast-fall are per-fighter, and `fastFallV > terminalV` for every character.

---

## What pycats actually has today (`[IN-REPO]` — the key reframe)

The ticket/`provenance.py` framing "a **single global** fall speed" is now only half-true:

- **A per-fighter terminal cap already exists and is consumed.** `FighterData.max_fall_speed`
  (`combat/data.py`, default `MAX_FALL_SPEED`, added #126) → `Fighter.max_fall_speed`
  (`entities/fighter.py`) → applied per-fighter in `entities/fighter_physics.py`:
  `apply_gravity(p.fighter.vel, p.fighter.gravity, p.fighter.max_fall_speed)`.
- **Cats already override it:** `birky.json` = 12, `gnok.json` = 12.96; `nalio` / `narz` set nothing
  and inherit the global default 13.
- So the config `MAX_FALL_SPEED = 13` is a **default**, not the live per-fighter value. pycats already
  matches the engine on "terminal is per-fighter."
- **The real gap** vs. the engine is the **base-terminal vs fast-fall split**: pycats has one
  per-fighter cap (which numerically models the *fast-fall* terminal, Q1) and **no second value and no
  fast-fall trigger**. There is no `fast_fall_speed` field and no fast-fall mechanic (confirmed by
  #1069).
- **One subtlety for the ARC child:** `apply_gravity` clamps `vel.y` to `max_fall_speed` **every
  frame, including knockback descent** (`vel.y = min(vel.y + gravity, max_fall_speed)`). Today's high
  cap (13) rarely bites; a *lowered base* cap would clip downward knockback and change trajectories —
  see the option-space breakage notes.

---

## Q5 — Recommendation / option space (for the ARC/decision child)

Framing: the engine (Q2–Q4) has **no global cap** and **two** per-fighter values (base terminal +
fast-fall). pycats has **one** per-fighter value that numerically is the fast-fall terminal. A faithful
model therefore reinterprets today's `max_fall_speed` as the **fast-fall** terminal (or as the base),
and adds the missing second value.

- **Option A — split the existing per-fighter field into base + fast-fall (recommended shape to
  evaluate).** Reinterpret `FighterData.max_fall_speed` as the **base** terminal and *lower* per-cat to
  base values (Mario-type ≈ 9); add a per-fighter `fast_fall_speed` (≈ today's 13 for Mario-type),
  reached only when the fast-fall trigger fires. Matches the engine model exactly; reuses the #126
  per-fighter plumbing. **Breaks:** goldens (every base drop changes fall arcs); `KNOCKDOWN_VY_THRESHOLD
  = 8.0` (a slower base fall means fewer ground-impact knockdowns unless fast-fall / knockback drives
  `vy ≥ 8` — the threshold may need re-basing); knockback descent (the per-frame clamp would now clip
  downward KB at ≈ 9 unless KB / fast-fall bypasses or raises the cap); existing per-cat tuning (birky
  12 / gnok 12.96 become *fast-fall* values and need an authored base counterpart).
- **Option B — remove the config global entirely; every `FighterData` must specify base + fast-fall.**
  Deletes `MAX_FALL_SPEED` from `config/physics.py`; forces `nalio`/`narz` to author explicit values.
  Most faithful to "no global concept," biggest diff, no default fallback. Same golden / threshold /
  knockback breakage as A, plus provenance-registry churn (the `MAX_FALL_SPEED` row + drift-guard go
  away or move per-fighter).
- **Option C — keep a global default cap as a pycats-only safety clamp.** Acknowledge the engine has
  none; retain a global only as an anti-runaway / determinism backstop above every fighter's fast-fall
  value (so it never bites in normal play). Least faithful, smallest diff; only justified if a concrete
  determinism / runaway-velocity need is shown — otherwise it re-introduces the very artifact this
  ticket questions.

**Cross-cutting "what breaks" for any base change** (applies to A and B):
- **Goldens** — fall trajectories shift the frame a fighter reaches terminal; expect broad golden
  regen. Quantify before committing.
- **`KNOCKDOWN_VY_THRESHOLD = 8.0`** (`config/physics.py`, `fighter.py` land-impact check) — currently
  safely below the 13 cap; a base near 9 sits just above it, and a base below 8 removes ground-fall
  knockdowns entirely (only knockback / fast-fall would trigger prone). This threshold likely needs
  re-derivation alongside the split.
- **Knockback trajectories** — `apply_gravity`'s per-frame clamp interacts with KB-set `vel.y`. The ARC
  child must decide whether fast-fall / knockback descent is exempt from the base cap (as in the engine,
  where fast-fall *raises* the effective terminal) or clamped.

**No spec is chosen here.** These are the forks for the fast-fall ARC/decision ticket to rule with the
human.

---

## Blocked / deferred source

- **Tier-1 (retail Melee decomp / DOL·.rel disassembly): not gathered — no local decomp reachable.**
  Searched the usual local roots (`~/Documents/Study/*/melee`, `~/…/doldecomp*`, `~/melee`); none
  present. This is the *same* deferral the fast-fall findings (#1069) made — Tier-1 fall-speed
  confirmation is scoped to the **#988** PM Tier-1 spike, not this ticket. Q2's "no global cap" and Q3's
  PM inheritance therefore rest on `[SECONDARY]` (meleelight) + `[TIER-3]` (SmashWiki), explicitly
  labelled. If a Tier-1 read is wanted before the ARC decision, that is a call for the human (obtain a
  decomp checkout / run under #988) — flagged here rather than quietly substituted.

## Cross-refs

Feeds the fast-fall ARC/decision child (base-vs-fast-fall re-basing fork) · fast-fall findings
`docs/research/2026-08-02-fast-fall-mechanics-findings.md` (#1069) · fast-fall epic #1068 · #120 / #384
(`MAX_FALL_SPEED` `DIVERGENCE` row in `provenance.py`; PX_PER_UNIT calibration) · #126 (per-fighter
`gravity` / `max_fall_speed` plumbing) · #785 (GAME-TUNED-px note) · #988 (PM Tier-1 spike — where a
`.rel`/DOL read would confirm Q2/Q3).
