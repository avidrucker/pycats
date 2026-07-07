# TIL 2026-07-06 — ELDERBERRY

**Context:** A long session across render, research, tooling, and screens: the ASCII glyph
fallback (#547), reorganizing the keyboard-controls epic (#476) and doing its thread 1 research
(#477), the first code-quality audit (#628), the testcat gray placeholder (#636) and exposing it
in the sim (#648), and char-select skin cycling (#650) plus its follow-ups. Recurring thread:
distrust the surface — the ticket's stated premise, a "green" test, a one-line fix, a label —
until you've checked the thing underneath it.

---

## 1. Reproduce first — the ticket's literal premise can already be false

**What happened:** #547 said `render_text_mixed` renders arrow/marker glyphs as `"?"` because
"there is no actual ASCII fallback map." I reproduced before touching it: forcing the degraded
config (`unicode_font_name = None`, and a dict with empty `supported_chars`) and rendering
`►←↑↓→✓` — every live glyph *already* substituted correctly. `_get_ascii_fallback` and the
`render_text_simple` replace-chain have existed since the 2025 unicode commit (`git log -S`). The
one genuinely-broken, in-scope case was **`▶` (U+25B6)** — the black-triangle twin of `►`, listed
in the ticket's Should-table but absent from the map — which no menu even uses.

**What I learned:** Had I trusted the premise I'd have "fixed" already-working code and written a
test that passes trivially (a fake red). Reproducing turned a vague "it's broken" into a precise
red→green on `▶` (red at `"?"`, green at `">"`). Separately, the ticket's table said `✓ → "x"`,
but the code sensibly used `✓ → "OK"` — I **kept "OK"** because a confirmation checkmark rendered
as `"x"` reads as a cross/reject (`"P1 x"` inverts `"P1 ✓"`), and flagged that one deviation with
its reason at close.

**The rule:** **Reproduce the exact observable before fixing; a ticket's stated symptom (and its
acceptance-table cells) can be stale or wrong — ship the real red→green and name any deliberate
deviation, don't implement the premise.**

---

## 2. Before filing an umbrella, search for the one that already exists — reorganize, don't duplicate

**What happened:** The user asked me to file a keyboard-controls epic (current → ideal → what
changes). It already existed as **#476** with three threads (#477/#553) plus two *siblings*
floating outside its checklist (#554 scope decision, #555 backend spike). I didn't file a parallel
epic. I rewrote #476's body around the user's three questions and **folded #554/#555 into its work
breakdown** so every child is indexed — then did thread 1 (#477) as its own findings doc.

**What I learned:** The failure mode here wasn't missing coverage — it was *organization*: a
100%-scoped epic can still have orphan children nobody can find. A duplicate epic would have
fragmented the tracker. The fix was an edit + a comment, not a new number.

**The rule:** **When asked to file an umbrella, first `gh issue list`/`view` for an existing one;
if it exists, reorganize its body and pull orphan siblings into its checklist rather than minting
a duplicate.**

---

## 3. When the first TDD red is masked by a collection error, do an explicit per-assertion revert-check

**What happened:** #650 (skin cycling) had six tests; on first run they all **errored at import**
(`ImportError: cannot import name 'ARCHETYPE_DEFAULT_SKIN'`) — so I never watched the *match-wiring*
assertion fail for the right reason. After implementing, all green. But "green after a collection
error" doesn't prove the wiring test can catch the bug. So I physically reverted the one line
(`palette_for(p1_palette or p1_char)` → `palette_for(p1_char)`), re-ran just that test, and watched
it go red (calico ≠ tabby), then restored.

**What I learned:** An import/collection error is a *masked* red — it hides whether each assertion
is actually able-to-fail. The revert-the-fix check is the only thing that proves it, and it has to
be done per-assertion for the load-bearing one, not inferred from "the suite was red once."

**The rule:** **A red caused by a collection/import error doesn't satisfy the able-to-fail proof —
revert the specific fix line and watch the specific assertion go red before trusting it.**

---

## 4. A placeholder needs a signal no real instance carries — and trace reachability through *every* gate

**What happened:** #636 asked to make the `testcat` fixture "clearly not a standard cat." My first
instinct (mid-gray, `128`) collided with an existing **`tabby`** OG skin that is *also* `128` gray
— but tabby has gold eyes. So I made testcat **fully achromatic including the eyes** (`64,64,64`):
no real archetype has gray eyes (nalio green, birky blue, narz green), so colorless eyes are the
unique marker. Then the user asked "can I actually see it?" — I traced *both* selection gates
(char-select grid and `watch.py`'s `--p1-char choices=CHARACTERS`, both = `ARCHETYPE_ROSTER`) and
found testcat unreachable, **and** that `sim/runner.py::build_players` hardcodes `calico`/`tabby`
colors, ignoring the char key's palette entirely. So "expose testcat" (#648) wasn't a one-line
`choices` add — it needs the sim to color via `palette_for`.

**What I learned:** "Distinct" isn't a color, it's a *discriminator* — pick the attribute no
legitimate instance shares (gray eyes), not one that merely looks different (gray body, which
tabby already is). And "does X render anywhere?" is answered by walking every gate to the pixel,
because a downstream hardcode can silently drop your data.

**The rule:** **Mark a placeholder with a property no real instance has; and before claiming
something renders, trace it through every selection gate AND the color/data path — a hardcode
downstream makes a one-liner a two-part change.**

---

## 5. A broken check command fails silently-wrong — verify its exit semantics, not just the summary

**What happened:** In the #628 code-quality audit I authored a `largest-module-size-bound` check as
`! find pycats -name '*.py' -exec awk … -o -print | grep -q .` — convoluted shell that exited 1 with
**empty stdout**, a false FAIL, even though `render_battle.py` (1197 lines) is under the 1300 bound.
The summary table just showed "FAIL"; only the evidence log (`reports/pycats/…​.log`) revealed the
empty output. I replaced it with `test $(find … -exec wc -l {} \; | awk '$1>1300' | wc -l) -eq 0`,
re-ran clean, and logged it as err #85 (VALIDATION_FAIL). The config also had to match pycats'
*actual* shape: no `pyproject.toml` (Python floor lives in `ruff.toml` `target-version`), no CI
(the gate is `.pre-commit-config.yaml`).

**What I learned:** A check that's wrong doesn't error loudly — it emits a plausible pass/fail.
The verdict is only as trustworthy as the command's exit semantics, which you confirm by reading
the evidence, not the scorecard. (Sibling to CHERRY's `$?`-after-a-pipe lesson the same day.)

**The rule:** **Before trusting a check's verdict, verify the command's exit semantics against its
own evidence log; and shape an audit config to the project's real layout, not the language's usual
one.**

---

## 6. The capability may already exist un-enabled — and `gh` validates labels before it creates

**What happened:** The #628 audit found ruff-format drift on `main`. Investigating "do we enforce
format at close?", I found pmtools **#106** already *built* a config-driven pre-close verify gate —
pycats just never set `close.verify` in `.claude/orchestrate.json`. The drift landed because the
layer was **off, not missing** (I filed #633 to enable it). Later, filing the FD-stage tickets, a
`gh issue create --label sequenced` failed with `'sequenced' not found` — I checked whether it had
created a partial issue (it hadn't; latest was still my prior number) and refiled without the label:
**`gh` validates labels before creating, so a bad label aborts the whole create, safely.**

**What I learned:** "We have a gap" is sometimes "we have the feature turned off" — check the tool's
existing capabilities before assuming new work. And a failed `gh create` on a nonexistent label is
atomic: nothing partial is made, so it's safe to retry (but verify the latest issue number first,
per the never-race rule).

**The rule:** **Before proposing new tooling, check whether the capability exists un-enabled; and
treat a label-validation `gh create` failure as atomic — verify no partial issue, then retry.**

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/text_utils.py` | `▶`→`">"` in the ASCII fallback map + `render_text_simple` chain (#547) |
| `docs/pm-reference/input-model.md` | PM input taxonomy, thread 1 of #476 (#477) |
| `$CODE_QUALITY_DIR/examples/pycats.edn` + `docs/research/2026-07-06-code-quality-audit-628.md` | 13-check audit config + scorecard (#628) |
| `pycats/characters/roster.py` | testcat gray placeholder palette (#636); `ARCHETYPE_DEFAULT_SKIN` (#650) |
| `pycats/char_select.py`, `battle_screen.py`, `screen_manager.py` | char-select skin cycling wired to the match (#650, Part 3 of #127) |
| #476 body | reorganized around 3 questions; #554/#555 folded into the checklist |

## Open threads

- The lessons above are process rules with no `RULES.md` landing yet — per the authority-path
  guidance they'd expire in `docs/learnings/`. Candidate for a "codify session process-lessons"
  RULES ticket (mirrors #484). Not filed — flagged for the human.
- #659→#660→#661 (FD measurements → v1 FD stage → post-v1 stage-selection epic) and #662/#663
  (skin-preview + de-modal start prompt) are queued; #662/#663 both touch `char_select.py` so must
  run in sequence, not parallel (see the handoff doc).

## Related artifacts

- Issues #547, #476, #477, #628, #633, #636, #648, #650, #659–663
- Sibling TILs 2026-07-06: [CHERRY](./today-i-learned-2026-07-06-cherry.md),
  [CHERRY (ruff)](./today-i-learned-2026-07-06-cherry-ruff.md),
  [BANANA](./today-i-learned-2026-07-06-banana.md),
  [DRAGONFRUIT](./today-i-learned-2026-07-06-dragonfruit.md),
  [GRAPE](./today-i-learned-2026-07-06-grape.md) — note the shared **ruff-format-scope** thread
  (BANANA #82, CHERRY #76/#642, me #628) all landing the same day.
