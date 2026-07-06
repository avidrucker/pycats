# TIL 2026-07-06 — DRAGONFRUIT

**Context:** A docs/tracker-lane session that scrubbed stray "PR" references (#601), created the PM data-sourcing map (#617), codified two RULES additions ("Suggest, don't act" #568, session process-lessons #484, value-sourcing routing #556), built the parity-light generator (#607), and verified-then-closed the 3-axis parity-labeling umbrella (#451).

---

## 1. A grep hit is a candidate, not a verdict — records of a mistake are not the mistake

**What happened:** #601 asked me to replace stray "PR" references (pycats has no pull-request workflow — pmtools pushes straight to `main`). The `grep -rinE '\bpull request\b|\bPR\b'` sweep returned three *kinds* of hit: four docs that used "PR" as if the workflow existed (the actual targets), the `today-i-learned-2026-07-05-grape-2.md` TIL + its README row whose entire *subject* is the invented-PR error (err 74), and a `pr` render-alias variable in a code snippet (a case-insensitive false positive). Scrubbing "PR" out of the TIL would have erased the record's meaning — the doc exists *to say no PR workflow exists*.

**What I learned:** A text-scrub ticket's grep is the *candidate set*, not the *edit set*. Each hit needs a genre check: is this word a live claim (fix it), a record documenting the word's absence/misuse (keep it), or a homograph (skip it)? The ticket's own scope note said as much ("point-in-time records"), but the reflex to "make the grep return zero" is the trap — the acceptance was "no hit that *implies a workflow*," not "no occurrence of the string."

**The rule:** **When a ticket's acceptance is a grep, edit the hits that match the *intent*, not every hit that matches the *pattern* — a record of a mistake keeps the word that names it.**

---

## 2. Put the emoji-using generator at repo root so `grep pycats/` stays clean

**What happened:** #607's acceptance included `grep -rn '🟢\|🟡\|🔴' pycats/` returns nothing — no hand-typed parity circles in source. But the generator itself *must* contain circle literals (the `_CIRCLE = {"FOUND": "🟢", ...}` status→circle map). The reconciliation was placement: `parity_report.py` lives at the **repo root** (mirroring `bench.py`/`watch.py`), not under `pycats/`, so its circle literals and the generated `docs/parity-status.md` both sit outside the grep's scope while the package stays pristine.

**What I learned:** The "no circles in source" invariant (#448's green-rot pre-mortem) is enforced by *directory boundary*, not by banning the glyphs everywhere. The grep scoped to `pycats/` is the machine-check; root-level tooling is the sanctioned place for the computed representation. I nearly reached for an escape (build the emoji from a codepoint) before noticing the boundary already solved it.

**The rule:** **When an acceptance grep forbids a token in a package dir, the tool that legitimately emits that token belongs *outside* the dir (repo-root script), not obfuscated inside it.**

---

## 3. On a generated artifact, "no committed file yet" is the meaningful TDD red

**What happened:** TDD on #607's up-to-date test felt circular at first — the test asserts `docs/parity-status.md` matches a fresh regen, but the file doesn't exist until I generate it. Running the test *before* generating gave a real RED (`check()` returns False on a missing file), and generating gave GREEN. Separately, the able-to-fail proof is a distinct test: monkeypatch a registry row `FOUND`→`TUNED` and confirm `check()` reds. For the monkeypatch to reach the generator, `parity_report` reads `provenance.TUNING_PROVENANCE` *dynamically* (via the module, not a bound top-level import) — a `from ... import TUNING_PROVENANCE` would have frozen the reference and made the able-to-fail test silently pass.

**What I learned:** A "committed artifact + up-to-date test" pair has two separable red states, and both are worth watching: (a) *no artifact* (the file-absent red, which is the genuine first TDD failure), and (b) *stale artifact* (the able-to-fail flip). And the drift-guard only bites if the generator resolves its input at call time.

**The rule:** **For a generated-and-committed artifact, watch the file-absent red first, then prove the drift-guard with a content flip — and read the source data through the module so a monkeypatch actually reaches it.** (Extends the able-to-fail discipline in RULES → *Fixing bugs* / *Process lessons*.)

---

## 4. A machine-global file created outside the repo isn't in the commit diff — say so

**What happened:** #568 ("Suggest, don't act") specified the canonical rule text goes in `~/.claude/CLAUDE.md` (machine-global, all projects), with a one-line pointer from pycats `RULES.md`. The global file didn't exist, so I created it. But only the `RULES.md` pointer is git-tracked — a reviewer reading the commit sees a one-line diff and *none* of the actual rule. I flagged it explicitly in the close comment ("this file is not git-tracked, so it does not appear in the commit diff").

**What I learned:** When a ticket's deliverable spans a tracked file and an untracked machine-global one, the commit under-represents the work by construction. The close comment is the only place the out-of-repo half is visible — leaving it implicit makes the change look trivial and unauditable.

**The rule:** **If part of a deliverable lands outside the repo (machine-global config, dotfiles), name it in the close comment — the commit diff can't.**

---

## 5. Verify-then-close an umbrella: check every child's live state and re-run the acceptance grep

**What happened:** #451 (the 3-axis parity-labeling tracker) had a comment thread that read "#451 closes when #607 lands," and #607 had just landed. Rather than trust the narrative, I resolved the live state of all ten referenced tickets (#448/#408/#452/#233/#580/#581/#582/#584/#598/#607 — all CLOSED via `gh issue view`) and re-ran the umbrella's own acceptance grep (`grep -rn '🟢\|🟡\|🔴' pycats/` → clean) before closing. It was an unclaimed tracker with no worktree/claim ref, so it closed via plain `gh issue close` + a clarifying comment (no `pmtools release` — nothing to release).

**What I learned:** An umbrella's comment thread is a *claim* about completion, written incrementally by whoever was here last; it can lag or misstate. The cheap confirmation — batch `gh issue view <children> --json state` + re-run the stated acceptance checks — turns "the thread says done" into "I verified done." And close mechanics differ: an unclaimed tracker is `gh issue close`, not the `pmtools release` path (which is for a claim *I* hold).

**The rule:** **Before closing an umbrella, re-verify every child's live state and re-run its acceptance checks — don't close on the comment thread's say-so; and match the close mechanic to whether a claim ref exists.**

---

## What landed

| Ticket | Change |
|---|---|
| #601 | Replaced 6 workflow-implying "PR" refs across 4 docs; kept the records + the `pr` variable |
| #617 | New `docs/pm-reference/where-to-find-source-data.md` (PM sourcing map + online/offline tracker) |
| #568 | "Suggest, don't act" → new `~/.claude/CLAUDE.md` section + RULES pointer |
| #484 | New RULES → "Process lessons" (calibrate-first, identity-refactor proof, research-produces-a-choice) |
| #556 | RULES → "Changing values" value-sourcing routing (from the #530 ruling) |
| #607 | `parity_report.py` + generated `docs/parity-status.md` + up-to-date/able-to-fail test (Pass C of #451) |
| #451 | Verified all children closed + acceptance grep; closed the parity-labeling umbrella |

## Open threads (candidates for codification — not yet filed)

- **Records-vs-workflow scoping** (lesson 1) and the **verify-then-close umbrella checklist** (lesson 5) are craft rules that currently live only here. If they recur, they'd earn a line in RULES → *Closing work* (the umbrella check) and possibly a *Referencing code & docs* note (the grep-intent-vs-pattern point). Not filing unprompted — flagged for a go-ahead.

## Related artifacts

- Prior session: [TIL 2026-07-05 DRAGONFRUIT](./today-i-learned-2026-07-05-dragonfruit.md)
- The invented-PR error this session's #601 scrubbed: [TIL 2026-07-05 GRAPE (2)](./today-i-learned-2026-07-05-grape-2.md)
- Issues #601, #617, #568, #484, #556, #607, #451
