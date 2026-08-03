# TIL 2026-07-05 — CHERRY (session 2)

**Context:** An afternoon fleet session that ran a filing → review → refine → implement loop across a cluster of docs/process tickets: a post-v1 breathing-animation ticket (#567), the ledge-recovery showcase beat (#421), a README rewrite (#577), a single-step dependency manifest (#583), and a referencing-hygiene rule (#579). Several tickets fed each other — the #577 README review spawned #583 and #579 — so the through-line was *reviewing my own work before doing it*.

---

## 1. The roadmap is generated from labels — "add to the roadmap" means apply a label

**What happened:** Asked to file a post-v1 breathing-animation feature (#567) "and add it to the roadmap as such." I went looking for a roadmap doc to edit. There isn't one to hand-edit: `docs/roadmap.md` is *generated* from the `v1` / `post-v1` issue labels (it even carries a "labels are the source of truth" regenerate footer). Once I filed #567 with the `post-v1` label, it appeared in the roadmap's deferred column automatically the next time the doc was regenerated.

**What I learned:** I briefly misread the regenerated doc and thought #567 was listed twice / in the v1 column — a false alarm that came from reading the compact list without checking which section header it sat under. The label *is* the roadmap entry; the markdown is a projection.

**The rule:** **When work-tracking state lives in labels, edit the label, not the generated artifact — and read a generated doc by its section headers, not line position.**

---

## 2. Probe the sim's state timeline before scripting a demo beat

**What happened:** #421 added a "ledge recovery" beat to the scripted showcase — from the hang, P1 presses UP for a neutral getup and climbs onto the stage. Before writing a single `InputSpan`, I ran a throwaway probe that printed P1's state/x/on_ground across frames 495→end. That told me the exact facts I needed: the grab lands at f501, the hang auto-releases at ~f621 (so a getup input around f603 is safely still hanging), and the getup produces `ledge_hang → ledge_getup → idle` on-ground. Only then did I place the inputs, then revert-checked the new test (remove the UP input → P1 stays hanging → the assertion goes red).

**What I learned:** Frame-scripted choreography is guess-and-check hell if you script first and observe later. A 15-line probe collapses a dozen trial runs into one, and it doubles as the evidence for where to put `dwell_at`.

**The rule:** **For a frame-scripted demo beat, dump the actual state timeline first, place inputs against observed frame windows, then revert-check that the new assertion can fail.**

---

## 3. Run issue-review on your own filing — and act on it like a reviewer, not the author

**What happened:** Before taking #583 (dependency manifest) and #579 (line-ref rule), I ran the issue-review skill on tickets I had just written myself. It paid off both times. On #583 the review asked "does the pinned `statecharts` v0.0.1 tag actually contain the symbols pycats imports?" — a question I hadn't encoded, which became the load-bearing AC3 and the thing I verified first. On #579 it flagged that a flat "never use line refs" over-reaches against commit-pinned permalinks (which don't rot) and quoted tool output — carve-outs that made the rule correct instead of dogmatic.

**What I learned:** Reviewing my own ticket surfaced gaps precisely because the review rubric asks author-blind questions ("could an agent start with zero follow-up?"). The author knows what they meant; the rubric doesn't, so it catches the unstated.

**The rule:** **Review your own tickets with the same skill and the same reject-by-default stance you'd use on someone else's; the gaps it finds are real even when you filed it.**

---

## 4. Validate an install doc against the code's real import graph, not the previous doc

**What happened:** #577 rewrote the README. The old Quickstart said `pip install pygame-ce` then `python -m pycats.game`. But the live game imports `statecharts` (via `fighter_chart` in `pycats/charts/`), an external sibling package — so a fresh clone following the old quickstart would `ModuleNotFoundError`. The old README had propagated an install path that never actually worked for a clean clone; I only caught it by grepping the tree's `from statecharts import` / `import` lines rather than trusting the prior dependency list. (Logged as error id=64.)

**What I learned:** A "how to install / run" doc is a claim about the dependency graph, and the graph is authoritative — not the last person's README. The bug had survived because everyone testing it already had the sibling installed.

**The rule:** **Verify an install/run doc against the tree's actual imports (grep `import X`), never against the manifest or README it's replacing.**

---

## 5. A pinned-dependency manifest is only proven in a fresh venv rebuilt from the pin

**What happened:** #583 declared `requirements.txt` with `statecharts @ git+…@v0.0.1`. The one meaningful test is not "does it work in my dev venv" (which has an *editable* local checkout that may be ahead of the tag) — it's a throwaway venv installed *from the pin*. I built one, confirmed statecharts resolved as v0.0.1 (non-editable) and all six imported symbols worked, then ran the suite against it. That clean run immediately caught a second thing: `imageio` — imported by the `--video` presenter and a caption test — was an undeclared, already-in-use dependency that only "passed" because my main venv happened to have it. Two tests `ModuleNotFound`'d until I declared it. (Logged as error id=66.)

**What I learned:** The dev environment's accumulated, pre-installed extras are exactly what hide a manifest's omissions. A clean rebuild is the only environment that tells the truth about what a manifest declares.

**The rule:** **To validate a dependency manifest, rebuild from it in a fresh venv (not the editable/dev env) and run the full suite there — the clean env exposes every undeclared-but-used dep.**

---

## 6. Reference locations by named landmark, not a raw line number

**What happened:** The #577 review kept bumping into stale line refs (the ticket's own gap inventory was `file.py:NN`-keyed, and those numbers had already drifted). That crystallised into #579: a RULES.md rule to point at a **function/class + file path** (or a bare symbol) for code and a **section heading** for markdown, with a line number allowed only as a secondary as-of hint. I practised it throughout the session's tickets and commits before the rule even landed.

**What I learned:** A line number is a locator that rots on the next edit; a landmark is greppable and self-correcting. Filing the rule and immediately using it in the same session made it stick far better than a rule I'd have to remember to apply later.

**The rule:** **Point at named, greppable landmarks — not line numbers — in every authored reference (tickets, reviews, commits, docs). Now in RULES.md → "Referencing code & docs".**

---

## What landed

| Artifact | Change |
|---|---|
| Issue #567 | Filed post-v1 breathing-animation feature; roadmap entry = the `post-v1` label |
| `pycats/sim/showcase.py`, `tests/test_showcase_demo.py` | Ledge-recovery showcase beat + able-to-fail test (#421) |
| `README.md` | Full rewrite: goals, one working install path, CPU-vs-behavior, current controls/layout (#577) |
| `requirements.txt`, `requirements-dev.txt`, `README.md` | Single-step install; pin `statecharts @ v0.0.1`; declared `imageio` (#583) |
| `RULES.md`, `CLAUDE.md` | "Referencing code & docs" landmark rule (#579) |

## Related artifacts

- Morning session: [TIL 2026-07-05 CHERRY](./today-i-learned-2026-07-05-cherry.md)
- Issues #567, #421, #577, #583, #579
