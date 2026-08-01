# ADR-0010 — CPU movement/behavior fix (V1): surgical jump re-arm, edge-hog reverted to canon, eyeball acceptance bar

- **Status:** Accepted
- **Date:** 2026-07-31

## Context

The #925 epic ("CPU behavior fidelity — fix un-PM-like weirdness") observed three problems
in seed-pinned `watch.py` sims: (1) **jitter-jumping** — bots bounce up/down in place instead
of approaching deliberately; (2) **Lv9 never closes** — a `specials` bot fireball-zones and
never enters melee; (3) a **general fidelity gap**. This ADR is the epic's **architect stage**
(#942, child 3), consuming its two prior child artifacts:

- **#927** — `docs/research/cpu-jitter-jump-findings.md`: the pycats-side **root cause** of the
  jitter.
- **#928** — `docs/research/pm-cpu-behavior-findings.md`: the Brawl-derived **reference model**
  (target behavior) across six axes.

**What those two establish (not re-litigated here):**

- The jitter is a **single root cause** in `AttackerController.decide`
  (`pycats/sim/controllers.py`): the #369 `_jump_up_stuck` "hold `up` for the first
  `JUMP_UP_STUCK_MAX` (90) frames" rule mismanages the jump press edge. A jump needs a fresh
  press edge (`FighterInput.handle_actions`: `pressed = held - prev`) **and** a jumpable state.
  When the initiating `up` press is eaten by a non-jumpable state (a dodge from the #338 evade
  roll, or hitstun), the 90-frame continuous hold blocks any re-press — the bot is stranded
  grounded holding a dead `up`, then late-hops once and repeats. It should instead **re-arm the
  press the instant the fighter becomes grounded-and-jumpable**.
- **Golden-safety constraint:** the jump-toward block is **not** gated on `self.level`, so it
  runs on the level-less chase bot used by many golden/parity tests (`test_dual_controller`,
  `test_bot_match_resolves`, and others). `JUMP_UP_STUCK_MAX = 90` was chosen (#369) to keep the
  first-90-frame window byte-identical to the old always-hold. Any change to that window perturbs
  those goldens unless the change is level-gated.
- The reference model's verdict: pycats' CPU **shape** is faithful across all six axes **except
  Axis 1 (movement/jump)**. Real CPUs approach **grounded** (dash→dash-attack, walk→grab);
  repeated in-place jumping is a documented **flaw** (*"jump continuously in place even if the
  obstacle can be jumped over"*) with **no canon value to preserve**.

The architect ticket posed five decisions. D1 (jump-fix approach) is an architecture fork; D2/D3
are architect calls; **D4 and D5 are game-design-value calls, ratified by the game designer**
(the human) on 2026-07-31, per the repo's "changing values / design decisions" rule.

## Decision

**D1 — Jump fix approach: surgical re-arm patch (not a rewrite).** Keep the #369 pulse structure;
fix only the edge management — re-arm the jump press the instant the fighter is
grounded-and-jumpable after an eaten press, instead of holding `up` dead for ~90 frames. This
directly targets the #927 root cause with minimal blast radius. A principled grounded-default
rewrite was declined for V1: it is a larger bet and the reference model has [GAP]s (no per-level
movement table) that would make parts of it guesswork. The result is **eyeball-gated on
`watch.py`** before close; a rewrite is the fallback only if the patch still reads twitchy.

**D2 — Golden-safety: gate the new re-arm logic to leveled bots** (`self.level is not None`),
mirroring the existing level gates on smash (#714), tilt-convert (#292), and anti-stall (#368).
The level-less default path stays byte-identical → no sim-golden or `test_battle_screen_render`
re-baselining. The jitter only manifests in leveled `watch.py` duels; the level-less chase bot is
a test fixture, not a played opponent.

**D3 — Lv9 no-close (epic problem 2): defer to its own investigate → architect → dev cycle.**
Problem 2 has had **no root-cause investigation** (child 1 covered only the jitter). The repo's
repro/spec-first rule requires an investigation before a DEV fix. This slice stays **Axis-1
(jitter) only**; a separate `[investigate]` child for the Lv9 fireball-zoning no-close is filed
downstream under #925 (one at a time).

**D4 — Edge-hog (#404): revert to canon for V1** (game-designer ruling). Per the documented Brawl
behavior *"CPUs never attempt to edgehog if they're on the stage"*, V1 leveled bots do **not**
contest the ledge. This flips the architect's provisional recommendation (which was to keep the
divergence). Post-V1, intentional, level-scaled edgehogging is a designed goal tracked by a new
epic (see Consequences).

**D5 — "PM-faithful enough" bar: behavioral / eyeball for V1** (game-designer ruling). V1 is
faithful enough when there are no visible glitches (Axis-1 jitter gone), bots approach and use
their kit at appropriate ranges, and difficulty reads as skill — accepted via the human's
eyeball-OK on `watch.py` sims, **not** a metric. This reflects that no PM-specific CPU-AI source
exists (all Brawl-derived) and #928's per-level numbers are [GAP]. A stricter metric-based bar is
a designed post-V1 goal tracked by a new epic (see Consequences).

## Consequences

**DEV decomposition (V1) — filed one at a time downstream under #925, not here:**

1. **Axis-1 jump re-arm (D1).** In `AttackerController.decide` (`pycats/sim/controllers.py`),
   re-arm the jump press when grounded + wanting-up + in a jumpable state + `up` was held last
   frame with no jump — gated to `self.level is not None` (D2). Regression test must be able to
   fail: assert the leveled bot no longer holds a dead `up` across the stuck window (red on the
   current code, green after the re-arm), and assert the level-less golden path is byte-identical.
   Eyeball-OK on the #925 repro (`watch.py --p1-level 7 --p2-level 7 --p1-char nalio --p2-char
   birky --seed 1`) before close.
2. **Revert edge-hog to canon (D4).** Disable the `edge_hog` behavior for V1 in
   `AttackerController` (the `edge_hog` / `_edge_hog_target` path). Because it is off by default
   and `run_battle`'s CPU-vs-CPU path passes no `ledges` (so it is already dead there per #927
   §4), the observable change is confined to leveled duels that do plumb `ledges`; confirm the
   golden/default paths are unaffected. Regression test asserts a leveled bot no longer leaves the
   stage to contest the ledge.

The Lv9 no-close (D3) is **not** in this decomposition — it awaits its own investigate child.

**Two post-V1 epics filed (game-designer requested, 2026-07-31):**

- **#952** — post-V1 intentional CPU edgehogging (research → architect → dev): progressively add
  deliberate, level-scaled ledge contesting. Any edgehog value is a `DIVERGENCE` (canon says
  "never"), not sourced-as-canon.
- **#953** — post-V1 metric-based CPU behavior fidelity (research → architect → dev): raise the
  bar from eyeball to sourced quantitative targets, gated on closing #928's [GAP]s first.

**Trade-offs accepted:**

- V1 leveled bots are **more exploitable at the ledge** (no edgehog) — a deliberate canon-faithful
  floor, with the competent version deferred to #952.
- V1 acceptance is **human-judged, not machine-checked** — fast to ship, but the regression suite
  proves only golden stability, not "looks right"; #953 closes that gap later.
- The surgical patch (D1) fixes the observable jitter but does **not** re-architect the jump
  decision toward a grounded default; if eyeball review finds residual twitchiness, the rewrite
  fallback reopens as a new slice.

**Explicitly ruled out for V1:** a from-scratch controller rewrite; changing the level-less golden
path; any Lv9 no-close fix; inventing per-level movement/reaction numbers (no basis — #928 [GAP]).

## Refs

#925 (epic), #942 (this architect slice), #927 (root cause), #928 (reference model), #952 / #953
(post-V1 epics this ADR spawns), #714 (surfaced the jitter; smash level-gate precedent), #915
(smash-usage policy — separate track), #369 / #367 (jump-toward pulse), #338 (evade roll — the
dodge that eats the press), #368 (anti-stall, ruled out), #404 (edge-hog reverted for V1), #292
(tilt-convert level-gate precedent), ADR-0003 (tuning-data provenance — `FOUND` vs `DIVERGENCE`).
Source: `pycats/sim/controllers.py` (`AttackerController.decide`, `_jump_up_stuck`,
`level_params`, `edge_hog`, `_edge_hog_target`), `pycats/entities/fighter_input.py`
(`FighterInput.handle_actions`), `pycats/sim/runner.py` (`run_battle`).
