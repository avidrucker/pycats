# CPU smash-attack policy — findings (per-level trigger / frequency / timing / charge / direction)

**Ticket:** #915 (research) · feeds the CPU-fidelity epic #925, parent CPU epic #231.
**Date:** 2026-08-04 · **Agent:** banana (opus-4.8).
**Purpose:** ground a proposed per-level CPU smash policy in primary sources, to retire the
five `#714` V1 placeholders in `AttackerController` (`pycats/sim/controllers.py`). This is a
**research** doc — it reports findings + an option space. It does **not** decide the policy;
that is a follow-on architect/decision (ARC) ticket with the human.

---

## Provenance ceiling — read this first (evidence-quality flag for the human)

**There is no Project M / Brawl CPU-AI datamine.** No OpenSA / PMDT / brawllib_rs artifact maps
CPU level 1–9 to reaction frames, smash-usage rate, charge probability, or a personality field.
The two-agent search (existing repo docs + fresh external primaries) confirms this as a **sourced
negative**.

The strongest primary that exists is the **Melee decompilation** — `doldecomp/melee`, file
`src/melee/ft/ftcpuattack.c` (the real Melee CPU attack-decision code; project self-reports ~84%
decompiled). It answers most of the five questions **concretely for Melee**. Brawl/PM evidence is
**qualitative SmashWiki prose only** (no code).

**Consequence for parity:** any pycats CPU smash model attributed to "PM 3.6" is, at best,
**inference from Melee's decompiled model + Brawl's qualitative wiki description** — *not* a PM
primary source. PM inherits Brawl's AI (weakly-sourced), and the Brawl wiki page adds only a few
smash-specific sentences on top of Melee's mechanism. Per the cite-primary parity rule
([[pm-parity-cite-primary-not-inference]]), every number below that pycats would adopt must be
labelled PRIMARY-MELEE / WIKI-QUALITATIVE / INFERENCE / NOT-FOUND. **Evidence sufficiency is the
human's call** ([[evidence-sufficiency-is-the-humans-call]]) — this doc flags the tier; it does not
rule the policy in or out.

Builds on (does not duplicate): `pm-cpu-behavior-findings.md`,
`2026-06-29-pm-cpu-difficulty-levels-1-9.md`, `2026-06-30-cpu-ai-decision-model.md`,
`2026-07-01-smash-charge-damage-formula.md`, `2026-07-07-cpu-level-scaling-per-character.md`.
The strongest of those (`pm-cpu-behavior-findings.md` §Axis 4) **explicitly punts the whole smash
slice to this ticket** — so those docs frame the questions but do not answer them.

---

## What #915 replaces — the five `#714` V1 placeholders

Current state in `AttackerController` (`pycats/sim/controllers.py`), self-labelled
`⚠ PLACEHOLDER_MECHANIC_DECISION (NOT PM-sourced)`:

| # | Dimension | V1 placeholder (in code today) |
|---|-----------|--------------------------------|
| 1 | **Trigger** | flat `SMASH_KILL_PERCENT = 100.0` — one kill-percent read, identical every level |
| 2 | **Frequency** | no smash-specific knob; rate emerges only from the shared `follow_through_p` roll |
| 3 | **Timing** | shared `reaction_delay` + `attack_period` ladder (no smash-specific commit timing) |
| 4 | **Charge** | always full charge (engine auto-fire) |
| 5 | **Direction** | forward-smash only; up/down deferred to #916 |

Level cut: `"smashes"` unlocks at **Lv5+** in `LEVEL_PARAMS` (also a placeholder cut). The infra a
sourced policy plugs into already exists: `reaction_delay` (30→1 across Lv1–9), `follow_through_p`
(0.15→1.0), `whiff_punish` (Lv5+), `reach_aware` (Lv5+), `enabled_moves`.

---

## Findings, per question

### Q1 — Trigger (why a reference CPU throws a smash)

- **PRIMARY-MELEE (the actual mechanism):** attack choice is a **geometry + prediction filter over
  a level-gated, weighted candidate list** — *not* a kill-percent or weight read. The CPU predicts
  the target's position `t` frames ahead and keeps only attacks whose reach matches:
  ```c
  if (list->x20 > cpu->level) { list++; continue; }        // min-level gate per attack
  t = list->x04;
  relx = (tgtVx * t + tgtX) - (fpVx * t + fpX);            // predicted-position lookahead
  ```
  (`ftcpuattack.c`, selection loop; the `list->x20 > cpu->level` gate recurs at three sites.)
  Inputs are position, velocity, gravity, facing, reach — **no percent / weight / blast-zone term.**
  So the reference "trigger" is **spacing/reach against a predicted position, gated by level.**
