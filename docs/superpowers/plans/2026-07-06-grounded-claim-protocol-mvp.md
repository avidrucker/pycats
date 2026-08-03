# Grounded-Claim Protocol — MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the smallest slice of the Grounded-Claim Protocol that prevents both observed failures (ledge prose-mislabel, #363 title-classification): the `grounded-claim` skill + the per-project `.claude/evidence.json` config + the reflex RULES line.

**Architecture:** Approach A — a project-agnostic protocol (the global `grounded-claim` skill + the reflex rule) reads a per-project config (`.claude/evidence.json`) that names the canon, the evidence map, and the value registry. The skill enforces the two grounding authorities (canon-quote vs decision-record) and the governed-scope boundary; a validation test keeps the config pointing at real files. Design: `docs/superpowers/specs/2026-07-05-grounded-claim-protocol-design.md`; grill review: `…-grill.md`.

**Tech Stack:** Markdown (SKILL.md), JSON (config), Python stdlib (`json`, `pathlib`) + pytest for the config-validation test. No new dependencies.

## Global Constraints

- **No new dependencies** — validation uses stdlib `json` + `pathlib` only (RULES → "Dependencies").
- **Banned words** in all output/docs/commits: avoid *crisp* and *honest/honestly* (docs/banned_words.md).
- **Reference by named landmark** (function/symbol + path; section heading for markdown), not raw line numbers (RULES → "Referencing code & docs").
- **pycats is fleet mode** — the skill's autonomous-mode behavior (halt-and-record) is load-bearing, not optional (grill F3).
- **Config lives in `.claude/`** version-controlled, alongside `orchestrate.json` (config-driven-pm-skills-design, D4).
- **Skills are global/canonical** (`~/.claude/skills/`), zero project assumptions baked in (D4).

## Ticket mapping (pycats tracking)

| Task | Deliverable | pycats vehicle |
|---|---|---|
| 1 | `.claude/evidence.json` + validation test | **new DEV ticket** (in-repo, testable) |
| 2 | `~/.claude/skills/grounded-claim/SKILL.md` | cross-project (global) — authored under the same DEV ticket's session, but the file is not a pycats repo artifact; note it in the ticket |
| 3 | reflex RULES line | **#562** (already OPEN) — ratify/extend, do **not** file a duplicate |

---

### Task 1: Per-project config `.claude/evidence.json` + validation test

**Files:**
- Create: `.claude/evidence.json`
- Test: `tests/test_evidence_config.py`

