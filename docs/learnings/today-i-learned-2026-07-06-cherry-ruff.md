# TIL 2026-07-06 — CHERRY (ruff-tooling session)

**Context:** A three-ticket chain, all `area:docs`/`area:tracker` tooling. #625 flipped
two stale ⏳ clone rows to ✅ in `docs/pm-reference/where-to-find-source-data.md`. #540
brought the root scripts (`watch.py`, `bench.py`, `bench_render.py`, `conftest.py`) under
the #502 ruff lint+format pre-commit hook. That widening surfaced pre-existing format drift
in `pycats/`, which I filed as #642 and then took. Two self-caught errors along the way
(#89, #92).

---

## 1. `$?` after a pipe is the pipe's exit, not the command's — and it masked a red hook

**What happened:** Verifying #540, I ran the format check piped through `tail` to trim
output:

```bash
.venv/bin/ruff format --check pycats/ watch.py ... | tail -2; echo "fmt exit=$?"
```

It printed `fmt exit=0`, so for a moment I believed the format hook was green. It wasn't —
`ruff format --check` was exiting **1** (two `pycats/` files would reformat). `$?` had
captured `tail`'s exit status (always 0 here), not ruff's. I only noticed because the
*visible* output still said `Would reformat: pycats/sim/presenters.py` — the text
contradicted the "exit 0" I'd just printed. Re-running the check un-piped showed the real
exit 1.

**What I learned:** Any time you pipe a check/lint/test command into `head`/`tail`/`grep`
and then read `$?`, you are reading the **last** pipeline element's status, not the check's.
For a command whose entire purpose is its exit code, the pipe silently throws that away. The
near-miss here was reporting a red hook as green — invisible, exactly the failure class that
bites hardest.

**The rule:** Never judge a check command by `$?` after a pipe — run it un-piped (or read
`${PIPESTATUS[0]}`). Logged as error #89.

---

## 2. Widening coverage surfaces pre-existing rot — reveal it and scope a follow-up, don't over-scope in place

**What happened:** #540 widened the ruff hook from `pycats/` to also cover the root scripts.
Running the widened `ruff format --check` immediately flagged **two `pycats/` files** —
`pycats/characters/birky_cat.py` and `pycats/sim/presenters.py` — as needing reformat. My
branch had touched neither (`git diff origin/main -- pycats/` was empty), so this was
**pre-existing** drift, red on main independent of my ticket. It was tempting to just
`ruff format pycats/` and be done. That is exactly the #597/#76 over-scoping trap: blanket-
formatting untouched files drags unrelated churn into a ticket about something else. Instead
I: (a) shipped #540's real deliverable (root scripts clean + hook widened), (b) documented
the pre-existing drift candidly in the commit + closing comment, (c) filed **#642** as a
tightly-scoped follow-up naming exactly the two files, and (d) took #642 next once the human
gave a go-ahead.

**What I learned:** When you extend a guard (a linter's path set, a test's coverage, a
type-checker's strictness), the guard will light up rot that predates you. Two failures to
avoid: silently absorbing the fix (scope creep that hides the pre-existing defect in an
unrelated commit) **and** silently leaving it unmentioned (the guard is now red on main and
nobody knows why). The correct move is the middle path: land your scoped change, surface the
rot as its own record, and let a separate scoped unit fix it.

**The rule:** A widened guard that exposes pre-existing failures gets your deliverable +
a *separate* scoped ticket for the rot — never a blanket in-place fix, never silence.
(Reinforces the existing "don't over-scope ruff" rule; surfaced #597/#76.)

---

## 3. "Verify before asserting" applies to a one-line living-doc flip too

**What happened:** #625 asked me to flip two clone rows from ⏳ pending to ✅ offline in a
living tracker. The trivial version is to just edit the markers. Instead I first confirmed
both clones actually existed on disk **and** matched their expected upstreams —
`~/Documents/Study/Rust/brawllib_rs/` (origin `rukai/brawllib_rs`) and
`~/Documents/Study/JavaScript/meleelight/` (origin `schmooblidon/meleelight`) — before
writing ✅ and the paths. The ticket even called this out ("accurate living-doc, not blind
flip").

**What I learned:** The repo's "read the source before asserting" discipline isn't only for
PM/canon mechanics claims — it applies to any doc edit that asserts a state of the world.
"The clone is available at path X" is a checkable claim; flipping the marker without the
check is asserting from memory. A ✅ that turns out wrong is worse than the ⏳ it replaced,
because ⏳ signals "unverified" and ✅ signals "confirmed."

**The rule:** Before flipping a living-doc status marker to "done/available," verify the
underlying fact on disk (or via the tool) — a status flip is an assertion, and assertions
get grounded.

---

## 4. An acceptance criterion must be feasible against the tool's *actual* output

**What happened:** When I filed #642, I wrote an acceptance criterion: "`git diff -w` shows
no non-whitespace change" (to prove the reformat was behavior-preserving). Taking the ticket,
that criterion turned out to be **infeasible**: `ruff format`'s reflow of the
`presenters.py` `__init__` signature to one-arg-per-line adds a **magic trailing comma**
after the last parameter. A comma is a real token, not whitespace, so it survives `git diff
-w` by design. The criterion I'd authored could never pass for that file, even though the
change is genuinely behavior-preserving (a trailing comma in a Python parameter list is
inert).

**What I learned:** I wrote a definition-of-done based on an assumption about a tool's output
(`ruff format` only touches whitespace) that was wrong for a specific, common case
(collection/signature wraps carry a magic trailing comma). The right proof of behavior-
preservation was the **green suite** plus reasoning that the only new token is inert — not a
`git diff -w` emptiness that the formatter itself precludes. `birky_cat.py` (pure comment-
alignment) *did* satisfy the empty-`diff -w` bar; the criterion just wasn't universal.

**The rule:** Don't promise `git diff -w` emptiness for a `ruff format` (or any formatter
that can add magic trailing commas) — scope behavior-preservation acceptance to "suite green
+ only inert tokens added." Logged as error #92.

---

## What landed

| Artifact | Change |
|---|---|
| `docs/pm-reference/where-to-find-source-data.md` | Flipped #614/#616 clone rows ⏳→✅ with verified on-disk paths (#625) |
| `.pre-commit-config.yaml` | Widened both #502 ruff entries from `pycats/` to include the root scripts (#540) |
| `watch.py`, `bench.py`, `bench_render.py` | One-time `ruff format` (never-formatted root scripts) (#540) |
| `pycats/characters/birky_cat.py`, `pycats/sim/presenters.py` | `ruff format` the two pre-existing-drift files; #502 hook now fully green (#642) |

## Open threads

- The #502 pre-commit hook enforces `--select F,I,E722,E702,E402,UP` explicitly, which does
  **not** include `E501` even though `ruff.toml`'s `[lint] select` does. Noticed in passing;
  not investigated — whether the hook should carry E501 to match the config is a separate
  question, not filed.
- `tests/` remains outside the ruff regime (deliberately out of scope for #540). Whether the
  test tree joins is still an open call.

## Related artifacts

- Sibling TIL same day: [cherry (dizzy/hitstun/shield)](./today-i-learned-2026-07-06-cherry.md)
- Issues #625, #540, #642 · error rows #89, #92 · prior over-scoping lesson #597/#76