- **WIKI-QUALITATIVE (the one explicit deliberate smash trigger, Brawl-onward):** shield-break
  punish — *"finally, take the advantage to unleash a fully charged smash attack on a foe stunned
  from a broken shield."* (SmashWiki, *Flaws in artificial intelligence*).
- **NOT FOUND:** kill-percent read, weight-aware read, near-blast-zone smash logic — no source
  (wiki or decomp) documents any of these. The pycats `SMASH_KILL_PERCENT=100` trigger is
  **unsourced** — it has no primary basis and would need a game-designer `decision:`.

### Q2 — Frequency / randomness ("seldom, random, mistimed" at low level)

- **PRIMARY-MELEE (the actual error model):** low-level "seldom & random" is produced by **three
  multiplicative, level-scaled gates**, all in `ftcpuattack.c`:
  1. **Linear probability gate** — a decision fires with probability `0.05 × level`
     (`HSD_Randf() < 0.05F * temp_r31->level`), i.e. ~5% at Lv1 → ~45% at Lv9. Recurs at 5 sites.
  2. **Per-attack min-level unlock** — `if (list->x20 > cpu->level) continue;` makes stronger
     attacks (incl. smashes) **unavailable** below a per-attack level threshold. This is the
     mechanical basis for the wiki's *"low-level CPUs … use a weak attack such as a neutral attack
     or tilt, while high-level CPUs use aerial attacks, smash attacks, and grabs more prominently."*
     (SmashWiki, *Artificial intelligence*).
  3. **Level-scaled periodic window** — a behavior is only allowed during part of a 240/300-frame
     cycle (`ftCo_800B885C`): Lv1 allowed 60/300 frames, Lv5 allowed 60/240 frames, etc.
- **WIKI-QUALITATIVE (cross-game summary):** *"the level of an AI opponent determines how likely
  they are to follow through with a decision, as well as how fast they react, which results in the
  illusion of more skill."* (SmashWiki, *Artificial intelligence*). The decomp is the concrete
  realization of "how likely they follow through" — and it validates the pycats approach of an
  emergent low-level rate via a probability gate rather than injected error (consistent with the
  `[PYCATS-ORIGINAL]` no-injected-near-miss stance in `2026-07-07-cpu-level-scaling-per-character.md`).

### Q3 — Timing (per-level reaction delay)

- **PRIMARY-MELEE (exact per-level table):** `ftCo_800B63D8`, commented *"Tells the fighter to
  wait for a random amount of time, based on the CPU level. Lower CPU levels wait for longer.
  Level 9 doesn't wait at all."* Verified verbatim in the decomp (`rand = HSD_Randf() ∈ [0,1)`):

  | In-game level | Wait command | Frames |
  |---|---|---|
  | Lv1 | `(int)(40*rand)+5` | 5–44 |
  | Lv2 | `(int)(35*rand)+5` | 5–39 |
  | Lv3 | `(int)(30*rand)+5` | 5–34 |
  | Lv4 | `(int)(25*rand)+5` | 5–29 |
  | Lv5 | `(int)(25*rand)` | 0–24 |
  | Lv6 | `(int)(20*rand)` | 0–19 |
  | Lv7 | `(int)(15*rand)` | 0–14 |
  | Lv8 | `(int)(10*rand)` | 0–9 |
  | Lv9 | `(int)(5*rand)` | 0–4 |

  A second inverse-level timer (`ftCo_800B9704`): `cpu->x34 = (10 - cpu->level) * (rand*15 + 15) + 10`
  — again shrinking as level rises. **This is a directly adoptable per-level reaction ladder** and
  the pycats `reaction_delay` (30→1) is a plausible re-anchor onto it.
- **WIKI-QUALITATIVE (Brawl, defensive):** *"CPUs had a reaction time of one frame, and thus, did
  not read button inputs."* (SmashWiki) — a *defensive* one-frame reaction claim, not a datamined
  per-level table; consistent with pycats' Lv9 `reaction_delay=1`.
- **Smash-specific commit timing** (how long after an opening a smash specifically starts) is
  **NOT decoded separately** — Melee routes all attacks through the same reaction wait.

### Q4 — Charge (do reference CPUs charge smashes?)

