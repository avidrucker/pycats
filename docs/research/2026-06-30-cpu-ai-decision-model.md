# PM/Melee/Brawl CPU AI decision model — how the AI *brain* decides (#251)

> Research findings (#251, first child of umbrella #250). Where #148
> (`docs/research/2026-06-29-pm-cpu-difficulty-levels-1-9.md`) mapped the
> **difficulty *scalar*** (reaction speed × follow-through × capability unlocks),
> this doc maps the **decision model** — *how the AI brain chooses what to do each
> frame*, and especially **when it shields**. Findings only — **no controller code**.
>
> Motivating complaint (the headline question, #251 Q2): high-level pycats bots
> shield in open space with **no enemy/projectile near** — because #238's
> `shield_chance` rolls **every frame unconditionally**. Is that faithful to the
> Smash lineage, or should a high-level CPU shield **reactively**?
>
> Prioritises **Project M → Melee → Brawl**. Code grounded against
> `pycats/sim/controllers.py` / `runner.py` / `entities/attack.py` at HEAD.
> Date: 2026-06-30. Agent: FIG. Area: `area:combat`.

## TL;DR — the headline answer

**A high-level Smash CPU shields *reactively*, not at random. A *low*-level CPU
shields at random (or almost never).** SmashWiki is explicit on both ends:

- Low level: *"unlikely to shield or dodge an attack, using rolls simply to
  reposition themselves… and almost never using their shield at all, or **at random
  times** in Brawl."*
- High level: *"almost always defend from attacks"* with *"one-frame reactions"*
  enabling *"disproportionate perfect shielding."*

So pycats has it **backwards at the top of the ladder**: the unconditional per-frame
`shield_chance` is a faithful model of a *low*-level "shields at random times" CPU,
but the **opposite** of a high-level CPU, which should shield *because* it detects an
incoming attack. The fix (#250 child 2) is **not** to raise/lower `shield_chance` —
it is to make the high-level shield **conditional on a detected threat**, while
keeping the random roll as the *low*-level flavour.

**The decision model is reactive if-then scripting over on-screen state.** SmashWiki:
the CPU AI *"invariably rel[ies] on some form of 'if-then' script"* — a set of
condition→action rules evaluated against the **visible game state**, not a planner
and not input-reading. Toomai (2013) measured a **1-frame reaction time** and
concluded CPUs *"did not read button inputs to form decisions"* — they react to
on-screen state (positions, an active hitbox, a launched projectile). The difficulty
level governs **how fast** the rule fires (reaction frames) and **how reliably** it
commits (follow-through probability), *not which rules exist* — Lv1 and Lv9 share the
same decision space (consistent with #148's "both decide the same things" finding).

**Why this matters for pycats:** our `AttackerController.decide(a, t, frame)` is
**already an if-then rule set evaluated per frame** — the same *shape* as the real
AI. The gap is purely the **inputs** to those rules: today the rules see only the two
players' positions; the missing ingredient for reactive defence is a **threat signal**
(is an attack/projectile incoming?). That signal already exists in the sim — it's just
not handed to `decide()` yet. See *pycats expressibility* below.

## Q1 — Decision structure: how is "what to do this frame" chosen?

**Verdict: a reactive if-then rule set over on-screen state — a "situation → response"
script, not a planner, not a learner, not (provably) a behaviour-state machine.**

- SmashWiki characterises all Smash CPU AI as relying on *"some form of 'if-then'
  script"* — discrete conditions mapped to responses. The community calls the
  per-character variations *"scripts [that] will perform inhumane stuff
  reactionary"* (e.g. frame-perfect powershields/reflects).
- The behaviour is **per-situation and predictable**: CPUs *"exhibit the exact same
  response to certain actions"* and *"never change their playstyle."* This is the
  signature of a stateless-ish condition table, not a deliberative planner.
- **No learning / no adaptation** (outside amiibo) — disproven by ROM disassembly;
  the "CPUs learn mid-match" claim is a myth. Keep pycats deterministic/seeded.
- **No authoritative source exposes the actual data structure** (a literal subaction
  table vs a weighted selector vs a small FSM). The `doldecomp/brawl` decompilation
  is WIP and the search surfaced **no published AI decision-table dump**. So at the
  *implementation* level this is a **gap**; at the *observable-behaviour* level the
  "if-then over visible state, gated by reaction-time + follow-through-probability"
  model is well-supported and is the right abstraction to build against.

**Confidence:** behaviour model = *explicit* (SmashWiki). Exact internal structure =
*gap* (provenance-limited; Brawl decomp incomplete).

## Q2 — Shielding (the reported issue): reactive or random?

**Verdict: reactive at high level, random/absent at low level. Difficulty scales the
*reliability and speed* of a reactive shield, not its existence.**

| Level band | Shield behaviour | Source |
|---|---|---|
| **Low (Lv1–3)** | *"almost never using their shield at all, or **at random times** in Brawl"*; rolls used only to *reposition*, not to defend | **explicit** |
| **Mid (Lv5)** | occasional/inconsistent defence | inferred (between ends) |
| **High (Lv7–9)** | *"almost always defend from attacks"*; **1-frame reactions**; *"disproportionate perfect shielding"*; *"perfect shield, roll, sidestep, or air dodge almost any attack"* | **explicit** |

**What triggers a defensive option:** an **incoming attack detected on-screen** (a
hitbox the CPU can react to within its reaction window) — the high-level CPU then
selects shield / spot-dodge / roll / air-dodge. Concrete documented trigger
(SmashWiki, described for *Ultimate* — provenance caveat): a CPU *"will put up their
shield when a player is approaching from around two character lengths away"* — i.e.
the trigger is a **proximity/approach** signal, and (at low level) it is exploitable
precisely because it is a fixed reactive rule. The **reactivity is the point**: a
high CPU shields *because something is coming*, which is exactly what pycats' high
levels fail to do.

**Shield vs dodge vs roll:** sources don't give a clean per-option decision rule
beyond "high CPUs use all of them reactively; low CPUs mostly roll, and to reposition
rather than to evade." Treat the **shield-vs-dodge/roll split as a `gap`** — pick a
sensible pycats policy (shield as the primary reactive defence; dodge/roll later) and
mark it a tuning choice, not measured data.

**Air-dodge is over-reactive (an exploit):** high CPUs *"almost always air dodge as
soon as possible when launched in tumbling state"* — a *reactive* response to the
"I'm in tumble" state, exploitable for follow-ups. Useful later (#250 child 3) and a
reminder that reactive ≠ smart.

**Confidence:** low/high ends = *explicit*; mid-curve and the shield/dodge/roll
selection = *inferred*/*gap*. The Brawl "at random times" wording is the strongest
single line for the #250 thesis: random shielding is the **low-level** model.

## Q3 — Spacing / approach / retreat / whiff-punish

**Verdict: reactive and exploitable; approach is committal, "punishing" is mostly
defend-then-counter, not true whiff-punish.** Documented Brawl behaviours:

- **Approach:** *"When dashing a long distance… CPUs often attack with a basic dash
  attack, rarely using dash grabs or aerial attacks"* → easy to punish. *"They tend
  to grab when starting to walk close to the player"* (a close-range grab rule).
- **Projectile spacing flaw:** *"Most CPUs often jump before shooting projectiles,
  even if these are fired in a straight horizontal trajectory… causing them to
  miss."* And a CPU with a chargeable projectile *"charges and fires it constantly"*
  regardless of absorb/reflect — i.e. **range-band → fire** with no read of the
  opponent's option.
- **Post-launch "punish":** *"CPUs that launch an opponent upwards will just stay on
  the ground waiting for them to come down, spamming up tilts and up smashes as they
  get near"* — a position-triggered cadence, easily dodged. This is the closest thing
  to whiff-punish and it's crude.
- **Retreat:** mostly absent as a deliberate spacing tool; rolls are the main
  repositioning primitive at low level.

**pycats read:** our existing `standoff`/`attack_range`/`fireball_range` band logic
*already* models the "range-band → poke/attack" rule faithfully (and even reproduces
the "fire at range regardless of opponent option" flaw). The reactive upgrade for a
later child is **whiff-punish**: attack *because the opponent just committed a move
and is now in recovery* — which needs the same threat/attack-state signal as reactive
shielding (read `t`'s current move + its recovery window). **Confidence:** behaviours
*explicit*; the pycats mapping is a design proposal.

## Q4 — Edge-guarding / ledge

**Verdict: a documented, level-independent *weakness* — model it as weak on purpose,
low priority for pycats (also gated on ledge mechanics #14).**

- *"CPUs have generally poor edgeguarding abilities, simply standing on the edge of
  the stage and spamming weak projectiles… instead of attacking offstage."*
- *"CPUs never attempt to edgehog… never leave the stage to grab a ledge."*
- *"CPUs never avoid or fight off edgeguarders during their recovery"* → much easier
  to KO than a human; *"never meteor cancel in Brawl."*
- Ledge approach delay: *"When the player grabs a ledge, CPUs will stand still at a
  distance… for some seconds before pursuing."*

So even a Lv9 edge-guards badly. For pycats: when ledge/recovery mechanics land (#14
/ recovery specials), model edge-guard as **enabled but deliberately imperfect** (low
follow-through), per #148's earlier recommendation. **Confidence:** *explicit*
(documented flaw). Lowest priority of the #250 children.

## Q5 — How reaction-time + the difficulty scalar gate the above

**Verdict: the scalar gates *latency* and *commit-probability*; both Lv1 and Lv9 run
the same reactive rules, but Lv1 reacts slowly/unreliably and Lv9 near-instantly.**

- *"the level of an AI opponent determines how likely they are to follow through with
  a decision, as well as how fast they react"* → **two knobs**: reaction frames ↓ and
  follow-through probability ↑ as level rises (this is #148's core finding, restated
  at the decision-model level).
- Lv9 = **1-frame reaction** (Toomai 2013) → reacts to almost any on-screen attack →
  reliable reactive shield/perfect-shield. A low CPU's long reaction window means the
  threat has often already connected, so its shield *looks* random/late — which is
  why a random per-frame roll is an acceptable *low*-level approximation.
- **What a Lv9 reacts to that a Lv1 ignores:** an incoming hitbox/projectile inside
  the reaction window (Lv9's window ≈ everything; Lv1's ≈ almost nothing → effectively
  unreactive). This is the exact lever pycats already has: `reaction_delay` (#232).

**The clean synthesis for #250:** keep the #148/#231 ladder, and make the **shield
rule itself reactive**, gated by the *existing* `reaction_delay` + a per-level
*reliability*. Low level → falls back to the existing random `shield_chance` (faithful
"shields at random times"); high level → shields **on a detected threat** within the
reaction window with high reliability. **Confidence:** *explicit* on the mechanism;
the exact blend is a tuning choice.

## Q6 / pycats expressibility — what our protocol can do today, and the seam

The faithful model ("react to on-screen attack state, gated by reaction-time +
follow-through-probability") maps cleanly onto pycats — **the if-then shape already
exists; only the threat input is missing.** Grounded facts:

- **The decision shape already matches.** `AttackerController.decide(a, t, frame)` is
  a per-frame if-then rule set with exactly the right knobs already present:
  `reaction_delay` (#232 latency), `follow_through_p` (#238 commit-probability),
  `self.rng` (#166 seeded, golden-safe), `enabled_moves` (#248 capability gate).
- **The threat signal exists in the sim but isn't handed to `decide()`.** Two seams:
  - **Melee threat — *no protocol change needed*.** `decide` already receives the
    opponent `t`, and a `Player` exposes `t.current_move` / `t.attack_timer` /
    `t.move_frame` / `t.state`. So "the opponent is mid-attack / in startup near me"
    is **readable today** — enough for reactive shielding against *melee* and for
    whiff-punish (attack when `t` is in recovery). Zero-wiring, golden-safe.
  - **Projectile threat — *needs the `attacks` group wired in*.** A fireball is a
    **detached** `Attack` sprite (`entities/attack.py`): it carries `.owner`,
    `.velocity` (`(vx,vy)`; `None` = a static melee hitbox), `.rect`, and resolved
    hit-circles, and lives independently of its owner — so `t.current_move` does
    **not** reflect an in-flight fireball. To shield a projectile the controller must
    see the live `attacks` group. `run_battle` already holds that group
    (`runner.py:117`, passed to `p.update(..., attacks)`), but controllers are called
    `controller(p1, p2, frame)` — **the group is not passed.** Wiring it (e.g.
    `decide(a, t, frame, attacks=None)` with a `None` default, or a setter the runner
    calls) is the **one protocol change** the threat-aware-shield child must make.
    Filter to the opponent's incoming hitboxes with `atk.owner is t` and a
    near/closing test on `atk.rect`/`atk.velocity`.
- **Golden-safety rule (unchanged from #148/#238/#248):** the **default (level-less)**
  `AttackerController` drives the `full_match` golden — every change MUST leave it
  **byte-identical**. Pattern: gate all new reactive behaviour behind a level/knob
  whose **default is the old behaviour**, never touch `self.rng` on the default path,
  and give any new `decide` parameter a default (`attacks=None`) so existing callers
  and goldens are unaffected. Verify with the full suite + `git status tests/golden/`.
- **Determinism:** threat detection is a pure function of the frame-start snapshot
  (positions + the `attacks` group), so it stays deterministic and replay/golden-safe;
  the only RNG is the existing seeded reliability roll.

## Recommended DEV decomposition for #250 (file one at a time, per RULES)

Lazy decomposition — file the next child only when starting it. Ordered by the user's
complaint first, then by dependency:

1. **DEV: threat-aware shielding** *(the user's exact complaint — do first).* Make the
   high-level shield **conditional on a detected incoming threat** instead of the
   unconditional per-frame roll. Scope:
   - Wire a threat signal into `decide` (the seam above — melee via `t`'s move state
     needs no protocol change; **projectile** reaction needs the `attacks` group
     passed in, default `None` → golden-safe).
   - High level: shield when an opponent hitbox/projectile is incoming within the
     `reaction_delay` window, with high reliability; **low** level: keep the existing
     random `shield_chance` flavour (faithful "shields at random times").
   - **Verify in a real `run_battle`/headless loop, not just a stubbed `decide()`** —
     a green unit test ≠ a working feature (the #248 gotcha: the Lv9 fireball
     unit-tested green but didn't manifest until checked in a full battle).
   - Golden-safe: default/level-less path byte-identical; new `decide` param defaulted.
   *(first; the only one that touches the controller protocol)*
2. **DEV: reactive spacing / whiff-punish / approach.** Attack *because the opponent
   just whiffed and is in recovery* (read `t.current_move`/recovery window — reuses
   the child-1 threat seam, melee branch). Optionally model the documented approach
   flaws (committal dash-attack) as flavour. *(after 1)*
3. **DEV: edge-guarding + ledge behaviour.** Lowest priority; **gated on ledge
   mechanics (#14) + recovery specials**. Model as *enabled but deliberately
   imperfect* (low follow-through) per the documented weakness. *(after #14)*

This **layers reactivity onto the #231 ladder** (which stays) — it does not rewrite
the difficulty scalar (#148/#231 own that).

## Caveats & gaps

- **No PM-specific CPU AI source exists** — PM is Brawl-derived for AI (consistent
  with #148/#48/#24). All behaviour here is **Brawl-sourced**; PM-exactness confidence
  is **low by provenance**, not by contradiction.
- **The internal data structure is a `gap`** — "if-then script" is the *observable*
  model; no published Brawl AI decision-table dump was found (doldecomp/brawl is WIP).
  Build against the behaviour model, not an assumed table.
- **Provenance mix:** the *"shields at random times"* (low) and *"perfect shield…
  one-frame"* (high) lines are **Brawl-specific**; the concrete *"shield when a player
  approaches ~two character lengths away"* trigger is described for **Ultimate** —
  cited as the *shape* of a reactive trigger, not a Brawl-exact distance. The exact
  pycats reaction distance/window is a **tuning starting point**, not measured data.
- **Shield vs spot-dodge vs roll selection per situation is undocumented** — `gap`;
  pycats should pick shield as the primary reactive defence and treat the split as a
  tuning choice.
- **DI / teching per level is undocumented** (carried over from #148) — do not invent.
- All numeric thresholds proposed for the DEV work are **guesses** (`⚠`), to be
  playtested — same discipline as #148's Q5 table.

## Sources

| Source | Quality | Gives |
|---|---|---|
| [SmashWiki — Artificial intelligence](https://www.ssbwiki.com/Artificial_intelligence) | secondary (authoritative community) | follow-through-probability + reaction-speed model; 1-frame reaction (Toomai 2013); CPUs don't read inputs; reactive high-level defence |
| [SmashWiki — Flaws in artificial intelligence](https://www.ssbwiki.com/Flaws_in_artificial_intelligence) | secondary | the *"if-then script"* characterisation; predictability/no-adaptation; approach-distance shield trigger (Ultimate); edge-guard weakness |
| [SmashWiki — List of flaws in AI (SSBB)](https://www.ssbwiki.com/List_of_flaws_in_artificial_intelligence_(SSBB)) | secondary | Brawl per-situation behaviours: shield "at random times" (low), approach (dash-attack/grab), projectile-jump flaw, post-launch up-tilt spam, edge-guard/recovery flaws |
| Toomai (2013), via SmashWiki | secondary | Lv9 = 1-frame reaction; CPUs react to on-screen state, not button inputs |
| [doldecomp/brawl](https://github.com/doldecomp/brawl) | primary (WIP) | Brawl decompilation in progress — **no published AI decision-table** yet (the internal-structure gap) |
| #148 doc `2026-06-29-pm-cpu-difficulty-levels-1-9.md` | primary (repo) | difficulty *scalar* mapping this doc extends; the Lv1/3/5/7/9 knob table |
| `pycats/sim/controllers.py`, `runner.py`, `entities/attack.py` (HEAD) | primary (repo) | the `decide()` if-then shape; `self.rng`/`reaction_delay`/`follow_through_p` knobs; `Attack.owner`/`.velocity`; the `attacks`-group seam |
