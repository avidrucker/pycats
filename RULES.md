# pycats — project conventions

## Work tracking

- **Single source of truth: GitHub issues.** Actionable work lives in the issue
  tracker (`gh issue list`), not in markdown TODO files. (`TODOS.md` was retired
  into issues on 2026-06-22; the original list is preserved in git history.)
- pycats runs the **fleet** orchestration workflow (`.claude/orchestrate.json`,
  `mode: "fleet"`). Triage + assignment via the `/fruit-agent-orchestrate` skill;
  agents claim work with `pmtools claim <issue> --as <fruit>` and close it with
  `pmtools close <issue>` (see [Closing work](#closing-work)).

## Labels & priority

- **`severity:*` is for DEFECTS ONLY** (bugs). It describes the *impact of a
  defect*: `high` = data corruption / broken output / blocking; `medium` = real,
  visible defect; `low` = cosmetic or latent.
- **Features / enhancements do NOT get a `severity:*` label.** They carry
  `enhancement` and rank *below* triaged bugs in the work queue — this is
  intentional: fix what's broken before adding more. To pull a specific feature
  forward, **assign it directly** — the ranked queue is advisory and the human
  orchestrator overrides it.
- **`blocked`** encodes real dependencies (e.g. a feature gated on a
  prerequisite). Prefer it over faking severity to express ordering.
- The label taxonomy is a **shared cross-project convention** created by
  `scripts/create-standard-labels.sh`. Don't invent project-local severity
  meanings — keep labels identical across repos.

### Area labels (`area:*`)

- **Every ticket gets exactly one `area:*` label at filing time** — the
  project-local subsystem it belongs to. The current set:
  - `area:display` — rendering, fullscreen, zoom, resolution, display preferences
  - `area:combat` — knockback, hitstun, hitboxes, dodges, attacks, off-stage mechanics
  - `area:entities` — Fighter/Player state machine (dizzy, prone, ledge-hang, decomposition)
  - `area:screens` — screen system/manager, start/win-loss screens, menus, skins, input feedback
  - `area:watch` — `--watch` / `--vs` spectator battles
  - `area:tracker` — ticket discipline, TODO reconciliation, rules/process docs

  **One area per issue:** if it spans two, pick the dominant one (the orchestrator
  uses the *first-listed*) and **make a suggestion of how to effectively split the
  ticket** if it genuinely needs two lanes. **Why:** `/fruit-agent-orchestrate`
  partitions the backlog into per-agent lanes by `area:*` (at most one cluster per
  agent), so an unlabelled ticket lands in the wildcard pool and weakens the
  same-file collision guard. (Reproducible label *creation*: `avidrucker/pmtools#69`.)

## Filing work

- **A question or suggestion is not authorization to create work.** "Have you done
  X?", "did you Y?", "is Z done?", or "this would be good" asks for an *answer* or
  surfaces an *option* — it is not a cue to file an issue, claim a worktree, or
  start coding. Answer the question (or present the option) and **stop**;
  file/claim/execute only after an explicit go-ahead ("yes, do it", "take that
  ticket", "go ahead"). Filing-and-claiming is outward-facing and costly to
  unwind — when unsure whether you've been authorized, ask. (Front-end mirror of
  "surface the contradiction before an outward-facing close" under *Fixing bugs*.)
- **No unprompted research.** When asked for a specific action (file/log/label/claim/
  edit a named thing), do **exactly that** — do not first run greps, file reads, or
  issue listings that weren't requested. Resolving the minimal input the asked action
  strictly requires (e.g. looking up a command's required argument, or reading the one
  file you're about to edit) is fine; open-ended investigation — "let me check how X
  works", "let me see what else exists" — is not: ask "want me to look into X first?"
  and wait for a yes. Burned tokens and the "I didn't ask you to research" correction
  are the tell (errors db 23/24). (Execution-time complement of "a question is not
  authorization" above: that rule bars acting when only *asked* a question; this one
  bars over-acting when *given* an action.)
- Shape every ticket as a complaint: **have X / should have Y / repro**
  (yegor-bdd).
- **Repro/spec-first for unclear bugs.** If a bug's symptom isn't specific enough to
  write have/should/repro, file a **`research`** ticket to validate / spec /
  reproduce it first, then create the DEV bug ticket once the repro is known.
  Never file a half-specified DEV ticket.
- **Reconcile a worktree-found failure against current `origin/main` before filing
  it.** `pmtools claim` guarantees a fresh base *at claim time* (it fetches and
  hard-blocks a claim when local `main` is behind `origin/main`), but sibling agents
  keep merging *during* your session, so a long-lived worktree base drifts behind and
  a failure you see may already be fixed upstream. Before filing a regression found
  in a worktree, `git fetch origin main` and check the open-issue list / `git log
  origin/main` — confirm it still reproduces on **current** `origin/main`, not just
  your (possibly stale) base. The claim-time guard cannot cover mid-session drift, and
  `pmtools status` does not surface it today (#171). (Cousin of "merged ≠ what your
  tree has" under *Closing work* and the stale-tracker caution.)
- **Verify a delegated/audit finding — or a user-reported symptom — in the code
  before filing or acting on it.** A subagent's finding, an audit's claim, or a
  user's "X is broken / it works like Y" is a *lead, not a fact* — it reads with the
  authority of prose but may not match what the code does. Before turning any reported
  "X is broken / unwired / works like Y" into a ticket or an outward-facing change,
  open the named `file:func` and confirm it. Precedents: **#189** (two reported
  follow-ups — an "unwired" `StatechartScreenEngine`, a "mis-keyed" Nalio d-tilt —
  both wrong on inspection; filing them would have duplicated #100/#142); **#453**
  (the "Esc doesn't back out of sub-menus" report was wrong on mechanism — Esc was
  hold-to-quit, never a back key). (Same spirit as reconcile-before-filing above and
  "surface the contradiction before an outward-facing close" under *Fixing bugs*.)
- **Lazy decomposition for research epics.** A multi-thread investigation gets
  ONE umbrella `research` tracker issue listing the threads; file each child
  thread **one at a time**, finishing it before filing the next sibling. This
  avoids premature decomposition (yegor: only decompose when about to start work).
- **Verify a ticket's identity before stating it; mint IDs/refs one at a time.** Two
  clauses from the #535/#536 misnumbering (errors db 51), ratified in **#541**:
  **(A) Verify before you state.** Never tell the human — or write into any doc,
  commit, or comment — a ticket's **number or title** until it's confirmed from a
  real lookup: the `gh issue create` return URL *for that specific create*, or
  `gh issue view <N>`. Never infer a number from filing order or from a batched
  command's stdout ordering.
  **(B) Mint IDs/refs sequentially, never concurrently.** Never run **ID/ref-minting
  mutations** in parallel — `gh issue create` **and** `pmtools claim` (which mints a
  claim ref + worktree, same race class): file/claim one, confirm the returned
  identifier, then do the next. No `&`, `wait`, `xargs -P`, or concurrent tool calls
  that each mint an ID/ref. Read-only `gh`/`pmtools` calls **may** still run in
  parallel — the ban is only on concurrent ID/ref-minting mutations. (The failure was
  filing two issues concurrently → GitHub assigned their numbers in race order → they
  landed swapped, then propagated into a committed doc + comments before verification.)

## Dependencies

- **Adding a dependency needs explicit human approval — propose, don't install.**
  Any way of pulling in undeclared code is gated: `pip install` (even a dev `.venv`),
  manifest/lockfile edits, `npm`, `apt`. Proceed only on an explicit "yes" (the
  `pyflakes`-into-`.venv` install during #193 is the case this forbids). Fine without
  asking: **using** a declared dep (`pygame-ce`, `pytest`, `statecharts-py`), and
  **suggesting/explaining** a library — the gate is on installing, not discussing.
  **Why:** a new dep is supply-chain + reproducibility surface, and "it's
  dev-only/harmless" is how silent installs get normalized. pycats is stdlib-only by
  design (`settings.py`, "no new dependency, per #94").

## Fixing bugs

- **Every bugfix lands a regression test in the same commit.** A fix without a
  test is not done — the test is what stops the bug from coming back (and from
  being *re-filed*: #7's original fix `b480ae0` shipped with no test, so the
  behavior looked broken a year later and was re-filed and re-investigated from
  scratch). This is the repo's expression of yegor-bdd (a bug is a failing test).
- **The test must be able to fail.** Before claiming the fix works, confirm the
  new test is **red without the fix and green with it** — revert the fix (or stub
  it), watch the test fail, then restore. A test that has never been red proves
  nothing (it may assert the wrong thing or never reach the branch). See
  `docs/learnings/today-i-learned-2026-06-23-dragonfruit.md` §1 & §4.
- **Already-fixed / non-reproducing bug?** If a reported bug does not reproduce on
  current `main`, the deliverable is still the *missing* regression test (find the
  commit that fixed it, add the can-fail guard), not a no-op close. Surface the
  contradiction to the reporter before an outward-facing close.

## Testing

- **Golden-safe by default-identity — not by hand.** A new present-layer or behavioral
  feature is golden-safe when its **default is an exact identity on the sim/golden path**:
  gate it off-by-default so the golden cat / scripted controller never exercises it, and the
  goldens stay byte-identical *by construction*. Precedents — the default cat has no smash
  (#327); the level-less controller has every AI flag `False` (#312); `font_scale=standard`
  ⇒ `round(base*1.0) == base` (#345); a `dict`-subclass `Keymap` drops into `controls[...]`
  unchanged and a `None` nickname renders the identical `"P1"`/`"P2"` (#438). Extend a shared
  render primitive behind a **default-identity kwarg** for the same reason
  (`draw_menu_button(pressed=False)`, #332). Assert the identity with a byte-identity /
  render-parity oracle test, and prefer this to regenerating or hand-editing goldens to chase
  a diff — regenerate only once every remaining diff is explained. See
  `docs/learnings/today-i-learned-2026-07-01-dragonfruit.md`.
- **AI / behavioral integration tests must (a) drive the REAL loop and (b) be
  discriminating.** A controller test that calls `decide()` on a stub can pass while the live
  loop **drops** the input — the #248/#370 "emit-but-don't-convert" gotcha — so drive the
  actual `run_battle` loop, not just the policy. And a real-loop test that *also passes with
  the feature turned off* is not testing the feature: **revert-check the integration test**
  (mutate the feature off, confirm the test goes red), exactly as for a unit test (see *Fixing
  bugs* → "able to fail"). Both halves bit in one session — a melee-poke test the ordinary
  attack already satisfied (fixed with a below-the-lip foe, `dy > 60`; #413) and a recovery
  `y`-comparison silently broken by a KO→respawn to `y = -1000` (switched to asserting the
  input is emitted in-loop; #409). See
  `docs/learnings/today-i-learned-2026-07-01-dragonfruit.md`.

## Code conventions

- **Read the optional `Player`/control surface defensively in shared combat/input
  code.** `systems/combat.py::process_hits` and `entities/fighter_input.py` are
  exercised by lightweight test stubs that model only the documented *minimal*
  contract (rect, facing, hurtbox, `receive_hit`, …), not the full `Player`. Any
  new read of an optional attribute or key — `defender.state`, `controls["special"]`,
  … — must use `getattr(obj, "attr", default)` / `dict.get(key, default)` with a
  safe default, never a bare `obj.attr` / `controls[key]`. The safe default is the
  inert reading: an unbound action is "unpressable"; a defender without `.state` is
  "not crouching". Precedent — this bit twice: **#137** (`process_hits` read
  `defender.state == "crouch"` → `AttributeError` reddened `main` via the stub-based
  `test_multi_hitbox`/`test_clank`) and **#143** (the move-selection seam read
  `controls["special"]` → `KeyError` on the 16 test control maps that omit it).

- **Never restore a monkeypatched global by hand in a test — use the `monkeypatch`
  fixture (or `try/finally`).** A manual restore is skipped if the test throws before
  its last line, leaking the stub into every later test. **Diagnostic:** a change that
  reddens tests in *files the diff never touched* = a leaked global from an earlier
  failing test. Bit twice: `os.environ` at module top (#345, ~15 tests), hand-restored
  `settings.load` (#453, ~19 tests).

## PM-parity markers (`⚠` / `🔬` / `❓`)

Inline glyph markers make unresolved-vs-Project-M work **greppable**. Use them at write
time. (Axis A of the labeling system #451; design #448; the human-facing key lives on
**#452**. Codebase audit + rules of record: `docs/research/2026-07-02-pm-parity-marker-audit.md`.)

| Marker | Means | `grep -rn` answers |
|---|---|---|
| `⚠` (U+26A0) | **guessed** — value present but unconfirmed vs PM | "what's unpinned?" |
| `🔬` (U+1F52C) | **needs research** — a concrete sourcing/derivation is queued | "what's the research backlog?" |
| `❓` (U+2753) | **open question** — an undecided design/behaviour point | "what's undecided?" |

- `⚠` and `🔬` **co-occur** (`⚠🔬`) on a guessed value that is also queued for sourcing.
  `grep ⚠` = every unpinned value; `grep 🔬` = the subset with an active sourcing action.
- Mark only **unresolved** things. The #233 provenance registry's *resolved* states —
  `FOUND` / `TUNED` / `DIVERGENCE` — get **no** marker (marker = "still open"; the
  registry classification is the resolution; the two compose).
- **Convention once.** Mark a documented, repeated convention in **one** place (e.g. a
  module-docstring note that "hitbox positions are approximated per #120"), not on every
  repetition — repeated markers become noise (#448 "marker soup"). Don't re-mark a
  continuation line whose comment is already marked.
- An `❓` should **reference its `decision` / research ticket** where one exists
  (e.g. `❓ … — see #466`), so the code points at the discussion instead of duplicating it.

## Changing values

- **A value change must cite its basis.** Any change to a tuning/gameplay constant — a
  config value or balance number (frame windows, speeds, damage, knockback, thresholds,
  timers, cooldowns, hitbox sizes) — must point to **one** of:
  1. **Research findings / data** — a sourced PM/Melee value (rukaidata, SmashWiki, a PM
     changelog, or an in-repo `docs/research/*` finding), cited in the commit **and** the
     constant's comment; **or**
  2. **A game-designer decision** — a citation to a design doc (an ADR, a `docs/` design
     note, or a ratified `decision:` ticket) where the human designer chose the value.
- **Game-feel alone is not a basis.** A round number, a mid-band guess, or bare "it feels
  better" is **not** sufficient — such a change is declined and closed **`wont-do` /
  `vapid`** (precedent: **#489**, a `DOUBLE_TAP_WINDOW` bump that rested on a feel-pick
  after **#407** found PM has no faithful number to copy). A genuinely un-pinned value
  **stays at its current number**, carrying its `⚠`/GUESS marker, until basis (1) or (2) exists.
- **Picking a surrogate is a decision, not a DEV edit.** When no faithful value exists,
  *choosing* one is a `decision:` ticket (e.g. **#491**); the ratified choice then becomes
  basis (2). Record which basis applies in the commit, the constant's comment, and its
  `combat/provenance.py` entry (**#233** / ADR-0003) as **FOUND** (sourced) or **TUNED**
  (designer-chosen) — never presented as sourced when it is a guess.
- This gates *changing* a value; the `⚠`/`🔬`/`❓` markers above only *label* an unpinned
  one — the two compose (a changed value should shed its `⚠` and land a `FOUND`/`TUNED` entry).

## Surfacing run/sim commands

When a change would **benefit from or require a live run or simulation** to verify
— anything observable: the running game loop, rendering/scaling, input, screens or
menus, audio, or sim output — the agent's **final response MUST include the exact
command(s) to run it, with full absolute paths**, so the human can copy-paste and
manually test (the agent can't drive the GUI). **pycats-only** — other repos in the
Study tree do not inherit this rule.

- **When it applies:** the change is runnable/observable. A pure-internal refactor
  with full test coverage and no behaviour change doesn't strictly need it, though a
  run command is still welcome.
- **Full paths, not `python -m pycats.game` alone.** Worktrees have no `.venv`, so
  point the interpreter at the **main repo's** `.venv` and run from the checkout.
  Present it as a `REPO=` / `PY=` variable block (one assignment per line), not an
  opaque one-liner:

      REPO=/abs/path/to/pycats                   # the checkout (main repo or worktree)
      PY=/abs/path/to/pycats/.venv/bin/python    # ALWAYS the main repo's venv
      cd "$REPO" && "$PY" -m pycats.game

- **Pick the command that shows the change:** the live game (`-m pycats.game`), a
  replay/match (`watch.py`, `watch.py --match`), or a recorded video
  (`watch.py --match --video media/clip.mp4`). The README "How to Run" section and
  the `watch.py` commands are the canonical sources — cite the one that exercises
  the change, with absolute paths filled in.
- **There is no `main.py` or top-level launcher — never invent `python main.py`.**
  The only entry points, all run from the repo root, are `-m pycats.game` (live
  game), `watch.py` (replay/match), and `bench.py` (benchmark). `python main.py`
  fails with `No such file or directory`. If unsure, the README "How to Run"
  section is authoritative — read it rather than guessing a conventional path.

## Claiming work

- **Run the full suite right after `pmtools claim`, before you change anything.** A
  fresh worktree branches off whatever `main` is *right now*, and in fleet mode
  another agent may have just merged a mid-flight (or even red) change. Confirm
  green first:

      SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
        /abs/path/to/pycats/.venv/bin/python -m pytest -q

  If it's red, the failure is **not yours** — fix `main` first (or `git merge
  origin/main` to pull in a fix that landed after you branched) before building, so
  you never attribute a pre-existing failure to your change, or ship on top of a
  broken baseline. (#177; fleet merge race.)

## Closing work

The fleet closes via **`pmtools close`**, which owns the racy push to `main` and
the gated worktree teardown. Follow this order — do **not** improvise:

1. **Work in your claimed worktree.** `pmtools claim <N> --as <fruit>` created it
   under `.claude/worktrees/<fruit>-issue-N` on branch `<fruit>/issue-N`.
2. **Commit on the feature branch, with `Closes #N` in the commit _body_.** The
   subject may keep the repo's `type(scope): summary (#N)` style, but the body
   MUST carry the `Closes #N` keyword: it is both the GitHub auto-close trigger
   *and* exactly what `pmtools close` scans for (and recovers on). `git log
   --oneline` only shows the subject — put the keyword in the body, not the title.
3. **Land + tear down with `cd <main> && pmtools close <N>`, run from the main
   checkout.** `close` resolves the worktree + branch from the issue number
   (pmtools#104, `008cb2a`), so run it from the main repo root — **not** from inside
   the worktree it deletes. It loops fetch → rebase `origin/main` → push `HEAD:main`
   until it lands, then — only after confirming the commit reached `origin/main` —
   deletes the claim ref, closes the issue, and removes the worktree + branch.
   Because your shell stayed in the main checkout the whole time, it is never
   stranded in a deleted directory. (Running from *inside* the worktree still works
   but strands your shell — prefer from-main.)
4. **Run the pre-close error self-audit.** Before posting the closing comment,
   re-read the session from claim → now, enumerate every log-error trigger event
   (including resolved ones), log any missing rows (`pmtools error log`), and include
   one of `error self-audit: N row(s) logged (#…)` or `error self-audit: no loggable
   errors this session` in the closing comment. See the **log-error** skill for the
   trigger list + fields. This turns silence into a checkable acknowledgement — a
   clean session and a forgotten log stop looking identical.

**Never `git push` to `main` directly, and never manually `git merge` your feature
branch into `main`.** `pmtools close` exists to make the close atomic and
race-safe: a hand-typed push-then-teardown can tear down a worktree *after* a
race-rejected push, destroying work that is still only local (the lccjs "#200
incident"). Hand-closing also leaves a dangling `refs/claims/issue-N` that
`pmtools close` would otherwise sweep.

**pycats specifics (differences from lccjs):**

- **Velocity is off** (`storage.velocity.enabled = false`) — no velocity CSV row
  rides in the close commit.
- **No code markers** — pycats does not use `@todo`/`@inprogress #N` markers, so
  there is nothing to delete in the close commit; just include `Closes #N`.
- **The errors store is live** (`storage.errors.enabled = true`) — `pmtools error
  log '<json>'` records to `~/.pmtools/pycats/pmtools.db`. The step-4 self-audit
  logs to it, so the `error self-audit: …` line is always available to state.
- **Fallback only if `pmtools` is unavailable:** `gh issue close <N>` plus a
  closing comment. Prefer the tool whenever it is installed.

**Close-time caveats:**

- **Run from the main checkout and `close` exits 0 cleanly.** Before teardown,
  `pmtools close` chdirs its *own* process back to the main root, so from `<main>` it
  never deletes the cwd it is standing in — it returns **0** after `CLOSE OK …` /
  `commit <sha> … on origin/main`. Your shell also stayed in `<main>` the whole time,
  so there is no strand and no cwd to recover: comment and keep working in place.
- **Legacy from-worktree behaviour (avoid — prefer from-main above).** If you instead
  run `close` from *inside* the worktree, its final step deletes the cwd you are
  standing in: the process returns **exit 1** after a *successful* close (trust the
  `CLOSE OK` banner, not the code — pmtools#8), and your shell is left in a deleted
  directory (`getcwd: cannot access parent directories`, with a stale `wt-…-issue-N`
  in your prompt) until you `cd /abs/path/to/pycats`. From-main (pmtools#104) avoids
  all of this — which is why it is the default in step 3.
- **Post the closing comment from `<main>` (where you already are)**, and include the
  step-4 `error self-audit: …` line:

      gh issue comment <N> --body "Closed in <sha>. <summary>
      error self-audit: no loggable errors this session"
- **No-code tickets close differently.** `pmtools close` needs a `Closes #N`
  *commit* to land and verify; a **decision / research / comment-only** ticket has
  none. Close those with `gh issue close <N>` (after posting the ruling/finding as
  a comment), then **`pmtools release <N>`** to drop the claim ref + worktree. Do
  **not** fabricate a no-op commit just to satisfy `pmtools close`.
