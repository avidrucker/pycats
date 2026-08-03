# TIL 2026-07-20 — GRAPE

**Context:** A workflow-hardening session. The owner noticed I'd started staying
pinned to the **main checkout** and prefixing every command with `cd <worktree>`,
losing their ambient sense of which branch/worktree they were on. We traced the
cause, then turned the fix into durable guidance: a memory, a WRITER ticket
(**#780**), and — dogfooding the new rule end-to-end — the RULES.md edit itself.
This is the follow-through on yesterday's #763 lesson that a diary entry expires
unless it's codified.

---

## 1. `pmtools claim` does not move the session — `EnterWorktree` does

**What happened:** The owner asked why I keep working from `main` and `cd`-ing on
every command, when I "used to know" which worktree I was on. Root cause:
`pmtools claim` creates the worktree with `git worktree add`, an **external**
command. It makes the directory on disk but does **not** change the session's
working directory — so the shell stays in the main checkout, and every command has
to carry its own `cd <worktree>`. That is the exact footgun behind yesterday's two
errors (id=150 editing #718 against main; id=158 handing over a run command that
pointed at main).

**What I learned:** There is a harness tool — `EnterWorktree` with a `path` — that
moves the session's cwd for real. Calling it right after `pmtools claim` means bare
commands run in the worktree, `CLAUDE.md`/memory reload for that directory, and
`pwd` finally tells the truth. I had been reading its "only when the user says
worktree" guard conservatively and defaulting to inline `cd`; the pycats fleet
workflow is exactly the standing instruction that guard asks for. I could not tell
the owner whether the harness itself changed underneath me — I have no visibility
into prior sessions — so I said so instead of inventing a "this used to be
different" story.

**The rule:** **After `pmtools claim`, call `EnterWorktree` with the worktree path;
on exit call `ExitWorktree keep`. Claim makes the directory — only `EnterWorktree`
moves the session into it.**

---

## 2. Dogfood the process change on the ticket that introduces it

**What happened:** #780 *is* the "enter the worktree after claim" rule. So I ran
the new loop on #780 itself: `claim` → `EnterWorktree path:<wt>` → verified `pwd`
reported `.claude/worktrees/wt-grape-pycats-780` → ran the suite there with **bare**
commands (1397 passed, 1 xfailed, no `cd` prefix) → edited RULES.md → committed →
`ExitWorktree keep` back to main → `pmtools close 780` from main.

**What I learned:** Executing the new rule while writing it is the cheapest possible
proof it works — every step was live evidence, not a claim. The `ExitWorktree keep`
before `pmtools close` matters specifically because the session is now *inside* the
worktree that `close` deletes; exiting to main first is what keeps the shell from
being stranded in a deleted directory (the same outcome the old "run close from
main" rule protected, now reached from an entered worktree).

**The rule:** **When a ticket changes the workflow, execute the new workflow to ship
it — the run is the regression test for the rule.**

---

## 3. The pmtools#128 branch shape now closes clean — the `issue-` rename is stale

**What happened:** On #718 (yesterday) `pmtools claim` minted a branch without an
`issue-` token and `pmtools close` couldn't resolve the worktree, so I renamed it
with `git branch -m …issue-718…` before closing. Today #780 claimed as
`br-grape/pycats-780-docs-rules-agent-must-enterworktree` — same tokenless shape —
and `close` resolved and tore it down with **no rename** (`CLOSE OK`, exit 0 from
main).

**What I learned:** My cached belief that close needs an `issue-` token in the branch
was outdated. RULES.md already documents `br-<fruit>/<project>-N` as the pmtools#128
"standard" mint shape that `close` resolves natively (legacy `issue-N` forms still
parse for back-compat). The proactive `git branch -m` I'd been doing is now
unnecessary ceremony — verify the tool's current behavior before re-applying a
remembered workaround.

**The rule:** **Don't pre-apply a remembered workaround against a tool that has since
been fixed — re-check its behavior first. The `br-<fruit>/<project>-N` branch closes
without a rename.**

---

## 4. Don't reconstruct a file line from memory for an `Edit` `old_string`

**What happened:** Adding the MEMORY.md index row, I typed the anchor `old_string`
from memory — including a paraphrased `(green suite ≠ looks right)` gloss that
wasn't in the actual line — and the Edit failed with `String to replace not found`
(error id=172). Re-reading the file's tail and copying the exact existing row made
it apply first try.

**What I learned:** This is the recurring "verify file contents before asserting"
reflex in a new spot: an `Edit` anchor is an assertion about the file, and memory
paraphrases. The read-gate exists precisely because reconstructed text drifts from
the byte-exact original.

**The rule:** **Read the exact line before using it as an `Edit` `old_string` —
never reconstruct it from memory.**

---

## Process note

Mid-session the project CLAUDE.md gained a rule: **file new issues with
`pmtools file`** (alias `create`; wraps `gh issue create` behind the
area/role/severity gates), not bare `gh issue create`. I filed #769/#780 earlier
with bare `gh` before the rule surfaced; going forward, issue creation routes
through `pmtools file` (and this TIL's own issue, #804, did). Note the gate rejects
`--severity low` on a non-defect, so a TIL files with `--area tracker --role WRITER`
and no severity.

## What landed

| Artifact | Change |
|---|---|
| `RULES.md` (Claiming/Closing work) | `EnterWorktree` after claim; `ExitWorktree keep` before `pmtools close` (#780) |
| `memory/enter-worktree-after-claim.md` | Durable feedback memory for the same rule |

## Related artifacts

- [TIL 2026-07-19 GRAPE](./today-i-learned-2026-07-19-grape.md) — the worktree/cwd errors this rule prevents
- Issue #780 (this rule), #769 (run/sim command must target the worktree), #763 (yesterday's TIL)
