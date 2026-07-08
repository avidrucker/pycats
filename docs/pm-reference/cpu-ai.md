# CPU / computer-player AI

> How a **Project M / Brawl** computer player *thinks* and how its skill scales from
> level 1 to 9 — plus a candid map of which of **pycats'** per-level behaviors are
> **parity** (traceable to the games) and which are **pycats-custom** (designed here).
> Folds in the CPU research docs rather than duplicating them (#148 / #251 / #48 / #285
> / #343 / #702) and the ratified design decision #704.

## Intro — scope & provenance (read first)

**There is no PM-specific CPU-AI source.** Project M is a Brawl mod and inherits Brawl's
CPU brain unchanged; no PM changelog, datamine, or dev note documents a PM-specific AI.
So **this reference documents *Brawl* CPU AI** and treats it as PM's (consistent with
[`2026-06-29-pm-cpu-difficulty-levels-1-9.md`](../research/2026-06-29-pm-cpu-difficulty-levels-1-9.md)
§TL;DR and [`2026-06-25-npc-behaviors-and-dual-controller.md`](../research/2026-06-25-npc-behaviors-and-dual-controller.md)).
PM's relevant divergences from Brawl are **mechanical** (Melee-style movement, air-dodge,
no tripping — see `movement-and-tech.md`), **not a different AI brain**.

**Confidence is provenance-limited.** The sources are **secondary-tier** — community
datamining (SmashWiki) and one frame-analysis (Toomai, 2013). Endpoints (Lv1 behavior,
Lv9 = 1-frame reaction) are explicit; the per-level curve between them is **inferred**.
Treat every number as a starting point, not a datamined constant.

