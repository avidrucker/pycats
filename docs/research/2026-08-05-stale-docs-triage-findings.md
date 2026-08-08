# Stale / low-value docs — triage findings (2026-08-05)

**Status:** findings — triage only, **no deletions performed**. Closing artifact for **#1260**
(`chore(docs): audit + triage stale/low-value docs for pruning`). Every removal below is a
*proposal*; the destructive step waits on human sign-off and lands downstream, one ratified set at a
time (mirrors the "don't delete what you didn't author without confirmation" rule).

## Method

Swept all 346 tracked `*.md`. Signals gathered: last-commit date, line count, **inbound-reference
count** (basename grep across every tracked `.md` + `.py`, minus self), plus per-doc reads verifying
the staleness claim against `gh` issue state and current code. Five clusters were investigated in
parallel; each candidate carries a **verbatim** staleness quote.

**Higher bar applied (per the ticket):** the authoritative homes (`RULES.md`, `README.md`,
`CLAUDE.md`, `docs/mechanics-index.md`, `docs/project-m-parity.md`, `docs/banned_words.md`,
`CONTEXT.md`, ADRs) and the **dated archive** (`docs/learnings/**` TILs, dated `docs/research/**`
findings) are default-**keep** — proposed for removal only with specific evidence of supersession or
error, never merely "old."

## Summary

| Bucket | Count | Destructive? | Gate |
|---|---|---|---|
| **A — Prune** (spent one-off, work shipped/closed, no durable content lost) | 11 | yes | human ratify → downstream `git rm` |
| **B — Merge-forward** (superseded, fold the salvage part) | 1 | yes | human ratify |
| **C — Relocate** (misfiled, *not* low-value — companion cleanup) | 10 | no (move) | separate follow-up; needs link-rewrite |
| **D — Keep-but-drifted** (refresh, *not* removal — adjacent) | 3 | no (edit) | out of this ticket's prune scope |
| **Keep** (verified, no action) | ~320 | — | — |

The dated archive (`docs/research/` 183 + `docs/learnings/` 58 = 241 files) is default-keep: a
same-topic-pair + self-declared-supersession sweep found **one** whole-doc supersession (Bucket B);
every other supersession marker is an inline correction banner inside an otherwise-valid point-in-time
artifact — self-annotated history, which the repo's own `pycats-code-review-2026-08.md` prescribes
keeping over deleting.

---

## Bucket A — Prune candidates (high confidence)

Each: tracking issue **CLOSED** (or a pre-tracker one-pass artifact), **0–1 inbound**, and any durable
finding already preserved in code, a TIL, or a retained design spec.

### A1. Retired kaomoji / emoji face-render exploration (3 docs)

The kaomoji/emoji skin these explored **shipped in #108, then was retired in #114** in favor of pure
ASCII. `pycats/ui/cat_faces.py` records the outcome verbatim:

> `The retired kaomoji/emoji glyph styles (ᓚᘏᗢ / (=^･ω･^=) / 🐱) are gone (#114, superseding #103/#105).`

