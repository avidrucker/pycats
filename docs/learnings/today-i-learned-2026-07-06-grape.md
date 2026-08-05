# TIL 2026-07-06 — GRAPE

**Context:** A three-ticket session — an architect spike (#507, dual-surface demo/sim playback), a
tooling clone + gated recipe (#614, brawllib_rs for PM move-data datamining), and a follow-on epic
(#619) — that closed by filing a machine-provisioning ticket in a *different* repo (the dotfiles
`linux-mint-setup#2`). The through-line: ground every claim in a real source, name the structure
before designing on top of it, and respect the gates (human ratification, dependency approval, repo
ownership) instead of stepping over them.

---

## 1. Verify a tool against its own source before writing how to run it

**What happened:** #614 wanted a "run recipe" for brawllib_rs — how to point it at PM 3.6 `.pac`
files and emit move data. I did **not** write the invocation from memory of how Rust CLIs usually
look. I read the clone's `readme.md`, then the actual `examples/*.rs` sources (`dump_fighter`,
`high_level_frame_data`, `first_active_frames`), then grepped `src/high_level_fighter.rs` for
`Serialize` and the hitbox field names. Every line of the recipe is grounded: the `-d`/`-m`/`-f`/`-l`
flags came from the example's `getopts` block; the subaction→move map (`FSmash → AttackS4Start`) came
verbatim from `first_active_frames.rs`; the "serde is present but `serde_json` is not" caveat came
from `Cargo.toml`.

**What I learned:** This is the same discipline as "cite the primary source, don't infer" (my PM-parity
lesson), applied to *tooling*. A recipe written from familiarity looks right and fails on first run —
wrong flag names, an assumed JSON exporter that isn't wired, a subaction name that doesn't exist. The
grep for `serde_json` is the tell: it turned a confident "emit JSON with `--json`" into an accurate
"JSON needs a small dev-dep add; `bincode` is already here." Familiarity is a hypothesis; the source
is the fact.

**The rule:** **Before documenting how to run a tool, read its source (readme, examples, manifest, the
struct fields) and ground every flag/name/capability in what's actually there — never transcribe from
how similar tools usually work.**

---

## 2. Name the structural asymmetry before designing a shared seam

**What happened:** #507's job was to let one demo definition drive two surfaces (terminal CLI + a
future in-game tutorial screen) without duplicating interaction logic. The unlock wasn't a feature —
it was noticing the two surfaces have **inverted control flow**: the CLI's `run_battle` owns a
*blocking pull loop* (the presenter freezes it to dwell — golden-safe *because* the sim can't advance
while blocked), whereas the in-game FSM owns cadence and **cannot block** (it must pump input and
render every frame). Once I named that asymmetry, the seam was obvious: you can't reuse the loop, so
decouple "advance one frame" from "the loop that calls it," and make the interaction logic a *pure,
non-blocking per-frame reducer* both surfaces tick. It also immediately killed the tempting-but-wrong
option ("embed `run_battle` in the tutorial screen") — that inherits the blocking loop and freezes the
FSM.

**What I learned:** When two subsystems must share logic, the first question isn't "what's the shared
interface" — it's "how do their control-flow / ownership models differ?" The asymmetry is what makes
the naive shared interface a trap. Naming it first turns a vague "find an abstraction" into a forced
move.

**The rule:** **Before proposing a seam between two subsystems, name their control-flow/ownership
asymmetry explicitly — the seam falls out of the asymmetry, and it exposes the naive-reuse trap the
asymmetry sets.**

---

## 3. A ratification gate means file + present + hold the close — not auto-close

**What happened:** #507 pre-filed its implementation children (#514/#515) as **blocked until the
design is confirmed thorough by a human — ratified, not merely present**. So when the design doc was
done I committed it with `Closes #507` but **did not run `pmtools close`**. I presented the design and
the two open decisions via a question prompt, and only after the human ratified did I close #507, post
the ratification comment, and remove the `blocked` labels from #514/#515.

