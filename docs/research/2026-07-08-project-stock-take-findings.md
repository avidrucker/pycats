# Project stock-take — active work-threads, themes & per-lane focus

> Findings doc for **#719** (RESEARCH, `area:tracker`). A point-in-time **snapshot** of what
> pycats is working on as of the date below. Every ticket reference is grounded in a live
> `gh issue list` pull taken while writing this doc — but the queue moves fast (fleet mode),
> so treat this as **perishable**: re-run the pull before relying on any single `#N` state.
>
> **As-of:** 2026-07-08 · **Author:** GRAPE · **Method:** `gh issue list --state open --limit 100`
> + recent-closed momentum scan + the epic/umbrella bodies.
>
> Relationship to **#185** ("orientation map — live"): #185 is the older *pointer* map
> (filed 2026-06-29) and is now **stale** — it still headlines the statecharts screen-flow
> port (#100) and Phase-2 moveset (#142) as the lead arcs and references closed umbrellas
> (#13/#14 ledge, #56/#99 parity). This doc is the fresh snapshot; see **§4 Candidates** for
> the recommendation on reconciling the two.

---

## 1. The active threads (high level)

Eleven threads are in motion. Ordered roughly by recent commit/close momentum, not priority.

| # | Thread | What it is | Primary lane(s) | Heat |
|---|--------|-----------|-----------------|------|
| A | **Domain decomplect** — skin/palette/character/selection (DDD + hexagonal) | Unbraid `char_name`'s four jobs; real named Characters + Skins; retire the testcat shim | entities, screens, display | 🔥 hot |
| B | **game.py shell modularization** | Extract DisplayManager / GameShell / `step()` seam so the top loop is testable | screens | 🔥 hot |
| C | **CPU opponents, AI & balance sim** | Lv1–9 difficulty, in-game Human/CPU selection, round-robin balance matrix | combat, screens, watch | 🔥 hot |
| D | **PM data-verification & decision/value churn** | Source-verify guessed values against primaries; ledger the decisions; cut churn | tracker, combat | 🔥 hot |
| E | **The five PM-archetype cat fighters** | Nalio/Birky/Narz (+2) as Mario/Marth/Kirby/DK/Fox; the v1 headline arc | combat, entities | 🌡 warm |
| F | **Font / text / HUD legibility** | Font-stack hardening (done), HUD hierarchy, background-independent legibility | display | 🌡 warm |
| G | **Ledge / respawn / entity-state mechanics** | Ledge regrab-invuln, respawn invincibility, movement layer, intangibility model | entities, display, combat | 🌡 warm |
| H | **Input architecture, controls & profiles** | N-controller backends, keyboard scope, user profiles + keybindings | entities, screens | 🧊 cool |
| I | **Screens / menus / UX polish** | Feedback cues, audio decision, char-select display, changelog, stats screen | screens | 🧊 cool |
| J | **Showcase & tutorial sims** | Choreographed Nalio-vs-Birky demo; in-app tutorial simulations | watch | 🧊 cool |
| K | **Docs / contributor DX / process tooling** | Custom-mechanics doc, claim-ledger skill, PDD gap, code-anchor convention | docs, tracker | 🌡 warm |

"Heat" = recent close/commit activity in the last ~2 weeks, not importance. A cool thread can
still be v1-critical (e.g. much of the fighters arc is gated, not abandoned).

---

## 2. Per-thread detail — major items, status, settled decisions

Status legend: **open** · **blocked** (`blocked` label) · **epic** (container) · **decision**
(needs human routing) · **✅** (recently closed, carried as settled).

### A — Domain decomplect (skin / palette / character / selection)
The most active refactor of the last two weeks. A `/decomplect` + `/grill-me` session
(2026-07-06) produced the handoff → spike **#673** ✅ → spec **#675** ✅, then a phased
hexagonal migration.
- **#672** — epic (`research,area:entities,area:tracker`). Open, nearly complete.
- Phases landed ✅: #686 (rewire build_players/create_from_selection), #692 (repoint char_name's
  3 Player seams), #694 (placeholder flat-gray cat), #695 (`PlayerSnap.character` field), #696
  (Phase 2b default golden flip to Nalio).
- **#706** — open. Phase 2c: flip the `full_match` golden to Nalio (chase vs idle).
- **#689** — **blocked** (`research,area:screens`). Re-audit the #680 domain ↔ #682 char-select
  cosmetic seam *after* #672 closes.
- **#718** — open. 2nd sim player must default to a distinct skin (two same-character fighters
  render identically today).
- **#677** — open. Base/starting Skin colour-theme per Character (Nalio red-blue, Narz blue-black,
  Birky pink-red).
