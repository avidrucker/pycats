# Config-driven PM skills + centralized `pmtools` — Design Spec

- **Date:** 2026-06-22
- **Status:** Draft — awaiting user review
- **Author:** Avi (with Claude)
- **Driving repo:** `pycats` (this repo) — but the work spans several repos (see §3)

---

## 1. Problem

Two skills the user relies on for project management were built against **lccjs**
(a Node project) and bake in lccjs-specific assumptions, so they don't serve other
projects — concretely, `pycats` (Python/Pygame):

- **`fruit-agent-orchestrate`** hardcodes `npm run puzzle:status` / `claim` /
  `preflight` (Node scripts), the lccjs GitHub label taxonomy, and a worktree-per-
  fruit-agent parallel model. `pycats` is not a Node project, has **0 open issues**,
  and **none** of those labels.
- **`yegor-pm`** is ~90% portable methodology; its only couplings are `gh` issues and
  the `pdd` CLI, both already language-neutral.
- The lccjs PM scripts are duplicated and already **drifting** (`hermes-skills` copy ≠
  `claude-config` copy).
- `pycats` currently tracks work in flat markdown (`TODOS.md`, `docs/research/BACKLOG.md`),
  not in an issue tracker.

## 2. Goals / Non-goals

**Goals**
- One **stack-agnostic canonical** copy of each skill, serving lccjs + pycats + future
  projects from a single source.
- Skills bake in **zero project assumptions**; everything project-specific lives in a
  per-project **config file**.
- Labels remain a **single shared convention** across all projects (not in config).
- Extract the lccjs PM scripts into **one centralized repo** with **per-language ports**
  (JS + Python now; Babashka/Clojure later), kept in lockstep by a shared contract +
  golden fixtures.
- `pycats` adopts **GitHub issues** so the generalized skill has a substrate to read.
- Config can also express **repo host/manager** (GitHub vs GitLab) and **project
  language(s)**.

**Non-goals (YAGNI)**
- Full GitLab parity now (no GitLab project exists yet) — design the seam, stub the adapter.
- Python ports of the **fleet-only** guards (`claim`, `preflight`) before pycats actually
  runs parallel agents.