- **PRIMARY-MELEE (NO):** *"They additionally never charge smash attacks (the Ice Climbers'
  forward smash being the sole exception)."* (SmashWiki, *Flaws…*). **Corroborated by the decomp:**
  the only `charge` variable in `ftcpuattack.c` is `fp->u.gw.x2238_panicCharge` — a
  character-specific *special-move* hold (G&W/DK/Samus neutral-B), **not** smash charging. There is
  no smash-charge-duration code path.
- **WIKI-QUALITATIVE (Brawl+, YES but duration undocumented):** *"CPUs can now properly charge up
  or hold smash attacks and special attacks"* (SmashWiki, *Flaws…*). Only the shield-break case is
  specified as *"fully charged."* **How charge duration is chosen in general is NOT documented**
  (sourced negative).
- **Reconcile with the charge *mechanic* doc:** `2026-07-01-smash-charge-damage-formula.md` sources
  the window (60 frames = 1 s) and full-charge multiplier (1.4×, damage-only) — that tells a policy
  *what a charge does*, not *when a CPU chooses to charge*. The pycats V1 "always full charge" is
  **contradicted by Melee** (which never charges) and only **weakly supported by Brawl** (can charge;
  full-charge attested solely for shield-break). This is the single largest divergence to rule on.

### Q5 — Direction (fsmash vs usmash vs dsmash)

- **PRIMARY-MELEE (mechanism):** direction/among-move choice is a **weighted-random roll over the
  geometry-eligible, level-gated candidates** — the CPU sums candidate weights and rolls one:
  ```c
  r = HSD_Randf();
  for (i=0;i<count;i++) sum += sp3C[i].weight;   // struct field: +18 weight
  ...                                            // normalize, roll r into a weight bucket
  ```
  Which candidate is up/forward/down-smash depends on **which entries' reach reaches the predicted
  target** (reach fields), then the weighted roll. So direction is effectively "whichever smash's
  hitbox reaches the predicted position, tie-broken by weighted RNG" — **not** an angle/DI-aware
  directional read.
- **WIKI-QUALITATIVE (the one positional cue):** *"CPUs that launch an opponent upwards will just
  stay on the ground waiting for them to come down, spamming up tilts and up smashes."* (SmashWiki,
  *Flaws…*) → target-above ⇒ up-smash.
- **PARTIAL / NOT DECODED:** the exact opcode→move mapping (which weight is fsmash vs usmash vs
  dsmash) is **not decoded** (raw hex targets in the decomp). Mechanism is confident; per-direction
  weights are not.
- **Scope note:** direction *implementation* (usmash/dsmash) is **#916's** territory, not this
  policy proposal's — but the finding above is what #916 should build on.

---

## Option space (findings, not a decision — for the ARC/decision ticket)

Each dimension, with the sourced options and their evidence tier. The human/architect picks; where
no primary exists, the choice is a game-designer `decision:` ([[give-opinion-gate-is-on-commit]]).

**Q1 Trigger**
- **A. Spacing/predicted-reach, level-gated** — PRIMARY-MELEE; matches the real mechanism; reuses the
  existing `reach_aware`/`whiff_punish` infra. No kill-percent.
- **B. Keep a kill-percent read** (retain `SMASH_KILL_PERCENT`, perhaps per-level) — **unsourced**;
  a pycats game-feel choice; would need a `decision:` ruling. Simpler than A.
- **C. Add shield-break punish as an explicit full-charge smash trigger** — WIKI-QUALITATIVE
  (Brawl); orthogonal to A/B; low priority if pycats lacks shield-break state.

**Q2 Frequency**
- **A. Probability gate `p ≈ 0.05 × level` per smash decision** — PRIMARY-MELEE; drop-in as a
  smash-specific roll layered on the existing `follow_through_p`.
- **B. Keep emergent-only** (no smash-specific knob; rely on `follow_through_p`) — status quo;
  cheapest; less faithful to the per-decision Melee gate.
- **C. Per-attack min-level unlock** (smash gated at a chosen level; today Lv5) — PRIMARY-MELEE
  mechanism; the *threshold* itself is unsourced (Lv5 in code vs Lv7 in an older table) → `decision:`.

**Q3 Timing**
- **A. Re-anchor `reaction_delay` onto the Melee wait table** (Lv1 5–44f … Lv9 0–4f) — PRIMARY-MELEE;
  the current 30→1 ladder is close in shape but not sourced; adopting the table makes it sourced.
- **B. Keep the current ladder** — status quo; unsourced but already tuned.

