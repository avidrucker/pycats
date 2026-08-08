# NPC spacing / footsies models — how should the AI controller relate standoff, attack range, and reach? (#343)

> Research findings (#343, child of the #250 AI umbrella; **blocks #277**). Surfaced
> implementing #277: the live tuning has `standoff` (30–35) *inside* the reach-aware
> `_melee_range` (58) at every reactive level, so #277's "approach to attack range /
> footsies" instruction is self-contradictory. This doc asks what NPC fighting-game
> controllers *typically* do, so #277's model is chosen from evidence rather than
> guessed. **Findings + spec recommendation only — no controller code.**
>
> Prioritises the **Smash lineage** (pycats' explicit target: Project M → Melee →
> Brawl), then contrasts general fighting-game AI. Code grounded against
> `pycats/sim/controllers.py` at HEAD. Date: 2026-06-30. Agent: FIG. Area: `area:combat`.

## TL;DR — the headline answer

**Smash CPUs do not do footsies. They approach committally and attack by proximity;
deliberate spacing, baiting, and retreat-as-spacing are documented *non*-behaviors.**
SmashWiki (Melee flaws): CPUs *"always walk toward the player… then spam their dash
grab and jabs at close range."* CPUs are *baited by* the player, they do not bait.
Retreat as a spacing tool is absent — rolls are the only repositioning primitive.

So the premise under #277 — idle *outside* strike range, dart in, bait a whiff — is a
**human** skill (the SmashWiki *Spacing* article is about player technique), not how a
faithful Smash CPU behaves. **pycats' current range-band model (approach → attack at
proximity, `standoff < attack_range`, stand inside strike distance) is already the
faithful one.**

Consequences for #277:
- **Reject model B (true footsies — widen `standoff` outside range).** It makes the
  CPU do the one thing real Smash CPUs explicitly *don't*, and it retunes the
  difficulty ladder (#231/#148), which #277 scopes out.
- **Recommend model A (press-in / no-retreat when safe), minimally.** The only
  evidence-faithful sliver of "reactive spacing" is: when the opponent is *vulnerable*
  (in move recovery), don't back off — stay pressed in to land the close-range punish,
  matching the documented "spam jabs at close range" + crude position-triggered punish.
- **Keep `standoff` inside/at melee range.** Do not widen it. The reach-awareness from
  #335 is a *pycats refinement* beyond real CPUs (which use a flat per-game proximity
  band) — fine to keep, but it is not a footsies enabler.
- **Reframe #277 away from "footsies"** in its wording; flag **#338** (retreat-as-
  spacing) as weakly faithful and recommend it become *reactive roll/dodge-away* (which
  IS documented) or be deferred.

## Q1 — Does the NPC idle *inside* or *outside* its attack range?

**Inside. Smash CPUs approach to proximity and attack; they do not hold a spacing gap
outside their range.** Verbatim (SmashWiki, *Flaws in artificial intelligence*):

- Melee: *"CPUs now have an even poorer approach, always walking towards the player
  while periodically using projectiles, then spamming their dash grab and jabs at
  close range."*
- Brawl: *"They have become much better at approaching, as they now use their full
  dashes to move and finally try to attack grounded foes with aerials."*
- Ultimate (reactive-defense trigger, proximity-based): *"CPUs will put up their shield
  when a player is approaching from around two character lengths away."*

"Footsies" — move between close and mid range to *bait* a whiff and punish it — is a
**player** skill; the SmashWiki *Spacing* page describes dash-dancing, wavedashing, and
short-hop fast-falling as *human* movement tools. No source describes a CPU holding a
deliberate spacing gap outside its own reach.

**pycats read:** the controller idling at `standoff` (30–35) *inside* `_melee_range`
(58) — i.e. standing within strike distance and attacking on a proximity gate — is the
faithful posture, not a bug to "fix" by widening the gap.

## Q2 — Approach vs. hold vs. retreat, and what drives it