- **#676** — open. Recolor the char-select tile with the cycled skin; retire the external preview cat.
- **Settled:** the ubiquitous-language model (Skin / Character / Selection / PlaceholderSkin), the
  three Player seams (number → colour + name), and the row-key-stays-slot snapshot decision (#675 spec).

### B — game.py shell modularization
A clean, near-finished decomposition of the untestable top-level loop.
- **#687** ✅ — spike proving feasibility.
- **#698** ✅ (C1) DisplayManager · **#701** ✅ (C2) `main()` + `__name__` guard · **#707** ✅
  (C3) App/GameShell + `step()` seam.
- **#18** — open. Scope & complete the screen system (manager + transitions) — the remaining umbrella.
- **Settled:** the display/input shell is now an injectable object with a `step()` seam; the loop no
  longer runs at import (closes the long-standing dispatch blindspot).

### C — CPU opponents, AI & balance sim
- **#231** — epic (`area:combat`). CPU difficulty Lv1–9 + named-character match setup.
- **#702** ✅ research · **#703** ✅ curve interpolation · **#704** ✅ decision (near-miss +
  accidental-press human-error direction approved).
- **#714** — open. Teach the CPU AttackerController to commit smash attacks (kill-confirm).
- **#691** — epic (`area:screens`). In-game per-slot Human/CPU selection + level, reusing #231's controllers.
- **#684** — open (`area:watch`). Round-robin CPU-vs-CPU balance sim (seeded matchup matrix).
- **#619** — epic (`area:watch,post-v1`). In-app tutorial simulations.
- **Settled:** the CPU human-error model (#704); the level-curve interpolation shape (#703).

### D — PM data-verification & decision/value churn
The process/rigor backbone. Two umbrellas + a ledger effort.
- **#638** — epic (`research,area:tracker`). PM primary-source verification pass — build a dump
  capability, then source-verify rules/values/metrics.
- **#631** — umbrella (`research,area:tracker`). Quantify & mitigate decision/value churn; **#651**
  child — diagnose churn causes + propose guardrails.
- **#705** ✅ Decision-Log ledger + ADR · **#712** ✅ / **#713** ✅ PCS-ID grounded-claim ledger.
- **#721** — epic (`enhancement,area:tracker`). Build the claim-ledger skill + tooling (execute #712's ruling).
- **#517** — open. Audit all TIL docs against RULES.md (codified vs orphaned lessons).
- **#503** — open. Assess the PDD (puzzle-driven-development) gap vs lccjs.
- Open **combat decisions** awaiting human routing: **#491** (DOUBLE_TAP_WINDOW), **#242**
  (air-dodge intangibility window), **#65** (dodge speed/duration), **#66** (shield-then-direction
  air dodge), **#288** (cross-cutting-concerns catalog), **#554** (keyboard-control scope).

### E — The five PM-archetype cat fighters (v1 headline)
Mostly **gated** on the moveset seam and per-archetype engine prereqs, hence "warm not hot."
- **#117** — epic parent (`area:combat,v1`). Five cats as Mario/Marth/Kirby/DK/Fox.
- **#142** — epic. Phase 2 moveset (move-selection seam + Nalio's data-driven kit).
- **#294** — epic. Narz (Marth archetype, disjointed swordfighter).
- **#228** — epic parent. Birky (Kirby archetype, floaty featherweight); **#261** — Birky's remaining
  non-data engine prereqs (fast-fall, specials, selectability).
- **#566** — tracker. Complete the 3 selectable archetypes (Nalio / Birky / Narz).
- **#271** — tracker. Source/playtest the guessed Nalio-fireball projectile constants; **#192** —
  replace guessed air-dodge values; **#243** — per-character waveland traction.

### F — Font / text / HUD legibility
- ✅ recently: **#709** (font-factory test-isolation leak), **#711** (pygame font-usage guide), plus
  the #550 HUD visual-hierarchy work.
- **#551** — open. Background-independent HUD legibility (text shadow/backplate).
- **#336** — open. Respawn countdown indicator near the stock/damage HUD.
- **#241** — **blocked**. Revert hit/hurtbox overlay to default OFF before release.
- **Settled:** single-source font sizes in `config.py`; `scaled_font_size` chokepoint; the
  cached-fake leak guard (`_no_fake_fonts_leaked`, RULES.md).

### G — Ledge / respawn / entity-state mechanics
- **#267** — epic (`area:entities,v1`). PM ledge mechanics v1 follow-ups.
- **#482** — epic. Full-PM respawn model (revival platform + invincibility + grounded spawn).
- **#720** — architect (`area:docs,v1`). Single spec for ledge-regrab invuln cutoff + HUD, governing
  **#656/#657/#658** (grab-invuln / grabs-left dots — #657/#658 **blocked** on the spec).
- **#506** — **blocked**. Respawn invincibility (slice 1 of #482). **#539** — validate PM
  respawn-invincibility. **#527** — architect the two-layer intangibility model.
- **#388** — epic. Basic walk/dash/run movement layer. **#603** — crawl (post-v1).
- **#400** — **blocked**. Hit on a vulnerable ledge-hanger → knockback. **#613** — research: can a
  fighter be dizzy while airborne? **#683** ✅ — flat 21f ledge invuln (dropped percent-scaling).

