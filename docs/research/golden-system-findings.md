# Golden-test system — how it works (plain English) + option space

**Ticket:** #992 (RESEARCH, moderate). **Role:** knowledge-capture + option space.
**Status:** findings only — no build, no pick, no spec. Any improvement in Part 2 is a
follow-on DEV/ARC ticket downstream of this doc.

**Motivation:** during #979 (the left/right move-speed fix) the mandatory golden
"re-baseline" was a source of confusion — it was not obvious what a golden *is*, what
gets saved where, or why a golden failed. This doc explains the system in plain English
and then lays out concrete ways to make it more legible/valuable.

---

## Part 1 — How goldens work today (plain English)

### The one-sentence version

A **golden test** runs a fixed, deterministic simulation, writes down exactly what
happened, and on every future run re-runs the same sim and checks that *exactly* the same
thing happened again. If a code change moves the sim, the golden fails — which is either a
bug you just caught, or a change you meant to make (and must then re-record on purpose).

Nothing about a golden is random or wall-clock-dependent: same inputs → same frames →
same recorded bytes. That determinism is what makes byte-for-byte comparison a valid
regression detector.

### The two files per scenario (this is the part that confuses people)

Each sim golden scenario saves **two** files under `tests/golden/`:

| File | What it is | Readable by a human? | Size |
|---|---|---|---|
| `<name>.json` | The **oracle** — the full per-frame recording of the whole sim. Every frame, every fighter's position/velocity/state/percent/lives, every active hitbox. This is the byte-exact detector: it fails on *any* difference, however tiny. | No — it's a large opaque blob (e.g. `combat.json` ≈ 163 KB, ~754 frames). | big |
| `<name>.summary.json` | The **digest** — a tiny semantic summary of the same run: frame count, final phase, winner, how many frames had an active attack, and per-fighter {states reached, lives start·end·min, max percent, KO frames}. | **Yes** — ≈0.6 KB of pretty-printed JSON that git-diffs cleanly. | tiny |

The digest is the human-facing layer. When something changes, you read the *summary* diff
(a few readable lines like "P2 max percent 88.14 → 85.14, KO frame 601 → 600"), not the
opaque blob. The blob is only there to catch changes the summary is too coarse to notice
(a 1px position shift, say).

Concrete example — `tests/golden/combat.summary.json` records that in the combat scenario,
Nalio (P1) never takes damage and Birky (P2) reaches 85.1394% and is KO'd at frame 600,
with 44 attack-active frames and no winner declared yet at the end. That's the whole story
of a 754-frame fight in ~40 readable lines.

### The engine: `check_or_update` (`tests/golden_util.py`)

Every golden test ends with one call: `check_or_update(name, snaps)`. It has exactly two
modes, chosen by an environment variable:

- **Check mode (default, `PYCATS_UPDATE_GOLDENS` unset):**
  1. Compute the summary of this run and assert it equals the committed
     `<name>.summary.json` — **so a behaviour change fails first with a small readable
     diff**, naming the field that moved.
  2. Then assert the full serialized run equals the committed `<name>.json`. On mismatch
     it reports the **first differing frame** (index + a truncated dump of both sides) so
     you can localize the divergence.
  3. If either committed file is missing, it fails and tells you to record it.

- **Record mode (`PYCATS_UPDATE_GOLDENS=1`):** it does **not** compare — it *overwrites*
  both `<name>.json` and `<name>.summary.json` with this run's output and passes. This is
  the "re-baseline"/"regen": you are declaring "the new behaviour is now the expected
  behaviour."

So "regen the goldens" = "run the sim once more and save its current output as the new
baseline." Nothing more magical than that. The danger — and the reason for the review
protocol below — is that record mode passes *unconditionally*, so it will happily bless a
regression as the new normal if you don't check what changed.

### What gets recorded — `serialize` and `summarize`

- `serialize(snaps)` — turns the per-frame snapshot list into one deterministic JSON
  string (tuples → arrays, no whitespace). This is the byte-exact oracle content.
- `summarize(snaps)` — walks the same snapshots and distils the semantic digest. It reads
  each fighter row **by name** (`PlayerSnap(*row)`), so the snapshot tuple can grow new
  trailing fields without breaking the summary (that's how the `character` field was added
  later without touching this code).

### The scenarios (`tests/test_golden.py`)

Three deterministic battles are locked:

| Scenario | What it exercises | Who plays |
|---|---|---|
| `default` | 200 frames driven by the scripted default timeline — general movement/idle behaviour. | Nalio vs Nalio |
| `combat` | A scripted combat script + 240-frame tail that racks damage with jabs then lands a fully-charged forward-smash for a real side-blast KO — exercises `hurt` and `ko`. | Nalio vs Birky |
| `two_npc` | 600 frames with **both** fighters driven by AI controllers (attacker vs follower) — locks the dual-controller code path; seeded RNG pinned for determinism. | AttackerController vs FollowerController |

