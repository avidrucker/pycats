# research-spec #199 — ICE scoring for pycats prioritization

**Status:** spec / recommendation only. This ticket does **not** create labels, edit
`.claude/orchestrate.json`, or change any skill. It hands a follow-up DEV ticket a
decided representation, scale, composition rule, and integration sketch.

**Author:** GRAPE · lane `area:tracker` · 2026-07-01

---

## TL;DR

- **Adopt lccjs's ICE rubric verbatim** (I×C×E, same scales, same tiebreak) so the
  shared `puzzle-triage` / `fruit-agent-orchestrate` skills rank pycats the same way
  they rank lccjs. The skills *already* read `stats/ice-scores.csv`; pycats just
  doesn't produce that file yet.
- **Representation: a committed advisory CSV** at `stats/ice-scores.csv` —
  **hand/PM-maintained, no database, no new dependency.** This is the one material
  divergence from lccjs (which stores scores in a `better-sqlite3` DB and *exports*
  the CSV). pycats is stdlib-only by rule; the flat file *is* the source of truth here.
- **Composition: ICE slots into the existing `bug → blocker → ICE` order as the
  third key**, replacing today's `severity → estimate → lowest#` proxy. It does **not**
  float above bugs. Confirmed: ICE only orders the tier left after bugs and blockers
  are placed — in practice ~all of the enhancement/research backlog.
- **Backfill (~45–51 issues) belongs to the follow-up, as a considered human/PM pass,
  not a label auto-sweep** — pycats features carry no `severity:*` by rule, so lccjs's
  severity→Impact auto-derive collapses to a near-constant I=1 and gives almost no signal.

---

## 1. How lccjs represents and computes ICE (the reference)

Source: `~/Documents/Study/JavaScript/lccjs/scripts/ice-score.js` (`npm run ice:score`,
823 lines). RICE preceded it and was retired in #956/#997 (`scripts/archive/rice-export.js`).

**Storage — a SQLite DB, not labels or issue bodies.** Scores live in an `ice_scores`
table in the canonical `~/.lccjs/lccjs.db` (via the `better-sqlite3` dependency). The
script upserts rows, then **exports two derived artifacts**, committed to the repo:
- `stats/ice-scores.csv` — the machine-readable ranking spine (atomic temp-file→rename write).
- `stats/ice-scores.md` — a rendered, human-readable ranked table with the rubric inline.

CSV columns: `issue,title,type,I,C,E,ice_score,ice_rank,tier,yegor_priority,actionable,provisional,labels,notes,updated_iso`.

**Scales:**

| Dim | Scale |
|---|---|
| **I (Impact)** | 3=massive · 2=high · 1=medium · 0.5=low · 0.25=minimal |
| **C (Confidence)** | 1.0=high · 0.8=medium · 0.5=low |
| **E (Ease)** | 10=trivial · 7=easy · 5=moderate · 3=hard · 1=very hard |

**Formula:** `ICE = I × C × E`. Ease **multiplies** (a #1327 fix — the old `I×C/E`
inverted ease and sank quick wins, so the 10=easy scale now points the same way as the
score). Tiebreak `+ 1/(issue×1000)` — earlier issues win ties but can never flip a
higher-scored ticket.

