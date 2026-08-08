# Project M CPU difficulty levels 1–9 → deterministic pycats mapping (#148)

> Research findings (#148, child of umbrella #24). Scopes the *specific* behavioral
> differences between PM/Brawl CPU levels 1–9 and proposes a concrete deterministic
> parameter table for the five target levels **1, 3, 5, 7, 9** that a follow-up DEV
> can set on the existing controller protocol. **Findings only — no controller code.**
>
> Builds on #48 (`docs/research/2026-06-25-npc-behaviors-and-dual-controller.md`);
> coordinates with #144 (`docs/research-findings-144-pm-randomness-survey-dragonfruit-2026-06-26.md`)
> and #141 (mirror-match). Code grounded against `pycats/sim/controllers.py` at HEAD.
> Sources: SmashWiki *Artificial intelligence* + *Difficulty*; Toomai (2013).
> Date: 2026-06-29. Agent: DRAGONFRUIT. Area: `area:combat`.
> (The ticket suggested the filename `…2026-06-26…`; dated to actual authoring per repo convention.)

## TL;DR

PM is **Brawl-derived** for CPU AI — no PM-specific authoritative source exists
(consistent with #48). Brawl CPU difficulty is a **single 0–100 scalar** that tunes
**two continuous knobs** — *reaction speed* and *follow-through probability* — with a
**few discrete capability unlocks** layered on top (move-kit richness, recovery
variety at ~Lv6, shield propensity). Both a Lv1 and a Lv9 CPU *decide* to do the same
things; the level governs **how fast** and **how reliably** the decision fires.

**The key change since #48:** the **seeded-RNG seam (#166) has landed.** Controllers
now carry `self.rng` (a fixed-seed `random.Random` by default → byte-identical
goldens/parity; live callers inject a clocktime/`--seed` Random). So PM's *stochastic*
difficulty knobs — follow-through probability, "shields at random times" — are now
expressible **faithfully and golden-safe**, which #48 had to forgo. The mapping below
is therefore a **hybrid**: deterministic knobs for reaction delay / cadence / spacing /
capability gating, and **seeded-RNG rolls** for the inherently-probabilistic knobs.

A graded 1→9 ladder **is** achievable on the existing protocol — #48's deferral
("demo opponents, not a difficulty ladder") was a function of the then-missing RNG
seam, which now exists.

## Q1–Q3 — Per-level behavior table (Brawl/PM)

Confidence: **explicit** = stated on SmashWiki; **inferred** = reasoned from the
explicit mechanism; **gap** = unstated by any source found.

| Axis | Low (Lv1–3) | Mid (Lv5) | High (Lv7–9) | Confidence |
|---|---|---|---|---|
| **0–100 scalar** | Lv1=0, Lv3=21 | Lv5=42 | Lv7=60, Lv9=100 | **explicit** |
| **Reaction time** | slow; "waits a long time before eventually" acting | moderate | Lv9 = **1-frame** reactions (Toomai 2013); near-frame-perfect | **explicit** (ends), **gap** (Lv2–8 numbers) |
| **Follow-through** | "almost never" commits a chosen action | sometimes | Lv9 "almost always… instantly" | **explicit** |
| **Move kit** | "stand next to opponent, weak attack" (jabs/tilts) | begins aerials | aerials, **smashes, grabs** "more prominently" | **explicit** (low/high), **gap** (exact per-level unlocks) |
| **Shield usage** | "almost never," repositions with rolls | occasional | "almost always defend from attacks"; Lv9 perfect-shields | **explicit** |
| **Recovery** | "simple, predictable pattern," single up-special (e.g. Luigi Lv1–5 = Super Jump Punch only) | single | **alternates** techniques (Luigi **Lv6–9** = +Green Missile +Cyclone) | **explicit** — a **discrete threshold at ~Lv6** |
| **Edge-guarding** | weak / ineffective | weak | still a **known weakness** even high (improves but never good) | **explicit** (a documented flaw) |
| **DI / teching** | — | — | — | **gap** (not discussed per level) |
| **Button-mash speed** | very slow | — | Lv9 very fast (frame-perfect) | **explicit** |
| **General flaws** | can't be mind-gamed · doesn't learn · won't bait/adapt · poor edge-guard | (same — flaws are level-independent) | (same) | **explicit** |

**Q2 verdict (interpolation vs unlocks):** *both.* The **dominant** mechanism is a
**continuous curve** on two knobs (reaction frames ↓, follow-through probability ↑ as
the scalar rises) — Lv1 and Lv9 share the same decision space. **Layered on top** are a
**few discrete capability unlocks**: recovery-variety flips at **~Lv6** (the clearest
threshold), and move-kit richness (aerials → smashes/grabs) and shield propensity ramp
in steps rather than perfectly smoothly. So: model a smooth scalar **plus** a small set
of level-gated capabilities.

**Q3 verdict (PM-specific?):** **No authoritative PM-specific CPU source found** —
PM is a Brawl mod and is **Brawl-derived** here (matches #48 and the
`brawl-projectm-fighter-states.md` caveat that no PM-specific state/AI doc exists). PM's
*relevant* divergences are mechanical (Melee-style movement/air-dodge, no tripping —
see #144), not a different AI brain. Treat all level behavior as Brawl-sourced;
confidence on PM exactness is **low by provenance**, not by contradiction.

## Q4 — Stochastic PM knobs → deterministic/seeded pycats equivalents

Each PM difficulty effect, with its pycats expression. "**det**" = pure
cadence/threshold (position + integer-frame only, RNG-free). "**rng**" = a
`self.rng` roll at the controller edge (#166), still reproducible under the fixed
default seed.

| PM effect | Nature | pycats knob | Mech |
|---|---|---|---|
| Reaction speed | latency | `reaction_delay` frames before acting on a state change | **det** (frame buffer) |
| Follow-through probability | stochastic | `follow_through_p` — roll `self.rng.random() < p` per decision window | **rng** (#166) |
| Attack frequency / aggression | cadence | `attack_period` (already on `AttackerController`) | **det** |
| "Shields at random times" / shield propensity | stochastic | `shield_chance` — roll per frame (the **existing** `IdlerController.shield_chance`, #166's first consumer) | **rng** (#166) |
| Commit distance / spacing | spatial | `standoff` / `attack_range` (already present) | **det** |
| Move-kit richness | capability | `enabled_moves` set gated by level | **det** (gate) |
| Recovery variety | capability | `recovery_variety` flag (single vs alternating) gated at ~Lv6 | **det** (gate) |
| Edge-guard attempts | capability+stochastic | `edgeguard` enabled Lv7+, kept imperfect via a low `follow_through_p` | **det gate + rng** |

This directly answers #48's open tension: with #166 in place we **no longer must**
collapse the reaction knob to zero or drop probability — the *felt* difficulty
(hesitation, inconsistent shielding) is now reproducible. Goldens stay byte-identical
because the default seed is fixed; only live/`--seed` matches vary. Coordinate with
#144's "what this means for pycats" (this is exactly a sanctioned seeded surface).

## Q5 — Deterministic parameter table for Lv 1 / 3 / 5 / 7 / 9

The knob values a future difficulty-parameterized controller sets per level. **The
*axes* are sourced (Q1); the *numbers* are pycats interpolations — `⚠ tuning starting
points`, low confidence, to be playtested.** `reaction_delay`/`attack_period`/`standoff`
in frames/px; `follow_through_p`/`shield_chance` ∈ [0,1] fed to `self.rng`.

| Knob | **Lv1** | **Lv3** | **Lv5** | **Lv7** | **Lv9** | Mech | Source |
|---|---|---|---|---|---|---|---|
| scalar (0–100) | 0 | 21 | 42 | 60 | 100 | — | **explicit** |
| `reaction_delay` (f) | 30 | 20 | 12 | 6 | 1 | det | ends explicit (Lv9=1), curve inferred |
| `follow_through_p` | 0.15 | 0.35 | 0.55 | 0.80 | 1.00 | rng | mechanism explicit, values inferred |
| `attack_period` (f) | 48 | 36 | 24 | 16 | 10 | det | inferred |
| `shield_chance` | 0.00 | 0.05 | 0.15 | 0.40 | 0.85 | rng | low/high explicit, values inferred |
| `enabled_moves` | jab | +tilts | +aerials | +smash, grab | full +specials | det gate | explicit ramp, thresholds inferred |
| `recovery_variety` | single | single | single | alternating | alternating | det gate | **threshold ~Lv6 explicit** |
| `edgeguard` | off | off | off | basic† | basic† | det+rng | high-level weakness explicit |
| `standoff` (px) | 45 | 40 | 35 | 32 | 30 | det | inferred |

† "basic" edge-guard stays deliberately imperfect (PM/Brawl CPUs never edge-guard
well) — model it as enabled but with a low follow-through so it whiffs often.

Notes: `attack_period`/`standoff` already exist on `AttackerController`;
`shield_chance` already exists on `IdlerController` (#166). `reaction_delay`,
`follow_through_p`, `enabled_moves`, `recovery_variety`, `edgeguard` are **new** knobs
the DEV tickets add. A single `level → params` table (a dict or small dataclass) keyed
1–9 with the 5 target rows filled first; intermediate levels interpolate or reuse the
nearest filled row.

## Recommended DEV decomposition (file one at a time, per RULES)

Lazy decomposition — file the next only when starting it:

1. **DEV: difficulty-parameterized controller scaffold** — a `level`→knob-table seam
   on (or wrapping) `AttackerController`, wiring the **deterministic** core first:
   `reaction_delay`, `attack_period`, `standoff`. Golden-safe by construction (no rng
   path yet). Lands the Lv1/3/5/7/9 table as data. *(first; independent)*
2. **DEV: seeded follow-through + shield propensity** — consume #166's `self.rng` for
   `follow_through_p` and per-level `shield_chance`. A parity test pins identical
   output under the fixed default seed; a seed change visibly alters timing (mirrors
   #166's `IdlerController` test). *(independent of 1's merge; both touch only
   `controllers.py`)*
3. **DEV: per-level move-kit gating** (`enabled_moves`) — **gated on the moveset seam
   #142/#143** (needs a real selectable kit to gate). Until then Lv-difference is
   cadence/reaction/shield only.
4. **DEV: recovery-variety + basic edge-guard** — gated on recovery specials (#142
   specials slice) and ledge work (#14). Lowest priority; biggest dependency.
5. *(optional)* **DEV: `watch.py --cpu-level N`** + a Lv1/3/5/7/9 demo battle, so the
   ladder is visible/benchmarkable.

Sequence: **1 → 2** now (both `controllers.py`-only, no external deps); **3** after
#142; **4** after recovery+ledge. Relates to the cat-archetype epic #117 (difficulty ×
archetype is a later cross-product).

## Caveats & gaps

- **All numeric per-level values in Q5 are pycats inventions** (interpolations of the
  sourced *axes*) — explicitly tuning starting points, not measured PM data.
- **No source gives per-level reaction frames** for Lv2–8 (only Lv9≈1-frame is
  measured). The `reaction_delay` curve is a smooth guess between the endpoints.
- **No PM-specific CPU source exists** — provenance-limited to Brawl (secondary-tier
  SmashWiki + Toomai's GIF analysis), consistent with #48/#24.
- **DI/teching per level is undocumented** — left as a `gap`; do not invent a ladder
  for it without a source.
- Exact move-kit unlock thresholds (which level first uses aerials vs smashes) are
  inferred; the table places them sensibly but they want playtest validation.

## Sources

| Source | Quality | Gives |
|---|---|---|
| [SmashWiki — Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence) | secondary (authoritative community) | follow-through-probability + reaction mechanism, shield/recovery/edge-guard by level, flaws |
| [SmashWiki — Difficulty](https://www.ssbwiki.com/Difficulty) | secondary | 0–100 scalar mapping (Lv1=0…Lv9=100) |
| Toomai (2013), via SmashWiki | secondary | Lv9 = 1-frame reaction (CPUs don't read inputs) |
| #48 doc `2026-06-25-npc-behaviors-and-dual-controller.md` | primary (repo) | archetype taxonomy, scalar anchors, controller protocol |
| #144 doc `research-findings-144-pm-randomness-survey…` | primary (repo) | which PM surfaces are sanctioned for a seeded seam |
| `pycats/sim/controllers.py` (#166 seam) | primary (repo) | `self.rng`, `AttackerController`/`IdlerController` knobs |
