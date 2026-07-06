# TIL 2026-07-06 — BANANA

**Context:** A session driving PM-parity plumbing and one real value correction. Reviewed
issues #615 and #599; ratified + landed a new RULES clause (#618: every research ticket
must produce ≥1 findings doc); and corrected pycats' smash-charge constants to Project M
values (#599: `SMASH_CHARGE_FRAMES` 60→59, `SMASH_CHARGE_SCALE` 1.4→1.3671). The value
change is where most of the lessons came from — a two-line config edit that rippled into a
golden KO, four test files, and a formatter mishap.

---

## 1. A tuning-value correction can silently *delete* a golden's whole reason to exist

**What happened:** #599 weakened the charged forward-smash by ~2.4% (Melee's 1.3671×
restored over Brawl's 1.4×, plus one fewer charge frame). The combat golden
(`test_golden_combat`) exists to exercise the `ko` state via a scripted side-blast KO
(Nalio fsmashes Birky, #588). After the value change the golden failed with
`'ko' never reached` — Birky now *survived* at ~86%. The KO had been landing right at the
blast-line margin, and the weaker smash tipped it under. The ticket had predicted "it should
still ko, just at a slightly different frame/percent." That prediction was wrong.

**What I learned:** `PYCATS_UPDATE_GOLDENS=1` would **not** have fixed this — the failure was
a hardcoded `assert "ko" in all_states`, not a blob diff. Blindly regenerating would have
either stayed red or (if I'd also weakened the assertion) laundered away the exact coverage
the golden was built for. The right move was to *preserve the behavior under test*: raise the
scripted rack-up (34→36 in-place jabs) so the corrected smash still KOs, then do a **semantic**
regen and verify `combat.summary.json` still shows `ko_frames` present and `lives_end` still
dropping by one. A marginal scenario is fragile: any nerf near the threshold can erase it.

**The rule:** **When a value change reds a golden, ask whether the behavior-under-test still
happens — if a nerf erased it, restore the scenario to reproduce it; never regen a KO away or
weaken the assertion to force green.**

---

## 2. `ruff format <dir>` formats every file under the path, not just the ones you changed

**What happened:** To satisfy "run ruff format before committing," I ran
`ruff format pycats/ tests/`. It reformatted **193 files** — the whole tree — because pycats
isn't uniformly ruff-formatted (tests/ isn't gated, and other files had drifted). I'd created
a massive diff with three lines of actual #599 change buried in it. Recovered by listing my 7
intentional files and `git checkout --`-ing the other 186 back to HEAD. Logged as error #82.

**What I learned:** `ruff format` is not "format my diff" — it's "format everything I point it
at." The pre-commit gate here is `ruff format --check pycats/` (whole-tree *check*), but my
per-commit responsibility is only that **my** changed files are clean. Formatting files I
didn't touch is both out of scope and, when the tree has pre-existing drift, actively harmful.

**The rule:** **Scope the formatter to the files you edited — `ruff format <file1> <file2>` (or
`--check` first) — never a bare directory, unless the whole tree is already known-clean.**

---

## 3. Verify a doc is *actually* stale before "fixing" it — mine was already right

**What happened:** The user asked me to make sure the #595 reference doc
(`docs/pm-reference/smash-charge-hold.md`) was accurate and to fix it *first* if not. A prior
comment thread had flagged it as needing a "downgrade to contested" correction. But that
correction had been **retracted** and never applied — the doc's Q4 already stated 59 / 1.3671
with the verbatim SmashWiki quote and the correct Melee lineage. There was nothing to fix
pre-emptively. The only edit warranted was a *post*-change refresh: once #599 flipped the
config, the doc's "pycats today = 60 / 1.4 ⚠" gap table would go stale, so that got updated as
a consequence of the change, not before it.

**What I learned:** "A comment said this doc is wrong" is a lead, not a fact. Read the doc
against the current sources before editing — a flagged correction may have been superseded, and
editing on the stale flag would have *introduced* an error into an accurate doc.

**The rule:** **Before "fixing" a doc someone flagged, read it against ground truth — confirm
the staleness is real and current; a retracted flag is not a work item.**

---

## 4. A human ruling records a decision; it is not a green light to implement the follow-up

**What happened:** After the human ratified a two-clause rule ("both, as written", #618), I
posted the ruling comment *and* wrote "Proceeding to the RULES.md edit…" and started
claim-prep recon — before being told to take the follow-up. The user caught it: "did you claim
#618? I just said to put the ruling on the ticket." I had not actually claimed it, but I'd
announced I would. Logged as error #80; corrected the comment to mark the edit unclaimed.

**What I learned:** This is the mirror of over-*deferring* (last session's lesson). Recording a
ratification is one action; executing the downstream RULES/DEV edit is a separate one that
needs its own go-ahead. The human-gate sits on the outward, hard-to-reverse *commit* — and
"posting a comment that says I'm about to implement" already leans over that gate.

**The rule:** **Ratifying a decision and implementing it are two authorizations — record the
ruling, then stop and wait for an explicit go-ahead before claiming/editing the follow-up.**

---

## 5. Fleet worktrees may have no pre-commit hook — unformatted files leak onto main

**What happened:** While recovering from lesson 2, `ruff format --check pycats/` flagged two
files I never touched (`birky_cat.py`, `presenters.py`) as unformatted **at HEAD**. Checking
`git rev-parse --git-path hooks/pre-commit` showed **no hook installed** in this clone.
`pre-commit install` is manual per-clone setup; fleet worktrees skip it, so commits land
without the format/lint gate ever running — which is how those two files reached main
unformatted (via other agents' feat commits).

**What I learned:** The pre-commit config existing in the repo does *not* mean the gate ran on
any given commit. In a fleet, the on-demand `ruff` run is the *only* gate you can rely on, and
it only covers what you choose to check. Pre-existing main drift is real and is not yours to
silently fix inside a feature commit (that's lesson 2 again, at a larger blast radius).

**The rule:** **Don't assume the pre-commit gate ran — verify your own files with an explicit
`ruff` invocation, and treat pre-existing main drift as a separate ticket, not feature-commit
scope.**

---

## What landed

| Artifact | Change |
|---|---|
| `RULES.md`, `CLAUDE.md` | Ratified rule: every `research` ticket produces ≥1 findings doc (#618) |
| `pycats/config.py`, `pycats/combat/provenance.py` | Smash charge → PM 59 / 1.3671; provenance rows re-cited, superseding #581 (#599) |
| `pycats/sim/input_script.py` | Combat golden rack-up 34→36 jabs so the corrected smash still KOs (#599) |
| `tests/golden/combat.*`, `test_golden.py`, `test_status_registry.py`, `test_status_timer_bar.py` | Semantic golden regen + charge-bar readout 50%→51% over the 59f ramp (#599) |
| `docs/pm-reference/smash-charge-hold.md` | Post-change refresh of the gap table + a corroborating source (#599) |

## Open threads

- Two files (`birky_cat.py`, `presenters.py`) are committed-unformatted on `main` — candidate
  for a small standalone format-fix ticket to green the whole-tree `ruff format --check` gate.

## Related artifacts

- Issues #618 (rule), #599 (value correction), #615 (research ticket reviewed)
- Error rows #80 (ruling ≠ authorization), #82 (repo-wide `ruff format`)
- Prior TIL: [2026-07-05 BANANA](./today-i-learned-2026-07-05-banana.md)
