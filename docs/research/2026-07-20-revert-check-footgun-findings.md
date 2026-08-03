# Preventing the "git checkout wipes uncommitted edits" revert-check footgun

**Ticket:** #791 (RESEARCH · moderate scope) · **Date:** 2026-07-20 · **Agent:** APPLE

## Problem

The able-to-fail / revert-check step (RULES.md → *Fixing bugs* → "The test must be
able to fail") requires temporarily breaking a fix, watching the test go red, then
**restoring**. When the restore is `git checkout <file>` and that file *also* holds
unrelated uncommitted edits, `git checkout <pathspec>` reverts the **whole file to
HEAD** — discarding the fix and any other uncommitted work along with the temporary
mutation.

This is not a one-off. It has recurred **at least six times** despite a standing
memory (`git-checkout-revert-check-footgun`) that warns against it:

| When | Ticket | File | Store row |
|------|--------|------|-----------|
| origin (memory) | #34 | `pycats/entities/player.py` | (pre-store; memory only) |
| 2026-07-01 | #396 | `pycats/entities/fighter.py` | errors #44 |
| (dated in note) | #550 | `pycats/config.py` | errors #137 |
| 2026-07-13 | #731 | `pycats/sim/runner.py` | errors #142 |
| 2026-07-19 | #676 | `pycats/char_select.py` | errors #157 |
| 2026-07-20 | #783 | `Makefile` | errors #175 |

Every instance is the same shape: a **mutation was made** (via `sed`/`cp`/inline
edit), confirmed red, then **`git checkout <file>` was used to undo it** — and
checkout took the uncommitted fix with it. A rule-in-memory alone has not stopped
recurrence, which is the core question this ticket asks: what makes prevention *not*
depend on the agent remembering the rule at the moment of undo.

## Q1 — Candidate restore techniques and how each fails

The revert-check has two shapes, and the safe restore differs by shape:

- **Shape A — revert the whole fix:** remove the entire fix, confirm red, restore it.
- **Shape B — neuter one line:** inject a temporary mutation *on top of* the fix
  (hardcode a value, comment out a guard), confirm red, then undo just the mutation.

**All six recorded failures are Shape B** — a temporary mutation undone with a
whole-file `git checkout`.

| Technique | How it restores | Failure modes |
|-----------|-----------------|---------------|
| **Edit-out → Edit-back** — undo the mutation with the inverse of the same Edit that made it | Only the mutated hunk moves; the harness tracks the change | (a) Requires the *mutation* to have been made with the Edit tool too — if you mutated via `sed`/`cp` there is no Edit to reverse, and the mind reaches for `git checkout`. (b) Stale `.pyc` if the two edits are the same byte size within ~1s (see `mutation-check-stale-pyc`, errors #86) — orthogonal to edit-vs-checkout, mitigated by clearing `__pycache__` or preferring `monkeypatch`. |
| **`cp` backup → `cp` restore** | Restores from the aside copy, preserving the file's other edits | (a) **Process gap** — on #783 the backup was made and then *not used* (the agent reached for `git checkout` instead). Making the backup does not force restoring from it. (b) Stale `.pyc` after a `cp`-back (errors #86, memory). (c) Depends on remembering to make the backup first. |
| **`git stash push` → `git stash pop`** | Symmetric save/restore of the *whole tree*; `pop` brings every edit back | Safe against edit-loss (pop restores everything), but: (a) whole-tree, all-or-nothing — it stashes the fix *and* every unrelated edit, so it fits Shape A (drop the whole fix) far better than Shape B (neuter one line while keeping the rest present). (b) `pop` can conflict. |
| **`git checkout -p` / `git restore -p`** (hunk-scoped) | Interactively discard only the mutation hunk | (a) **Not usable in this harness** — the Bash tool blocks interactive git flags (`-i`, `-p` patch mode). (b) Even where available, you must correctly distinguish the mutation hunk from the fix hunk; adjacent lines can merge into one hunk, discarding both. |
| **`git checkout <file>` / `git restore <file>`** (the footgun itself) | Reverts the whole pathspec to HEAD | Discards **all** uncommitted edits in the file, not just the mutation. This is the recurring failure — verified empirically (below). |

### Empirical confirmation (git 2.43.0)

A throwaway repo with a dirty file (`FIX` + an extra uncommitted line + a mutation):

```
$ git checkout f.txt
Updated 1 path from the index
$ cat f.txt
line1
FIX          # <- reverted to HEAD; the mutation AND the uncommitted extra line are gone
```

`git checkout <pathspec>` silently takes the whole file to HEAD. There is no
confirmation and no dirty-file guard.

## Q2 — Recommended canonical technique

> **Make the revert-check mutation with the Edit tool, and undo it with the inverse
> Edit. Never `git checkout` / `git restore` a whole file to undo a revert-check.**

Why this one is both safest **and** hardest to forget:

1. **The undo is symmetric with the mutation — there is no separate "how do I
   restore?" decision** where `git checkout` sneaks in. You did `Edit(A → mutated)`;
   you undo with `Edit(mutated → A)`. No git command ever enters the loop, so the
   footgun has no opening. This directly answers Q2's "does not depend on remembering
   a rule at the moment of undo": the safe path *is* the natural path, because you
   reverse the tool you just used.
2. **It touches only the mutated hunk** — unrelated uncommitted edits are never at
   risk, by construction.
3. **The harness tracks Edit state** (read-before-edit is enforced), so the reverse
   Edit is a first-class, verifiable operation rather than an untracked shell side
   effect.
4. **It sidesteps the stale-`.pyc` footgun** — an in-place Edit is harness-tracked;
   `cp`-back and `checkout` can leave stale bytecode (`mutation-check-stale-pyc`,
   errors #86).

The single discipline that makes it stick: **mutate via Edit in the first place.**
The recurrences all began with a *shell* mutation (`sed`/`cp`/inline), after which
"restore the file" naturally maps to `git checkout <file>`. If the mutation is an
Edit, the undo is obviously the reverse Edit.

**Complements / fallbacks (not the default):**

- **Same-size-within-1s edits:** clear `__pycache__` before the confirming run, or
  prefer `monkeypatch` / a test-level parametrization to flip the feature off without
  touching the source at all (errors #86 note).
- **Shape A (drop the whole fix):** `git stash push` → run → `git stash pop` is
  acceptable and loss-safe (may conflict on pop).
- **`git restore -p` is unavailable here** (interactive; blocked by the Bash tool).

## Q3 — Guidance edits that make it stick (exact targets)

The memory alone failed six times, so reinforce at the point of the *rule* (RULES.md),
not only the point of recall (memory). Both edits are downstream DEV/DOCS work — this
research ticket only names them.

1. **RULES.md → *Fixing bugs* → "The test must be able to fail" bullet** *(primary —
   this is the doc gap).* It currently says "revert the fix (or stub it), watch the
   test fail, **then restore**" but never says *how* to restore — and the natural
   reach (`git checkout <file>`) is the destructive one. Add a clause naming the safe
   restore: *reverse the same edit (Edit-back); never `git checkout <file>`, which
   reverts the whole file to HEAD and discards your uncommitted fix.*

2. **Memory `git-checkout-revert-check-footgun`.** It is correct but framed as a
   prohibition ("don't do X"). Re-frame to **lead with the positive canonical rule**
   (mutate-via-Edit, undo-via-inverse-Edit) so recall surfaces the safe *action*, not
   just the ban. Update the recurrence evidence (now ≥6: #34, #396, #550, #731, #676,
   #783).

3. **RULES.md → *Testing* → "revert-check the integration test" bullet.** Same
   able-to-fail restore concern; it already cross-references *Fixing bugs → able to
   fail*, so edit #1 covers it by reference — no separate wording needed, just verify
   the cross-ref still points at the amended text.

4. **The `tdd` skill (able-to-fail / refactor step)** — *candidate, lower priority.*
   The concrete `git checkout` footgun is pycats-workflow-specific and the `tdd` skill
   is a shared cross-repo skill; the load-bearing homes are RULES.md + the memory. A
   one-line "undo a revert-check mutation by reversing the edit, not by checking out
   the file" would not hurt, but is optional.

## Q4 — Tooling guard: file or defer?

**Verdict: FILE a follow-up DEV ticket — but scoped as "spec + evaluate a guard,"
not "build a specific hook."**

Reasoning:

- **Six recurrences despite a standing memory is the exact signal that a mechanical
  backstop is warranted.** #791's own framing — "a rule-in-memory alone is
  insufficient" — is the argument for a guard that does not depend on remembering.
- **A native git hook cannot do it.** Git has **no `pre-checkout` hook** (the only
  place a veto could live). `post-checkout` runs *after* the worktree is already
  updated — verified empirically: the hook fires on a path checkout, but by the time
  it runs the file is already reverted and the uncommitted edits are already gone, and
  githooks(5) states the hook "cannot affect the outcome." So the destructive checkout
  cannot be intercepted by any stock-git hook.
- **Therefore the only feasible guard is a wrapper**, e.g. a `git` alias/shim or a
  dedicated `revert-check <file>` helper that refuses to `git checkout <pathspec>`
  when the pathspec is dirty (or that performs an Edit-safe mutate/restore itself).
  Shimming a core git command is more invasive and can surprise other workflows, which
  is exactly why the DEV ticket should **evaluate** the wrapper vs. a lighter helper
  before committing to a mechanism — not pre-decide "install hook X."

The primary defense ships now via the Q3 guidance edits; the wrapper is
belt-and-suspenders. **Do not build the guard under this ticket** (out of scope) —
file it downstream of this doc.

## Recommendations summary

- **Q1:** Four viable techniques; the footgun (`git checkout <file>`) and interactive
  `-p` are ruled out (destructive / unavailable). All six recorded failures are
  Shape-B mutations undone by whole-file checkout.
- **Q2:** **Mutate via Edit, undo via the inverse Edit.** Safest and forget-proof
  because the undo is symmetric with the mutation — no `git checkout` ever enters the
  loop.
- **Q3:** Amend RULES.md *Fixing bugs* "able to fail" bullet (name the restore
  method — the primary gap) and re-frame the memory to lead with the positive rule;
  the *Testing* bullet inherits by cross-ref; the `tdd` skill is an optional add.
- **Q4:** **File** a DEV ticket to spec/evaluate a `revert-check` wrapper (a native
  git hook is impossible — no `pre-checkout`, and `post-checkout` fires too late).
  Do not build it here.

## Downstream tickets (file one at a time, after this doc)

1. **DOCS:** apply the Q3 guidance edits (RULES.md able-to-fail bullet + memory
   re-frame).
2. **DEV (blocked on nothing, low priority):** spec + evaluate a `revert-check`
   wrapper / `git checkout` dirty-file guard, per Q4.