Each also asserts a couple of non-vacuity guards inline (e.g. combat asserts `hurt` and
`ko` are actually reached; two_npc asserts both fighters actually moved) so the golden
can't quietly degrade into "nothing happened."

### The other two golden-bearing modules

`tests/golden/` is not only the sim scenarios. Two more modules honor the same
`PYCATS_UPDATE_GOLDENS=1` flag:

- **`tests/test_golden_summary.py`** — unit tests for `summarize()` itself (does it count
  frames, dedupe states, detect KO frames and the lives arc, count attack frames?). These
  don't read a committed file; they guard the digest logic that the review protocol relies
  on. If `summarize` were wrong, the readable diffs would lie.
- **`tests/test_screen_parity.py`** — a different kind of golden: it records the
  **screen-flow transition sequence** (main_menu → options → char_select → playing →
  pause → win_screen …) as `tests/golden/screen_parity.json`. This is a small FSM-trace
  blob, **not** a pixel/sim recording and it has **no** summary sidecar — you review its
  diff directly. It exists because the old second screen engine was deleted (ADR-0002); the
  frozen trace stands in for the deleted engine so the surviving statechart engine still
  has something to be checked against.

> Note the naming trap: `screen_parity.json` is a *screen-flow FSM trace*. It is not a
> render/pixel test and not a per-frame sim snapshot. A render-only or default-flip change
> generally does **not** touch it; a change to the menu/screen graph does.

### The regen/review workflow (`tests/golden/REGEN_PROTOCOL.md`)

When a code change legitimately moves the sim, the goldens must be re-recorded — but
**reviewed, not rubber-stamped**. The protocol:

1. **`make goldens`** — runs the three flag-honoring modules with
   `PYCATS_UPDATE_GOLDENS=1` in a headless env, rewriting every `<name>.json`, its
   `.summary.json`, and `screen_parity.json` in one command, then prints a review reminder.
2. **Read the sidecar diffs, not the blob:** `git diff tests/golden/*.summary.json`. For
   every changed field, confirm a specific code change in the *same* diff explains it. The
   protocol lists red flags: a KO **disappearing**, `lives_end` rising, `percent_max`
   dropping toward 0, or a state like `hurt`/`ko` no longer reached — these usually mean
   combat got *weaker*, i.e. a regression you'd be laundering into the baseline.
3. **Cross-check the raw goldens** (`git diff --stat tests/golden/*.json`): every raw
   change should map to an intended sidecar change — except a pure position tweak, which
   can move the raw without moving the sidecar (expected).
4. **Explain it in the commit** — which behaviour changed and why the regen is semantic,
   not blind.
5. **Re-run the suite** after regen.