**Approach is committal; hold is proximity-band → attack; retreat-as-spacing is
absent.** (SmashWiki, *Flaws*; corroborated by the #251 decision-model doc §Q3.)

- **Approach:** walk/dash straight in. Melee: *"spamming their dash grab and jabs at
  close range."* The trigger is **distance**, not opponent state.
- **Hold / attack:** a **range band → action** rule. Close range → jabs/grab; *"a
  certain distance"* → projectiles (*"Projectile-using CPUs will prioritize using them
  at a certain distance, making it very easy to anticipate"*). No read of the
  opponent's option — the #251 doc calls this the "fire at range regardless of opponent
  option" flaw, which pycats already reproduces.
- **Retreat:** *no* documented deliberate walk-retreat spacing. Repositioning is done
  with **rolls** (a low-level primitive), and edge/ledge approach even *waits* (*"CPUs
  will stand still at a distance… for some seconds before pursuing"*). So a "retreat
  from a threat" behavior (#338) as a *walk-away spacing* tool is **not** faithful;
  a reactive **roll/dodge-away** would be.

## Q3 — Reach relationship (own vs opponent reach)

**Real CPUs use a single flat per-game proximity band, not a reach-derived function.**
"Close range → jab/grab" and "a certain distance → projectile" are fixed thresholds,
identical across characters — there is no evidence a CPU derives its commit distance
from its own or the opponent's move reach.

**pycats read:** the reach-awareness added in #335 (`_melee_range` = per-character
committed-move reach) is a **refinement beyond** faithful CPU behavior — a reasonable
one, because pycats has asymmetric per-character reach (#285) and a flat band would
whiff short-reach moves. But it is a *quality* improvement, **not** a footsies enabler:
knowing your reach lets you attack from the right distance; it does not imply standing
*outside* it. Deriving spacing from the *opponent's* reach (DEV-B, a #338 follow-up) has
**no** basis in documented CPU behavior — it would be a pycats-original enhancement, to
be justified on "satisfying opponent" grounds, not faithfulness.

## Q4 — Difficulty modulation

**Difficulty scales reaction speed + follow-through reliability, not spacing
intelligence.** (SmashWiki *AI* + #148 doc.) Brawl/PM difficulty is a single 0–100
scalar over reaction time and follow-through, plus a few capability unlocks; *"both a
Lv1 and a Lv9 CPU decide to do the same things."* Spacing sophistication is **not** one
of the knobs — even a Lv9 CPU *"can't be mind-gamed · doesn't learn · won't bait/adapt ·
poor edge-guard"* (#148, level-independent flaws). So the spacing model is essentially
**level-independent**; what a higher level does is approach/react *faster and more
reliably*, not space more cleverly.

**pycats read:** any reactive-spacing behavior should ride the existing reaction/
follow-through scalars (gate on level, like `reactive_shield`/`whiff_punish`), and
should *not* introduce a per-level spacing-IQ ladder. This matches #277's `reactive_spacing`
knob approach.

## Context — general (non-Smash) fighting-game AI

Outside the Smash lineage, distance **is** a central AI state variable, but the
implementations split:

- **Classic if-then / state-machine AI** buckets the gap (far / mid / close) and picks
  from a per-bucket action table — defensive profiles keep distance, aggressive ones
  approach and pressure. This is spacing-*flavored* but still reactive scripting, not
  optimal footsies.
- **True footsies / neutral** (bait a whiff, punish, "stand where your options are
  strong and the opponent's are weak") is treated as a **high-level human** skill in
  design writing, and only **reinforcement-learning** agents (e.g. the FTG-AI / "pro-
  level RL" line) actually learn it — well outside pycats' deterministic if-then
  controller.

So even in the broader genre, a hand-authored controller like pycats' is expected to do
**distance-band reactive scripting**, not learned footsies. This *reinforces* the Smash
finding: the faithful and the practical model coincide — approach + proximity attack +
reactive defense, tuned by reaction/follow-through.

## Q5 — Recommendation for #277

**Faithfulness principle (the guiding rule):** pycats models the faithful CPU baseline
— *approach + proximity attack + reactive defense* — and selectively **fixes only the
flaws that break the game**, not the flaws that merely make the CPU beatable. Precedent:
#292 fixed the never-KO jab-lock (which is *itself* the documented Melee flaw *"spamming
jabs at close range"*) because an unwinnable match is broken; it did **not** try to give
the bot human footsies. Spacing should follow the same rule.

Recommended model for #277 — **(A) press-in / no-retreat, minimal:**

**Design/seam (revised):**
- Keep the `reactive_spacing` knob (True for levels 5/7/9; default off → golden-safe).
- In the movement block, when `reactive_spacing` **and** the opponent is *vulnerable*
  (in move **recovery**, no incoming threat) **and** the bot is within melee range:
  **suppress the `adx < standoff-8 → away` back-off** — hold or press `toward` instead
  of drifting back. Otherwise (threatened, or default) the `standoff` dance is unchanged.
- `standoff` stays **inside** melee range (approach-to-commit). **Do not widen it.**
- Deterministic (position + opponent move-phase only; no `self.rng`). Decoupled from the
  shield branch (testable via `reactive_spacing=True, reactive_shield=False`).

**Acceptance (revised):**
- [ ] With the opponent in recovery and the bot at a gap below `standoff-8`, a
  `reactive_spacing` bot does **not** move away (holds/presses); a default bot moves away.
- [ ] With the opponent winding up (a threat), the `reactive_spacing` bot's spacing is
  unchanged from default (retreat is #338's concern, reframed — see below).
- [ ] Low/default behaviour unchanged; default `AttackerController` golden byte-identical.

**Reject model B (widen `standoff` outside range).** It is anti-faithful (CPUs don't
space), retunes the difficulty ladder (#231/#148, out of #277's scope), and shifts
leveled behavior broadly. If a genuine footsies bot is ever wanted, it is an RL/original
feature, filed separately and *not* claimed to be Smash-faithful.

**Reframe #277's wording** away from "footsies/space outside reach" to
"press-the-advantage on a vulnerable opponent." **Flag #338** (retreat-from-threat): a
*walk-retreat* spacing tool is not faithful; recommend it become a reactive
**roll/dodge-away** (documented CPU repositioning) or be deferred. **DEV-B** (opponent-
reach into the retreat band) has no faithfulness basis — keep it parked unless justified
as an original "satisfying opponent" feature.

## Termination

All five questions answered with sourced evidence; a single recommended model (A) named
for #277 with a concrete standoff↔range↔reach relationship (standoff stays inside melee
range; reach-awareness is a refinement, not a footsies lever). Follow-up: update #277's
Design/seam + acceptance to the above (or comment the revision), and re-scope #338.

## Non-goals

- Implementing the #277 controller change (that ticket / a spin-off).
- Per-archetype balance tuning (#117); reworking the difficulty ladder (#231/#148).

## Cross-refs & sources

Blocks **#277**; re-scopes **#338**; parks **DEV-B**. Parent #250; builds on the #251
decision-model doc (§Q3 spacing), #148 difficulty ladder, #285 reach catalogue, #335
`_melee_range`. Movement block: `pycats/sim/controllers.py`.

Sources:
- [SmashWiki — Flaws in artificial intelligence](https://www.ssbwiki.com/Flaws_in_artificial_intelligence) (approach/spam-by-distance/bait quotes)
- [SmashWiki — Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence) (if-then reactive scripting; difficulty scalar)
- [SmashWiki — Spacing](https://www.ssbwiki.com/Spacing) (footsies as a *player* skill)
- [Adaptive AI for Fighting Games (Ricciardi & Thill, Stanford CS229)](https://cs229.stanford.edu/proj2008/RicciardiThill-AdaptiveAIForFightingGames.pdf) and [Creating Pro-Level AI with Deep RL (arXiv:1904.03821)](https://arxiv.org/pdf/1904.03821) (distance as a state variable; footsies via RL, not if-then)
- In-repo: `docs/research/2026-06-30-cpu-ai-decision-model.md` (#251), `docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md` (#148), `docs/research/2026-06-30-ai-controller-reach-awareness.md` (#285).