The one durable capability finding ("colour emoji renders in pygame"; "flip the *surface*, not the
*characters*") survives in `docs/learnings/today-i-learned-2026-06-26-dragonfruit.md` and in the
shipped code.

| Path | Inbound | Staleness signal | Rec |
|---|---|---|---|
| `docs/kaomoji-research.md` | 0 | Bare glyph collection "for reference, testing, and fun"; no ticket tie, no code consumer; the kaomoji it lists were retired in #114. | prune |
| `docs/research-findings-cat-ascii-emoji-103.md` | 0 | #103 CLOSED; lead rec "**Lead with a tintable kaomoji skin**" was built (#108) then reversed (#114). Durable finding preserved in the 06-26 TIL. | prune |
| `docs/research-findings-directional-kaomoji-105.md` | 0 | #105 CLOSED; recommended `ᓚᘏᗢ (tinted per cat)` is named among the retired styles in `cat_faces.py`. Surface-flip lesson preserved in the TIL + code. | prune |

> **Kept from the same cluster:** `docs/research-findings-110-cat-kaomoji-ascii-heads.md` is **not**
> superseded — its two ASCII blocks are the *live* shipped art (`_ASCII_PROFILE_LINES` /
> `_ASCII_34_LINES` in `cat_faces.py`). It is the design record for the current faces. **Keep**
> (see Bucket C: it is also misfiled and could relocate).

### A2. Point-in-time test snapshot (1 doc)

| Path | Inbound | Staleness signal | Rec |
|---|---|---|---|
| `docs/snapshot-current-tests-overview.md` | 1 | Self-labeled `Snapshot as of 2026-07-04` — `**~1,088 tests across 179 files**` and `Only **1 of 179 files** uses a mock`. Live `find tests -name 'test_*.py'` → **297** files. Every count is ~1.5–2× off. | prune |

Its evergreen explainer (monkeypatch pattern, the meaning of `x` in test IDs) is the only salvage and
could fold into a living test doc; the counts-driven body is a spent snapshot.

### A3. Spent one-pass execution plans + one seeding scaffold (7 docs, `docs/superpowers/`)

`docs/superpowers/plans/` holds dated one-pass DEV plans; a plan whose issue **closed** is spent. The
matching **design-of-record specs are all kept** (Bucket "Keep") — only the execution scaffolding
prunes.

| Path | Staleness signal (issue state via `gh`) | Rec |
|---|---|---|
| `plans/2026-06-21-pm-phase0.md` | Pre-tracker; the "parity-oracle flip" it scopes shipped (statechart is now the primary engine). 0 inbound. | prune |
| `plans/2026-06-21-statecharts-benchmark.md` | Pre-tracker; "Default backend is `legacy`" — statechart since became primary. 0 inbound. | prune |
| `plans/2026-06-24-phase1-knockback-foundation.md` | `#40 CLOSED … pycats/combat/knockback.py`; spec #39 + umbrella #38 CLOSED. 0 inbound. | prune |
| `plans/2026-06-30-ledge-hang.md` | `#14 CLOSED Add ledge-hang state`. Lone inbound is a see-also pairing it with the retained spec+test. | prune |
| `plans/2026-07-06-fixed-burst-ledge-invuln-dev-plan.md` | `#683 CLOSED … flat 21f fixed burst`; spike #552 + decision #543 CLOSED. Lone inbound is a historical TIL. | prune |
| `plans/2026-07-06-grounded-claim-protocol-mvp.md` | `#624 CLOSED … Grounded-Claim Protocol MVP`; the skill + `.claude/evidence.json` shipped. 0 inbound. | prune |
| `specs/2026-06-22-issue-migration-draft.md` | Body: "REVIEW BEFORE CREATION… Nothing is created until you approve this list… then I run `gh issue create` per approved block." One-time issue-seeding scaffold; repo is now >#1200. 0 inbound. | prune |

> **Kept from this cluster:** `plans/2026-07-04-ruff-rule-expansion.md` — self-labeled discretionary
> optional-polish backlog tied to ADR-0006; retains the measured rule counts + child sequence.
> **Flag:** its parent epic **#505 is now CLOSED**, so confirm the optional backlog is still wanted
> before keeping long-term. All 8 `docs/superpowers/specs/` design docs are design-of-record
> (referenced by tests / `RULES.md` / skills) → keep.

---

## Bucket B — Merge-forward (1 doc)

| Path | Staleness signal | Rec |
|---|---|---|
| `docs/research/cpu-jitter-jump-findings.md` | Successor `cpu-jitter-jump-v2-findings.md` (#966) header: `> **Supersedes the root cause in [#927]** … and the fix approach in **#959 / ADR-0010 D1**`; its TL;DR: "neither is the eaten-press lock #927 root-caused." | merge-into `cpu-jitter-jump-v2-findings.md` |

**Soft flag.** v2 already links back to v1 with a correction note on #927. Under the fleet convention
(keep superseded artifacts annotated), the strictly-accurate call is: fold v1's reusable
repro/instrumentation template into v2, then remove v1 — **or** leave v1 in place with its annotation.
This is the only archive doc where a later doc redid the scope and refuted the central conclusion.

---

## Bucket C — Relocate, not prune (companion cleanup; **no removals**)

Nine `research-*` / `research-spec-*` docs (plus kept `-110` from A1) sit **loose in `docs/` root**
instead of the `docs/research/` archive — a **legacy location**, not a per-doc accident. **None are
prune-worthy:** each is a CLOSED-ticket closing artifact, several cited from **code**. Surfaced here so
the misfiling gets a deliberate follow-up, but it is a **move**, gated on rewriting the inbound links.

| Path | Why keep / provenance | Live inbound to rewrite on move |
|---|---|---|
| `docs/research-120-smash-units-and-sources.md` | Foundational (PX_PER_UNIT≈5.4, raw-combat rule); heaviest footprint. | `pycats/combat/provenance.py`, `pycats/config/physics.py`, `parity-status.md`, ~15 docs |
| `docs/research-spec-675-skin-char-model.md` | Ratified design for shipped `pycats/loadout/`. | `pycats/loadout/__init__.py` |
| `docs/research-spec-119-mario-cat-pm.md` | Nalio provenance (down-tilt PM3.6 values). | 5 docs (incl. spec-290) |
| `docs/research-spec-290-narz-marth-pm.md` | Narz provenance (tipper = tuple-order). | `docs/research/2026-08-04-dancing-blade-mechanic.md` |
| `docs/research-spec-328-smash-charge.md` | Charge/smash input-seam + schema decisions (no `docs/research/` duplicate). | — |
| `docs/research-spec-794-gnok-dk-pm.md` | Gnok body-geometry ratification; sibling of `docs/research/gnok-dk-pm-data-findings.md`. | — |
| `docs/research-spec-199-ice-scoring.md` | Design/rubric for shipped `stats/ice-scores.csv` (wired in `orchestrate.json`). | `escalation-rubric-findings.md` |
| `docs/research-findings-141-clank-priority-…-2026-06-26.md` | Own closing record; #869 refines (not replaces) its 9%-window claim. | 2 |
| `docs/research-findings-144-pm-randomness-survey-…-2026-06-26.md` | Un-superseded RNG survey; cited by a CPU doc. | `2026-06-29-pm-cpu-difficulty-levels-1-9.md` |
| `docs/research-findings-110-cat-kaomoji-ascii-heads.md` | Design record for live face art (see A1). | — |

**Recommendation:** file one follow-up to `git mv` these into `docs/research/` **with** the inbound
link updates in the same commit. Do **not** prune — the link-rewrite cost is why this is a deliberate
move, not a mechanical one.

---

## Bucket D — Keep-but-drifted (refresh, not removal; out of prune scope)

Flagged for completeness — these are **not** removal candidates; they need a small edit, which belongs
to a content-fix ticket, not this prune triage.

| Path | Drift | Suggested fix |
|---|---|---|
| `docs/roadmap.md` | Label-generated; `v1 label — 24 open` (live: 28) and lists #475/#508/#567 as open (all CLOSED). | Regen from the label (commands are in the doc's footer). |
| `docs/pygame-fonts.md` | Content accurate but path landmarks stale: `pycats/text_utils.py`, `pycats/runtime_settings.py`, `pycats/cat_faces.py` → now under `pycats/ui/` + `pycats/storage/`; one `config.py` vs `config/menu.py` inconsistency. | Update the file-path landmarks + the one config-path line. |
| `docs/tooling-git-bug-offline-recipe.md` | Keep (closing artifact of research #654; tool-unadopted is the recorded outcome) — but uses the banned word "load-bearing" ×2. | Content fix belongs to the banned-word sweep family (#1245 and children), not here. |

---

## Ratification ask (for the human)

**Bucket A (11) + Bucket B (1)** are the ready-to-approve prune/merge list — every item has a CLOSED
tracking issue (or is a pre-tracker one-off), 0–1 inbound, and no durable content lost. Approve any
subset; each approved set lands as a downstream `git rm` / merge commit, **one set at a time**.

**Bucket C (10 relocate)** and **Bucket D (3 refresh)** are non-destructive companion cleanups worth a
follow-up each, but outside this ticket's prune scope — call them separately.

Nothing here has been deleted. No doc leaves the tree without an explicit go-ahead.
