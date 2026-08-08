# Spawn + respawn mechanics — one catalog (initial spawn + post-KO respawn) — findings (#1317)

> **Agent:** FIG · **Authored:** 2026-08-07 · **Ticket:** #1317
>
> Canon = **Project M 3.6** (Brawl base; PM restored much Melee behavior). This is the
> **consolidation** child of epic **#1316**: one place that catalogs every **initial-spawn**
> and **post-KO respawn** rule of the parity target, each marked
> **FOUND** / **FOUND-by-engine** / **GUESSED**, with **pycats current state** beside it and a
> match verdict, so the downstream ARC/decision child (#1316 child 2) has a ready gap table.
> It **consolidates, it does not re-derive** the three prior docs — #480 (the ratified model),
> #830 (invincibility validation), #1310 (KO→re-entry delay + display). **Findings only — no
> ruling, no code, no value change.** Every V1 / post-V1 / neither disposition is the decision
> child's job, not this doc's.

## How to read the markers

| Marker | Meaning |
|---|---|
| **FOUND** | Sourced to a primary/secondary the parity work trusts — SmashWiki (series-universal, Brawl included) and/or the meleelight engine, in agreement. |
| **FOUND-by-engine** | Read from the **meleelight** Melee-engine reimplementation (`~/Documents/Study/JavaScript/meleelight/`, local clone #616); PM→Melee is an `[inference]` (strong, not a PM-3.6 primary quote). SmashWiki does not cover the point. |
| **GUESSED** | No primary quote and no engine line pins it — a convention-level or inferred value, flagged so the decision child knows it is soft. |

**Tiering caveat (carried from #830/#1310).** meleelight is a **Melee** reimplementation, so
every engine-only number is Melee→PM `[inference]`. SmashWiki's respawn coverage is
**series-universal** (it does not name PM-3.6-specific values) and its spawn coverage is thin
(most of it is *post-KO*, not match-start). A **Project-M-CC** codeset cross-check (#664) would
upgrade the engine-only rows from `[inference]` to explicit-PM. The pycats-current-state column
is read from source this session (`pycats/entities/fighter.py`, `player.py`, `sim/runner.py`,
`config/render.py`, `config/stage.py`, `combat/provenance.py`) — not from the prior docs.

## Prior art (consolidated here, not restated)

- [`2026-07-03-pm-spawn-respawn-mechanics.md`](./2026-07-03-pm-spawn-respawn-mechanics.md) (#480)
  — reporter-ratified **full-PM revival-platform model**; the design of record. Implementation
  epic **#482** (now superseded into #1316).
- [`2026-07-21-respawn-invincibility-validation-findings.md`](./2026-07-21-respawn-invincibility-validation-findings.md)
  (#830) — validated post-drop invincibility: **120 f flat**, **not** truncated by acting, renders
  as a **blink/flicker** not a solid tint.
- [`respawn-timer-findings.md`](./respawn-timer-findings.md) (#1310) — the KO→re-entry **delay**
  (~2.5 s pre-platform, engine) and the on-screen **display** treatment (no numeric countdown;
  platform + blink + stock text).

---

## Part A — Initial spawning (match start)

The parity target's match-start behavior is the **thinnest-sourced** area: SmashWiki's respawn
pages are almost entirely about *post-KO* re-entry, so most match-start rules are convention-level
(GUESSED) rather than quoted. #480 rated the grounded-start claim "medium-high confidence, not a
quoted frame value."

| # | Rule | Parity target (PM/Melee) | Provenance | pycats current state | Match? |
|---|---|---|---|---|---|
| A1 | **Spawn position** | Fixed per-stage start points on the stage surface | **GUESSED** (convention; #480 "medium-high, not quoted") | Fixed `PLAYER{1,2}_START_{X,Y}` near the thin-platform surface (`config/render.py`, `sim/runner.py`) | ~ (fixed points ✓, see A2 for grounded) |
| A2 | **Grounded vs airborne** | **Grounded** on the stage — not airborne | **GUESSED** (convention; #480) | **Airborne** — `reset_to_spawn` sets `on_ground=False`; fighter drops from `START_Y` | ✗ |
| A3 | **Control at spawn** | Full control from the start | **GUESSED** (convention) | Full — input is live immediately (fighter falls under player control) | ✓ |
| A4 | **Jump count at spawn** | Full jump count | **GUESSED** (convention) | Full — `jumps_remaining = max_jumps` in `reset_to_spawn` | ~ (right count, wrong basis — airborne, so it is *midair* jumps not grounded; see A2) |
| A5 | **Match-start invulnerability** | **None** at match start (respawn invincibility is a *post-KO* affordance, not a match-start one) | **GUESSED** (absence; SmashWiki ties the 120 f window to *respawn*, not match start) | **None** — `invincible_timer = 0`, `intangible = False` after `reset_to_spawn` | ✓ |
| A6 | **Facing** | Fighters face **inward** (toward stage centre / the opponent) at start | **GUESSED** (convention; no SmashWiki quote) | Inward — P1 (left slot) `facing_right=True`, P2 (right slot) `facing_right=False` (`sim/runner.py`); restored from `original_facing_right` on every reset | ✓ |

**Reading of Part A.** pycats matches the parity target on control, no-spawn-invuln, and facing;
the one clear divergence is **grounded (target) vs airborne (pycats)** — A2, which also makes A4's
"full jumps" a right-count-wrong-basis match (grounded-start fighters have their grounded jump;
pycats' airborne-start fighters have only midair jumps until they land). Almost every Part-A row is
**GUESSED** — the match-start rules are the least-sourced part of the whole area and the place a
decision most needs to flag "we are asserting convention, not a quoted PM value."

---

## Part B — Post-KO respawn

This is the deeply-sourced half (three prior docs). The canonical KO→controllable sequence in the
Melee-lineage engine is **DEAD → REBIRTH → REBIRTHWAIT → (leave) → invincible descent**.

### B.1 — Timing (KO → re-entry)

| # | Rule | Parity target | Provenance | pycats current state | Match? |
|---|---|---|---|---|---|
| B1 | **DEAD phase (blast-off / gone)** | ~61 f (~1.0 s), off-screen, uncontrollable | **FOUND-by-engine** (`DEADUP.js` `interrupt()`: `timer > 60`); PM `[inference]` | Part of one invisible 120 f freeze; no off-screen phase | ✗ |
| B2 | **REBIRTH phase (platform descent)** | ~91 f (~1.5 s), descending, intangible | **FOUND-by-engine** (`REBIRTH.js` `interrupt()`: `timer > 90`); PM `[inference]` | none (no platform to descend to) | ✗ |
| B3 | **KO → controllable again** | ~152 f (~2.5 s) sum (DEAD 61 + REBIRTH 91) | **FOUND-by-engine**; PM `[inference]` | **120 f / 2 s** single invisible freeze (`RESPAWN_DELAY_FRAMES = int(2*FPS)`) | ✗ (close in wall-clock, wrong structure) |
| B4 | **Star-KO duration (secondary anchor)** | "often about 2 seconds" (KO-type-dependent; Star/Screen KO slower than blast KO) | secondary, approximate (SmashWiki Star KO) | n/a (no KO-type distinction) | — |

`RESPAWN_DELAY_FRAMES` is registered **TUNED** in `combat/provenance.py` ("pycats respawn freeze
~2s … ruleset value, no canon") — it is a pycats invention, not a sourced canon number, and it is
close to the ~2.5 s engine total only by coincidence of wall-clock.

### B.2 — Revival platform

| # | Rule | Parity target | Provenance | pycats current state | Match? |
|---|---|---|---|---|---|
| B5 | **Platform exists** | Yes — fighter reappears standing on a floating platform above stage centre | **FOUND** (SmashWiki Revival platform + engine) | **None** — fighter drops airborne from `START_Y` | ✗ |
| B6 | **Platform location** | Top-centre, above the stage | **FOUND** (SmashWiki) | n/a | ✗ |
| B7 | **Platform type** | Standable, pass-through (drop-through via down) | **FOUND** (#480 §1) | n/a | ✗ |
| B8 | **Grounded on platform** | Yes → full jump count while on it; leaving forfeits the grounded jump (the #466/#473 rule) | **FOUND** (#480 §5) | n/a (no platform; spawn is already airborne) | ✗ |
| B9 | **Auto-vanish timeout** | **300 f / 5 s** of inaction, then it disappears | **FOUND** (SmashWiki "disappear by itself after 5 seconds" + `REBIRTHWAIT.js` `spawnWaitTime > 300`) | n/a | ✗ |

### B.3 — Intangibility + invincibility

| # | Rule | Parity target | Provenance | pycats current state | Match? |
|---|---|---|---|---|---|
| B10 | **On-platform intangibility** | Intangible the entire time on the platform | **FOUND** (SmashWiki + `hurtBoxStateUpdate` `hurtBoxState=1`) | **None** | ✗ |
| B11 | **What ends intangibility** | Any action (aerial, air-dodge L/R, double-jump, special, stick tilt `>0.3`) **or** the 300 f timeout | **FOUND** (`REBIRTHWAIT.js` `interrupt()`) | n/a | ✗ |
| B12 | **Post-drop invincibility duration** | **120 f / 2 s**, flat (Ultimate's wait-scaled 60–120 **not** adopted) | **FOUND** (SmashWiki Invincibility + `REBIRTHWAIT.js` `invincibleTimer=120` on every leave-path) | **None** — `invincible_timer` cleared to 0 on respawn; the #802 machinery exists but nothing sets it nonzero at spawn | ✗ |
| B13 | **Does acting truncate the 120 f?** | **No** — runs in full regardless of actions (only the *on-platform intangibility* ends on action; the two phases behave oppositely) | **FOUND-by-engine** (`physics.js` unconditional decrement; grep found only `=120` grants and `--`); PM `[inference]` | n/a | ✗ |

### B.4 — On-screen display

| # | Rule | Parity target | Provenance | pycats current state | Match? |
|---|---|---|---|---|---|
| B14 | **Numeric respawn countdown** | **None** — the series never shows "3… 2… 1"; the only visualized respawn timer is Smash 4's platform edge fading yellow→red (still not a number) | **FOUND** (absence across all titles) | none | ✓ (both show no number) |
| B15 | **Revival platform (visual)** | Translucent floating platform, top-centre | **FOUND** (SmashWiki) | none | ✗ |
| B16 | **Invincibility blink/flicker** | Character **blinks** during the 120 f window; meleelight toggles body colour on a **~9 f period** (`render.js` `% 9 > 3`) — blink, not solid tint; intangible & invincible render identically | **FOUND-by-engine** (blink cadence); PM `[inference]` | **None** (`invincible_timer` never set, so no cue renders) | ✗ |
| B17 | **Stock / lives indicator** | Persistent stock icons or a count, always on-screen | **FOUND** (SmashWiki) | **Present** — HUD draws `Lives: N` text (`render/hud.py` `_emphasis_lines`) | ~ (info present; text not head-icons) |

**The #336-vs-#1310 conflict, catalogued (not ruled).** Rows B14 and B16 are the two ends of the
open display conflict the decision child must settle: **#336** proposed a numeric `RESPAWN 1.4s`
countdown on the default HUD; **B14** finds no Smash/PM title shows a respawn countdown, and
**#1310** recommends the platform + blink + stock-text convention instead. Both #1311's minimal-HUD
direction and B14's absence-finding point away from a numeric countdown, but this doc **records the
tension without resolving it** — that is #1316 child 2's ARC/decision job.

---

## Part C — Gap summary (for the decision child)

Ranked by how far pycats sits from the parity target, so the decision child can triage V1 / post-V1
/ neither:

**Clear divergences (target ≠ pycats):**
- **A2 grounded vs airborne match-start** — the one match-start gap; drags A4 (jump basis) with it.
- **B1–B3 the two-phase KO delay** — pycats collapses DEAD+REBIRTH into one invisible freeze;
  ~2.5 s (target) vs 2 s (pycats), wrong structure.
- **B5–B9 revival platform** — entirely absent in pycats (the biggest single feature gap).
- **B10–B13 intangibility + invincibility** — machinery exists (#802 `invincible_timer`,
  tangibility honors it) but nothing grants it on respawn; on-platform intangibility absent.
- **B15–B16 platform + blink render** — no respawn visual cue at all.

**Already matching (no gap):**
- **A3 control at spawn**, **A5 no match-start invuln**, **A6 inward facing**, **B14 no numeric
  countdown**, and (informationally) **B17 stock indicator** via `Lives:` text.

**Soft / least-sourced (flag before ruling):**
- **All of Part A is GUESSED** — match-start rules have no quoted PM value; a decision here is
  asserting convention, and A1/A2 in particular would benefit from a Project-M-CC (#664) check
  before being pinned.
- **B1/B2/B3/B13/B16 are FOUND-by-engine** (Melee `[inference]`) — strong but not PM-3.6-primary;
  the same #664 cross-check would upgrade them.

**Open conflict for the decision child:** the numeric-countdown question (B14 absence + #1310
recommendation + #1311 minimal-HUD) vs **#336**'s owner-agreed countdown. Recorded here; ruled
there.

---

## Sources

- SmashWiki — [Revival platform](https://www.ssbwiki.com/Revival_platform),
  [Invincibility](https://www.ssbwiki.com/Invincibility), [Respawn](https://www.ssbwiki.com/Respawn),
  [Star KO](https://www.ssbwiki.com/Star_KO) (verified 2026-08-07 in #1310)
- meleelight (Melee engine reimplementation, local clone #616) —
  `src/characters/shared/moves/DEADUP.js`, `REBIRTH.js`, `REBIRTHWAIT.js`; `src/main/render.js`;
  `src/physics.js` (`hurtBoxStateUpdate`)
- Prior pycats findings: #480
  ([`2026-07-03-pm-spawn-respawn-mechanics.md`](./2026-07-03-pm-spawn-respawn-mechanics.md)), #830
  ([`2026-07-21-respawn-invincibility-validation-findings.md`](./2026-07-21-respawn-invincibility-validation-findings.md)),
  #1310 ([`respawn-timer-findings.md`](./respawn-timer-findings.md))
- pycats source (read 2026-08-07): `pycats/entities/fighter.py` (`reset_to_spawn`),
  `pycats/entities/player.py` (`reset_to_spawn`, `_handle_death_and_freezes`),
  `pycats/sim/runner.py` (player construction + facing), `pycats/config/render.py`
  (`PLAYER{1,2}_START_{X,Y}`), `pycats/config/stage.py` (`RESPAWN_DELAY_FRAMES`),
  `pycats/combat/provenance.py` (`RESPAWN_DELAY_FRAMES` TUNED)

## Termination

Every initial-spawn (Part A) and post-KO respawn (Part B) rule of the parity target catalogued in
one place, each marked FOUND / FOUND-by-engine / GUESSED with its source, beside pycats' current
state and a match verdict; the gap summary (Part C) triages the divergences and flags the
least-sourced rows and the one open display conflict for the decision child. Consolidates #480 /
#830 / #1310 without re-deriving them. Findings only — no ruling, no code, no value change.
