# PM/Melee/Brawl CPU behavior — general reference model (#928)

**Role:** RESEARCH. **Child of #925** (CPU-behavior-fidelity epic). `area:combat` / `combat:cpu`.
**Agent:** banana. **Date:** 2026-07-31.

> **What this doc is.** The *reference-model* half of #925: a self-contained picture of how a
> Project M / Melee / Brawl CPU behaves across six axes — movement/approach, spacing/neutral,
> defense, attack selection, level scaling, and known weaknesses — so the architect (#925 child 3)
> has one target to design the pycats CPU fixes against. It is investigation only; **no controller
> code**. The **smash-usage** slice of attack-selection is **#915** — referenced, not duplicated.
> It bridges explicitly to **#927** (the pycats jitter-jump root cause), whose fix this model informs.

> **Provenance discipline (grounded-claim / cite-primary rule).** Every behavior is tagged
> **[PRIMARY]** (a verbatim SmashWiki sentence, re-fetched first-hand for this doc — not read from a
> repo proxy), **[INFERENCE]** (reasoned from a primary mechanism), or **[GAP]** (no source found).
> All quotes below were pulled directly from the three SmashWiki pages in §Sources on 2026-07-31.

> **Provenance ceiling (unchanged from #48/#148/#251).** *No PM-specific CPU-AI source exists.* PM
> is a Brawl mod and is **Brawl-derived** for AI; its relevant divergences are *mechanical* (Melee-
> style movement, air-dodge, no tripping — see #144), not a different AI brain. Treat every behavior
> here as **Brawl-sourced secondary** (SmashWiki + Toomai 2013); confidence on PM-exactness is *low
> by provenance*, not by contradiction. Numeric pycats knob values elsewhere in the repo are
> `⚠ tuning starting points`, never PM-pinned.

---

## TL;DR — the reference model in one paragraph

A Smash CPU is a **reactive if-then rule set evaluated every frame against the visible on-screen
state** — not a planner, not a learner, not an input-reader. [PRIMARY] *"they all invariably rely
on some form of 'if-then' script."* The **difficulty level tunes two continuous knobs — reaction
latency and follow-through probability — plus a few discrete capability unlocks**; a Lv1 and a Lv9
CPU run the *same* rules, but Lv1 reacts slowly and rarely commits while Lv9 reacts in ~1 frame and
almost always commits. [PRIMARY] *"the level of an AI opponent determines how likely they are to
follow through with a decision, as well as how fast they react."* Its behavior is **committal,
proximity-driven, and predictable** — it approaches by walking/dashing into range and attacking by
distance-band, defends reactively only at high level, and carries a set of **canonical, level-
independent weaknesses** (poor edge-guarding, never edgehogs, over-eager air-dodge, jumpy neutral
against projectiles). The naturalness gap pycats sees is **not** that its `decide()` is the wrong
shape — it is exactly this if-then shape already — but that a few of its rules produce *visibly
mechanical* output (the #927 jitter is the clearest case) that even a real Brawl CPU avoids.

---

## Axis 1 — Movement & approach (when jump vs. stay grounded)

*The axis that most directly informs #927. This is the thinnest-covered axis in prior docs, so it
carries the most net-new primary grounding here.*

**Model: a real CPU approaches on the GROUND (walk/dash) and treats jumping as a specific, mostly
reactive/positional option — not a repeated neutral fidget.** [INFERENCE from the primary quotes
below, which describe jumping only in narrow, named situations, never as a general approach tool.]

Primary evidence — the documented jump behaviors are all **situational**, and two are explicitly
flagged as *flaws*:

- [PRIMARY] *"When dashing a long distance towards the player, CPUs often attack them with a basic
  dash attack, rarely using dash grabs or aerial attacks instead."* → the default approach is a
  **grounded dash into a dash attack**, not a jump-in.
- [PRIMARY] *"they tend to grab when starting to walk close to the player."* → close-range approach
  is a **grounded walk → grab**, again no jump.
- [PRIMARY] *"most CPUs often jump before shooting projectiles, even if these are fired in a
  straight horizontal trajectory, such as Blaster or Charge Shot, causing them to miss."* → a
  documented **jump flaw**, tied to projectile use, not a healthy approach pattern.
- [PRIMARY] *"jump continuously in place even if the obstacle can be jumped over."* → the canonical
  **repeated-in-place-jump flaw**. This is the real-CPU analogue of the pycats #927 jitter — but
  note it is described as a **stage-navigation** bug (against an obstacle), and even so is called
  out as a flaw, i.e. **not desirable to reproduce.**
- [PRIMARY] *"the CPU always runs away and jumps onto a platform if there is one nearby, fleeing to
  others if the player comes near."* → jumping is used to **retreat to a platform**, a positional
  move, and (in context) a stalling flaw.

**Level scaling of movement:** [GAP] no source gives a per-level movement/jump table. The general
scalar (reaction ↓, follow-through ↑) is the only sourced lever; a higher level *reacts and commits*
faster but the *movement vocabulary* (walk, dash, situational jump) is the same at every level.
[INFERENCE]

**Target for pycats (bridge to #927):** a natural bot **defaults to a grounded approach** and only
jumps when there is a *reason* (target genuinely above and reachable, a platform to contest, a gap
to cross). The #927 finding is that pycats' jump-toward pulse fires a *repeated in-place hop*
whenever the target is nominally above — precisely the *"jump continuously in place"* flaw the wiki
lists as a defect. So the reference model says: the #925 architect should make the jump **decisive
and infrequent** (one clean jump when warranted, then commit), not tune the pulse cadence. Ground
approach is the canon default; the jitter has **no canonical behavior to preserve** — it is a flaw
in both the real CPU and pycats.

---

## Axis 2 — Spacing / neutral

**Model: committal, proximity-driven approach — CPUs do NOT space, bait, or footsie.** [PRIMARY /
INFERENCE] The documented neutral is "get into range, then attack by distance-band," which is why
CPUs are exploitable:

- Approach is committal (Axis 1: dash → dash-attack; walk → grab). There is no evidence of a CPU
  *retreating to reset neutral* as a spacing tool; the one retreat behavior is the platform-flee
  flaw above. [PRIMARY for the behaviors; INFERENCE that deliberate spacing is absent.]
- [PRIMARY] *"the CPU often charges and fires it constantly regardless of whether the player can
  absorb or reflect it."* → neutral is **range-band → fire**, with no read of the opponent's option
  — the opposite of baiting.
- Post-advantage "spacing" is crude and positional: [PRIMARY] *"CPUs that launch an opponent
  upwards will just stay on the ground waiting for them to come down, spamming up tilts and up
  smashes as they get near."*

**Level scaling:** the *reliability and speed* of the same committal approach rises with level;
the *committal nature itself does not change*. [INFERENCE, consistent with the two-knob model.]
Prior repo research (#343, `2026-06-30-npc-spacing-footsies-models.md`) reached the same conclusion
and is the constraint on any pycats spacing work: **model spacing as proximity-band accuracy, never
as footsies/baiting.**

**Target for pycats:** the existing `standoff` / `attack_range` / `fireball_range` band logic in
`AttackerController` already models this faithfully (and even reproduces the "fire at range
regardless of opponent option" flaw). No change needed for fidelity; the naturalness work is on
movement (Axis 1) and defense (Axis 3), not spacing.

---

## Axis 3 — Defense (shield / spot-dodge / roll / air-dodge)

**Model: reactive at high level, random-or-absent at low level. Difficulty scales the reliability
and speed of a reactive defense, not its existence.**

- [PRIMARY] *"lower level CPUs are unlikely to shield or dodge an attack … almost never using their
  shield at all, or at random times in Brawl. On the other hand, higher-level ones almost always
  defend from attacks."* → low = random/absent; high = reactive.
- The reactive trigger is **proximity/approach-based**: [PRIMARY] *"CPUs will put up their shield
  when a player is approaching from around two character lengths away, which can be exploited with
  shield-breaking moves."* (Provenance note: this line lives on the general *Flaws* page; #251 read
  it as Ultimate-flavored. Cite it as the *shape* of a reactive trigger — a fixed reactive rule,
  exploitable because fixed — not a Brawl-exact distance. [PRIMARY wording / INFERENCE on the
  exact game.])
- Air-dodge is **over-reactive** — a canonical exploit: [PRIMARY] *"High-level CPUs almost always
  air dodge as soon as possible when launched in tumbling state, which can be easily exploited."*
  A reminder that *reactive ≠ smart*: the high-level CPU reacts to the "I'm in tumble" state
  reflexively and is punished for it.
- **Shield vs. spot-dodge vs. roll selection per situation is [GAP]** — no source gives a clean
  per-option rule beyond "high CPUs use all of them reactively; low CPUs mostly roll, and to
  reposition rather than to evade." A pycats policy should pick shield as the primary reactive
  defense and treat the split as a tuning choice.

**Level scaling:** [PRIMARY on the ends] low almost-never / random ↔ high almost-always reactive,
enabled by the 1-frame reaction (Axis 5). Mid-curve is [INFERENCE].

**Target for pycats:** this is already implemented — `reactive_shield` (Lv5+, threat-gated) vs. the
low-level unconditional `shield_chance` roll, plus the reactive roll-away (`evade_chance`). The
reference model *validates* the existing #251-derived design; no fidelity gap here.

---

## Axis 4 — Attack selection

**Model: choose the attack by RANGE/POSITION band and situation, from a level-gated move kit —
crudely and predictably.** (The **smash-usage** sub-slice — when/how-often a CPU throws a smash by
level — is **#915**; not duplicated here.)

Primary evidence for the selection rules:

- Dash range → dash attack: [PRIMARY] *"…CPUs often attack them with a basic dash attack, rarely
  using dash grabs or aerial attacks instead."*
- Walk-close → grab: [PRIMARY] *"they tend to grab when starting to walk close to the player."*
- Opponent-above → up-tilt / up-smash by position: [PRIMARY] *"…spamming up tilts and up smashes as
  they get near."*
- Range-band → projectile, no option-read: [PRIMARY] *"…charges and fires it constantly regardless
  of whether the player can absorb or reflect it."*

**Move-kit richness scales with level** (the discrete-unlock layer): low levels *"stand next to
opponent, weak attack"* (jabs/tilts) and high levels use aerials, smashes, and grabs *"more
prominently"* — established [PRIMARY] in #148 §Q1 and carried here; the exact per-level unlock
thresholds are [INFERENCE].

**Target for pycats:** the `enabled_moves` capability gate + the position-based move-select seam
(neutral→jab, toward→f-tilt #292, up/down→u/d-tilt, at-kill%→smash #714) already model "select by
band/position from a gated kit." Faithful; the open item is the smash *policy* (#915), not the
selection *shape*.

---

## Axis 5 — Level scaling (what actually changes 1→9)

**Model: two continuous knobs + a few discrete unlocks. The decision SPACE is level-independent.**

- [PRIMARY] *"the level of an AI opponent determines how likely they are to follow through with a
  decision, as well as how fast they react."* → the **two knobs**: follow-through probability ↑ and
  reaction latency ↓ as level rises.
- Same rules at both ends: [PRIMARY] *"both a level 1 and a level 9 AI will decide to do something
  such as input an attack, but the level 1 will almost never do so."*
- The reaction floor is measured: [PRIMARY] *"it was ultimately demonstrated that CPUs had a
  reaction time of one frame, and thus, did not read button inputs to form decisions."* (Toomai
  2013, via SmashWiki.) → Lv9 ≈ 1-frame reaction; and crucially the CPU **reacts to on-screen
  state, not inputs** — so it cannot be mind-gamed by a fake-out.
- The discrete unlocks layered on top: move-kit richness (jab→tilts→aerials→smashes/grabs/specials)
  and **recovery variety flips at ~Lv6** — the single *explicitly-sourced* discrete threshold in the
  whole ladder (#148 §Q1). Everything else (exact per-level reaction frames Lv2–8, exact unlock
  levels) is [GAP] / [INFERENCE].

**Where "seldom / random / unskilful at low levels" comes from mechanically:** *not* injected error
— it emerges from **long reaction latency + low follow-through probability**. A low CPU *decides*
the right thing but reacts too late and usually fails to commit, so it *looks* hesitant and random.
[PRIMARY mechanism.] (pycats' optional near-miss / accidental-press human-error models, #702 Axes
3–4, are explicitly **[PYCATS-ORIGINAL]**, not Smash-sourced — Smash uses hesitation, not fumbling.)

**Target for pycats:** fully implemented and already the most-grounded part of the ladder —
`level_params()` interpolation over the sourced anchors (`reaction_delay`, `follow_through_p`,
`attack_period`, `standoff`, `shield_chance`) + level-gated flags. See #148 §Q5 and #702 Axis 1.

---

## Axis 6 — Known weaknesses (canon flaws — preserve as flavor vs. remove as bugs)

These are **documented, level-independent** — even a Lv9 CPU has them. The architect must decide
per-flaw whether pycats keeps it (canonical charm / difficulty ceiling) or removes it (reads as a
bug in a small roster). All [PRIMARY]:

| Canonical flaw (verbatim) | Keep or drop for pycats? |
|---|---|
| *"CPUs have generally poor edgeguarding abilities, simply standing on the edge of the stage and spamming weak projectiles"* | **Keep** — already modeled as deliberately-imperfect edge-guard (low follow-through). |
| *"CPUs never attempt to edgehog if they're on the stage; they never leave the stage to grab a ledge to prevent another character from grabbing it."* | **Design call** — pycats added an edge-hog (#404) that *does* contest the ledge, deliberately *diverging* from canon. Architect decides whether to keep the divergence. |
| *"CPUs never avoid or fight off edgeguarders during their recovery, making them much easier to KO than human players."* | Keep as flavor (a difficulty ceiling), gated on recovery mechanics. |
| *"When the player grabs a ledge, CPUs will stand still at a distance away from the ledge for some seconds before pursuing the ledge hanging player."* | Neutral — a minor delay; low priority. |
| *"jump continuously in place even if the obstacle can be jumped over."* | **Drop** — this IS the #927 jitter; a flaw in both. No canon value to preserve. |
| *"most CPUs often jump before shooting projectiles … causing them to miss."* | **Drop-ish** — pycats' fireball bot fires from the ground; do not add a pre-fire jump. |
| *"High-level CPUs almost always air dodge as soon as possible when launched in tumbling state, which can be easily exploited."* | Optional flavor (an exploitable high-level tell); gated on air-dodge AI. |
| *"they never change their playstyle, and players cannot use them to adapt"* / *"predictable, usually having the exact same response to certain actions"* | **Inherent** — pycats' deterministic if-then already has this; it is the nature of the model, not a bug to fix. |

The unifying primary characterization: [PRIMARY] *"they all invariably rely on some form of 'if-then'
script"* and *"Since CPUs are unable to learn or adapt … they never change their playstyle."*

---

## Consolidated reference model (architect-facing, #925 child 3)

| Axis | Canonical behavior | pycats status | Fidelity gap? |
|---|---|---|---|
| 1 Movement/approach | Grounded walk/dash default; jump only situational (above-target, platform, cross-gap); repeated in-place jumping is a **flaw** | jump-toward pulse over-fires (the #927 jitter) | **Yes — the #927 fix target** |
| 2 Spacing/neutral | Committal, proximity-band, no baiting | `standoff`/range-band logic faithful | No |
| 3 Defense | High=reactive, low=random/absent; over-eager air-dodge | `reactive_shield`/`evade`/`shield_chance` faithful | No |
| 4 Attack selection | Range/position band from a level-gated kit; crude | `enabled_moves` + position move-select faithful; smash policy = #915 | Only smash policy (#915) |
| 5 Level scaling | Two knobs (reaction↓, follow-through↑) + discrete unlocks; same decision space | `level_params()` interpolation faithful | No |
| 6 Known weaknesses | Documented, level-independent flaws | mixed (some kept, edge-hog diverges) | Per-flaw design call |

**Headline for the architect:** the pycats CPU's *shape* is faithful across all six axes; the
only genuine **fidelity gap is Axis 1 (movement/jump)**, and it coincides exactly with the #927
jitter root cause. The reference model's prescription — *grounded approach by default, decisive
infrequent jumps, never a repeated in-place hop* — is the design target. Everything else is either
already faithful or a bounded design call (Axis 6 flaws, Axis 4 smash policy #915).

---

## Caveats & gaps

- **No PM-specific CPU-AI source** — everything is Brawl-derived secondary (provenance ceiling above).
- **PM's Melee-style movement** (faster ground movement, air-dodge, no tripping — #144) changes the
  *options* a CPU has, not the *brain* selecting them; whether PM re-tuned the reaction/follow-
  through curve is **[GAP]** — no source. [INFERENCE] the brain is Brawl's.
- **Per-level movement/jump table is [GAP]** — the two-knob scalar is the only sourced lever; do not
  invent a per-level jump-frequency ladder without a source.
- **Shield vs. spot-dodge vs. roll selection is [GAP]** (carried from #251).
- **DI / teching per level is [GAP]** (carried from #148) — do not invent.
- **Exact reaction frames Lv2–8 are [GAP]** — only Lv9≈1-frame is measured; the curve is inferred.
- The concrete *"two character lengths"* shield distance is a general-*Flaws*-page line of uncertain
  game-exactness — cite as the *shape* of a reactive trigger, not a measured Brawl distance.

---

## Downstream

Per #925, the **architect ticket (#925 child 3)** is filed after this doc lands (one at a time). It
should design the Axis-1 movement/jump fix against this model, consuming **#927** (pycats root
cause) + this doc (target behavior), and rule on the Axis-6 per-flaw keep/drop calls (esp. the
edge-hog divergence). The smash-policy slice remains **#915**. This doc root-cause-free: it
establishes the target, it does not design or implement the fix.

---

## Sources

| Source | Quality | Gives (first-hand quotes re-fetched 2026-07-31) |
|---|---|---|
| [SmashWiki — Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence) | secondary (authoritative community) | two-knob model; Lv1-vs-Lv9 same-decision; 1-frame reaction / no input-reading (Toomai 2013); low-random-vs-high-reactive shielding |
| [SmashWiki — Flaws in artificial intelligence](https://www.ssbwiki.com/Flaws_in_artificial_intelligence) | secondary | *"if-then script"*; predictability / no-adaptation; the ~two-character-length shield trigger |
| [SmashWiki — List of flaws in AI (SSBB)](https://www.ssbwiki.com/List_of_flaws_in_artificial_intelligence_(SSBB)) | secondary | Brawl per-situation behaviors: dash-attack approach, walk-close grab, jump-before-projectile, jump-in-place, post-launch up-tilt spam, charge-fire-regardless, air-dodge-on-tumble, edge-guard/edgehog/recovery flaws, ledge-standoff |
| Toomai (2013), via SmashWiki | secondary | Lv9 = 1-frame reaction; CPUs react to on-screen state, not inputs |
| `docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md` (#148) | primary (repo) | difficulty scalar + per-level table; recovery-variety ~Lv6 threshold; move-kit ramp |
| `docs/research/2026-06-30-cpu-ai-decision-model.md` (#251) | primary (repo) | decision-model (if-then), reactive-vs-random shielding, spacing/whiff-punish, edge-guard |
| `docs/research/2026-07-07-cpu-level-scaling-per-character.md` (#702) | primary (repo) | full 1–9 curve, per-character gating, near-miss/accidental-press (pycats-original) |
| `docs/research/2026-06-30-npc-spacing-footsies-models.md` (#343) | primary (repo) | Smash CPUs approach committally by proximity — spacing ≠ footsies |
| `docs/research/cpu-jitter-jump-findings.md` (#927) | primary (repo) | pycats jitter-jump root cause — the Axis-1 counterpart this model targets |