### H — Input architecture, controls & profiles
- **#476** — epic (`research`). PM input-handling parity (taxonomy + architecture plan). **#553** /
  **#555** — controls catalogue + N-controller (keyboard + GameCube backends). **#554** — decision:
  keyboard-control scope.
- **#438** — epic. User profiles & custom keybindings. **#479** — profile create/select UI in
  char-select. **#442** — **blocked**. Stats logging for saved profiles.

### I — Screens / menus / UX polish
- **#544** — epic (`post-v1`). a11y/UX polish follow-ups from the #346 audit.
- **#354** — research/proposal: adopt lccjs zero-dep system sound + menu polish; **#445** — decision:
  adopt an audio subsystem? **#361** — menu activation feedback. **#391** — colour toggles by state.
- **#460** — dedicated end-of-battle stats screen. **#134** — in-app changelog screen. **#663** —
  replace modal start overlay with a below-grid message. **#682** ✅ / **#416** — char-select
  per-player display + focus feedback. **#127** — epic: alt skin/palette selection per character.

### J — Showcase & tutorial sims
- **#308** — epic (`area:watch,v1`). Captioned Nalio-vs-Birky showcase demo. Beats: **#428**
  (aerials), **#430** (defensive options), **#431** (ledge-getup variants).
- **#619** — epic (`post-v1`). In-game tutorial simulations.

### K — Docs / contributor DX / process tooling
- **#604** — parent. `custom-pycats-mechanics.md` (precedence + invented/divergent mechanics).
- **#168** — epic. Architecture-review follow-ups (docs seeding + deferred decisions).
- **#337** — convention: cite code anchors by file+symbol, not line numbers (partly ratified in RULES.md).
- **#493** — adopt statecharts-py as a pip package (not `-e` local path). **#50** — migrate free-form
  `#### TODO:` comments to PDD `@todo #N` / delete.
- ✅ recently: **#710** (CPU-AI PM reference doc), **#711** (font guide), **#713** (PCS-ledger doc).

---

## 3. Lane index (area:* → threads)

Cross-reference for fleet assignment. A thread can span lanes; listed under its primary.

| Lane | Threads present | Notable open anchors |
|------|-----------------|----------------------|
| `area:combat` | C, D, E, G | #231, #117, #142, #294, #228, #714, #684 |
| `area:entities` | A, E, G, H | #672, #482, #267, #388, #476, #527 |
| `area:screens` | B, C, H, I | #18, #691, #438, #544, #127, #689 (blocked) |
| `area:display` | A, F, G | #551, #336, #656/#657/#658, #241 (blocked) |
| `area:watch` | C, J | #684, #308, #619 |
| `area:docs` | K | #604, #168, #720, #493 |
| `area:tracker` | D, K | #638, #631, #721, #517, #503, #566, #337 |

---

## 4. Candidates for a downstream grooming pass (Q5)

Flagged only — **not** acted on here (this is a research ticket). File/close/relabel one-at-a-time
downstream per RULES.md.

1. **#185 is stale — refresh or supersede.** Its "live orientation map" still headlines the
   statecharts screen-flow port (#100) and Phase-2 moveset as the lead arcs and references closed
   ledge/parity umbrellas. Options: (a) rewrite #185's body to point at this snapshot's threads, or
   (b) close #185 and adopt a dated-snapshot cadence (this doc) instead of a "live" ticket that rots.
   *Recommend (a)* — keep one lightweight pointer ticket, repoint it, and link this doc.
2. **Decision backlog is large and unrouted.** Six open combat/entities decisions (#491, #242, #65,
   #66, #288, #554, plus #445 audio) need human routing. Candidate: a single decision-triage session
   (`guide-human-decision`) to clear or defer the batch — churn thread #631 exists precisely to
   reduce this cost.
3. **Blocked cluster around ledge/respawn HUD.** #657/#658 are blocked on the #720 architect spec;
   #506 on #482; #400 on #267. #720 is the unblock lever — sequencing it first frees three tickets.
4. **Possible thread consolidation — process tooling.** #638 / #631 / #651 / #712→#721 / #705 /
   #503 / #517 all orbit "rigor & anti-churn." They are legitimately distinct efforts but could share
   one umbrella index for visibility. Candidate for a tracker-lane grooming note, not a merge.
5. **Verify "epic possibly-complete."** #672 is nearly done (only #706 + blocked #689 remain);
   #142/#117 are long-lived. Worth a per-epic child-checklist verify to confirm none are closable.

---

## 5. Proposed follow-ups (listed, none filed by this ticket)

- **DOCS/tracker:** refresh #185 to point at this snapshot (candidate 1).
- **DECISION:** batch decision-triage session for the six unrouted combat/entities decisions (candidate 2).
- **SEQUENCING:** prioritize #720 (architect spec) to unblock #657/#658 (candidate 3).
- **RESEARCH cadence:** decide whether to re-run this stock-take on a fixed interval or on-demand
  (candidate 1's option b).

Each is filed one-at-a-time downstream of this doc, only on an explicit go-ahead.