**Two override tiers sit *above* the ICE queue,** expressed as **labels**
(`priority:critical`, `priority:elevated`). `critical` is human-only; `elevated` is
human or PM agent. Applying either **requires an audit comment** (who / why / expiry) —
the script writes label + comment atomically and refuses to record the tier in the DB if
either `gh` write fails (#963).

**Provisional auto-sweep (`--auto`, #1322):** for every unscored open issue, derive a
rough I/C/E from labels alone — `I` from `severity:*` (critical→3, high→2, medium→1,
low→0.5, else 1), `C=0.8` neutral (labels can't reveal confidence), `E` a coarse guess
from type (docs/chore→7, research/spike→3, else 5) — and mark the row `provisional=1` so
a human refines it later. Keeps the table from silently going stale.

**Epics/trackers are never scored (`isEpicOrTracker`, #1566)** — they are containers, not
units of work; a scored tracker pollutes the ranking.

**Worth copying vs leaving behind:**

| Copy | Leave behind |
|---|---|
| The **rubric** (scales + `I×C×E` + tiebreak) — verbatim, for cross-project uniformity | The **SQLite DB + `better-sqlite3`** — a new dependency pycats forbids |
| The committed **`stats/ice-scores.csv`** contract (the skills already read it) | The **DB→CSV export** machinery — pycats edits the CSV directly instead |
| **`provisional` flag** + **epic/tracker exclusion** | The **rich RICE migration path** (`--seed-from`) — pycats has no RICE history |
| The **override-tier + audit-comment** discipline (optional for pycats — see §4) | |

---

## 2. Representation options for pycats

Scored on: agent-readable without extra tooling · human-writeable at filing time ·
drift resistance · fit with the existing `gh`-based collection.

| Option | Agent-readable | Human-writeable | Drift resistance | Fit with `gh` flow | Verdict |
|---|---|---|---|---|---|
| **A. `ice:impact-N` / `ice:confidence-N` / `ice:ease-N` label triplets** | ✅ in the `gh issue list --json labels` pycats already runs | ⚠ 3 label picks per issue; fractional scales (0.25, 0.8) don't fit label names cleanly | ✅ score lives on the issue | ❌ **label sprawl**: 5+3+5 = 13 value labels × the taxonomy, ~150+ label-applications across the backlog; every re-score = label churn + a `gh` write; pollutes the shared cross-repo label set (RULES.md: keep labels identical across repos) | ✗ |
| **B. `ICE: I/C/E` line convention in the issue body** | ⚠ needs a per-issue body fetch (`gh issue view N`) + parse; not in the cheap `--json labels` sweep | ✅ one line at filing time | ❌ silent drift — a stale body line is invisible; no diff review | ⚠ N extra `gh` calls at triage time (the skills deliberately avoid per-body reads except for `sequenced` tickets) | ✗ |
| **C. Advisory CSV keyed by issue #** (`stats/ice-scores.csv`) | ✅ `grep -v '^#' stats/ice-scores.csv` — **zero tooling, zero network** | ✅ edit one row; a stdlib maintainer script is an easy follow-up | ✅ **git-tracked → drift shows in the PR diff, review-gated**; one file to eyeball | ✅ **the two skills already hardcode this exact path**; join to issues by number | ✅ **recommended** |

### Recommendation: **Option C — committed advisory CSV, hand/PM-maintained.**

Rationale:
1. **Drop-in for the skills.** `puzzle-triage` and `fruit-agent-orchestrate` already
   read `stats/ice-scores.csv` and degrade gracefully when it's absent ("unscored issues
   sort last, flagged needs-ICE"). Creating the file *is* the integration — no reader change.
2. **Zero new dependency.** pycats is stdlib-only by rule (`settings.py` "no new
   dependency, per #94"; the `pyflakes`-into-`.venv` install was forbidden). lccjs's
   DB-backed design needs `better-sqlite3`; a flat CSV needs nothing. The one accepted
   trade: pycats loses lccjs's upsert/atomic-export/migration machinery and instead treats
   the CSV as the primary artifact a human or agent edits directly.
3. **Drift is visible, not silent.** A CSV row change lands in a reviewable PR diff;
   a body line or a mislabelled issue does not.
4. **No label sprawl / no per-body reads** — the two costs that sink A and B.

**Columns:** reuse lccjs's exact header so the skills parse identically —
`issue,title,type,I,C,E,ice_score,ice_rank,tier,yegor_priority,actionable,provisional,labels,notes,updated_iso`.
`ice_score`/`ice_rank` are derived; a maintainer script (follow-up) can recompute them,
or a human can fill `ice_score = I×C×E` by hand for a first pass. `yegor_priority` and
`labels` may be left blank for pycats.

---

## 3. Scale + how it composes with the pycats order

**Scale: adopt lccjs's rubric verbatim** (§1 table + `ICE = I×C×E`, tiebreak
`+1/(issue×1000)`). Reason: the ranking skills are a *shared cross-project convention*;
keeping the rubric identical (same argument RULES.md makes for labels) means
`puzzle-triage` ranks pycats and lccjs by the same math with no per-repo special-casing.
The 5/3/3-point scales are coarse on purpose — fast to assign, hard to bikeshed.

**Composition — the pycats-specific decision.** pycats' order is **not** lccjs's.
lccjs treats ICE as the spine (ICE folds severity in via Impact) under just the two
override tiers. pycats' `fruit-agent-orchestrate` Step 3 fixes an explicit precedence
(#9), and the human's stated order confirms it: **bug → blocker → ICE**.

So ICE slots in as the **third and lowest** sort key, **replacing today's proxy**:

```
Actionable ordering (unchanged tiers, real ICE swapped into slot 3):
  1. Bugs first          — `bug` label or bug()/fix() title prefix; jumps the queue regardless of ICE
  2. Blockers second     — a ticket that unblocks other open work (high leverage)
  3. ICE score           — WAS: severity → shortest estimate → lowest#   (the ad-hoc proxy #199 flags)
                           NOW: ice_score (desc) → severity (tiebreak) → lowest# (FIFO)
```

Answering the ticket's Q3 directly:
- **Does ICE replace the estimate→# tiebreak, or sit under severity?** It **replaces the
  whole `severity → estimate → lowest#` proxy** that currently occupies slot 3. Severity
  demotes to an ICE-tiebreak (it's already folded into ICE via Impact); estimate drops out
  (velocity is off, #199 keeps it out of scope); lowest-# stays as the final FIFO tiebreak.
- **Does ICE only rank the untriaged-enhancement tier?** **Yes.** Bugs and blockers are
  placed by keys 1–2 *before* ICE is consulted; ICE only orders what remains. Because pycats
  currently has **1 `bug` and 9 `blocked`** issues, "what remains" is ~all of the
  enhancement + actionable-research backlog — which is exactly the tier that needs principled
  ranking today.

This keeps pycats' "fix what's broken before adding more" rule (RULES.md) intact: a
high-ICE quick-win enhancement can outrank a *harder* enhancement, but never jumps ahead
of an open bug.

> **Divergence flagged for the follow-up:** `puzzle-triage` v0.3.0 documents ICE as the
> *top* actionable axis (override-tier → ICE → severity), matching lccjs. pycats keeps
> **bug → blocker → ICE** (`fruit-agent-orchestrate` #9). The two skills already disagree
> on where ICE sits; pycats should follow its own bug-first order. The follow-up should
> not "fix" `fruit-agent-orchestrate` to match lccjs — the divergence is intentional.

---

## 4. Orchestration wiring

Both skills currently **hardcode** `stats/ice-scores.csv`. So the **minimum viable wiring
is simply creating that file** — no config change required; the skills pick it up.

The **clean seam** is the existing `advisory` block in `.claude/orchestrate.json`
(today it holds `clusterFile` / `sequencingDocRef`, both `null` in pycats). Add:

```jsonc
"advisory": {
  "iceSource": "stats/ice-scores.csv",   // path the ranking skills read; null => degrade to proxy
  "clusterFile": null,
  "sequencingDocRef": null
}
```

`advisory.iceSource` is a **path, not a command** (ICE data is a read artifact, unlike the
`enrichment.*` commands). Making it config-driven — vs. the current hardcode — lets a repo
without ICE degrade explicitly and signals intent. This requires a one-line reader change
in each skill (read `advisory.iceSource`, fall back to `stats/ice-scores.csv`, then to the
severity proxy if absent). **That skill edit is follow-up scope, not this ticket.**

**Recommended follow-up wiring order** (all in the DEV ticket): (a) create
`stats/ice-scores.csv` with the header; (b) add `advisory.iceSource` to `orchestrate.json`;
(c) teach the two skills to read the key (optional — the hardcode already works); (d)
optional stdlib `scripts/ice_score.py` maintainer (recompute `ice_score`/`ice_rank`,
`--auto` provisional sweep) using only `csv` + `subprocess`(gh) — **no `better-sqlite3`.**

**Override tiers (`priority:critical` / `priority:elevated`): optional for pycats,
defer.** pycats already has a manual-override mechanism — RULES.md: "to pull a specific
feature forward, **assign it directly** — the ranked queue is advisory and the human
orchestrator overrides it." Formal priority-tier labels + the audit-comment discipline are
lccjs parity, worth adopting later, but not needed for a first ICE cut. Note if adopted
they'd sit **above bugs** (matching lccjs), the only thing that does.

---

## 5. Backfill (scope of the follow-up, not this ticket)

**In scope of the follow-up? Yes — but as a considered pass, not a sweep.**

Backlog today: **67 open**, of which ~**51 are actionable** (excluding 9 `blocked`,
6 `decision`, 3 `deferred`, 1 `proposal`, plus `humans-only`/`wontfix`). Minus
epics/trackers (never scored, §1), the backfill target is **~45–51 issues**.

**Key pycats-specific caveat:** lccjs's `--auto` sweep derives Impact from `severity:*`.
**pycats features carry no `severity:*` by rule** (severity is defects-only; the whole
backlog has exactly **1** severity label). So a severity→Impact auto-derive would assign
nearly every issue the fallback **I=1, C=0.8, E=5** — a near-constant score with no
discriminating power. Therefore:

- **Do not lead with a label auto-sweep** for pycats — it produces a flat, useless ranking.
- **Do a one-time human/PM ICE pass** over the ~45–51 actionable issues, assigning real
  I/C/E per issue (a few seconds each on the 5/3/3 scales). A `provisional=1` auto-sweep
  can still seed rows so none are missing, but the human pass is what gives the ranking value.
- Sequence it *after* the representation + wiring land, so scores are written straight into
  the agreed CSV.

---

## 6. Follow-up DEV ticket — proposed scope (to file, not build here)

> **feat(tracker): add ICE scoring — `stats/ice-scores.csv` + orchestrate wiring** ·
> `area:tracker` · `enhancement`
>
> **Have:** no ICE data; the ranking skills fall back to the `severity → estimate →
> lowest#` proxy (#199).
> **Should have:** a committed `stats/ice-scores.csv` (lccjs columns/rubric, §1–2), an
> `advisory.iceSource` key in `.claude/orchestrate.json` (§4), and the two skills reading it.
> **Tasks:** (a) create the CSV with header + a first human/PM backfill of the ~45–51
> actionable issues (§5); (b) add `advisory.iceSource`; (c) teach `puzzle-triage` /
> `fruit-agent-orchestrate` to read the key (fallback to the hardcoded path, then to the
> proxy); (d) *optional* stdlib `scripts/ice_score.py` maintainer (recompute + `--auto`),
> **no new dependency**.
> **Out of scope:** `better-sqlite3` / any DB; reviving velocity/estimates; the
> `priority:*` override tiers (separate, optional — direct-assignment already covers manual override).

---

## Termination checklist (from #199)

- [x] **(a)** lccjs's mechanism summarized — §1 (DB→CSV export, scales, `I×C×E`, tiers, `--auto`, epic exclusion).
- [x] **(b)** each representation option scored, one recommended — §2 (→ committed advisory CSV).
- [x] **(c)** scale + composition-with-Yegor-order decided — §3 (lccjs rubric verbatim; ICE = slot-3 key replacing the proxy, under bug→blocker; ranks only the post-bug/blocker tier).
- [x] **(d)** follow-up DEV ticket scope outlined — §6 (create CSV + backfill + wire `advisory.iceSource` + optional stdlib maintainer). No implementation done here.