- Moving the label taxonomy into config.
- Auto-deriving a dependency graph / `puzzle:status --json` redesign (tracked separately
  in lccjs as #1046).

## 3. Decisions on record (from brainstorming)

| # | Decision |
|---|---|
| D1 | pycats workflow: **solo today, fleet-ready later** (skill must scale solo → parallel). |
| D2 | Issue substrate: **migrate pycats to GitHub issues**. |
| D3 | Edit target: **generalize the canonical skills** (shared single source), not per-project forks. |
| D4 | Generalization mechanism: **config-driven (Option 2)**, skill bakes in no assumptions; borrow graceful-degradation from Option 1. |
| D5 | Labels: **standardized shared convention**, NOT in config. |
| D6 | PM scripts: extract to a **new dedicated repo** with **per-language ports** (JS + Python now, Babashka later), cloneable. |
| D7 | `issueLimit` default **50** (avoid GitHub API throttling). |
| D8 | Config also expresses **`host`** (github\|gitlab) and **`languages`**. |

## 4. Architecture overview

Five pieces:

1. **Generalized `fruit-agent-orchestrate`** — reads `.claude/orchestrate.json`, runs the
   universal data collection (`gh`/`glab` issue list, `git worktree list`, `date`), and
   adapts behavior (solo vs fleet, enrichment on/off) from config. Degrades gracefully
   when keys/labels/tools are absent.
2. **`.claude/orchestrate.json`** — per-project config (§5), version-controlled.
3. **`pmtools` repo (new)** — centralized home for `status` / `claim` / `preflight`, with a
   language-neutral `CONTRACT.md`, shared golden `fixtures/`, and per-language ports
   (`js/`, `py/`, later `bb/`) all graded against the same fixtures (§6).
4. **Provider adapter** — thin `host` → CLI mapping (`github`→`gh`, `gitlab`→`glab`) used by
   both the skill and `pmtools` (§7). GitHub implemented; GitLab stubbed.
5. **pycats enablement + yegor-pm touch-up + drift reconciliation** (§8–§10).

## 5. Config schema — `.claude/orchestrate.json`

Per-project, version-controlled. **Absent ⇒ generic defaults** (a fresh repo works,
degraded). Any missing key falls back to its default.

```jsonc
{
  // --- identity / provider ---
  "host": "github",                 // "github" | "gitlab"  → selects gh|glab adapter
  "repo": null,                      // "owner/name"; null => derive from `git remote`
  "languages": ["python"],          // drives pmtools port selection + @todo grep globs

  // --- workflow ---
  "mode": "solo",                    // "solo" | "fleet"
  "roster": ["APPLE","BANANA","CHERRY","DRAGONFRUIT",
             "ELDERBERRY","FIG","GRAPE","HONEYDEW","INCABERRY"],
  "issueLimit": 50,
  "worktreeBranchPattern": "^(?<agent>[a-z]+)/issue-(?<issue>\\d+)",  // fleet
  "defaultBase": "origin/main",      // fleet — claim's base branch

  // --- centralized PM tooling ---
  "pmtools": {
    "home": "~/code/pmtools",        // clone location; null => enrichment disabled
    "port": "py"                      // "py" | "js" | "bb"; null => derive from languages[0]
  },
  // explicit command overrides (escape hatch; WIN over pmtools{} derivation)
  "enrichment": {
    "statusCommand": null,           // e.g. "npm run puzzle:status" (lccjs shim); null => skip + note
    "claimCommand": null,
    "preflightCommand": null
  },

  // --- tooling paths (defaults shown; override only if nonstandard) ---
  "paths": {
    "worktreeDir": ".claude/worktrees",
    "evidenceDirs": ["docs/logs", "docs/research"],
    "scratchDir": null               // null => ~/.pmtools/<repo>/
  },

  // --- optional integration ---
  "testCommand": null,               // e.g. ".venv/bin/python -m pytest"; reserved for verify/unit-test seam

  // --- advisory (non-blocking hints) ---
  "advisory": {
    "clusterFile": null,             // e.g. "puzzle-clusters.csv"; null => skip overlap hints
    "sequencingDocRef": null
  }
}
```

**Enrichment command resolution order** (per command):
1. explicit `enrichment.<x>Command` if non-null → use verbatim;
2. else if `pmtools.home` non-null → derive `<home>/<port>/<tool>` invocation
   (`port` defaults to `languages[0]`'s port);
3. else → command unavailable → **skip the step and note it** in output.

### 5.1 Concrete configs

**lccjs** (`.claude/orchestrate.json`) — preserves today's behavior explicitly:
```json
{
  "host": "github",
  "languages": ["javascript"],
  "mode": "fleet",
  "pmtools": { "home": "~/code/pmtools", "port": "js" },
  "enrichment": {
    "statusCommand": "npm run puzzle:status",
    "claimCommand": "npm run claim",
    "preflightCommand": "npm run preflight"
  },
  "advisory": {
    "clusterFile": "puzzle-clusters.csv",
    "sequencingDocRef": "docs/learnings/today-i-learned-2026-06-05-dragonfruit.md"
  }
}
```

**pycats** (`.claude/orchestrate.json`):
```json
{
  "host": "github",
  "languages": ["python"],
  "mode": "solo",
  "issueLimit": 50,
  "pmtools": { "home": "~/code/pmtools", "port": "py" },
  "enrichment": { "statusCommand": null, "claimCommand": null, "preflightCommand": null }
}
```
`statusCommand` stays effectively off until pycats source carries `@todo #N` PDD markers
(see §8 step 4).

### 5.2 What configs deliberately do NOT carry

The **label taxonomy** (`severity:*`, `blocked`, `proposal`, `wontfix`, `humans-only`,
`decision`, `research`), the priority ranking keys (severity → estimate → number), the
`@todo`/`#N:Mm` PDD marker grammar, and human-routing label names. These are **shared
conventions**, identical across projects, referenced directly by the skill, and the skill
**tolerates their absence** (untriaged issues sort as ⚪; empty partitions stay empty).

## 6. `pmtools` repo — contract + ports + parity

### 6.1 Layout
```
pmtools/
  CONTRACT.md      # language-neutral spec: commands, flags, stdin/stdout shapes, exit codes
  fixtures/        # golden cases: given (git-grep hits + worktree list + issues) => expected output
  js/              # Node port (seeded from lccjs scripts/{puzzle-status,claim,preflight}.js)
  py/              # Python port
  tests/           # each port runs the SAME fixtures, asserts identical output
  README.md        # clone + wire-up
  # bb/  — Babashka/Clojure port, later
```

### 6.2 CLI surface (from the three lccjs scripts)
- `pmtools status [--strict] [--json]` — reconcile `@todo`/`@inprogress` markers ↔ worktrees
  ↔ issues. **Solo-relevant.** (← `puzzle-status.js`, 338 lines)
- `pmtools claim <issue> [slug] --as <name> [--base <ref>] [--dry-run] [--custom]` — stake a
  worktree under a fruit identity. **Fleet-only.** (← `claim.js`, 872 lines)
- `pmtools preflight <issue>` — stamp start time, run start-of-task reads, assert issue OPEN.
  **Fleet-only.** (← `preflight.js`, 173 lines)

### 6.3 Parity strategy (neutralizes the per-language drift tax)
- `CONTRACT.md` is the **single behavioral source of truth**.
- `fixtures/` are **language-neutral golden I/O cases** (input repo state as JSON → expected
  stdout/exit code).
- Every port has a test harness that feeds the fixtures and asserts the golden output.
- **Rule:** a behavior change = edit `CONTRACT.md` + a fixture, then make *every* port green.
  Ports cannot drift silently because they're all graded against one fixture set.

### 6.4 Parameterize lccjs-isms during extraction
- `~/.lccjs/preflight-<issue>.iso` → `<scratchDir>/preflight-<issue>.iso`
  (default `~/.pmtools/<repo>/`).
- `docs/logs/`, `docs/research/` evidence scan → `paths.evidenceDirs`.
- worktree path template → `paths.worktreeDir` + `worktreeBranchPattern`.
- the `gh ...` invocations → provider adapter (§7).

### 6.5 Build order (YAGNI)
1. `status` — JS **and** Python (only solo-useful tool).
2. `claim` / `preflight` — extract to JS, **defer Python port** until pycats goes fleet.
3. Babashka port — later, when a Clojure project needs it.

## 7. Repo-host / provider adapter

`host` selects a thin adapter mapping the operations the skill + pmtools need onto the
host CLI:

| Operation | GitHub (`gh`) | GitLab (`glab`) |
|---|---|---|
| list open issues + labels | `gh issue list --state open --json …` | `glab issue list --json …` (shape differs) |
| view issue state | `gh issue view N --json state` | `glab issue view N` |
| create label | `gh label create …` | `glab label create …` |

- **GitHub adapter: implemented** (both current repos are GitHub).
- **GitLab adapter: stubbed** — surface a clear "gitlab adapter not yet implemented" message;
  fill in when a GitLab project arrives.
- Adapter lives in `pmtools` (so ports share it) and the skill references operations
  abstractly ("list open issues") rather than hardcoding `gh`.

## 8. pycats enablement

1. **Standardized labels** on `avidrucker/pycats` — the shared taxonomy, created by a
   reusable `gh label create` script (same script every project runs, so labels stay
   identical): `severity:high|medium|low`, `blocked`, `proposal`, `wontfix`, `humans-only`,
   `decision`, `research` (+ `bug`/`enhancement`/`documentation` defaults).
2. **Migrate `TODOS.md` (~25 items) + `docs/research/BACKLOG.md` → GitHub issues**, shaped as
   `yegor-bdd` complaints (have X / should have Y / repro) where the source allows. Heaviest
   manual piece — **semi-automated draft, user reviews before bulk `gh issue create`.**
3. **Add `pycats/.claude/orchestrate.json`** (§5.1 pycats config).
4. **(Optional, later)** adopt `@todo #N:Mm` PDD markers in pycats source so `pmtools status`
   becomes meaningful; only then flip `statusCommand` on.

## 9. yegor-pm touch-up (light)

- Add an explicit **"stack-agnostic — works for Python/pytest, Node, Clojure"** note to
  `yegor-pm/SKILL.md`.
- Audit the 10 sub-skills for any smuggled Node/npm assumption (expectation: none — `pdd`
  gem + `gh` are already language-neutral). Fix any found.
- No structural change.

## 10. Sync-drift reconciliation + rollout

- Reconcile the divergent `lccjs/hermes-skills/.../fruit-agent-orchestrate` copy to the
  generalized canonical version, or mark it deprecated, so there's exactly one true source.
- Add lccjs's `.claude/orchestrate.json` (§5.1) so its current behavior is preserved
  **explicitly** rather than relying on skill defaults (defaults are now solo/no-enrichment).
- Verify `fruit-agent-orchestrate` and `yegor-pm` canonical locations
  (`claude-config/skills/…`, `yegor-pm-skills/skills/…`) are the edited source; check the
  `.claude/skills` symlinks resolve to them.

## 11. Sequencing / phases

1. **P1 — pmtools scaffold:** new repo, `CONTRACT.md`, `fixtures/`, GitHub adapter, JS+Py
   `status` extracted from lccjs and passing shared fixtures.
2. **P2 — generalize the skill:** rewrite `fruit-agent-orchestrate` to read config + degrade;
   add config schema doc; solo-mode output path.
3. **P3 — lccjs config + drift fix:** add lccjs `.claude/orchestrate.json`, reconcile the
   hermes copy, confirm lccjs behavior unchanged.
4. **P4 — pycats labels + config:** standardized label script run on pycats; add pycats
   `.claude/orchestrate.json`; dry-run the skill (solo) against the empty/early issue list.
5. **P5 — pycats migration:** TODOS/BACKLOG → issues (reviewed), re-run skill to confirm a
   real ranked queue.
6. **P6 — yegor-pm annotate:** stack-agnostic note + sub-skill audit.
7. **(Deferred)** `claim`/`preflight` Python ports + pycats PDD adoption + GitLab adapter +
   Babashka port — when pycats actually goes fleet / a GitLab or Clojure project appears.

## 12. Risks

- **Port parity drift** — mitigated by the contract + shared fixtures (§6.3); the discipline
  must actually be followed on every change.
- **Changing skill defaults breaks lccjs** — mitigated by adding lccjs's explicit config
  (§10) **before** generalizing, and by P3 verifying lccjs output is unchanged.
- **Migration quality** — ~25 TODOs → well-formed complaints is judgment work; user-review
  gate before bulk creation (§8 step 2).
- **`gh` rate limits** during migration/triage — `issueLimit: 50` + batching.

## 13. Open questions

- `pmtools` clone path convention — `~/code/pmtools` assumed; confirm preferred location for
  the `pmtools.home` default.
- Should `testCommand` be wired into a verification/`yegor-unit-tests` flow now, or just
  reserved in the schema? (Spec currently: reserve only.)
- Babashka port timing — purely on-demand, or scaffold `bb/` empty now for symmetry?