There is also a hard interlock (ADR-0003 / #233): if a regen is justified by changing a
combat/physics **tuning constant**, the same diff must update that constant's `Provenance`
row (`pycats/combat/provenance.py`) or `tests/test_tuning_provenance.py` reds — so a value
change can't produce a golden regen without also updating its documented provenance.

### What a failure looks like in practice

- **Behaviour change** → summary assertion fires first: a small readable diff naming the
  field that moved ("P2 percent_max 88.1394 → 85.1394"). This is the fast, legible signal.
- **Sub-semantic change** (e.g. a 1px position drift the summary doesn't track) → the raw
  `<name>.json` comparison fires with "first divergence at frame N" + a truncated dump of
  the actual vs expected frame.
- **Missing file** → "Golden file missing … run with PYCATS_UPDATE_GOLDENS=1 to record it."

### #979 in these terms (the concrete case that motivated this doc)

The move_rect fix changed horizontal stepping, which legitimately moved two of the sims.
Only fields that trace to horizontal rounding changed: `combat.summary.json` KO frame
601→600 and P2 `percent_max` 88.1394→85.1394, plus one line each in three raw `.json`
files; `default.summary.json` and `two_npc.summary.json` were unchanged. That diff pattern
— traceable, small, no red-flag fields — is exactly what a *legitimate* regen looks like.
The re-baseline was collateral of the fix, **not** the proof of the fix (the proof was
`tests/test_move_rect_symmetry.py`). Conflating "the goldens changed" with "the fix works"
was the confusion this ticket captures.

---

## Part 2 — Option space to make it more accessible/valuable

Enumerated candidates with tradeoffs. **No recommendation and no prioritization** — each
is a potential follow-on ticket. Grouped by theme.

### A. Legibility at failure time

**A1. Auto-print the summary diff on a golden failure.**
Today check mode reports the first differing frame (raw) and, separately, the summary
mismatch as text. It does not show a *field-level* summary diff (expected vs actual,
per changed key) in the pytest output.
- *Pro:* the cause is legible without any manual `git diff` step — the failure output
  itself says "percent_max 88.14 → 85.14." Lowers the barrier for someone who's never
  seen the system.
- *Con:* more formatting code in `golden_util`; risk of a noisy dump if many fields
  change. Needs a compact "only changed keys" renderer.

**A2. First-divergence context, not just the single frame.**
The raw failure prints one frame. It could also print which *fighter/field* first diverged
and a few frames of lead-in.
- *Pro:* localizes sub-semantic drift (the 1px case) far faster.
- *Con:* the raw blob is deliberately opaque; risk of re-inventing the summary layer at
  the wrong altitude. May be redundant once A1 exists for the common case.

### B. Discoverability / onboarding

**B1. A plain-English onboarding doc + glossary, linked from the contributor guide.**
Define "golden", "oracle", "digest/sidecar", "re-baseline/regen", "check vs record mode"
in one place (this Part 1 could seed it).
- *Pro:* removes the exact confusion #979 hit; cheap; no code risk.
- *Con:* docs drift from code unless linked from the modules themselves; needs an owner to
  keep current.

**B2. Point the code at the doc.** Add a one-line "new here? see docs/…/golden-system"
pointer in `golden_util.py` and the failure message.
- *Pro:* discovery happens exactly when someone hits a golden for the first time.
- *Con:* trivial but another string to keep in sync.

### C. Inspecting what a golden actually contains

**C1. A "golden explainer" command** — e.g. `make golden-show NAME=combat` that prints the
summary in prose ("754 frames, Birky KO'd at frame 600 at 85% …") without running pytest.
- *Pro:* lets you understand a scenario without reading JSON or the test.
- *Con:* new surface to maintain; overlaps with just reading the sidecar.

**C2. A replay-watch mode for a recorded golden.** There is currently **no** way to *watch*
a committed golden play back; `watch.py` re-simulates live (it is not a byte-exact replay
of the saved frames). A viewer that renders `<name>.json` frame-by-frame would make a
golden visually inspectable.
- *Pro:* turns an opaque recording into something you can see; strong for reviewing a regen
  ("does the new combat *look* right?").
- *Con:* biggest build of the set — needs a renderer that consumes the snapshot schema;
  schema-coupling means it must track snapshot shape changes; arguably out of proportion to
  how often goldens are reviewed.

### D. Coverage

**D1. Document (and then close) coverage gaps.** Enumerate what is *not* locked by a
golden: which characters (only Nalio/Birky appear in sim goldens today), which
moves/mechanics, which scenarios (e.g. no ledge/recovery golden, no projectile golden).
- *Pro:* makes the blind spots explicit; each gap becomes a candidate golden.
- *Con:* more goldens = more regen surface and more to review on every intended change;
  coverage for its own sake can lock in low-value scenarios.

**D2. A per-character movement golden.** Given #979 was a per-character movement bug, a
small golden that exercises each cat's walk/dash/run both directions would have caught it.
- *Pro:* directly guards the class of bug that motivated this work.
- *Con:* overlaps with the targeted `test_move_rect_symmetry.py`; a golden is a coarser
  tool than a focused assertion for this specific invariant.

### E. Guardrails against rubber-stamped regens

**E1. Require a reason line per changed summary field at regen time.**
E.g. `make goldens` refuses to leave changed sidecars uncommitted without an accompanying
note, or a commit-hook checks that a golden change ships with a rationale.
- *Pro:* structurally enforces the REGEN_PROTOCOL step that's currently honor-system.
- *Con:* friction on every legitimate regen; hard to make the check meaningful rather than
  a rubber-stamp of its own ("reason: intended").

**E2. CI annotation of golden changes.** Have CI post the summary diff on any PR that
touches `tests/golden/*.summary.json`, so a human reviewer always sees the semantic delta.
- *Pro:* review happens in the PR, where a second person can catch a laundered regression.
- *Con:* depends on CI/PR workflow this project may not run; no effect on local-only work.

### F. Naming / structure

**F1. Clarify the `screen_parity.json` naming.** It reads like a render/pixel parity file
but is a screen-flow FSM trace with no sidecar — a known trip hazard.
- *Pro:* removes a real source of "did my render change break parity?" confusion.
- *Con:* renaming a committed golden + its test references is churn for a naming-only gain.

**F2. Co-locate a per-scenario README.** A one-liner per scenario ("combat = Nalio fsmash
KOs Birky off the side") next to the goldens.
- *Pro:* answers "what is this scenario?" at the point of the file.
- *Con:* another doc to keep in sync with the test docstrings that already say this.

---

## Out of scope (restated)

- Building or configuring any Part 2 option.
- Picking or prioritizing among them, or writing a spec — that is a follow-on ARC/decision
  ticket with the human, downstream of this doc (research reports findings + option space
  only).

## Grounding pointers

`tests/golden_util.py` (`check_or_update`, `serialize`, `summarize`), `tests/test_golden.py`
(the 3 sim scenarios), `tests/test_golden_summary.py` (digest unit tests),
`tests/test_screen_parity.py` + `tests/golden/screen_parity.json` (screen-flow trace),
`tests/golden/REGEN_PROTOCOL.md` (review protocol), the `goldens` target in `Makefile`,
`pycats/combat/provenance.py` + `tests/test_tuning_provenance.py` (the tuning interlock,
ADR-0003/#233). Related: #979 (the fix whose re-baseline motivated this), #985 (Rect-write
audit follow-up).