> **Important:** pycats' controllers are **RNG-free / position-driven** by design (goldens
> stay byte-identical); authentic Smash CPU AI is **stochastic and reaction-driven**. pycats
> borrows the *taxonomy and tendencies*, not the mechanism (#48). Since the seeded-RNG seam
> (#166) landed, the genuinely-probabilistic knobs are expressible **golden-safe** under a
> fixed default seed.

## How a Brawl/PM CPU decides

The difficulty of a Brawl CPU is a **single 0–100 scalar** (Lv1 = 0 … Lv9 = 100) that tunes
**two continuous knobs** plus **a few discrete capability unlocks**
([SmashWiki — Difficulty](https://www.ssbwiki.com/Difficulty); [SmashWiki — Artificial
intelligence](https://www.ssbwiki.com/Artificial_intelligence), via #148):

1. **Reaction speed** (continuous) — how many frames the CPU waits before acting on a
   state change. Lv1 "waits a long time before eventually" acting; **Lv9 = 1-frame**
   reaction (Toomai, 2013 — CPUs do *not* read inputs; they react frame-fast).
2. **Follow-through probability** (continuous, stochastic) — the chance the CPU *commits*
   a chosen action. Lv1 "almost never" commits; Lv9 "almost always … instantly."
3. **Discrete capability unlocks** layered on top — move-kit richness (jabs/tilts →
   aerials → smashes/grabs), shield propensity, and **recovery variety** (single up-B →
   alternating techniques) which flips at **~Lv6** (the one *explicitly-sourced* discrete
   threshold).

Both a Lv1 and a Lv9 CPU *decide to do the same things*; the level governs **how fast** and
**how reliably** the decision fires. A key refinement on shielding (#251): **high-level CPUs
shield *reactively*** (only on a detected incoming threat — "almost always defend from
attacks"), while **low-level CPUs shield at *random* times**.

### The level-independent flaws (all levels)

Brawl/PM CPUs, *even at Lv9*, share documented weaknesses (SmashWiki, via #148): they
**can't be mind-gamed**, **don't learn or adapt**, **won't bait**, and **edge-guard poorly**
(it improves with level but never becomes good). These are design-faithful "seams" a human
can exploit — not bugs.

## Per-level behavior — "plays poorly" (low) → "plays expertly" (high)

Adapted from #148 §Q1–Q3. Confidence: **explicit** = stated by a source; **inferred** =
reasoned from the mechanism; **gap** = undocumented.

| Axis | Low (Lv1–3) | Mid (Lv5) | High (Lv7–9) | Confidence |
|---|---|---|---|---|
| 0–100 scalar | Lv1=0, Lv3=21 | Lv5=42 | Lv7=60, Lv9=100 | explicit |
| Reaction time | slow; "waits a long time" | moderate | Lv9 ≈ **1 frame** (Toomai) | ends explicit, curve gap |
| Follow-through | "almost never" commits | sometimes | "almost always… instantly" | explicit |
| Move kit | stand + weak jabs/tilts | begins aerials | aerials, **smashes, grabs** | low/high explicit |
| Shield usage | "almost never," random | occasional | reactive; Lv9 perfect-shields | explicit |
| Recovery | single up-B, predictable | single | **alternates** techniques (~Lv6) | explicit threshold |
| Edge-guarding | weak/ineffective | weak | still a **known weakness** | explicit flaw |
| Button-mash | very slow | — | Lv9 frame-perfect | explicit |
| Mind-games / adapt | none (can't be baited, doesn't learn) | none | none | explicit |

## Parity vs pycats-custom — the classification

Every per-level behavior pycats implements (`pycats/sim/controllers.py :: LevelParams` /
`level_params`), tagged by provenance. **SOURCED = parity** (traceable to Brawl/PM or the
findings doc that sourced it). **RESEARCH-INFORMED = pycats tactical** (a pycats-original
controller policy, derived from a findings doc but *not* a documented Brawl CPU behavior).
**CUSTOM-#704 = Avi-approved** (a pycats-original human-error/flavor system with **no** Smash
source — a design decision, recorded `TUNED`, not sourced-when-guessed).

### Parity — sourced (the difficulty ladder proper)

| pycats behavior | Knob | Source |
|---|---|---|
| Reaction ramp (slow → 1-frame) | `reaction_delay` 30→1 | **SOURCED** — SmashWiki AI + Toomai (#148) |
| Commit reliability | `follow_through_p` 0.15→1.0 | **SOURCED** — follow-through mechanism (#148) |
| Attack cadence / aggression | `attack_period` 48→10 | inferred from the scalar (#148) |
| Shield propensity | `shield_chance` 0.0→0.85 | **SOURCED** — low/high explicit (#148) |
| Reactive vs random shielding | `reactive_shield` (Lv5+) | **SOURCED** — #251 (high reactive, low random) |
| Move-kit gating | `enabled_moves` jab→+tilts→+aerials→+specials | **SOURCED** ramp, thresholds inferred (#148) |
| Deliberately-imperfect edge-guard | `edge_guard` on-stage only, never good | **SOURCED** — documented weakness (#148/#251) |
| Recovery to the ledge (variety ~Lv6) | `recover` (Lv5+) | **SOURCED** threshold (#148) |

### pycats tactical — research-informed, pycats-original policy

These make higher levels "play expertly" but are **not** documented Brawl CPU behaviors —
they are pycats controller policies from the AI-improvement epics (#250 / #312), each backed
by a findings doc. Faithful *in spirit*, original *in mechanism*.

| pycats behavior | Knob | Basis |
|---|---|---|
| Whiff-punish (hit during opponent's move recovery) | `whiff_punish` (Lv5+) | #274 (RESEARCH-INFORMED) |
| Reach-awareness (range from the committed move) | `reach_aware` (Lv5+) | #285 / #335 |
| Press-the-advantage spacing (no footsies) | `reactive_spacing` (Lv5+) | #277 / #343 |
| Reactive roll-away evade | `evade_chance` (Lv7+) | #338 |
| Edge-hog / ledge denial | `edge_hog` (Lv7+) | #404 / #312 |
| Anti-stall backstop | (Lv-gated) | #368 (guards the #292 non-resolving match) |

### pycats-custom — Avi-approved (#704), no Smash source

The three ratified human-error / flavor systems (design decision #704) — recorded `TUNED`,
values are playtest starting points, implemented one DEV ticket at a time (#702 follow-ups):

| pycats behavior | Model | Direction | Provenance |
|---|---|---|---|
| **Per-character mechanic tuning** | `special_usage_level` + `spacing_accuracy` per fighter (Nalio fireball zoning, Birky multi-jump recovery, Narz tipper spacing) | uses each kit *better* as level rises | **CUSTOM-#704** — Smash gives only a shared scalar, never per-character CPU tuning |
| **Near-miss** | `near_miss_p` / `near_miss_px` | deliberately mis-spaced attacks, **peaked low-mid**, → 0 by Lv9 | **CUSTOM-#704** — Smash uses hesitation, not injected whiffs |
| **Accidental-press** | `misinput_p` + guardrails | spurious/dropped inputs, **highest at Lv1**, → 0 at Lv9; **never** off-stage / self-KO | **CUSTOM-#704** — Smash Lv9 is error-free by design |

**Why "custom, not parity":** authentic Brawl CPUs make low levels look weak through
**hesitation + slow reaction** (low `follow_through_p`, long `reaction_delay`) — they do
**not** inject mistakes, and Lv9 is *frame-perfect / error-free*. The #704 systems are a
pycats design choice to make low-mid levels read as *human learning* more legibly than pure
hesitation does; they are labelled game-feel, not reproductions.

## Sources

- **Primary (secondary-tier, via #148):** [SmashWiki — Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence)
  (follow-through + reaction mechanism, shield/recovery/edge-guard by level, the flaws);
  [SmashWiki — Difficulty](https://www.ssbwiki.com/Difficulty) (the 0–100 scalar mapping);
  Toomai (2013), via SmashWiki (Lv9 = 1-frame reaction; CPUs don't read inputs).
- **Repo findings folded in here:**
  [`2026-06-29-pm-cpu-difficulty-levels-1-9.md`](../research/2026-06-29-pm-cpu-difficulty-levels-1-9.md) (#148),
  [`2026-06-30-cpu-ai-decision-model.md`](../research/2026-06-30-cpu-ai-decision-model.md) (#251),
  [`2026-06-25-npc-behaviors-and-dual-controller.md`](../research/2026-06-25-npc-behaviors-and-dual-controller.md) (#48),
  [`2026-06-30-ai-controller-reach-awareness.md`](../research/2026-06-30-ai-controller-reach-awareness.md) (#285),
  [`2026-06-30-npc-spacing-footsies-models.md`](../research/2026-06-30-npc-spacing-footsies-models.md) (#343),
  [`2026-07-07-cpu-level-scaling-per-character.md`](../research/2026-07-07-cpu-level-scaling-per-character.md) (#702).
- **Design decision:** [#704](https://github.com/avidrucker/pycats/issues/704) (near-miss +
  accidental-press + per-character tuning approved as pycats-custom); ledger #705.

## pycats status

- **Implemented:** the difficulty ladder — `pycats/sim/controllers.py :: LevelParams` /
  `LEVEL_PARAMS` / `level_params` — with per-level interpolation across 1–9 (#703). The
  parity + research-informed rows above are live; wired via `watch.py` (`--p1-level` /
  `--p2-level`). No in-game CPU picker yet ([#691](https://github.com/avidrucker/pycats/issues/691)).
- **Approved, not yet built:** the CUSTOM-#704 rows — DEV tickets are #702 follow-ups
  3–6, filed one at a time (`special_usage_level` → `spacing_accuracy` → near-miss →
  accidental-press).
- **Divergences:** the whole ladder is a pycats construction over a Brawl-derived, provenance-
  limited model — not PM-pinned. Recorded `TUNED` in `provenance.py` as each value lands.
- **Open questions:** [#24](https://github.com/avidrucker/pycats/issues/24); sim duration/
  termination that bounds a CPU match — [#708](https://github.com/avidrucker/pycats/issues/708).
