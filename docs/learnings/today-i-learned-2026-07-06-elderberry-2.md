# TIL — 2026-07-06 (ELDERBERRY, session 2)

Session themes: a blobless sparse clone of an offline data source (#664), backfilling a
test-gated provenance register (#535), a thorough spike-before-file plus additive-render TDD
(#682), and tracking a consumer that landed *after* its migration plan was written
(#682 ↔ #680/#672). Second ELDERBERRY TIL of the day (first was #668).

## Clone only the two files you need — blobless partial + cone sparse-checkout (#664)

The task was "clone Project-M-CC so its text codesets are an offline cross-check source." The
repo is a **full PM build — ~824 MB** (`apps/`, `.pac`/`.rel` data), but the value is two text
files (`[Dev Resources]/codes-3_6.txt`, `[Text Codesets]/codes-cc-3_6.txt`). Pulling the whole
build to read ~500 KB is waste. The ticket's own "size note" pointed at the fix:
`git clone --filter=blob:none --no-checkout` (blobless: history without file contents) → `git
sparse-checkout init --cone` → `set` just the two dirs → `git checkout master` fetches only those
blobs. **~8 MB instead of 824 MB.**

Gotcha, logged as err id=111: `git sparse-checkout set "[Dev Resources]" "[Text Codesets]"` fails
with *"fatal: specify directories rather than patterns"* — `[]` are glob-special, and sparse-checkout
refuses them as ambiguous. Pass **`--skip-checks`**; cone mode still takes them literally as
directory names. And the acceptance was a **cross-check, not a fetch**: `wc -l codes-3_6.txt` must
== **8,044**, matching vanilla `RSBE01.gct`'s code count — that equality is what proves the text
file is the same codeset as the binary, not just that a file downloaded.

## In a provenance register, `Status` is canon-provenance; the value column is implementation state (#535)

Backfilling `project-m-rules-by-category.md` with Invuln + Respawn rows, the tension was: the
~120f respawn invincibility is **PM canon but unimplemented in pycats (#506)**. The four Status
tokens (FOUND/GUESS/TUNED/DIVERGENCE) have no "gap" value, so the clean split is: **`Status` =
provenance of the *canon finding*** (FOUND = sourced), **the `pycats value(s)` column = what the
code does today** — so a `FOUND` row legitimately reads **unimplemented** in the value column. I
added a reading-note saying exactly that, so a parity-worker scanning `Status=FOUND` isn't misled
into thinking it ships.

The keyed row is the machine-checked part: `RESPAWN_DELAY_FRAMES` maps 1:1 to a `combat/provenance.py`
key, so its Status cell must **lead with the registry's token** (`TUNED`) or `test_tuning_provenance.py`
(#635) reds — the gate joins manifest↔registry by the bare `Constant` name and compares
`_leading_status`. Model/mechanic rows carry a **blank `Constant`** and are intentionally
ungated. Each new row got a **verbatim T1/T2 quote + URL + tier** (brawllib_rs
`hurtbox_state_all = state` overwrite for Layer 1; SmashWiki Revival-platform "120 frames" for the
timed overlay) — cite the primary, don't paraphrase.

## Ask filing-depth first; then a spike earns its length by drawing scope fences (#682)

Asked to "file a ticket to implement selected-character displays," I offered
minimal/moderate/**thorough** and waited (the recurring ask-depth rule, err id=61). The human
picked thorough, and the spike's whole value turned out to be **boundary-drawing**: the char-select
screen already has a per-*character* grid, a #662 confirmation-preview cat (being retired by #676),
and #676's grid-tile recolor. The new "row of 4 P1-P4 player slots" is a *fourth* thing — a
per-*player* portrait row. Without reading `char_select.py` + #662/#676/#663 first, the ticket
would have silently overlapped one of them. The filed #682 spends most of its body on
in/out-of-scope fences against those neighbors, plus a soft "Sequenced after #672 Phase 1" because
it renders a `Selection` (Character + Skin).

## An additive render change regenerates nothing — but know *why* before you skip the golden (#682)

Implementing #682, the ticket warned char-select goldens might shift. They didn't, and the reason
is knowable in advance: `test_screen_parity` is an **FSM transition trace, not pixels**, and **no
byte-golden renders `char_select`** (grep'd the pixel-hash tests). A purely-*additive* new row
(new `_draw_player_slots`/`_player_slot_rect`, no existing element moved) therefore flips nothing —
confirmed by running the full suite (1266 = 1263 + 3 new), not by assuming. I still did the TDD
revert-check on an additive feature: drop the `palette_key=palette` override → the P1/P2 slot tests
red (fall back to the archetype default), structure test stays green. Additive ≠ untested. I also
eyeballed a rendered PNG (P1 void-black cat, P2 tiger-orange, P3/P4 gray "N/A") — the acceptance
said "eyeball," and a pixel-sample test can't see layout collisions.

## A consumer can outrun its migration plan — track the seam, don't fix it prematurely (#682 ↔ #680/#672)

#680 stood up the pure `pycats/domain/` model (`Selection`, `palette_of`, `resolve_selection`)
**unwired**; the epic #672 defers wiring to Phase 1b/1c. But #682 **landed a new
`char_select` cosmetic call site** (`_draw_player_slots` → `palette_for`/`palette_key`) *after*
#680's plan and #676 were authored — so **no phase ticket names it**, and unlike `_draw_confirmation`
(which #676 retires) it **persists**, so it won't be swept away for free. There was no bug and the
domain is still unwired, so the right response was **not** a fix and **not** a standalone
reconciliation ticket (which fragments the epic's phase plan): a **seam note on the epic #672** (for
Phase 1c to pick up) + a **`blocked` re-audit ticket (#689)** to re-check the seam once #672 closes
— auditing now would chase a moving target.

Re-checking live state mid-session mattered: I'd written "Phase 1b is not yet filed," and by the
time I acted it **was** — #686 had been filed *and* claimed by GRAPE while I worked. I caught it by
listing the live `claims` and reading the **worktree branch name** (`wt-grape-…-issue-686`) to
attribute the epic to GRAPE, rather than asserting from the stale earlier read. The fleet queue
moves under you; re-derive ownership from origin state before naming an agent or a ticket's status.

## Smaller notes
- `pmtools error log` schema: it rejects a row missing **`occurred_iso`** and rejects `summary` —
  the description field is **`message`**. Two failed attempts before id=111 landed; stamp the ISO
  time and use `message`.
- Worktrees have no `.venv`; run tests/ruff via the main-repo interpreter
  (`/home/avi/Documents/Study/Python/pycats/.venv/bin/python`). Ran `ruff format` (not just
  `--check`) before each commit.
