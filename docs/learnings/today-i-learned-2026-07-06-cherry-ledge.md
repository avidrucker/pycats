# TIL 2026-07-06 — CHERRY (ledge-invuln parity chain)

**Context:** A long session taking the ledge-grab intangibility mechanic from a
buggy shipped bar (#531) through primary-source validation (#536, #671), a ratified
decision (#670), a re-spec (#656/#657/#658), a scoping spike (#552), and finally the
implementation that dropped percent-scaling for a flat 21f fixed burst (#683). Six
error rows fell out of it (#102–#105, #110, #124) — most from over-trusting my own
prior output.

---

## 1. A plain-English re-explanation still has to be source-grounded

**What happened:** Asked to ELI5 my #531 work, I wrote that the ledge-invuln bar is
hidden during a ledge-hang because "the HANG bar owns that clock" and the window is
"shown a different way." Both false: #475 had **removed** the HANG bar entirely
(`timer_bar_specs(_fake(state="ledge_hang")) == []`). I re-derived repo state from
memory inside a "re-render, not redo" and shipped a falsehood. The user caught it;
errors #102 and #105 followed.

**What I learned:** The ELI5 skill says "translate your own prior words, don't solve
it again" — and I read that as license to skip re-reading the code. It isn't. A
re-render of a claim inherits the claim's need to be true; the plainer wording made
the wrong fact *more* confident, not less.

**The rule:** **Verify-before-asserting applies to an ELI5 too** — re-explaining a
claim never exempts it from the read-the-source gate (RULES → "Read the source before
asserting").

---

## 2. A feature can pass its test *and* its acceptance criteria yet never run in the game

**What happened:** #531's INVULN bar carried a `state != "ledge_hang"` suppression.
But `ledge_invuln_timer > 0` is only ever true *while* hanging — the timer is set at
grab and zeroed the instant the fighter leaves the edge. So the gate and the live
condition are mutually exclusive: the bar **never rendered in real gameplay**. It
"passed" only because the unit test used a synthetic `_fake(ledge_invuln_timer=N,
state="idle")` — a state combination that cannot occur. Error #103.

**What I learned:** Green tests + checked-off acceptance boxes proved the code did
what the *fake* asked, not what the *game* produces. The fake manufactured an
impossible world where the bar was reachable.

**The rule:** **For gated behavior, prove the gate is reachable against real state
transitions, not a hand-built fake** — a test whose fixture can't occur in play is a
tautology, not a guard.

---

## 3. Grep the open queue before filing a research ticket

**What happened:** The user asked me to "validate the 5-grab ledge thing with
research." Before filing anything, `gh issue list --search ledge` surfaced **#536**
(already auditing exactly this, with the PMDT primary quote in its body) and **#552**
(the fixed-burst spike). Filing a fresh research ticket would have duplicated both.

**What I learned:** The fastest research is the research someone already scoped. The
mechanic I was told to investigate was already two open tickets deep.

**The rule:** **Before filing a research ticket, search the open queue for the
mechanic** — the question may already be scoped, and a duplicate splinters the
findings doc.

---

## 4. Never predict a golden away — let the suite adjudicate, then read the sidecar

**What happened:** The #552 spike answered Q5 ("does the fixed burst shift any sim
goldens?") with "no regen expected — the AI edge-hog is golden-safe/off." Wrong. The
23→21 change reddened `full_match` and `two_npc`, with the **first divergence exactly
at a `ledge_hang` frame** (391 / 126): a fighter *passively* grabs a ledge mid-match
even when the AI never seeks one. edge-hog-AI-off ≠ no-ledge-grab. Error #124.

**What I learned:** The regen was safe to accept only because the *semantic* sidecars
(`<name>.summary.json` — frames, KOs, lives, states, winner, percent) were unchanged;
only raw positions shifted by the 2-frame-shorter window. That distinction (per
`tests/golden/REGEN_PROTOCOL.md`) is the whole difference between a truthful
re-record and laundering a regression.

**The rule:** **Don't predict a golden away — run the suite; if it regens, review the
semantic sidecar diff before accepting (REGEN_PROTOCOL), never rubber-stamp
`PYCATS_UPDATE_GOLDENS=1`.**

---

## 5. After retiring a constant, grep the whole repo — the plan's file list will miss one

**What happened:** The #552 DEV plan enumerated the files to touch and listed
`test_edge_hog.py` as the only affected test. But deleting `LEDGE_INVULN_MAX_FRAMES`
also broke `test_ledge_hang.py`, which used it as a loop bound. The plan's *own*
"step 7: grep the symbol repo-wide" is what caught it before the suite did.

**What I learned:** A carefully-written seam map is still an enumeration, and
enumerations of "everywhere a symbol is used" are exactly what greps are for. The
plan predicted 1 test file; reality had 2.

**The rule:** **A delete-a-symbol change ends with a repo-wide grep for the symbol,
not the plan's enumerated file list.**

---

## 6. rukaidata shows scripted subactions, not engine globals

**What happened:** For #671 I pinned PM 3.6's ledge-grab intangibility from rukaidata
(`CliffCatch` = fully intangible frames 1–21, flat across six characters). But the
*post-5-regrab* residual ("a few frames during the initial ledge snap") is a dynamic
engine anti-stall reduction — **not** in the subaction script — so rukaidata shows
only the normal 21f window, never the reduced one.

**What I learned:** This is the `DODGE_AIR_SPEED` limit again (#215/#222): a
scripted-move value is datamined-visible; an engine-hardcoded/dynamic value is not.

**The rule:** **Route an engine-global or dynamic-reduction question to a DOL/codeset
dump (#638), not rukaidata** — the subaction pages answer "what does this move
script do," never "what does the engine do to it."

---

## What landed

| Artifact | Change |
|---|---|
| `docs/research/2026-07-05-pm-ledge-intangibility-basis.md` | Audit: PM ledge invuln = fixed burst + 5-regrab cutoff, percent-scaling is a divergence (#536) |
| `docs/research/2026-07-06-pm-post-ledge-cutoff-frames.md` | Post-cutoff = non-zero snap residual, exact count engine-hardcoded (#671) |
| `docs/superpowers/plans/2026-07-06-fixed-burst-ledge-invuln-dev-plan.md` | Fixed-burst DEV plan (#552 spike) |
| `pycats/entities/ledge.py`, `config.py`, `provenance.py` | Flat 21f burst; deleted PER_PERCENT + MAX; regen parity-status (#683) |
| `tests/test_edge_hog.py` | 2 able-to-fail Piece-1 tests (fixed-constant + percent-invariance) |
| `tests/golden/{full_match,two_npc}.json` | Reviewed semantic regen (sidecars unchanged) |
| Decision #670, DEVs #656/#657/#658 | 5-regrab cutoff adoption + the dots re-spec of #531 |

## Open threads

- Lessons #2 (gate reachability) and #4 (golden prediction) aren't in `RULES.md` yet —
  their durable record today is error rows #103 / #124. Candidates for a RULES line or
  a `grounded-claim`-style checklist item; not filed unprompted.
- #656 (5-regrab cutoff) is the next implementable step, now unblocked by #683.

## Related artifacts

- Sibling TILs: [`-cherry.md`](./today-i-learned-2026-07-06-cherry.md),
  [`-cherry-ruff.md`](./today-i-learned-2026-07-06-cherry-ruff.md)
- Issues: #531, #536, #552, #670, #671, #683
- Memory: `rukaidata-engine-hardcoded-limit`, `pm-parity-cite-primary-not-inference`