**Q4 Charge**
- **A. Never charge (fixed no-charge), Melee-faithful** — PRIMARY-MELEE; contradicts current
  always-full-charge; weakest KO power.
- **B. Always full-charge (status quo)** — Melee-contradicted, Brawl-weak; strongest KO; simplest.
- **C. Situational charge** (e.g. full only on a shield-break-like opening) — WIKI-QUALITATIVE
  (Brawl); most faithful to "can charge" but duration rule is a `decision:` (undocumented).

**Q5 Direction** *(research feeds #916; not this policy's to implement)*
- **A. Positional: target-above ⇒ up-smash, else forward** — WIKI-QUALITATIVE; simplest faithful rule.
- **B. Weighted-RNG over reach-eligible smashes** — PRIMARY-MELEE mechanism; needs the per-direction
  weights, which are NOT decoded → would be pycats-chosen.
- **C. Keep fsmash-only (status quo)** — pycats V1; defer up/down to #916.

---

## Gap list — what #915 could **not** source (for the human to weigh)

1. **No PM/Brawl AI datamine** — the entire policy, if attributed to "PM 3.6", is inference from the
   Melee decomp + Brawl wiki. Flag on every adopted number.
2. **Kill-percent / weight / blast-zone trigger** — NOT FOUND in any source. The pycats
   `SMASH_KILL_PERCENT` has no primary basis.
3. **Charge-duration policy** — undocumented even in Brawl (only shield-break = "fully charged").
4. **Per-direction smash weights** — the Melee selection *mechanism* is decoded; the fsmash/usmash/
   dsmash weight mapping is not (raw hex opcodes).
5. **Smash-specific commit timing** — Melee routes all attacks through one reaction wait; no
   smash-only startup delay is separable.

## Suggested next step (one, filed one-at-a-time downstream)

An **ARC/decision ticket** to rule the Q1–Q5 options above into a pycats policy with the human
([[research-never-produces-spec]]) — most decisions are `decision:` where no primary pins the number
(trigger model, charge behavior, level thresholds). The DEV implementation follows the ruling; #916
consumes the Q5 direction finding.

---

## Provenance

| Value / claim | Status | Source |
|---|---|---|
| Attack choice = geometry+prediction filter over level-gated weighted list | FOUND (Melee) | `doldecomp/melee` `ftcpuattack.c` selection loop (`list->x20 > cpu->level`; `relx = …`) |
| Low-level rate = `0.05 × level` probability gate | FOUND (Melee) | `ftcpuattack.c` `HSD_Randf() < 0.05F * level` (5 sites) |
| Per-attack min-level unlock | FOUND (Melee) | `ftcpuattack.c` `list->x20 > cpu->level` (3 sites) |
| Per-level reaction wait table (Lv1 5–44f … Lv9 0–4f) | FOUND (Melee) | `ftcpuattack.c` `ftCo_800B63D8` (verbatim, verified) |
| Melee CPUs never charge smashes (ICs fsmash excepted) | FOUND (wiki) + corroborated (decomp) | SmashWiki *Flaws…*; `ftcpuattack.c` only charge var = `x2238_panicCharge` (G&W special) |
| Brawl+ CPUs can charge/hold smashes; shield-break = fully charged | FOUND (wiki, qualitative) | SmashWiki *Flaws…* |
| Direction = weighted-RNG over reach-eligible candidates | FOUND (Melee, mechanism) | `ftcpuattack.c` weighted `HSD_Randf()` over `.weight` (struct +18) |
| Target-above ⇒ up-tilt/up-smash | FOUND (wiki) | SmashWiki *Flaws…* |
| Kill-percent / weight / blast-zone smash trigger | NOT FOUND | (sourced negative — no wiki or decomp) |
| PM-specific per-level smash knob table | NOT FOUND | (sourced negative — no OpenSA/PMDT/brawllib_rs artifact) |
| Charge-duration selection rule | NOT FOUND | (sourced negative — undocumented in Brawl) |
| Per-direction (fsmash/usmash/dsmash) weights | NOT DECODED | `ftcpuattack.c` raw hex opcode targets |

**Sources:** `doldecomp/melee` → `src/melee/ft/ftcpuattack.c` (session copy verified;
functions `ftCo_800B63D8` reaction wait, `ftCo_800B9704` timer, `ftCo_800B885C` level-periodic
gate, attack-list selection loop). SmashWiki: *Artificial intelligence*,
*Flaws in artificial intelligence*, *List of CPU modes*.