**Interfaces:**
- Produces: `.claude/evidence.json` with keys `canon` (str), `evidence_map` (repo-relative path str), `value_registry` (repo-relative path str), `governed_domains` (list[str]). The skill (Task 2) consumes these keys by name.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_evidence_config.py
"""Validates the Grounded-Claim Protocol per-project config (.claude/evidence.json).

Guards two things: the config is well-formed, and every path it names actually
exists — so the skill never routes an agent at a missing map/registry.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".claude" / "evidence.json"

REQUIRED_KEYS = {"canon", "evidence_map", "value_registry", "governed_domains"}


def _load():
    return json.loads(CONFIG.read_text())


def test_config_exists_and_is_json():
    assert CONFIG.is_file(), f"{CONFIG} missing"
    _load()  # raises JSONDecodeError if malformed


def test_config_has_required_keys():
    cfg = _load()
    assert REQUIRED_KEYS <= set(cfg), f"missing keys: {REQUIRED_KEYS - set(cfg)}"


def test_config_paths_resolve():
    cfg = _load()
    for key in ("evidence_map", "value_registry"):
        p = REPO_ROOT / cfg[key]
        assert p.is_file(), f"{key} -> {cfg[key]} does not exist"


def test_governed_domains_nonempty_list():
    cfg = _load()
    assert isinstance(cfg["governed_domains"], list) and cfg["governed_domains"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_evidence_config.py -v` (where `PY=/home/avi/Documents/Study/Python/pycats/.venv/bin/python`)
Expected: FAIL — `test_config_exists_and_is_json` errors, `.claude/evidence.json` missing.

- [ ] **Step 3: Create the config**

```json
{
  "canon": "Project M 3.6",
  "evidence_map": "docs/project-m-rules-by-category.md",
  "value_registry": "pycats/combat/provenance.py",
  "governed_domains": ["canon", "in-repo-fact"]
}
```

Write to `.claude/evidence.json`.

- [ ] **Step 4: Run test to verify it passes**

Run: `"$PY" -m pytest tests/test_evidence_config.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Revert-check the guard is able to fail**

Temporarily change `value_registry` to `"pycats/combat/nope.py"`, run the test, confirm `test_config_paths_resolve` FAILS, then restore. (Proves the guard bites — RULES "Fixing bugs" revert-check discipline applied to the config guard.)

- [ ] **Step 6: Commit**

```bash
git add .claude/evidence.json tests/test_evidence_config.py
git commit -m "feat(evidence): add Grounded-Claim Protocol config + path-validation guard (#<DEV>)"
```

---

### Task 2: Author the global `grounded-claim` skill

**Files:**
- Create: `~/.claude/skills/grounded-claim/SKILL.md` (global; cross-project — not a pycats repo file)

**Interfaces:**
- Consumes: `.claude/evidence.json` keys from Task 1 (`canon`, `evidence_map`, `value_registry`, `governed_domains`).
- Produces: the trigger + procedure agents follow. No code interface.

This is authoring, not red-green TDD. Use `write-a-skill` / `skill-creator`. The SKILL.md must encode, verbatim from the spec:

- [ ] **Step 1: Frontmatter + trigger.** `name: grounded-claim`; `description` fires when an agent is about to **assert or classify** a governed claim — a **canon** mechanic/value, or an **in-repo fact** that is *not-in-view AND decision/artifact-bearing*. Triggers phrased like `author-vet-this-source` ("about to state a Project M / Melee / Brawl mechanic or a tuned value"; "classifying/deciding from a ticket/code fact recalled, not read").

- [ ] **Step 2: Load-the-config step.** Body step 1 = read the project's `.claude/evidence.json`; resolve `canon`, `evidence_map`, `value_registry`. If absent, the skill no-ops with a note (graceful degradation — a project without the config isn't governed).

- [ ] **Step 3: The two grounding authorities.** Encode: **canon-grounded** needs a *verbatim supporting quote* (from `pm-reference/` / the map's Primary-source doc — NOT `provenance.py`, whose `source` is a reference); **decision-grounded** (`TUNED`/`DIVERGENCE`) needs the *registry record + issue*, and the claim must carry a "not canon" tag; **neither** (`GUESS`/no record) → the gate.

- [ ] **Step 4: The claim lifecycle + fast path.** Mirror the spec's flow: authority in hand → cite inline (no gate); else route via `evidence_map` → resolve; else emit the deviation block.

- [ ] **Step 5: The deviation block + halt-and-record.** Include the exact block format. Interactive → wait for proceed/cite/drop. Autonomous/fleet → **withhold + log a grounding-debt row**, never proceed silently, never block forever.

- [ ] **Step 6: Validate the skill file.** Confirm: frontmatter parses (name + description present); the body names all four config keys; the deviation block is present verbatim. (Manual read-through; no test harness for global skills.)

- [ ] **Step 7: Smoke-test the trigger.** In a scratch prompt, state a PM mechanic from memory and confirm the skill would fire (self-check against the description). Record the check in the DEV ticket comment.

*(No git commit — global skill lives outside the repo. Note authoring + the smoke-check in the DEV ticket.)*

---

### Task 3: Reflex RULES line — route to #562 (human ratification gate)

**Files:**
- Modify (on ratification only): `RULES.md` + `CLAUDE.md` critical-rules list

**Not an agent-implemented task.** The reflex line is a **rules change**, which needs human ratification (RULES → "Changing values" requires a ratified `decision:` ticket). #562 is already OPEN for the adjacent cite-primary rule.

- [ ] **Step 1: Propose the exact line as a comment on #562**, reconciled with its cite-primary text:

  > **Read the source before asserting.** Ground a governed claim in its authority — a verbatim primary quote (canon) or the provenance record + issue (a pycats decision); the ticket **body** over its title, the **code** over memory, the **registry** over prose. No authority in hand → emit an evidence-deviation notice and get consent (interactive) or withhold + log (autonomous).

- [ ] **Step 2: Flag the open placement nit** (grill): host in "Changing values" vs extending #562's rule vs its own line — human decides.
- [ ] **Step 3: On human ratification**, edit `RULES.md` + the `CLAUDE.md` critical list at high salience (Hardening #2 — do not bury). This edit lands under #562's close, not this plan.

---

## Deferred (grill F5 — do NOT build on guessed need)

- **#575 consistency test** (Tier-1 structured + Tier-2 lint) — next after MVP; already its own ticket.
- **Freshness metadata** — until a stale-evidence incident occurs.
- **Gate-fire tally** — until the gate exists and fires enough to measure fatigue.

## Self-review

- **Spec coverage:** MVP = skill (Task 2) + config (Task 1) + RULES line (Task 3, via #562). #575 / freshness / tally explicitly deferred (matches spec's Implementation decomposition). ✓
- **Placeholders:** `#<DEV>` in Task 1's commit is the to-be-minted DEV issue number — filled at claim time, not a content gap. No TODO/TBD in steps. ✓
- **Type consistency:** the four `evidence.json` keys are named identically in Task 1 (produces) and Task 2 (consumes). ✓
