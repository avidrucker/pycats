# TIL 2026-06-29 — CHERRY

**Context:** A long session that finished **Phase 1 combat core** (#38: multi-hitbox #130, Nalio 3-box dtilt #132, clank #133, ground/air split + nair #136, hitlag #138, shieldstun #140), started **Phase 2 moveset** (epic #142, move-selection seam #143), and authored the **entire 13-doc Project M mechanics reference** (epic #147, docs #149–#175). Lessons below are the ones I'd want on a cold read next time.

---

## 1. A vanished KO in a golden isn't automatically a regression — investigate

**What happened:** Hitlag (#138) churned the goldens as expected (hits now insert freeze frames before launch). Two scenarios were textbook — every KO preserved, all shifted *later*. But `combat.summary.json` showed a **red flag**: P1's frame-267 KO **disappeared** and its `lives_end` rose 2→3. The REGEN_PROTOCOL explicitly calls a vanishing KO "almost always a regression."

**What I learned:** The protocol flag is a *prompt to investigate*, not a verdict. The decisive evidence was one field: P1's `percent_max` was **0 in both baselines** — P1 was never hit, so its old KO was a **self-destruct** (the attacker walking off the ledge). Hitlag now freezes the attacker ~8 frames per hit, so it advances less and stays on stage. Meanwhile P2 (the real target) still KO'd, later, and took *more* damage. Combat got *stronger*, not weaker — the opposite of what the flag suggested at a glance.

**The rule:** **When a semantic golden regen trips a red flag, find the field that explains it before judging — a vanished KO with 0% damage is a self-destruct, not weaker combat.** (Authority: `tests/golden/REGEN_PROTOCOL.md` already mandates "identify the cause"; this is that step done for real.)

---

## 2. In fleet mode, run the full suite the instant you claim

**What happened:** Mid-session, a fresh worktree was already on a **red `main`**: ELDERBERRY's #124 (crouch) had added `defender.state == "crouch"` to `process_hits`, which `AttributeError`'d the stub-based combat tests I'd merged earlier in #130/#133. Their branch predated my tests, so the merge gate never ran them together. I caught it only because I ran the suite right after claiming.

**What I learned:** A `pmtools` worktree is cut from `main` at claim time, so you inherit whatever red another agent just merged — and your "new" failures may not be yours. Per merge-gate discipline I fixed `main` first (filed `severity:high` #137, made the crouch read defensive, closed it), then `git merge origin/main` to pull the fix into my in-flight worktree before continuing.

**The rule:** **After every claim, run the full suite to establish a baseline; if it's red and not from your change, fix `main` first (own ticket) before your slice.** (Authority: saved to agent memory `fleet-merge-race-run-suite-early`; pairs with the merge-gate rule.)

---

## 3. Shared engine code must read the optional Player surface defensively

**What happened:** The same root cause bit twice. #137: `process_hits` assumed `defender.state` exists. #143: the new move-selection seam read `controls["special"]`, which `KeyError`'d on the **16 test control maps** that omit it. Both were fixed with `getattr`/`.get` — an unbound action is simply "unpressable"; a defender without `.state` is "not crouching."

**What I learned:** `process_hits` and `fighter_input` are exercised by lightweight stubs that model a *documented minimal contract*, not the full `Player`. Any new read of an optional attribute on those paths is a latent break waiting for the next stub-based test.

**The rule:** **In combat/input code reached by test stubs, read optional Player/control attributes via `getattr`/`.get`, never assume the full surface.** (Authority: encoded in the code itself via #137/#143; candidate for a RULES.md note — flagged here as the follow-up.)

---

## 4. The repeatable doc loop: file → /issue-review → claim → write → close → tick

**What happened:** 13 reference docs, each run through the identical loop: draft a ticket with the full quality kit (Audience, reference-depth guardrail, named sources, machine-verifiable acceptance incl. the index-row flip), run `/issue-review-skill` (every one scored READY 15/15 once the kit was standard), claim a worktree, write, verify links + suite, commit `Closes #N`, `pmtools close`, then tick the epic index row.

**What I learned:** Convergence is the win. After the first review flagged a missing **Audience** line and a **depth guardrail**, baking those into the template meant every later ticket passed cleanly — the review stopped finding structural gaps and started giving *write-time* guidance (which doc owns which boundary). A consistent template turns review from gatekeeping into calibration.

**The rule:** **Once a review surfaces a structural gap, fold the fix into your ticket template so the next N tickets inherit it — don't re-discover it.** (Authority: the `issue-review-skill` docs rubric; this session's #149→#175 cadence.)

---

## 5. In a multi-doc set, boundary discipline beats completeness

**What happened:** The biggest recurring review note across the reference set wasn't "missing content" — it was **doc-to-doc overlap**. character-data vs moveset-and-frame-data (structure vs values), ledge-mechanics vs stages-and-environment (interaction vs geometry), grabs/throws vs combat (throw KB), menus vs stages (stage select vs stage geometry). Each ticket pre-declared a "Boundary discipline" line naming exactly which sibling owns what, and footers **linked rather than restated**.

**What I learned:** A reference set's value comes from each doc having **one** job and cross-linking the rest. Two docs that both half-explain knockback are worse than one that owns it and one that links it. Also: **fold in existing research, don't duplicate it** — every doc cited `docs/research/*` instead of copying, so there's one source of truth per fact.

**The rule:** **In a multi-doc set, give each doc one concern, cross-link siblings, and fold in prior research rather than restating it.** (Authority: `docs/pm-reference/00-overview.md` codifies the per-doc template + footer contract.)

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/combat/` + `systems/combat.py` | Phase-1 combat core complete: multi-hitbox, clank, hitlag, shieldstun (#38 closed) |
| `pycats/combat/move_select.py` | Move-selection seam — direction×ground/air×A/B + the B button (#143) |
| `pycats/characters/nalio_cat.py` | Nalio real 3-box d-tilt (#132) + neutral-air (#136) |
| `docs/pm-reference/` (13 files) | Complete PM mechanics reference (epic #147 closed) |
| #137 | Mid-session `main`-red fix: defensive crouch-state read in `process_hits` |

## Open threads

- **Defensive-read rule** (lesson 3) lives only in code + this TIL — candidate for a RULES.md line on shared combat/input contracts.
- Phase 2 moveset (#142) is open: ground normals, aerials, specials scaffold, stale-move negation remain.
- Schema gap noted in several docs: one `startup/active/recovery` window per `MoveData` can't express sequential multi-hit (jab1-2-3, rapid jab, multi-hit d-air).

## Related artifacts

- Epics #38 (Phase 1, closed), #142 (Phase 2), #147 (reference, closed)
- Decision recorded #14: thin platforms aren't ledge-grabbable (PM parity)
- `tests/golden/REGEN_PROTOCOL.md`; sibling TIL [2026-06-26 CHERRY](./today-i-learned-2026-06-26-cherry.md)
