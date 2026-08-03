# Fighter statechart architecture — one general chart vs per-character charts vs hybrid

**Ticket:** #1010 (RESEARCH · `area:entities`). **Date:** 2026-08-01. **Author:** cherry.
**Status:** findings — **maps the option space, does not pick.** The choice is a downstream
ARC/decision ticket (research-never-produces-spec). No implementation, no spec here.

Sibling evidence: the meleelight action-state findings **#1011**
(`docs/research/2026-08-01-statechart-meleelight.md`) — its §3 three-tier
character-dependence taxonomy is the primary prior-art input to this doc.

---

## 1. TL;DR

- **pycats is already option A today**: a single builder, `build_fighter_chart(p)` in
  `pycats/charts/fighter_chart.py`, produces one general chart whose guards read the live
  `Player`/`Fighter`. Per-character variation is injected as **data** (moves, frame data,
  `max_jumps`, velocities), never as **graph shape**.
- **Four diverse archetypes ride that one chart right now** — nalio (Mario), birky
  (multi-jump floaty), narz, gnok (DK-ape) — including a multi-jump character, with **zero**
  per-character chart structure. That is the central empirical fact: to date, every
  cross-character difference has been expressible as data, so option A has not yet been
  strained.
- **The console/meleelight "reference" pattern is not option B.** It is a **shared engine
  action-state table + per-character move modules merged in** (`{...baseActionStates,
  ...Marth.moves}`) — i.e. structurally a **hybrid (C)**: one shared graph for the engine
  states (movement / defense / hitstun / ledge / death), per-character **additive** leaves
  for attacks/specials/throws. (#1011 §3.)
- **statecharts-py bounds "hybrid" to composition, not inheritance.** Charts are frozen
  immutable data assembled by pure builder functions; there is no subclass/mixin/override
  mechanism. A hybrid is expressed by **Python-level composition** — helper functions that
  return shared subtrees, plus per-character subtrees spliced into a shared skeleton.
- **Recommendation-space (not a pick):** the divergence pycats will actually meet is
  overwhelmingly (a) data or (b) **additive** per-character leaves (tether-hang, glide/float,
  a copy mechanic) plus a few **per-move transition-target overrides** (non-helpless up-B,
  #980 C6). That shape is the shared-core-plus-injection **hybrid**, and it is the natural
  growth of what pycats already has — reached by *adding a composition seam to today's option
  A*, not by rewriting to N charts. Full per-character charts (B) duplicate a ~25-leaf shared
  engine surface N times and invite golden/parity drift; the evidence for B is weak. The ARC
  ticket decides *when* and *how far* to formalize the seam; this doc supplies the tradeoffs.

---

## 2. What "the statechart" is in pycats today (baseline = option A)

`build_fighter_chart(p)` (`pycats/charts/fighter_chart.py`) builds a hierarchical + parallel
SCXML chart on statecharts-py. Two parallel regions under `root`:

- **`action`** (compound) — the action FSM: `actionable` (`grounded` {idle, walk, dash, run,
  crouch, shield} + `airborne` {jump, fall}), `attacking` {startup, active, recovery},
  `dodging` {dodge}, `hitstun` {hurt, stun}, `ko`, plus force-entered leaves `prone`,
  `getup_roll`, `getup_attack`, `helpless`, `landing_lag`, `ledge_hang`, `ledge_getup`,
  `smash_charge`.
- **`defensive_status`** (compound) — {vulnerable, intangible}, the #527 two-layer
  intangibility region running in parallel with the action FSM.

That is **~25 leaf states, all engine-generic**. Every guard is a lambda closing over the
owning `Player` `p` and reading live attributes (`p.attack_timer`, `p.fighter.dodge_timer`,
`p.fighter.vel`, `p.current_move.startup`, `p.fighter.max_jumps`-derived state, …).

**Where the character enters:** nowhere in the *graph*. It enters through the **data the
guards read**:

- `max_jumps` is a `fighter_data` field (`fighter.py`); multi-jump is resolved entirely in
  `fighter_input.py` by decrementing `jumps_remaining` — **the airborne region does not branch
  on jump count.** birky's extra jumps are a counter, not extra states.
- Move set / frame data / hitboxes are per-character JSON (`characters/data/<cat>.json`); the
  `attacking` sub-phase clock reads `p.current_move.startup/active`.
- Velocities, durations, `run_speed`, dash windows — per-character numbers the shared guards
  consume.

**Conclusion:** pycats is a textbook option A, and the four shipped cats are direct evidence
that A has absorbed real archetype diversity **without a single per-character state**. The
divergence has all been data. The open question #1010 asks is what happens when it *isn't*.

---

## 3. What statecharts-py permits (bounds on "hybrid")

From `statecharts-py/src/statecharts/chart.py` and `elements.py`:

- **Charts are plain frozen data.** `state()`, `parallel()`, `transition()`, `statechart()`
  are pure builder functions returning immutable `StateNode`s (frozen dataclasses). A chart is
  a nested data structure, assembled by ordinary Python calls.
- **Composition is trivial; inheritance does not exist.** There is no class hierarchy, mixin,
  or per-state override API. "Extending" a chart = writing a Python function that returns a
  subtree and splicing it into a parent's `children`. `build_fighter_chart` already does this
  (it assembles `grounded`, `airborne`, `attacking`, … as locals and nests them). A hybrid is
  the *same technique parameterized by character* — e.g. `airborne_leaves(p) + tether_leaves(p)
  if p.has_tether`.
- **Fail-fast id + target validation.** `Chart.__init__` raises `ValueError` on duplicate ids
  and on any transition/initial/history target that doesn't resolve. This is a **safety net
  for a hybrid**: a per-character subtree that references a non-existent state fails loudly at
  build time, not mid-frame. It also means per-character leaf **ids must be unique within a
  chart** — not a problem, because…
- **Every Player gets its own chart instance.** `make_engine` calls
  `Session(build_fighter_chart(player))` per player (`systems/state_engine.py`). There is no
  shared singleton chart. So per-character *structure* is already free of cross-character id
  collisions — nalio's chart and birky's chart are separate objects. (This is why B is even
  possible, and why C has no id-collision cost.)
- **Guards are arbitrary lambdas.** A per-character transition can be gated on any predicate,
  including a character flag (`p.fighter.has_glide`). So a "per-character override" of a shared
  leaf's exit can be expressed *within* option A as a guarded branch — the line between
  "data-driven A" and "hybrid C" is a spectrum, not a wall (see §6).

**Bound on hybrid:** anything expressible as "shared skeleton + per-character subtrees +
per-character guarded transitions" is clean in statecharts-py. Anything requiring one
character to *reshape* a shared leaf's identity (not just its exits) has no library affordance
and would push toward B for that character.

---

## 4. Divergence pressure — structure vs data (the crux)

The decisive question is **how much real fighter divergence is graph structure vs data.**
Evidence from #1011 §3 (meleelight three-tier taxonomy) + pycats' four shipped cats:

| Divergence source | Structure or data? | Evidence |
|---|---|---|
| Multi-jump count (Kirby 5 / Jiggs 5 / birky) | **Data** (`max_jumps` counter) | birky ships on the shared chart; meleelight gates on `charAttributes.multiJump && jumpsUsed<5` (#1011 §2 shared guards) |
| Frame durations (startup/active/recovery, wait length) | **Data** | #1011 §3 T1: shared states "vary only by frame durations" |
| Roll / air-dodge / tech trajectories, ledge-hang offset | **Data** (per-char velocity/offset arrays) | #1011 §3 T2: `ESCAPEB.setVelocities`, `CLIFFCATCH.posOffset` overridden post-setup |
| Move set (attacks / specials / throws) | **Additive structure** (per-char leaves) | #1011 §3 T3: `{...baseActionStates, ...Marth.moves}`; pycats `attacking` reads per-char `current_move` |
| Wall-jump | **Data** (per-state flag) | meleelight `wallJumpAble` per-state boolean (#1011 §2) |
| Tether / grapple recovery | **Additive structure** (a new hang state) | not yet in pycats; a leaf a tether cat has and others don't |
| Glide / float (Peach/Kirby) | **Additive structure** (a new float state) | not yet in pycats |
| Non-helpless up-B (Sing / Egg-throw, #980 C6) | **Per-move transition override** | the up-B exit routes somewhere other than `helpless`; pycats already routes up-B→`helpless` via `recovery_active` guards in `attacking` |
| Kirby copy ability | **Novel structure** (whole sub-mechanic) | the genuine hard case; no shared skeleton covers it |

**The pattern:** almost all divergence is either **(a) data** (counts, velocities, durations,
flags) or **(b) additive leaves** (states one character has that others lack). Very little is
**contradictory rewiring** — the same state behaving *structurally* differently per character.
The one recurring non-additive case is **per-move exit routing** (up-B → helpless vs not),
which is a guarded transition, not a reshaped state.

Two consequences:

1. The **shared engine surface is large and genuinely identical** across characters —
   movement, shielding, dodging, hitstun, prone/getup, ledge, KO, intangibility. That is the
   ~25 leaves pycats already shares. Nothing on the horizon rewrites these per character.
2. The **per-character surface is additive and small** — a move set (already data-driven in
   pycats' `attacking`), plus at most a handful of special leaves (tether-hang, float, copy)
   and a few guarded exits. This is precisely the shape a **hybrid** models, and precisely
   what the meleelight `{...base, ...moves}` merge *is*.

---

## 5. The option space

### A — One general chart (status quo)
One `build_fighter_chart(p)`; every character rides the same graph; all variation is data the
guards read. Additive per-character behavior, when it comes, is expressed as **guarded
branches** in the shared graph (`if p.fighter.has_glide: …` inside a shared leaf's transition
list) or as **always-present leaves that only some characters can reach** (a `float` leaf with
an entry guard no non-float cat satisfies).

### B — Per-character charts
Each character has its own builder (`build_nalio_chart`, `build_birky_chart`, …) or its own
chart module; no shared skeleton — each chart is authored/maintained independently. Per-Player
instancing already supports this with no id-collision cost (§3).

### C — Hybrid: shared core + per-character extension/override
A shared skeleton builder assembles the ~25 engine leaves once; per-character **composition
seams** splice in additive leaves and override specific transitions. Concretely in
statecharts-py: `build_fighter_chart(p)` calls `shared_engine_states(p)` for the common
subtree and conditionally appends `character_states(p)` (e.g. `tether_leaves(p)`,
`float_leaves(p)`) resolved from the character's data/capability flags. Sub-variants:

- **C1 — additive-only:** shared core is fixed; characters may only *add* leaves and *add*
  guarded exits, never change a shared leaf's behavior. (Matches meleelight's merge exactly.)
- **C2 — additive + override:** characters may also replace a named shared transition (e.g.
  up-B exit target) via a per-character override table applied after the shared build.
- **C3 — capability-composed:** the chart is assembled from **capability modules** (jump,
  ledge, tether, glide, copy), each a subtree + guards; a character declares which capabilities
  it has and the builder unions them. (The most structured; highest up-front cost.)

Note the **A↔C spectrum**: option A *already* contains proto-hybrid moves — `attacking` routes
to `helpless` only when `recovery_active` (a per-move capability), and `helpless`/`ledge_hang`/
`smash_charge` are force-entered leaves only some contexts reach. C is reached not by a rewrite
but by **naming the composition seam** and letting characters contribute to it.

---

## 6. Pros / cons / tradeoffs

Assessed across the dimensions #1010 names: divergence fit, statecharts-py fit,
maintenance/testing, determinism/perf, prior art.

### Divergence fit
- **A** — Perfect while divergence stays data or "always-present leaf + entry guard." Strains
  when a character needs a leaf that is *meaningless* for others (a `float` leaf clutters every
  chart) or when guarded per-character branches accumulate inside shared leaves (readability
  rot: the shared graph fills with `if p.has_x` special cases).
- **B** — Trivially fits any divergence (each chart is bespoke), but pays for it by
  **duplicating the identical engine surface**; the divergence it accommodates is mostly
  divergence that didn't need per-character *structure* in the first place.
- **C** — Fits the observed shape best: shared core stays clean, additive leaves live only on
  the characters that have them, per-move overrides are localized. Cost is the seam machinery.

### statecharts-py fit
- **A** — Native; it is what the library's data-composition already expresses.
- **B** — Native but N copies; the library gives no help *sharing* between them — you either
  copy-paste the engine subtree into each builder (drift risk) or factor it out, at which point
  you have built C anyway.
- **C** — Native and idiomatic: pure functions returning subtrees, unioned per character. The
  fail-fast id/target validation (§3) catches a mis-wired per-character subtree at build time.
  No inheritance is needed or available; composition is the intended extension mechanism.

### Maintenance + testing
- **A** — A single mechanic fix (e.g. #990 C1 helpless-flinch) is edited **once** and every
  character inherits it. One golden/parity surface. Onboarding a new cat = ship its data; no
  chart work. This is the current, low-friction reality (4 cats, no per-char chart code).
- **B** — A shared-mechanic fix must be applied **N times**, once per chart, with N chances to
  diverge — the render-parity/golden-drift failure mode this repo already guards against, now
  at the FSM level. N parity surfaces. Highest onboarding + upkeep cost.
- **C** — Shared-mechanic fix edited **once** in the core (like A); only genuinely
  per-character behavior lives per character. Parity surface = one shared-core golden + small
  per-capability goldens. Onboarding a *data-only* cat stays free; onboarding a cat with a new
  *capability* costs one capability module. Middle cost, and it scales with actual novelty
  rather than with character count.

### Determinism / perf
- **A** — One chart built per Player at construction; ~25 leaves; per-frame tick is one
  `send("tick")`. Cheap; already shipped and deterministic (byte-identical goldens).
- **B** — Same per-frame cost per chart; build cost and code size scale with N; no per-frame
  penalty. Perf is not the discriminator.
- **C** — Same per-frame cost; build unions a few subtrees (negligible). A character with more
  leaves has a marginally larger chart; irrelevant at these sizes. **Perf does not
  meaningfully separate the three** — this is a maintainability/clarity decision, not a
  performance one.

### Prior art
- **meleelight / console (Melee):** shared `baseActionStates` table + per-character move
  modules deep-merged per character (`{...baseActionStates, ...Marth.moves}`), then a few
  per-character **data** overrides on shared states (`setVelocities`, `posOffset`). Engine
  states (movement/defense/hitstun/ledge/death) are one shared graph varying only by frame
  data; attacks/specials/throws are per-character additive leaves. **This is hybrid C1 (+ data
  overrides), not A and not B.** (#1011 §3.)
- **pycats today:** the engine-states-shared half of that pattern (option A), with the move
  half still data-driven through `attacking` rather than as distinct per-character leaves. So
  pycats and the console converge on "shared engine graph"; they differ only in whether *moves*
  are leaves (console) or clock-driven data (pycats) — an orthogonal question to A/B/C.
- **fighter-states.md (#160):** documents the invariant both share — a fighter is "only ever in
  one action state," and today per-character variation is data, not graph shape.

**Summary table**

| Dimension | A (one chart) | B (per-char charts) | C (hybrid core+ext) |
|---|---|---|---|
| Fits observed divergence | ✅ until non-additive structure appears | ✅ always, but overkill | ✅ best fit for additive+override |
| statecharts-py idiom | ✅ native | ⚠ N copies, no share help | ✅ native composition |
| Shared-mechanic fix | ✅ once | ❌ N times (drift risk) | ✅ once (core) |
| New data-only cat | ✅ free | ❌ new chart | ✅ free |
| New capability cat | ⚠ clutters shared graph | ✅ isolated (but so is everything) | ✅ one capability module |
| Parity/golden surface | ✅ one | ❌ N | ➖ one core + small per-cap |
| Perf (build/tick) | ✅ | ➖ build scales w/ N | ✅ |
| Prior-art alignment | ➖ half of it | ❌ | ✅ matches console merge |
| Up-front cost | ✅ none (status quo) | ⚠ N builders | ⚠ build the seam once |

---

## 7. Recommendation-space (NOT a decision)

The ARC ticket makes the call; this section frames *the conditions under which each option
wins*, so that call is evidence-driven.

- **Stay on A** if the roster's near-term growth stays **data + always-present-leaf-with-guard**
  (more Mario/DK/Marth-shaped cats, more multi-jump floaties). A is carrying 4 cats with zero
  per-character chart code; there is no present cost to pay down, and premature seam-building is
  speculative structure (cf. don't-pre-decompose). The trigger to reconsider is **readability
  rot** (shared leaves accumulating `if p.has_x` branches) or the **first meaningless-leaf**
  (a `float`/`tether` leaf every chart carries but only one cat reaches).

- **Move to C** when the **first genuinely additive per-character capability** lands (tether
  recovery, glide/float, copy) *or* when per-move exit overrides (non-helpless up-B, #980 C6)
  start to multiply. C is the **natural continuation of A** — factor `build_fighter_chart` into
  `shared_engine_states(p) + character_states(p)` and let characters contribute leaves — not a
  rewrite. It preserves A's "fix-once, free-data-cat" economics while giving novel behavior a
  clean home. The sub-variant (C1 additive-only vs C2 +override vs C3 capability-composed) is
  itself an ARC sub-decision; C1 matches the console prior art most literally and is the
  cheapest first step.

- **Adopt B only** for a character so structurally alien that it shares little with the engine
  core (a hypothetical cat with a bespoke movement model). On current evidence **no roster cat
  approaches this** — the engine surface (movement/defense/hitstun/ledge/KO) is identical across
  every archetype considered, so B would duplicate ~25 shared leaves to isolate a handful of
  novel ones, buying isolation the repo already gets from C at a fraction of the drift risk. B
  is the weakest-supported option and should require a specific, named character that C cannot
  express cleanly.

**What would tip the decision** (evidence the ARC ticket should weigh, some pending #1009's
Tier-1 findings):
- The concrete next 2–3 archetypes' recovery/movement kits — do any need a non-additive
  reshape of a shared state? (If none, A/C; never B.)
- Count of anticipated per-move exit overrides (#980 C6 scope) — many ⇒ C2 over A.
- Whether moves should become per-character *leaves* (console style) or stay clock-driven data
  — orthogonal to A/B/C but interacts with C3.

---

## 8. Method / limits

- **Method:** read the current chart (`pycats/charts/fighter_chart.py`), the statecharts-py
  builder/index (`chart.py`, `elements.py`), the per-character data seams (`fighter.py`,
  `fighter_input.py`, `characters/roster.py`), and cross-referenced #1011 §3 for the meleelight
  prior-art taxonomy.
- **Limits:** divergence pressure for **unshipped** archetypes is reasoned from the four
  current cats + the Melee (Tier-2 meleelight) reference, not from a Tier-1 PM disassembly; the
  #1009 epic's later children (Brawl/PM Tier-1) may surface a per-character structural need not
  visible here. This doc maps options and conditions; it deliberately does **not** pick, and
  contains **no spec** — that is the downstream ARC/decision ticket's job.

## 9. Refs

Current chart `pycats/charts/fighter_chart.py` · engine wiring `systems/state_engine.py` ·
statecharts-py `chart.py`/`elements.py` (#493 to package) · per-char data seams `fighter.py`,
`fighter_input.py`, `characters/roster.py` · meleelight taxonomy **#1011**
(`docs/research/2026-08-01-statechart-meleelight.md` §3) · generalized-statechart epic
**#1009** · `docs/pm-reference/fighter-states.md` (**#160**) · intangibility two-layer **#527**
· helpless decision queue **#990** (C1/C6) · up-B/helpless **#980** · hitstun/helpless **#987**.
