# TIL 2026-07-06 — FIG

**Context:** A long build-out of the **Grounded-Claim Protocol** — a project-neutral "cite before you assert, or declare the deviation" system — from findings (#571) through design (#611), a critical grill (#620), the skill+config MVP (#624), a ratified RULES rule (#562), the detective-gate spike (#575) and its Tier-1 test (#635), a divergences accessor (#643), and a mechanical test-suite cleanup (#496). Process skills leaned on: brainstorming, decomplect, murphy-jutsu, grill-with-docs, guide-human-decision.

---

## 1. Grilling a design against the *code* walks back load-bearing claims

**What happened:** After brainstorming the protocol design (#611) I ran `/grill-with-docs` on it (#620), and the first thing I did was read `combat/provenance.py` — not re-reason. Two headline claims did not survive. The spec's flagship rule was "grounded = a verbatim supporting quote," but `MAX_FALL_SPEED`'s own registry entry reads *"DIVERGENCE … no source"* — a `TUNED`/`DIVERGENCE` value has **no primary quote by construction**, so the rule would shove every use of it through the consent gate forever. And I'd claimed the #575 consistency test would have caught the ledge bug; the registry already tagged it `TUNED` and the manifest already read non-canon — the lie was in prose, which a field-comparison can't see. Same pattern on #643: the grill found the "divergences view" I was about to build already exists as a one-line registry filter.

**What I learned:** A design reads as coherent right up until you check it against the data model it assumes. The grill's value wasn't polish — it *reversed* two decisions and deleted a whole artifact before any code existed.

**The rule:** **Grill a design by grounding each claim in the code it assumes, not by re-reasoning it — the wrong claims are the ones that sound right.** (Reinforces the ratified read-the-source rule, #562.)

---

## 2. Apply a discipline to its own roadmap — don't build on guessed need

**What happened:** The murphy-jutsu pre-mortem (#620) flagged a "complexity invoice": I'd specced 5 pieces for 2 observed failures. Turning the protocol's own rule on its roadmap, only 2 (skill + rule) prevent the real bugs; freshness metadata mitigates a failure that *hasn't happened*. So the MVP shipped 2 pieces (#624) and freshness/tally/lint were deferred as evidence-gated. On #643 the same discipline killed a duplicate doc: the registry *is* the divergences list, so I added accessors, not a synced file that could drift.

**What I learned:** The strongest use of a rule is to point it back at your own plan. "We might need it later" is exactly the guessed-need the protocol forbids.

**The rule:** **Defer any piece whose need is speculative; build only what a real, observed failure justifies — and hold your own roadmap to that bar.**

---

## 3. Ground, don't invent — the read-the-source rule in practice

**What happened:** #562 ratified "Read the source before asserting" into `RULES.md` + `CLAUDE.md` this session (via `/guide-human-decision`). Minutes later it bit me usefully: the #643 traceability guard needed `DODGE_FRAMES`/`DODGE_TIME` to carry a tracking issue, and my instinct was to pick a plausible number. Instead I searched — `gh issue list --search "dodge"` surfaced **#65** ("canonical dodge speed & duration"), and I read #65's *body* to confirm its scope covers "roll/dodge duration incl. ground roll" before attributing it. Grounded, not invented.

**What I learned:** The rule isn't abstract; the moment you want to fill a field with a "reasonable" value is exactly when it fires.

**The rule:** **When a field wants an issue/source/value, find the real one and read it — an invented-but-plausible reference is the exact anti-pattern.** (Authority: RULES → "Read the source before asserting", #562.)

---

## 4. Editing the provenance registry cascades to derived artifacts

**What happened:** On #643 I changed two `provenance.py` entries (added an `issue`, tweaked a source string). The unit tests were green — but the full suite red on `test_parity_status_report.py`: `docs/parity-status.md` is *generated* from the registry by `parity_report.py`, and my edit made the committed copy stale (errors #95/#96). Fix: `python parity_report.py` to regenerate.

**What I learned:** A registry edit that looks local isn't — a derived, committed artifact rides on it, and only the *full* suite catches the drift. The enforcement already exists (the parity-report test reds on staleness); I just have to run it and regenerate.

**The rule:** **After editing `combat/provenance.py`, run the full suite and regenerate `docs/parity-status.md` (`python parity_report.py`) — a committed artifact is derived from it.** (Self-enforced by `test_parity_status_report.py`.)

---

## 5. `ruff format` is not the pycats gate; `ruff check` is

**What happened:** On the #496 SDL-boilerplate delete, removing `import os` left F401 (unused import) and I001 (import-block sort) — both `ruff check --fix` handled. But `ruff format --check tests/` reported **"186 files would be reformatted"** — so the tests aren't format-clean and `ruff format` is clearly *not* the enforced gate (ADR-0006 gates lint, `ruff check`). Running `ruff format` would have dumped 186 unrelated files into my diff.

**What I learned:** The lint gate and the formatter are different tools with different scope. A whole-tree "would reformat 186 files" is the tell that the formatter isn't enforced — reaching for it is how you smuggle a giant unrelated diff into a mechanical ticket. (Matches CHERRY/BANANA's over-scope traps today: #76, #82.)

**The rule:** **The pycats gate is `ruff check` (lint), not `ruff format` — use `ruff check --fix` for F401/I001 fallout and never run `ruff format` across a tree you didn't touch.**

---

## What landed

| Ticket | Change |
|---|---|
| #571 | Findings: proactive PM-grounding mechanism |
| #611 / #620 | Grounded-Claim Protocol design + critical grill (2 claims walked back) |
| #624 | MVP: `grounded-claim` skill + `.claude/evidence.json` + validation guard |
| #562 | Ratified RULES rule "Read the source before asserting" (+ CLAUDE.md) |
| #575 / #635 | Detective-gate spike + Tier-1 registry↔manifest consistency test |
| #643 | Status accessors (`by_status`/`divergences`/`debt`) + traceability guard; DODGE→#65 backfill |
| #496 | Dropped redundant SDL `os.environ` boilerplate from 45 test files |

## Open threads

- `LEDGE_INVULN_PER_PERCENT` registry(`TUNED`)/manifest(`DIVERGENCE`) tag disagreement — flagged to **#536**, not adjudicated.
- Deferred protocol pieces (evidence-gated): Tier-2 prose lint, freshness metadata, gate-fire tally.

## Related artifacts

- Design: `docs/superpowers/specs/2026-07-05-grounded-claim-protocol-design.md`
- Grill: `docs/superpowers/specs/2026-07-05-grounded-claim-protocol-grill.md`
- Skill: `~/.claude/skills/grounded-claim/SKILL.md`
