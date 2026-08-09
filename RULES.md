# pycats — project conventions

## Work tracking

- **Single source of truth: GitHub issues.** Actionable work lives in the issue
  tracker (`gh issue list`), not in markdown TODO files. (`TODOS.md` was retired
  into issues on 2026-06-22; the original list is preserved in git history.)
- **All work is ticketed — research, decisions, dev, tests, docs alike.** Every unit of
  work happens inside a claimed ticket; nothing is worked without one, and work isn't
  proposed as something to just-do-now outside the ticket flow — suggest *filing a
  ticket* for it instead (see ~/.claude/CLAUDE.md → "Suggest, don't act"). Size is
  irrelevant: a one-line code change, a one-line doc edit, a small decision, or a quick
  research pass is still ticketed work. The only activity that happens **between** tickets
  is asking/answering questions about tickets, building context/understanding of what
  we're doing, and session housekeeping (clearing/compacting context). Anything beyond
  that waits for a ticket — if it should be done, we file one first. (Front-end
  complement of "a question is not authorization to create work" under *Filing work*, and
  "every ticket is worked in a claimed worktree" under *Claiming work*.)
- pycats runs the **fleet** orchestration workflow (`.claude/orchestrate.json`,
  `mode: "fleet"`). Triage + assignment via the `/fruit-agent-orchestrate` skill;
  agents claim work with `pmtools claim <issue> --as <fruit>` and close it with
  `pmtools close <issue>` (see [Closing work](#closing-work)).

## Labels & priority

- **`severity:*` is for DEFECTS ONLY** (bugs). It describes the *impact of a
  defect*: `high` = data corruption / broken output / blocking; `medium` = a
  visible defect; `low` = cosmetic or latent.
- **Features / enhancements do NOT get a `severity:*` label.** They carry
  `enhancement` and rank *below* triaged bugs in the work queue — this is
  intentional: fix what's broken before adding more. To pull a specific feature
  forward, **assign it directly** — the ranked queue is advisory and the human
  orchestrator overrides it.
- **`blocked`** encodes hard dependencies (e.g. a feature gated on a
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
  - `area:docs` — README, docs, setup, contributor workflow, and developer-experience documentation

  **Exactly one `area:*` per issue — never more.** If an issue spans two or more
  areas, suggest how to split it and ask the human directly: combined, or split. Some
  issues are inherently cross-cutting; those get **`area:cross-cutting`** (pending —
  see #1330, the cross-cutting-label + orchestrator-lane ticket, new), never several
  area labels stacked on one ticket. **Why:** `/fruit-agent-orchestrate` partitions
  the backlog into per-agent lanes by `area:*` (at most one cluster per agent), so an
  unlabelled ticket lands in the wildcard pool and weakens the same-file collision
  guard. (Reproducible label *creation*: `avidrucker/pmtools#69`.)

### Relationship labels (`parent` / `child`)

- **`parent`** — the ticket has sub-issues / tracks child slices (an umbrella or
  decomposition parent). **`child`** — the ticket has a parent / is a slice of a
  larger tracker. A ticket that sits **mid-tree** (both a parent and a child) carries
  **both** labels. These complement `area:*`: the area label says *what lane* the work
  is in, the relationship label says *what tree* it belongs to.
- **When to apply — at file/claim time, going forward.** When you file or claim a
  ticket, tag it `parent` if it has sub-issues, `child` if it has a parent, both if
  it's mid-tree. **Why:** GitHub's native sub-issue links (`parent:` / `sub-issues:`)
  don't surface in the issue **list** view (as of GitHub's 2026 UI), so while working a child you can't
  glance-see it's a slice of a bigger tracker, or that a parent has siblings you should
  finish/close alongside it. The label makes the tree visible in the list.
- **Backfill of already-open tickets is a one-time sweep, tracked separately** — this
  note governs new/claimed tickets from now on; retro-tagging the existing backlog is
  its own follow-up ticket, not an inline chore. (Labels created in **#641**.)

## Filing work

- **A question or suggestion is not authorization to create work.** "Have you done
  X?", "did you Y?", "is Z done?", or "this would be good" asks for an *answer* or
  surfaces an *option* — it is not a cue to file an issue, claim a worktree, or
  start coding. Answer the question (or present the option) and **stop**;
  file/claim/execute only after an explicit go-ahead ("yes, do it", "take that
  ticket", "go ahead"). Filing-and-claiming is outward-facing and costly to
  unwind — when unsure whether you've been authorized, ask. (Front-end mirror of
  "surface the contradiction before an outward-facing close" under *Fixing bugs*.)
  This holds **even when the question exposes something you forgot but arguably
  should have done**: the reflex to remediate on the spot — "did you log the jq
  error?" answered by logging it — is still *acting on a question*. Answer plainly
  first ("no — want me to?") and wait; a forgotten obligation is not self-authorization.
- **No unprompted research.** When asked for a specific action (file/log/label/claim/
  edit a named thing), do **exactly that** — do not first run greps, file reads, or
  issue listings that weren't requested. Resolving the minimal input the asked action
  strictly requires (e.g. looking up a command's required argument, or reading the one
  file you're about to edit) is fine; open-ended investigation — "let me check how X
  works", "let me see what else exists" — is not: ask "want me to look into X first?"
  and wait for a yes. Burned tokens and the "I didn't ask you to research" correction
  are the tell (errors db 23/24). (Execution-time complement of "a question is not
  authorization" above: that rule bars acting when only *asked* a question; this one
  bars over-acting when *given* an action.) Filing a ticket is **`file`**, not research:
  **"to make the ticket higher-quality" is not authorization** for an unprompted
  line-by-line audit or exhaustive gap catalogue. File the complaint at the depth asked; if
  a deeper pass would help, **offer a depth choice (minimal / moderate / thorough) and
  wait**, don't perform it (#577 / error #61: a filed README ticket answered with a full
  unprompted README review).
- **Suggest, don't act** — see ~/.claude/CLAUDE.md → "Suggest, don't act". When asked for a narrow action, do only that; propose anything further, don't perform it.
- Shape every ticket as a complaint: **have X / should have Y / repro**
  (yegor-bdd).
- **Open new issues with `pmtools file` (alias `create`), not bare `gh issue
  create`.** `pmtools file` wraps `gh issue create` behind the config-driven
  requirement gates: it enforces the role gate, maps `--area combat` →
  `--label area:combat`, and refuses a `--severity` that isn't on a `bug`
  (the "severity is for defects only" rule, enforced at filing time). Typical call:
  `pmtools file --title "feat: X" --area <area> --role <ROLE> --body-file <f.md>`
  (or `--body "…"`). Notes: `--role` is **required** and must be one of the 11 tokens in
  pmtools' `VALID_ROLES` (`store_core.py`, the SSOT): `DEV`, `TEST`, `WRITER`, `RESEARCH`,
  `SPIKE`, `ARC`, `PM`, `COMBO`, `DATA`, `CHORE`, `REVIEW` — note **`ARC`, not `ARCHITECT`**.
  The same set gates `pmtools velocity log`'s `role` field. **`--role` only validates — it
  adds no label.** `--role RESEARCH` won't add `research`, nor `--role DEV` add `enhancement`;
  add that label yourself. The one auto-label is `--area X` → `area:X`; `--severity` and extra
  `--label`s pass through (severity still gated to defects); `--allow-uncategorized` files
  without an area. Always **`--dry-run` first** and read the exact `--label` line — it's how
  you catch a missing semantic label before minting (#814 dry-ran under `--role RESEARCH` with
  no `research` label until added by hand). (Bare `gh issue create` still works and is what runs underneath,
  but `pmtools file` is the path that keeps the gates on.)
- **A `--label`/`--area` naming a nonexistent label fails the file — and `--dry-run`
  won't catch it.** `pmtools file` (and the `gh issue create` beneath it) rejects an
  unknown label, but `--dry-run` only *echoes* the `--label` line without checking the
  label exists on the repo, and pmtools reports the rejection as "gh unavailable" —
  hiding the cause. So **check names against `gh label list` before filing**, and when a
  file fails opaquely, re-run the underlying `gh issue create … 2>&1` to read the
  underlying rejection. Two traps: there is **no `refactor`/`chore`/`tech-debt` label** (a refactor
  is an `area:*` + `--role DEV`), and **no `sequenced` label** (express a dependency with
  the `blocked` label; see *Area labels* above for the valid `area:*` set — there is no
  `area:tooling`, rules/process work is `area:tracker`). (errors #300 — `--label refactor`
  failed 3×; #531 — rejection masked as "gh unavailable".)
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
- **Before filing for a fleet-visible red `main`, dup-check first.** A broken `main` is the
  most-double-filed thing — every agent sees the same red at once. `gh issue list --state
  open` + keyword-scan (failing test, stale constant, symptom) for an existing tracker; if
  one is in-flight, `git merge origin/main` to pull its fix instead of double-filing. #1212
  (the dup) duplicated #1211 (the narz neutral_b red-`main` fix, landed moments earlier;
  error #529). (Red-`main`-specific case of *reconcile before filing* above.)
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
- **Every `research` ticket produces ≥1 findings doc; follow-ups are optional.** Two
  clauses ratified in **#618**:
  **(A) The findings doc is the mandatory artifact.** A `research`-labelled ticket
  closes only when it has written **one or more** durable findings docs (e.g.
  `docs/research/<topic>-findings.md`) — a bare issue comment is **not** a sufficient
  closing artifact; the closing comment **links** the doc(s). "At least one" lets a
  single investigation emit multiple docs when it naturally splits. (Ties to the
  issue-review research rubric's "expected output format" check.) Producing the doc is
  necessary but not sufficient to close: a `research` ticket also passes the **human
  completeness gate** — the reporter OKs the findings before the close — see
  [Closing work](#closing-work) step 5.
  **(B) Follow-up tickets are optional and filed downstream of the doc, one at a
  time.** Findings **may** cause follow-up tickets (a DEV to implement, a `decision`
  to rule, or further `research`); those cite the findings doc as their source and are
  filed **one at a time** per *Lazy decomposition* and the sequential-minting rule
  below. Filing follow-ups is optional; the findings doc (A) is not.
  **(C) The findings doc carries the provenance header.** Every findings doc opens with
  the agent / authored-date / ticket header — see *Authoring docs*.
  **(D) The doc must answer the *literal* question asked — re-read it before closing.**
  Before closing a `research`/question ticket, re-read the ticket's exact question and
  confirm the findings answer *that* question, not an adjacent one that was easier or
  more interesting to answer. #141 (can two mirror-identical CPU AIs parry/shield each
  other indefinitely? — closed) was closed on the researcher's own judgment having
  answered a neighbouring question, not the one posed. Satisfying yourself the literal
  question is answered is part of the close, not the next reader's job.
  **(E) Keep the findings doc tight — say each thing once.** Lead with the answer, then
  the option space and provenance. **Plain-English explanation and necessary context
  stay** — the target is redundancy, not clarity; explain each thing in the fewest
  plain-English lines that keep it clear, and no more. Concretely, cut: the same point /
  number / citation restated across sections; repeated cross-references (link a sibling
  doc or source **once**, not in every section); block-requoting a source the doc already
  links (cite + a short quote, don't reproduce it at length); and scaffolding ("in this
  doc we will…", per-section recaps, a closing summary that echoes the opening). #950
  (grounded walk/dash/run are per-character, not global — closed) shipped a ~240-line doc
  that was "entirely way too long" (error #311) — the length was repetition and requoting
  across 5 pieces, not the explanations themselves.
  **(F) Research gives findings and the choices — it does not write the spec.** A
  `research` ticket says what's true and lays out the options to pick from. It stops
  there: it doesn't decide the design or write the final spec. That comes next, in a
  separate `ARC` / `decision` ticket where a human makes the call. #866 (RESEARCH:
  dash-attack mechanic — "V1 spec", closed) got written up as a spec with decisions
  already made, inside the research ticket — those decisions belong in the follow-up
  ticket, not this one. A title like "RESEARCH: … spec" is the warning sign: split it in
  two.
- **Verify a ticket's identity before stating it; mint IDs/refs one at a time.** Two
  clauses from the #535/#536 misnumbering (errors db 51), ratified in **#541**:
  **(A) Verify before you state.** Never tell the human — or write into any doc,
  commit, or comment — a ticket's **number or title** until it's confirmed from a
  confirmed lookup: the `pmtools file` (→ `gh issue create`) return URL *for that specific
  create*, or `gh issue view <N>`. Never infer a number from filing order or from a
  batched command's stdout ordering.
  **(B) Mint IDs/refs sequentially, never concurrently.** Never run **ID/ref-minting
  mutations** in parallel — `pmtools file` (which calls `gh issue create`) **and**
  `pmtools claim` (which mints a claim ref + worktree, same race class): file/claim
  one, confirm the returned
  identifier, then do the next. No `&`, `wait`, `xargs -P`, or concurrent tool calls
  that each mint an ID/ref. Read-only `gh`/`pmtools` calls **may** still run in
  parallel — the ban is only on concurrent ID/ref-minting mutations. (The failure was
  filing two issues concurrently → GitHub assigned their numbers in race order → they
  landed swapped, then propagated into a committed doc + comments before verification.)
- **Verify a ticket's *state* before stating a dependency or applying `blocked`.** Before
  you write "blocked by #N", "waiting on #N", or apply the `blocked` label, confirm #N is
  still open with `gh issue view <N> --json state` — never infer its status from a prose
  cross-reference, a title, or memory. A dependency asserted from prose can be stale: #14
  (ledge mechanics) was **CLOSED** when "edge-guard blocked by #14" was asserted as fact
  across many turns (error #26). (State is the status sibling of *Verify a ticket's identity
  before stating it* above, and an instance of "code/registry over memory" under *Read the
  source before asserting*.)

## Dependencies

- **Adding a dependency needs explicit human approval — propose, don't install.**
  Any way of pulling in undeclared code is gated: `pip install` (even a dev `.venv`),
  manifest/lockfile edits, `npm`, `apt`. Proceed only on an explicit "yes" (the
  `pyflakes`-into-`.venv` install during #193 is the case this forbids). Fine without
  asking: **using** a declared dep (`pygame-ce`, `pytest`, `statecharts-py`), and
  **suggesting/explaining** a library — the gate is on installing, not discussing.
  **Why:** a new dep is supply-chain + reproducibility surface, and "it's
  dev-only/harmless" is how unreviewed installs get normalized. pycats is stdlib-only by
  design (`settings.py`, "no new dependency, per #94").

## Fixing bugs

- **Every bugfix lands a regression test in the same commit.** A fix without a
  test is not done — the test is what stops the bug from coming back (and from
  being *re-filed*: #7's original fix `b480ae0` shipped with no test, so the
  behavior looked broken a year later and was re-filed and re-investigated from
  scratch). This is the repo's expression of yegor-bdd (a bug is a failing test).
- **The test must be able to fail.** Before claiming the fix works, confirm the
  new test is **red without the fix and green with it** — revert the fix (or stub
  it), watch the test fail, then restore **by reversing the same edit** (undo the
  mutation with the inverse Edit). Do **not** restore with `git checkout <file>` /
  `git restore <file>`: that reverts the whole file to HEAD and discards your
  uncommitted fix along with the mutation — a footgun that has recurred repeatedly.
  Mutating via Edit keeps the undo symmetric so `git checkout` never enters the loop;
  see `docs/research/2026-07-20-revert-check-footgun-findings.md` (#791). A non-Edit
  restore (`cp`/`sed` back) has a second trap: Python may keep serving the pre-restore
  `.pyc` from `__pycache__` (mtime-based invalidation misses a restored file), so the
  test stays red on the mutant value even though the `.py` reads correct — don't trust a
  post-restore "still red" until you `rm -rf __pycache__` before the confirming run
  (errors #86 — stale `config.pyc` read 60 not 59; #265 — cleared `__pycache__` → green).
  A test that
  has never been red proves nothing (it may assert the wrong thing, never reach the intended
  branch, nor whether a given fix is even guarded against regressions). See `docs/learnings/today-i-learned-2026-06-23-dragonfruit.md` §1 & §4.
- **Already-fixed / non-reproducing bug?** If a reported bug does not reproduce on
  current `main`, the deliverable is still the *missing* regression test (find the
  commit that fixed it, add the can-fail guard), not a no-op close. Surface the
  contradiction to the reporter before an outward-facing close.

## Testing

- **Keep goldens stable by making the default a no-op — not by editing goldens.** A new
  rendering or behavioral feature is safe for the golden tests when, **left at its default,
  it changes nothing on the sim/golden path**: gate it off by default so the golden cat /
  scripted controller never triggers it, and the goldens stay byte-for-byte identical
  without anyone touching them. Precedents — the default cat has no smash
  (#327); the level-less controller has every AI flag `False` (#312); `font_scale=standard`
  ⇒ `round(base*1.0) == base` (#345); a `dict`-subclass `Keymap` drops into `controls[...]`
  unchanged and a `None` nickname renders the identical `"P1"`/`"P2"` (#438). Extend a shared
  render primitive behind a **default-identity kwarg** for the same reason
  (`draw_menu_button(pressed=False)`, #332). Assert the identity with a byte-identity /
  render-parity oracle test, and prefer this to regenerating or hand-editing goldens to chase
  a diff — regenerate only once every remaining diff is explained. See
  `docs/learnings/today-i-learned-2026-07-01-dragonfruit.md`.
- **AI / behavioral integration tests must (a) drive the LIVE loop and (b) be
  discriminating.** A controller test that calls `decide()` on a stub can pass while the live
  loop **drops** the input — the #248/#370 "emit-but-don't-convert" gotcha — so drive the
  `run_battle` loop itself, not just the policy. And revert-check it exactly as a unit test
  (see *Fixing bugs* → "able to fail"): a live-loop test that *also passes with the feature
  turned off* isn't testing the feature. Both halves bit in one session — a melee-poke test the ordinary
  attack already satisfied (fixed with a below-the-lip foe, `dy > 60`; #413) and a recovery
  `y`-comparison broken with no test failure by a KO→respawn to `y = -1000` (switched to asserting the
  input is emitted in-loop; #409). See
  `docs/learnings/today-i-learned-2026-07-01-dragonfruit.md`.
- **Reproduce the observable in the live loop *before* writing the fix; if a facet is
  already safe, characterize it — don't fake a red.** (#424, two coupled lessons.) (1) A
  sibling feature can mask the bug, so a fix written blind ships a non-discriminating test —
  the edge-hog self-KO didn't reproduce until `jumps_remaining == 0`; reproduce the failing
  observable in the live `run_battle` loop first, then write the fix against that repro (the
  *able-to-fail* check under *Fixing bugs* proves the test discriminates). (2) When a facet
  is **already safe** and you cannot produce a red for it, do **not** dress a passing "it
  survives" assertion as discriminating coverage: ship a **characterization guard labeled as
  such** plus a **written finding** that the facet was verified safe. A characterization test
  pins current behaviour; a regression test proves a fix — say which you shipped.
- **When an addition reds a test, check what the test asserts before you build to keep it
  green.** Adding to a growable thing — skins, roster, config — can red a test for two very
  different reasons. Ask which: is it asserting a **behavior** (something the code must do),
  or a **frozen census** — `set(x) == {exact catalog}`, "there are exactly six skins" — that
  only pins today's inventory? A behavior red means fix the code; a census red is a brittle
  test objecting to growth. **De-census it** — assert the invariant that matters (membership,
  shape, uniqueness) via TDD — don't build structure to prop the census up. #750 (DEV: split
  the frozen OG-skin archive from the growable live skin set — closed) invented a frozen
  six-skin archive slice just to keep `set(x)==catalog` asserts green while #677
  (per-character starting skins — closed) added skins — ceremony that existed only to satisfy
  a brittle test.
- **Never hardcode the authoring worktree's issue #/path in an e2e test — derive
  `(path, issue)` from the live `git worktree list` at test time.** An e2e/CLI test that
  bakes in a specific issue number or worktree path (e.g. asserting issue 859 resolves to
  this checkout) passes only from inside that worktree, and reds the whole suite once the
  worktree is torn down and the suite runs on `main`. Instead read `git worktree list
  --porcelain` at runtime, pick a live issue-numbered worktree (prefer *this* checkout if
  it is one), and **skip** when none exists — so the test is worktree-agnostic. Precedent +
  exemplar: #895 (test_run_cmd coupled to the #859 worktree — closed) fixed exactly this in
  `_some_live_issue_worktree()` / `test_cli_resolves_a_live_worktree_from_its_issue_number`
  in `tests/test_run_cmd.py`.

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
  failing test. Bit **thrice**: `os.environ` at module top (#345, ~15 tests — pytest
  imports every test module at **collection**, *before* running any test, so a module-scope
  `os.environ.setdefault` runs once and leaks session-wide; set env only inside a test via
  `monkeypatch.setenv`, never at module scope), hand-restored
  `settings.load` (#453, ~19 tests), and a **cached-fake variant** (#550→#709): a test
  used `monkeypatch` *correctly*, but the fake `SysFont` product it created was cached in
  the **shared `text_renderer.font_cache`** singleton and outlived the patch (the cache
  holds the object, not the patched fn), reddening unrelated menu-render tests on reorder.
  **`monkeypatch` alone isn't enough when the fake lands in a shared cache — a test that
  injects a fake font/factory MUST flush the downstream cache in its own teardown**
  (`text_renderer.font_cache.clear()`). The autouse `_no_fake_fonts_leaked` guard in
  `tests/conftest.py` (#709) backstops this — it fails the *polluting* test by name (and
  evicts the fake so victims stay green) if a non-`pygame.font.Font` object is left in the
  shared cache. Font-stack usage + gotchas are written up in
  [docs/pygame-fonts.md](./docs/pygame-fonts.md) (§7).

- **A refactor/feature that EXPOSES a pre-existing, *unrelated* test failure — root-fix,
  never hide (ratified 2026-07-07, #550/#709).** When your reorder/cache-warming surfaces
  a latent test bug that isn't about your change's target, the *red gate* is not a `@todo`
  puzzle to defer — merge-gate/zero-tolerance (never merge red) outrank PDD. Resolve it to
  green via the cheapest **legitimate** rung, never a hidden one:
  - **Never** skip/quarantine the victim tests, and never dodge the trigger with a
    feature-local hack — both are fake green.
  - **A — trivial root-fix (default for a ≤~10-line, obviously-correct fix):** land it in
    the feature commit **with a documented note in the commit/close + a follow-up tracking
    ticket** (e.g. #550's inline `text_renderer` flush + this #709).
  - **B — non-trivial / risky fix:** **stop** — file the bug (its independent repro is the
    complaint), fix it first as its own reviewed unit (author ≠ reviewer), then rebase the
    feature. Available whenever the bug reproduces without the feature.
  - *Mechanical* test edits from a refactor (a renamed symbol, a moved seam) ride along
    freely; *behaviour/oracle* flips still go through the golden-regen author ≠ reviewer path.

## Agent tool-use (editing, worktrees & shell commands)

- **Read a file with the Read tool before your first Edit to it — `cat`/`grep`/`sed`/`head`
  via Bash does not count.** The Edit read-gate is satisfied only by the **Read tool** on
  that **exact path**; viewing the file through Bash leaves the gate unsatisfied and the
  first Edit fails with "File has not been read yet." (Logged repeatedly: errors 31/36/39/40,
  all `EDIT_PRECOND`.)
- **Edit the worktree path, not the main-repo absolute path.** `EnterWorktree` (see
  *Claiming work*) changes the session cwd, so **bare/relative** paths land in the worktree —
  but an **absolute main-repo path** in a tool call still writes to `main`, ignoring cwd.
  Editing `main` both pollutes its tree and does nothing for your tests: the suite imports
  the *worktree* copy of the package, so the edit you "made" isn't in the code under test (a
  phantom chase). After `EnterWorktree`, sanity-check `git -C <worktree> status --short` —
  your edits should show there, not in `main`. Recovery if you catch a main edit: re-apply it
  in the worktree, then `git -C <main> restore <files>` to revert main. (errors 207/#835,
  328/#967; worktree edit/run discipline #763.)
- **Don't put `\(...)` jq interpolation inside a single-quoted `gh -q`.** The shell
  mangles the backslashes before jq sees them, so `gh … --json … -q '"…\(.field)…"'` dies
  with a jq parse error (exit 1). Build the string with a plain jq pipe instead —
  `-q '[.labels[].name] | join(", ")'` or `-q '"#" + (.number|tostring) + " " + .title'` —
  or use `--template`, or one `-q '.field'` per value. (errors #155, #162 — each cost a
  failed `gh` call + retry.)
- **Don't hand-escape quotes inside a single-quoted `python3 -c`, especially in an
  f-string.** Once Bash is through it, the backslash-escaped quotes (`d[\"key\"]`) collide
  with the f-string's own quotes and Python dies with `SyntaxError: unexpected character
  after line continuation`. It's a shell-quoting × f-string interaction, not a Python bug,
  so it re-bites under time pressure. For anything past a trivial no-quote `-c`, use a
  heredoc (`python3 - <<'PY'`), a `gh -q '<jq>'` pipe, or write a scratchpad `.py`.
  (errors #93, #99.)

## Referencing code & docs

- **Point at named landmarks, not raw line numbers.** When an *authored* reference — a
  ticket, issue comment, review, commit message, or doc — points at a location, use a
  **stable landmark**. Line numbers drift the moment a file changes and then
  misdirect the next reader to the wrong (or deleted) line with no warning; a landmark is greppable and
  self-correcting.
  - **Code** → the **function / method / class name** + the **file path**
    (`build_stage()` in `pycats/sim/runner.py`), or the bare **symbol** when there's no
    enclosing definition (`LEDGE_GETUP_FRAMES` in `pycats/config/physics.py`) — never
    `runner.py:73` / `config.py:142`.
  - **Markdown docs** → the **section heading** (under `## Filing work` in RULES.md) —
    never `RULES.md:47`. (An authored doc also carries a provenance header — see
    *Authoring docs*.)
- A line number **may** ride along as a secondary, clearly-as-of hint (`~L73 at time of
  writing`), but never stand alone as the reference.
- **Carve-outs** — these don't rot, so a line number is fine: a **commit-pinned
  permalink** (`blob/<sha>/file#L73`) is a valid *primary* locator (it points at a frozen
  commit, not the moving branch), and **quoted tool output** (stack traces, `pytest` /
  `ruff` output, diffs) keeps its own line numbers. The rule governs the refs you *write*,
  not machine output you paste.
- **Gloss every ticket number inline.** Whenever you name an issue/ticket number in
  authored output — a reply, ticket, review, or doc — add a short one-line gloss of what
  it is on its **first** appearance, so the reader never has to recall or open the
  number: `#166 (the ledge-getup timing bug, closed)`, not a bare `#166`. A status tag —
  `(closed)` / `(in progress)` / `(new)` — is encouraged. Every *distinct* number gets
  its own gloss; later repeats of the same number don't need re-glossing. **Carve-out:**
  structured machine trailers (`Closes #N`, `Refs #N`, `Sequenced after: #N`) are
  tokens, not prose mentions — they take no gloss.

## Authoring docs

- **Every authored doc carries a provenance header at the top.** Any prose deliverable
  an agent writes — a `docs/research/*` findings doc, a spec, an ADR, a catalog, any
  standalone markdown produced as a ticket's artifact — opens with a one-line header,
  directly under the H1 title, naming **three** things:
  1. **Agent** — the authoring agent's fruit name (`FIG`, `CHERRY`, …).
  2. **Authored** — the absolute date `YYYY-MM-DD` the doc was written (never "today" /
     a relative date — matches the repo's absolute-date convention).
  3. **Ticket** — the issue the doc was produced for (`#N`).
- **Recommended format** — a blockquote line immediately below the H1, so headers are
  uniform and greppable:
  > `> **Agent:** FIG · **Authored:** 2026-08-07 · **Ticket:** #1298`
- **Why:** without the header, *who wrote a doc, when, and for which ticket* is not
  recoverable from the doc itself — you have to reverse it out of `git blame` + the
  filename. The header makes provenance self-contained and `grep`-able (`grep -rl
  '**Agent:**' docs/`).
- Related doc rules point at each other: the **findings-doc requirement** (under
  *Filing work* — every `research` ticket produces ≥1 findings doc) says a doc **must
  exist**; this rule says **how it's stamped**; **Referencing code & docs** says how to
  **point at** one (section heading, not a line number). Not in scope here: back-filling
  headers onto existing docs, or enforcing the header via tooling — file those separately.

## PM-parity markers (`⚠` / `🔬` / `❓`)

Inline glyph markers make unresolved-vs-Project-M work **greppable**. Use them at write
time. (Axis A of the labeling system #451; design #448; the human-facing key across all
three axes: **[docs/parity-labeling-legend.md](docs/parity-labeling-legend.md)** (#452).
Codebase audit + rules of record: `docs/research/2026-07-02-pm-parity-marker-audit.md`.)

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
  after **#407** found PM has no faithful number to copy). A truly un-pinned value
  **stays at its current number**, carrying its `⚠`/GUESS marker, until basis (1) or (2) exists.
- **Picking a surrogate is a decision, not a DEV edit.** When no faithful value exists,
  *choosing* one is a `decision:` ticket (e.g. **#491**); the ratified choice then becomes
  basis (2). Record which basis applies in the commit, the constant's comment, and its
  `combat/provenance.py` entry (**#233** / ADR-0003) as **FOUND** (sourced) or **TUNED**
  (designer-chosen) — never presented as sourced when it is a guess.
- **Routing a "source + pin a value" ticket** (which label, and how the steps chain; ruling in
  **#530**, `docs/research/2026-07-05-value-sourcing-classification.md`). The rule above sets the
  *basis* a value needs; this sets the **label** the sourcing work carries:
  - **Already sourced** in an in-repo `docs/research/*` finding → a single **DEV** (`enhancement`):
    swap the constant, record **FOUND**, cite the finding, land a proving test.
  - **Sourceable but not yet sourced** → **research → DEV**: the research finds and cites the value,
    then a DEV child (*blocked-by* the research) applies it.
  - **No faithful value exists** → **decision → DEV**: a `decision:` ticket where the human picks
    the surrogate (**TUNED**), then a DEV applies it — *choosing* is never a DEV edit.
  - **No `architect` label** for this work — the architect role maps to `research` (source it) or
    `decision` (invent it), not a separate label.
- This gates *changing* a value; the `⚠`/`🔬`/`❓` markers above only *label* an unpinned
  one — the two compose (a changed value should shed its `⚠` and land a `FOUND`/`TUNED` entry).
- **Use the named unit→px seam; don't inline the factor.** When converting Smash *units*
  to pixels in executable code, call the named seam — `combat/units.py::u(units)`
  (= `round(units * PX_PER_UNIT)`, integer-pixel per #80) for hitbox/hurtbox radii and
  offsets, or its float sibling `vel(units)` (= `round(units * PX_PER_UNIT, 2)`) for
  velocity/accel rates — never hand-write `round(x * PX_PER_UNIT)` or, worse, the bare
  magic `× 5.4`. Inlining re-introduces the manual math the seam exists to remove
  (`PX_PER_UNIT = 5.4`, `config/physics.py`). This has recurred in per-character movement
  authoring (ADR-0011, per-character grounded-speed model; #962, closed). **Carve-out:**
  the existing baked literals kept byte-identical under ADR-0003 C1 stay as-is, and their
  derivation **comments / provenance strings** cite `PX_PER_UNIT` by name (e.g.
  `round(3.1 * PX_PER_UNIT)`) — naming the factor rather than the magic `5.4` is the
  doc-form of the same rule.

## Read the source before asserting

- **Check a fact before you state it.** Before you assert or classify any fact that
  (a) touches an outside game — **Project M / Melee / Brawl** — or (b) is an **in-repo
  fact you're remembering instead of reading** and that feeds a commit, ticket, doc,
  classification, or closing summary, back it with a source you can point to: prefer the
  ticket **body** over its title, the **code** over memory, the **registry** over prose.
  The source is one of two:
  1. a **word-for-word quote from a primary source** (an outside game, or a `FOUND` value); or
  2. the **provenance record + the issue that decided it** (a pycats decision —
     `TUNED`/`DIVERGENCE`; `combat/provenance.py`, ADR-0003). A claim grounded in a pycats
     decision must be tagged **"not canon."**
- **No authority in hand → don't assert from a proxy.** Emit an **evidence-deviation
  notice** and get consent (interactive), or **withhold + log** the claim as a grounding
  debt (autonomous / fleet). A `GUESS`/unsourced value is a debt to drive to zero, never an
  unflagged assertion. The **`grounded-claim`** skill runs this reflex; **#575** is the
  detective backstop. (Protocol: `docs/superpowers/specs/2026-07-05-grounded-claim-protocol-design.md`;
  origin #571 / #611 / #620.)
- **A blocked fetch (4xx) on a wanted source is a pause, not a reroute.** When a
  `WebFetch` returns 4xx (402 paywall, 403 blocked, 404 not-found) on a primary or wanted
  source during research, **surface the blocked URL(s) to the human and pause before
  closing** — the human often has access and can paste the content, so rerouting straight
  to thinner secondary sources drops evidence that was one ask away. Log a
  **`NETWORK_FAIL`** row (see the log-error skill), and name the blocked URL(s) in the
  interim/closing comment. #1075 (RESEARCH: ROUNDS core mechanics — closed) closed on
  thinner sources because two Fandom pages returned HTTP 402 (error #417) — the human had
  them the whole time.
- **Read the module before asserting what it contains or that a capability exists — a
  shallow grep or an assumed shape is not evidence.** This is the everyday form of "code
  over memory" and applies to **any** claim about a file's contents or whether a capability
  exists in the repo, not only claims feeding a decision/artifact. A keyword `grep` **hit**
  locates a candidate to read; a `grep` **miss** proves only that *that spelling* is absent,
  not that the capability is (it may be named differently, split across modules, or built
  from primitives). Neither a grep result nor an assumed module shape substitutes for
  opening the module and reading the relevant code. Open it first, then assert.
- **Cite primary sources for parity/mechanics claims** (the PM instance of the reflex above).
  When asserting how Project M / Melee / Brawl behaves, pull a **verbatim quote** from a
  **primary source** — PMDT changelogs, rukaidata / `brawllib_rs`, OpenSA/dantarion,
  doldecomp — with the **URL + tier** (T1 primary / T2 secondary: SmashWiki, Liquipedia,
  Smashboards). **Label inference as inference** — never issue a **"refuted"/"confirmed"**
  verdict from a chain of reasoning over secondary facts; scope the verdict to what a primary
  quote supports and record the rest as a flagged **`gap`**. Flag Melee/Brawl/Smash-4/Ultimate
  values so they are **never attributed to PM unlabeled**. (Origin: #520 → correction #537,
  reframe #527, audit #536; ratified **#562**.) Two traps even with a primary in hand:
  **a verbatim quote isn't automatically confirmation** — it confirms only if it addresses
  *your* claim's character / version / context, not merely the same topic; and **a vague
  qualitative primary isn't a number** — "slightly faster" licenses no specific value, so
  record the number as a flagged **`gap`**, not a `FOUND`. The canonical PM evidence register
  is [`docs/project-m-rules-by-category.md`](docs/project-m-rules-by-category.md) (each
  mechanic → local doc + primary citation, gated by `tests/test_tuning_provenance.py`; parity
  front door [`docs/project-m-parity.md`](docs/project-m-parity.md)).
- **The verify-claims ledger lives outside the repo.** The claims ledger (`PYC-*` IDs,
  per-area subtrees, generated `INDEX.md`) was relocated to the sibling
  **`pycats-claims-data/`** — a plain untracked folder at `…/Study/Python/pycats-claims-data/`,
  outside the pycats tree, with no git history by design. `.claude/ledger.json` `dir` holds
  its absolute path; consumers resolve the ledger from there, not from an in-tree
  `claims-data/`. (#946.)

## Process lessons

Working-discipline lessons distilled from session retrospectives (TILs), codified here so
they outlive the session that surfaced them.

- **Calibrate before executing a planned sweep.** Before trusting a multi-module plan's
  ordering, recon the *current* state on disk — a module the plan lists may already be
  factored. Report an already-clean module as an explicit **finding**, not an unreported skip,
  so the plan's premise is corrected rather than quietly diverged from. (From the #410
  magic-number audit: combat/systems were already factored via ADR-0003; the debt lived
  in render/UI.)
- **An identity refactor needs an able-to-fail proof** (see *Fixing bugs*). A
  "behaviour-unchanged" refactor must be backed by evidence that behaviour did not change.
  Where goldens are thin (e.g.
  `screen_parity` is an FSM state-trace, not pixels), use a **before/after render-hash across
  the affected states**, and confirm the harness reds by flipping one constant before
  trusting a green. (Same able-to-fail discipline as *Fixing bugs* above; precedents #420 /
  #433 / #450.)
- **Research produces a design *choice*, not a unilateral fix.** When a parity fix collides
  with possible game-feel or design intent, surface the options to the reporter / designer as
  an A/B choice rather than auto-filing or auto-applying one branch — the research output is
  the *decision material*, not the decision. (E.g. #466 walk-off jump → A/B; #480 spawn
  model. Composes with *Changing values* above: picking a surrogate is a `decision:`, not a
  DEV edit.)
- **Lead with a recommendation, not "you decide."** When the human asks what to do, or is
  weighing a choice, give one opinionated, source-backed answer stated as your pick — not a
  neutral menu, not a punt. Voicing an opinion is free and is what they're asking for; the
  human gate (*Suggest, don't act*; "a question is not authorization") is on **doing** the
  outward or irreversible thing, not on saying what you'd do.
- **Surface a design fork before you settle it.** At any design/architecture decision —
  config schema, file layout, naming, data model, where something lives — put the options
  to the human (with your recommendation, per *Lead with a recommendation* above) and
  wait, rather than deciding unilaterally and revealing it in the closing summary. The
  design call is the human's. (Broadens "Research produces a design *choice*…" above
  beyond parity fixes; whether to commit/push is separately gated under *Closing work*.)
- **Flag evidence type: the human calls go/no-go.** When you review research/parity
  evidence, your job is to correctly categorize it — primary vs. inference, and where any
  gaps might be (see *Cite primary sources* under *Read the source before asserting*) —
  not to rule it too thin to build on. Whether to proceed on a Brawl-inherited value with
  no PM-3.6 primary or not, for example, is the human's call: present your categorization,
  plus your recommendation/suggestion if you have one plus your rationale — don't gate the
  work on your own judgement.

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
- **Use `make run-cmd`, don't hand-assemble paths.** The interpreter is **always** the
  main repo's `.venv` (worktrees have none), but the **working directory selects the code**:
  under `-m`, cwd is `sys.path[0]`, so `-m pycats.game` imports `pycats/` from whatever
  directory you `cd` into. Hand-typing a `WT=` path is the recurring mistake — a `WT`
  pointing at `main` launches the pre-change build and the reviewer sees the OLD behavior.
  Generate the command instead; it resolves an issue number / branch name / worktree path to
  the right worktree and fails loudly if none matches (never falling back to `main`):

        make run-cmd WHAT=<issue|branch|worktree-path>   # e.g. WHAT=859
        # prints:  cd '<resolved-worktree>' && make run

  `make run` resolves the main repo's venv from a worktree cwd
  (`VENV := $(GIT_COMMON)/../.venv/bin`), so no hand-typed `PY=`/`WT=` is needed.
  (`scripts/run_cmd.py <what>` is the same generator without `make`.)
  - **What it expands to** (moving parts — interpreter stays the main venv, only cwd changes):

        REPO=/abs/path/to/pycats; PY="$REPO/.venv/bin/python"   # ALWAYS the main repo's venv
        cd <REPO (merged) | worktree (unmerged)> && "$PY" -m pycats.game

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
- **Smoke-test the exact command before you hand it over.** Never surface a run/sim
  command you haven't run. Run the *exact* string first under a short auto-kill —
  `timeout 2 <command>` — and treat **exit 124** (the timeout killed an already-launched
  process) as pass; any other non-zero exit means it crashed at startup and must be
  fixed before handing over. This catches the malformed-command class: a wrong path, a
  bad flag, a missing module, or a stray empty env assignment. Testing a *near* variant
  does not count — #1086 (a storage-module refactor, closed) shipped a `-m pycats.game`
  launch carrying an empty `SDL_VIDEODRIVER=`/`SDL_AUDIODRIVER=` that crashed, verified
  only with `--help` (error #426). Smoke-test the verbatim `make run-cmd` output, not a
  paraphrase of it. (If the exact command needs a display the agent's headless box
  lacks, smoke-test it under `SDL_VIDEODRIVER=dummy` to confirm the entry point, paths,
  and flags resolve, and say that's what you did.)
- **Surface the run command *before* `pmtools close`, not after.** When closing a ticket
  for a runnable change, emit the exact full-path run command and **pause** so the human
  can launch and eyeball it *before* the merge — posting it after close denies them that
  pre-close launch. This holds for **any** runnable change, including new moves and combat
  data; don't judge a playable combat change "eyeball-exempt" and defer the run block to
  after close. #947 (DEV: Gnok smashes — closed) posted the run command only after
  `pmtools close` (COMPLIANCE_FAIL, error #307). (The run-command half of the *Human
  eyeball-approval gate*, Closing work step 4.)

## Producing visuals (renders / screenshots)

- **Don't produce renders or screenshots without explicit human authorization.** The
  agent must not, on its own initiative, generate a visual artifact for a human to look
  at — a game frame dump, a `scripts/compare_representative_frames.py` image, a Playwright
  browser screenshot, a plot/diagram PNG, or any other rendered image. **Suggesting** one
  is always welcome ("want a screenshot of X?"); **producing** one is gated on an explicit
  go-ahead.
- **Provide the command instead.** Give the human the exact command (full absolute paths)
  so they generate and inspect the visual themselves. For a live game run, that command
  comes from `make run-cmd` — see [Surfacing run/sim commands](#surfacing-runsim-commands).
- **Carve-out — test-internal render bytes.** Render/parity oracles and any golden
  generation that happens as part of running the suite are exempt: those bytes are consumed
  inside an assertion, not produced for a human to view. The rule targets visuals surfaced
  for inspection (attached, shown, or saved for the human).
- **Authorization is per-request.** A go-ahead for one visual is not standing permission
  for the next; re-ask. A human may grant standing/session permission explicitly.

## Claiming work

- **Every ticket is worked in a claimed worktree + issue branch — no exceptions
  without an explicit human OK for that specific ticket.** This is universal: DEV,
  RESEARCH, WRITER, ARC, `decision:`, no-code, and comment-only tickets **all** get a
  `pmtools claim <N> --as <fruit>` (which mints the claim ref + `.claude/worktrees/wt-<fruit>-<project>-N`
  on branch `br-<fruit>/<project>-N`) and an `EnterWorktree` into it before any edit,
  comment, ruling, or finding is written. **Rationale:** the worktree + issue-branch
  protocol is what lets the human see, at a glance, **which agent is working on which
  ticket** — `git worktree list` is the live board. Work done directly on `main` (or in
  an unclaimed checkout) is invisible on that board, so the human loses the ability to
  tell what is in flight and who owns it. The **only** way to skip the worktree is an
  explicit, per-ticket human go-ahead in the session.
  - **This claim/worktree requirement is separate from the close *path*, which
    does vary by type** (see "Closing work"): a `decision:`/commit ticket closes via
    `Closes #N` + `pmtools close`; a research / comment-only ticket closes via
    `gh issue close` + `pmtools release`. Both close paths still start from a claimed
    worktree — the type only changes how you *finish*, never whether you claim. Do not
    read "no-code tickets close differently" as "no-code tickets skip the worktree."
    (Prompted by #1307, where a `decision:` ruling was posted directly from `main`
    without a claim/worktree on the wrong belief that decision tickets skip it.)

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

- **Move the session into the worktree right after `pmtools claim` — call the
  `EnterWorktree` tool with the worktree path.** `claim` runs `git worktree add` (an
  external command): it creates the worktree directory on disk but does **not** change
  the session's working directory, so the shell stays pinned to the main checkout.
  Leaving it there forces a `cd <worktree>` prefix on every command and hides the working
  directory from the human — the footgun behind editing or running against `main` instead of
  the worktree (#763; error rows id=150 wrong-checkout, id=158 wrong run-command).
  `EnterWorktree` with the claimed path changes cwd for the session: bare commands run in the
  worktree, `CLAUDE.md`/memory reload for that directory, `pwd` is accurate, and the
  #769 run/sim `cd` becomes implicit. Do this before the suite run above so pytest
  imports the worktree's package. (Return to main at close time — see "Closing work".)

## Closing work

The fleet closes via **`pmtools close`**, which owns the racy push to `main` and
the gated worktree teardown. Follow this order — do **not** improvise:

1. **Work in your claimed worktree.** `pmtools claim <N> --as <fruit>` created it
   under `.claude/worktrees/wt-<fruit>-<project>-N` on branch
   `br-<fruit>/<project>-N` — the pmtools #128 "standard" mint shape (the legacy
   `<fruit>/issue-N` branch and old-canonical `…-<lang>-issue-N` forms still parse
   for back-compat). Note the branch and worktree-dir shapes differ:
   `.claude/orchestrate.json`'s `worktreeBranchPattern` parses the **branch column**
   of `git worktree list` (`br-<fruit>/<project>-N`), **not** the `wt-…` directory
   name.
2. **Re-run the full suite after your FINAL edit, before you commit.** The
   post-claim run (see "Claiming work") guards the *merge race* — a red inherited
   from another agent's mid-flight merge. It does **not** guard a red *you* introduce
   with a later edit: #757 dropped `evidenceDir` from `.claude/ledger.json` *after* its
   green post-claim run, and the broken `tests/test_ledger_config.py` merged anyway
   (fixed reactively in #762) — ruff had nothing to say about a broken Python assertion.
   So run the suite once more after your last change:

       SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
         /abs/path/to/pycats/.venv/bin/python -m pytest -q

   The `pmtools close` gate re-runs the suite too (step 5), so this is not the only net
   — but catching a red locally is faster feedback than a rejected merge.
3. **Commit on the feature branch, with `Closes #N` in the commit _body_.** The
   subject may keep the repo's `type(scope): summary (#N)` style, but the body
   MUST carry the `Closes #N` keyword: it is both the GitHub auto-close trigger
   *and* exactly what `pmtools close` scans for (and recovers on). `git log
   --oneline` only shows the subject — put the keyword in the body, not the title.
4. **Human eyeball-approval gate — for player-visible changes.** If the change is
   **player-visible** — anything a player sees on screen: rendering, UI/HUD text,
   layout, colors, animation, or screen flow — **show it to the human and get an
   explicit OK before you land it (step 6), even when the full suite is green.** A
   green suite proves behaviour/pixels are *stable*, not that they *look right*: the
   render-parity oracle is a byte comparison, not a judgment of appearance (#677), and
   #868 removed a HUD hint and merged before anyone eyeballed it. Surface the run/sim
   command (see [Surfacing run/sim commands](#surfacing-runsim-commands) — the run
   command is *how* the human eyeballs it) and wait for their confirmation; only then
   land. The human runs that command and inspects it themselves — the agent produces a
   screenshot for the gate only on explicit request (see [Producing visuals](#producing-visuals-renders--screenshots)).
   **Carve-out — no eyeball OK needed for a non-visible change:** logic, tooling,
   docs, or a render refactor proven byte-identical by a render-hash / parity oracle.
   (Ratified in-session 2026-07-21; #873.) **Apply this carve-out narrowly:** it
   exempts only a change whose byte-identity is *proven* by the oracle — not any change
   that merely touches the render path. #900 (a `render_battle` package split) was
   closed under this carve-out with no eyeball check and logged as a `COMPLIANCE_FAIL`
   (error #264): "it's a render refactor" is not the exemption; "the parity oracle shows
   byte-identical output" is. The sibling human gate for `research` tickets —
   completeness of the findings — is step 5 below.
5. **Human completeness gate — for `research` tickets.** Before you close a
   `research`-labelled ticket (whether via `pmtools close` or, for a no-code ticket,
   `gh issue close` + `pmtools release`), **present the findings doc — or a summary of
   it — to the human and wait for an explicit close go-ahead.** A findings doc can *look*
   complete to the agent yet read as incomplete to the reporter: #1317's spawn/respawn
   catalog closed with all of Part A (initial-spawn) marked GUESSED — no quoted PM value
   — and the reporter judged the research unacceptable only *after* the close. This gate
   is the RESEARCH twin of the player-visible eyeball-OK gate (step 4): the same "don't
   close until the human OKs" shape, keyed on ticket **type = `research`** rather than on
   visibility. Name for the human what to check — unsourced / GUESSED rows, an unanswered
   question, a missing or thin gap table, a repro that never landed — so the check is
   about the **completeness/quality of the findings**, not process. The go-ahead is a
   **precondition** of the close, not a replacement for the green-suite (step 2) or the
   error self-audit (step 7); those still stand. (The findings-doc requirement itself
   lives in [Filing work](#filing-work) → "Every `research` ticket produces ≥1 findings
   doc". Basis: #1317; ratified in-session 2026-08-07, #1320.)
6. **Return the session to main with `ExitWorktree keep`, then land + tear down with
   `pmtools close <N>` from the main checkout.** Because you entered the worktree at
   claim time (see "Claiming work"), the session is now *inside* the worktree — call
   the `ExitWorktree` tool with `action: keep` to move it back to the main checkout
   first. Use **`keep`**, never `remove`: `pmtools close` owns the teardown, so
   your job is only to leave the directory, not delete it. Then run `close` from the
   main repo root — it resolves the worktree + branch from the issue number
   (pmtools#104, `008cb2a`), so it must run from main, **not** from inside the worktree
   it deletes. Before pushing, `close` runs the `close.verify` gate (cwd=worktree, so
   it checks the code being merged): `ruff format --check` + `ruff check` on `pycats/`,
   then the **full pytest suite** under the SDL dummy drivers (`SDL_*=dummy … python -m
   pytest -q`, added #764); any failure aborts the close before anything reaches `main`.
   So a green close *does* mean the suite passed at merge — the pytest step is why;
   before #764 the gate was ruff-only and a broken test could merge green-gated (#757→
   #762). Then it loops fetch → rebase `origin/main` → push `HEAD:main` until it lands,
   then — only after confirming the commit reached `origin/main` — deletes the claim
   ref, closes the issue, and removes the worktree + branch. Exiting to main first
   keeps your shell from being stranded in the deleted directory. (No-code
   decision/research tickets close via `gh issue close` + `pmtools release`; the same
   `ExitWorktree keep` applies before running them from main.) There is **no post-close
   `ExitWorktree`**: `close` has already removed the worktree, so a post-close
   `ExitWorktree({remove})` is wasted motion and refuses anyway — the session no longer
   owns the directory (#708, error #187). The only `ExitWorktree` is the `keep` above,
   *before* `close`.
7. **Run the pre-close error self-audit.** Before posting the closing comment,
   re-read the session from claim → now, enumerate every log-error trigger event
   (including resolved ones), log any missing rows (`pmtools error log`), and include
   one of `error self-audit: N row(s) logged (#…)` or `error self-audit: no loggable
   errors this session` in the closing comment. See the **log-error** skill for the
   trigger list + fields. This turns silence into a checkable acknowledgement — a
   clean session and a forgotten log stop looking identical. The audit line captures
   only errors up to the moment you write it — any error during post-close cleanup (the
   `ExitWorktree`, a final verify) happens *after* that checkpoint and is never counted
   (#708's refused `ExitWorktree({remove})`, error #187, landed there). Re-scan the
   cleanup phase before treating the session as done; if cleanup errors, log the row and
   amend the audit line.

**Never `git push` to `main` directly, and never manually `git merge` your feature
branch into `main`** — **unless a human explicitly authorizes a direct merge + push
for a specific change in the current session.** `pmtools close` exists to make the
close atomic and race-safe: a hand-typed push-then-teardown can tear down a worktree
*after* a race-rejected push, destroying work that is still only local (the lccjs
"#200 incident"). Hand-closing also leaves a dangling `refs/claims/issue-N` that
`pmtools close` would otherwise sweep.

**The explicit-authorization carve-out.** When a human, in the current session,
explicitly authorizes a direct merge + push for a specific change, a direct `git
merge` + `git push origin main` is permitted — the authorizing human owns the race
and accepts it. This is for **attended, in-session** work only; for
unattended / fleet / ticket-close work the default stands (route through `pmtools
close`). The go-ahead permits the *push route*, **not** skipping the gate: the change
still ships with the suite green and the pre-close error self-audit done, and a
hand-close should still clean up its `refs/claims/issue-N` (via `pmtools release` or
by deleting the ref). Absent an explicit in-session go-ahead, always route through the
tool. (Basis: error id=74 — an agent refused a direct commit+push and invented a
review-gated merge flow this repo doesn't have; #600.)

**pycats specifics (differences from lccjs):**

- **Velocity is on** (`storage.velocity.enabled = true`, enabled 2026-07-13) — closing a
  code ticket requires a **velocity row first**, or `pmtools close` blocks with a
  velocity-row guard (`no velocity row for #N … Log your session first`). Log it before
  closing:

      pmtools velocity log '{"ticket":N,"role":"DEV","agent":"<fruit>",
        "started_iso":"<ISO>","finished_iso":"<ISO>","actual_min":<A>}'

  then re-run `pmtools close <N>`. This mirrors the `puzzle-velocity` / write-til flow.
  (History: velocity was off at repo setup — a deliberate choice, not an oversight — and
  turned on 2026-07-13; every pycats velocity row is dated 2026-07-13+.)
- **No code markers** — pycats does not use `@todo`/`@inprogress #N` markers, so
  there is nothing to delete in the close commit; just include `Closes #N`.
- **The errors store is live** (`storage.errors.enabled = true`) — `pmtools error
  log '<json>'` records to `~/.pmtools/pycats/pmtools.db`. The step-6 self-audit
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
  directory (`getcwd: cannot access parent directories`, with a stale
  `wt-<fruit>-<project>-N` in your prompt) until you `cd /abs/path/to/pycats`. From-main (pmtools#104) avoids
  all of this — which is why it is the default in step 5.
- **Post the closing comment from `<main>` (where you already are)**, and include the
  step-6 `error self-audit: …` line:

      gh issue comment <N> --body "Closed in <sha>. <summary>
      error self-audit: no loggable errors this session"
- **No-code tickets close differently — but are still claimed + worked in a
  worktree.** This bullet is about the *close path*, not whether you claim: every
  ticket is claimed into a worktree first (see "Claiming work" → the universal
  claim/worktree rule). `pmtools close` needs a `Closes #N` *commit* to land and
  verify; a **research / comment-only** ticket has none. Close those with `gh issue
  close <N>` (after posting the ruling/finding as a comment), then **`pmtools release
  <N>`** to drop the claim ref + worktree that the claim created. Note `release` takes
  the issue number **positionally** — `pmtools release <N> [--force]` — and has **no
  `--as` flag** (unlike `claim`); `pmtools release --as …` errors with `unknown arg: --as`.
  Do **not** fabricate a no-op commit just to satisfy `pmtools close`.
- **Closing a `decision:` ticket appends a Decision Log row.** When you close a
  ratified `decision:` ticket, append one row to `docs/decisions-ledger.md`
  (`date · issue # · area · one-line ruling · record`) — the append-only index of
  game-design rulings ([ADR-0007](adr/0007-decision-ledger.md); complements ADRs and
  `combat/provenance.py`, does not replace them). **Append-only:** a reversal is a new
  row citing the superseded issue, never an in-place edit. Because that row is a
  committed artifact, a `decision:` ticket closes via the **normal `Closes #N` +
  `pmtools close`** path — *not* the commit-less `gh issue close` + `pmtools release`
  path above (which stays for research / comment-only tickets). Convention basis:
  #705 / ADR-0007.

## Editor repo (`pycats-editor`, cross-repo work)

Some tickets filed in **pycats** track work in the **separate `pycats-editor` repo**
(`/home/avi/Documents/Study/Python/pycats-editor`), which couples to pycats via an editable
install (not a declared dependency) and uses a `src/` layout (`src/pycats_editor`). The
ticket lives in pycats; the code lives in the editor repo — which crosses up several defaults:

- **Claim + worktree go in the *editor* repo — never edit its `main` directly.** Claim mints
  a worktree under `pycats-editor/.claude/worktrees/wt-<fruit>-editor-<N>` on branch
  `br-<fruit>/editor-<N>` (note the **`editor-` project token** — omitting it is
  off-convention: #1154, err #472). Editing the editor's `main` uncommitted is a
  `COMPLIANCE_FAIL` (#1139 — editor save-not-byte-identical, closed; err #456). The editor
  has **no pmtools close**, so land the branch by hand: `git commit` → `git merge --no-ff`
  → `git push origin main`.
- **Run `pmtools` from a *pycats* cwd, not the editor cwd.** pmtools keys its store off the
  cwd's repo, so any pmtools call from `pycats-editor/` writes a stray
  `~/.pmtools/pycats-editor/pmtools.db` instead of the pycats store (#1139, err #457). Editor
  tickets are pycats tickets — run pmtools from a pycats checkout.
- **Test worktree editor code with `PYTHONPATH=<worktree>/src`.** The editable install pins
  imports to **`main`**'s `src/`, so a plain test run exercises main's code, not your
  worktree's. Point `PYTHONPATH` at the worktree's `src/` so the suite imports what you
  changed (the editor analogue of the *phantom chase* under *Agent tool-use*).
- **Close editor tickets via `gh issue close` + `pmtools release`** — there is no pycats
  commit to carry `Closes #N` (the code landed in the editor repo), so the commit-based
  `pmtools close` path doesn't apply. Post the closing comment, `gh issue close <N>`, then
  `pmtools release <N>` to drop the claim ref + editor worktree. (Same shape as no-code
  tickets under *Closing work*.)
- **Editor in-flight = a live worktree in `pycats-editor/.claude/worktrees/` + a
  `refs/claims/issue-N` on the *pycats* origin.** The claim ref lives on pycats (the ticket's
  home); the worktree lives in the editor repo — so `git worktree list` in *pycats* won't
  show it. Check the editor repo's worktree list.