**What I learned:** The fleet reflex is commit-`Closes #N`-then-`pmtools close` in one motion. An
explicit human-in-the-loop gate overrides that reflex: the deliverable being *filed* is necessary but
not *sufficient* to close when the ticket's own contract says a human must confirm quality first.
Committing early (capturing the work) and holding the close (respecting the gate) are separable — do
both.

**The rule:** **When a ticket or its children encode an explicit human-ratification gate, file/commit
the artifact but hold the close and present for sign-off — "filed" ≠ "ratified," and the close is the
human's to authorize.**

---

## 4. Gates nest, and provisioning work belongs in the repo that owns the machine

**What happened:** #614 had a clean split — the *clone* is fine to do now, but *running* it is gated
on human approval of a Rust toolchain (system install) + copyrighted PM `.pac` files. I cloned + wrote
the recipe, and parked the run. Two subtleties surfaced: (a) the gate **nested** — even the JSON-emit
path had its own smaller gate (`serde_json` isn't a dep, so adding it is itself a dependency decision),
which I flagged rather than quietly stepping over; and (b) when the human then asked to "update my
machine's tooling," the right home was the **dotfiles repo** (`linux-mint-setup`), not pycats — machine
provisioning is a dotfiles concern, and that repo has its own conventions (plain GitHub labels, no
`area:*` taxonomy, no pmtools), which I checked before filing `#2` there.

**What I learned:** "Don't install without approval" isn't a single checkpoint — a gated task can hide
a second gate one layer down (the JSON exporter's dep). And separation-of-concerns applies to *where a
ticket lives*, not just what code goes where: a game repo shouldn't host a "install Rust on my laptop"
task. Route provisioning to the machine's repo; route app work to the app's repo.

**The rule:** **When parking a gated task, scan for nested gates and flag them too; and file each piece
of work in the repo that owns that concern — machine provisioning → dotfiles, app work → the app repo —
using that repo's own conventions.**

---

## What landed

| Artifact | Change |
|---|---|
| #507 | Design doc `docs/research/2026-07-05-demo-sim-redesign.md`; ratified by human; closed (`0f588d6`) |
| #514 / #515 | `blocked` removed on ratification; sequencing note (#514→#515, same-function collision) posted |
| #619 | Filed — small epic: in-game tutorial simulations (steppable runner + tutorial screen), post-v1 |
| #614 | brawllib_rs cloned to `~/Documents/Study/Rust/`; gated recipe `docs/tooling-brawllib-rs-datamine-recipe.md`; closed (`951a3e88`) |
| linux-mint-setup#2 | Filed in the **dotfiles** repo — add a `rust` install.sh section (cargo/rustc for brawllib_rs); `.pac` as user-provided convention |
| `pmtools` errors | id=79 (GH_INFO — `gh issue view N --comments -q '.comments[]'` silently empty; use `--json comments -q`) |

## Open threads
- **#514 / #515** — near-term CLI slices, now unblocked; sequence #514 → #515 (both edit `LivePresenter._hold`).
- **#619** — in-game tutorial epic; children (steppable runner, then tutorial screen) filed one at a time, after #514/#515.
- **linux-mint-setup#2** — the Rust-toolchain provisioning that unblocks the #614 datamine run; awaits the human running `./install.sh rust` + supplying `.pac` files.

## Related artifacts
- Issues: pycats #507, #514, #515, #619, #614; dotfiles `linux-mint-setup#2`
- Docs: `docs/research/2026-07-05-demo-sim-redesign.md`, `docs/tooling-brawllib-rs-datamine-recipe.md`
- Prior TILs: [GRAPE 2026-07-05](./today-i-learned-2026-07-05-grape.md), [GRAPE 2026-07-05 (2)](./today-i-learned-2026-07-05-grape-2.md)
