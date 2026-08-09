# Spawn + respawn — per-rule disposition (V1 / post-V1 / neither)

> **Agent:** FIG · **Authored:** 2026-08-08 · **Ticket:** #1327

Rules every catalogued spawn/respawn mechanic **V1** (close the gap now), **post-V1**
(defer), or **neither** (accept pycats' behaviour / already-parity, no work). This is the
ARC/decision child (child 2 of 3) of epic **#1316**; it **consumes** the two findings docs
(it does not re-derive or re-source them):

- **Part A — match-start spawn:** [`pm-initial-spawn-findings.md`](../research/pm-initial-spawn-findings.md) (#1321)
- **Part B — post-KO respawn + gap triage:** [`spawn-respawn-catalog-findings.md`](../research/spawn-respawn-catalog-findings.md) (#1317)

Dispositions ratified with the reporter (human sign-off, 2026-08-08). Decision doc only —
**no code, and no DEV slices filed from here** (those are child 3, downstream, one-at-a-time).

## Anchor: inherit + correct

The tickets #1316 superseded were closed carrying dispositions; this doc **inherits** those
sides as the default and **re-rules only where the new findings force a change**:

| Superseded ticket (closed → #1316) | Prior side | Carried here as |
|---|---|---|
| **#482** full-PM respawn model (revival platform + intangibility + invincibility) | v1 | **V1** (kept) |
| **#506** respawn invincibility | v1 | **V1** (kept) |
| **#558** PM-faithful invincibility blink/flicker | post-v1 (deferred) | **post-V1** (kept) |
| **#336** numeric respawn countdown | v1 | **neither** (re-ruled — see B14) |

Two corrections the findings force onto the inherited model:

1. **#482's "grounded spawn" plank is void.** #482 listed *grounded spawn* as a V1 goal,
   built on #1317's convention GUESS that the target starts grounded. #1321 re-sourced it
   against the engine: the target starts **airborne** and **pycats already does too**
   (A2 already-parity). There is no grounded-spawn gap to close — that plank is dropped.
2. **#336's numeric countdown is dropped.** #336 (owner-agreed 2026-06-30) put a numeric
   `RESPAWN` countdown on the V1 HUD. Every finding since points the other way
   (B14: no Smash/PM title shows a respawn number; #1310; #1311 minimal HUD). This doc
   **supersedes** the 2026-06-30 agreement — see B14.

## Part A — match-start spawn (all already-parity)

Re-sourcing (#1321) confirmed pycats matches the target on every Part A rule; the one prior
"divergence" (A2 grounded-vs-airborne) dissolved. Recorded here so they are not re-litigated.

| # | Rule | Disposition | Basis (findings row) |
|---|---|---|---|
| A1 | Spawn position (fixed, symmetric, above surface) | **neither** | already-parity — #1321 A1 (FOUND-by-engine) |
| A2 | Airborne start (drops in) | **neither** | already-parity — #1321 A2; **voids #482's "grounded spawn" plank** |
| A3 | Control at spawn — entrance lockout | **neither** | accept pycats' frame-1 control (see below) |
| A4 | Jump count (full, midair-only until landing) | **neither** | already-parity — #1321 A4 |
| A5 | Match-start damage-invulnerability (none) | **neither** | already-parity — #1321 A5 |
| A5′ | Ungrabbable-during-entrance sub-gap | **neither** | rides on A3 (no entrance state) |
| A6 | Inward facing | **neither** | already-parity — #1321 A6 |

**A3 — accept frame-1 control (neither).** The target holds a non-controllable entrance
(~90 f start freeze + 60 f `ENTRANCE` drop) before control; pycats gives control from frame 1.
Ruled **neither**: it is a match-*start* cosmetic with no live-match parity impact, its
90 f + 60 f timing is the **least-sourced number in the whole area** (engine-only Melee
`[inference]`; SmashWiki confirms only that the entrance animation *exists*, not its length),
and it appears in no V1 feature. The A5′ ungrabbable-entrance sub-gap resolves the same way,
since there is no entrance state to host it.

## Part B — post-KO respawn

| # | Rule | Disposition | Basis (findings row) |
|---|---|---|---|
| B1 | DEAD off-screen phase (~61 f blast-off) | **V1** | full two-phase structure — #1317 B1 |
| B2 | REBIRTH descent on the platform (~91 f) | **V1** | inherited #482 — #1317 B2 |
| B3 | Two-phase KO timing (~2.5 s) | **V1** (structure) | replaces the 2 s freeze — #1317 B3; **frames `[inference]`, re-source before hard-coding** |
| B4 | Star-KO duration (KO-type-dependent) | **neither** | no KO-type distinction; informational — #1317 B4 |
| B5–B9 | Revival platform (exists, top-centre, pass-through, grounded-on-it, 300 f auto-vanish) | **V1** | inherited #482 — #1317 B5–B9 |
| B10–B11 | On-platform intangibility (+ what ends it) | **V1** | inherited #482 — #1317 B10–B11 |
| B12–B13 | Post-drop 120 f invincibility (not truncated by acting) | **V1** | inherited #506 — #1317 B12–B13; **V1 cue = solid tint** (see below) |
| B14 | Numeric respawn countdown | **neither** | dropped — no title shows one; **supersedes #336** — #1317 B14 |
| B15 | Revival platform (visual) | **V1** | needed to see the platform — #1317 B15 |
| B16 | Invincibility blink/flicker render | **post-V1** | inherited #558; V1 uses a tint instead — #1317 B16 |
| B17 | Stock / lives indicator | **neither** | info present as `Lives:` text; head-icon styling → post-V1 HUD polish (#550/#551) — #1317 B17 |

**B3 timing — the two-phase structure is V1, the exact split is `[inference]`.** V1 replaces
pycats' single ~2 s invisible freeze (`RESPAWN_DELAY_FRAMES`, registered **TUNED** in
`pycats/combat/provenance.py`) with the two-phase DEAD → REBIRTH re-entry. The 61 f / 91 f
split is engine-only Melee inference with no PM-3.6 primary; the V1 slice that hard-codes it
**must re-source the exact frames** (ideally a PM-3.6 primary / frame-data capture) first.

**B12–B13 invincibility cue — tint in V1, blink post-V1.** Post-drop invincibility is
**functional in V1** (#506). Its render splits by surface:

- **Default HUD (V1):** a **solid tint** — pycats' existing convention for invuln/intangible
  states. An intentional non-parity simplification (the target *blinks*, per B16).
- **`--dev` mode only (V1):** the invincibility window may surface as a `STATUS_SOURCES`
  timer-bar, reusing the #531 ledge-invuln pattern — a dev affordance, not on the default HUD.
- **Post-V1:** the PM-faithful **blink/flicker** render (B16) is the deferred polish, tracked
  by **#558**.

## V1 DEV-slice pointers (child 3 — NOT filed here)

Child 3 files these downstream, one at a time. Pointers only:

1. **Revival platform + two-phase KO re-entry** — replace the ~2 s freeze with DEAD (off-screen)
   → REBIRTH (platform descent); the platform (B5–B9, B15) + its descent (B2) + the timing
   structure (B1, B3). **Precondition:** re-source the exact frame split first (B3 note).
2. **On-platform intangibility** (B10–B11) — intangible while on the platform; ends on
   action or the 300 f timeout.
3. **Post-drop invincibility + tint cue** (B12–B13) — grant 120 f invincibility on platform
   dismount, not truncated by acting; render as a solid tint on the default HUD.
4. **(dev-mode) respawn-invuln status timer-bar** — one `STATUS_SOURCES` entry, #531 pattern,
   `--dev` HUD only.

Post-V1 parks (already tracked, not re-filed): **#558** invincibility blink; the A3 entrance
state (if ever revisited).

## Follow-up (noted, NOT filed here)

The parity register `docs/project-m-rules-by-category.md` still carries the pre-decision
respawn rows (*"unimplemented (#506, epic #482)"*, `RESPAWN_DELAY_FRAMES` TUNED). A **WRITER
slice** should refresh those rows to cite these dispositions once the child-3 DEV slices are
filed (so each row points at a live ticket, not a doc). Out of scope for this decision ticket;
file downstream, one at a time.

## Out of scope

- Re-deriving or re-sourcing any rule — the findings docs (#1317/#1321) are the inputs.
- Filing or implementing DEV slices — child 3, downstream.
- The general intangibility/invulnerability model (#527/#772) — this consumes their conclusions.

## Refs

Parent **#1316** (child 2 of 3). Inputs **#1321** (Part A), **#1317** (Part B). Superseded by
#1316: **#482** (kept V1, grounded-spawn plank void), **#506** (kept V1), **#336** (→ neither),
**#558** (kept post-V1). HUD context **#1311**, **#531**, #550/#551. Adjacent (consumed, not
re-derived) **#527**, **#772**. Consolidated prior research #480, #830, #1310.
