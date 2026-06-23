# PM Skills Generalization — Master Plan Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each plan task-by-task.

**Goal:** Generalize `fruit-agent-orchestrate` + `yegor-pm` into stack-agnostic, config-driven skills; centralize the lccjs PM scripts into a `pmtools` repo with per-language ports; and migrate pycats onto GitHub issues.

**Source spec:** `docs/superpowers/specs/2026-06-22-config-driven-pm-skills-design.md`

## Execution order (decided with user)

| # | Plan | File | Repos touched | Why this order |
|---|------|------|---------------|----------------|
| 1 | **B** — Generalized skill + configs | `2026-06-22-plan-b-generalized-orchestrate-skill.md` | `claude-config`, `lccjs`, `pycats` | Fastest path to the headline goal; pycats usable in solo mode immediately. lccjs config lands **before** skill defaults change (risk §12). |
| 2 | **A** — `pmtools` repo | `2026-06-22-plan-a-pmtools-repo.md` | new `pmtools` | Foundation for the enrichment path; de-risks cross-language parity. Plan B references `pmtools` commands but degrades to `null` without them, so B does not block on A. |
| 3 | **C** — pycats enablement + yegor-pm | `2026-06-22-plan-c-pycats-enablement.md` | `pycats`, `yegor-pm-skills` | Labels + TODO→issue migration give the generalized skill real data; yegor-pm annotation. |

## Cross-plan global constraints

- **Labels are a shared cross-project convention, NOT config** — `severity:high|medium|low`, `blocked`, `proposal`, `wontfix`, `humans-only`, `decision`, `research`. Identical on every repo.
- **Skills bake in zero project assumptions** — everything project-specific is in `.claude/orchestrate.json`.
- **`issueLimit` default = 50** (GitHub API throttling).
- **Canonical skill sources** (edit these, not the symlinks):
  - `fruit-agent-orchestrate` → `/home/avi/Documents/claude-config/skills/fruit-agent-orchestrate/SKILL.md`
  - `yegor-pm` → `/home/avi/Documents/Study/AI/yegor-pm-skills/skills/yegor-pm/SKILL.md`
- **Per-language ports stay in lockstep** via `pmtools/CONTRACT.md` + shared `fixtures/`.
- **Commit frequently**; each task ends with a commit. Work happens on feature branches, not on `main`/`master`.

## Dependency notes

- Plan B's pycats config sets `statusCommand: null`, so pycats works **without** Plan A.
- Plan A's `status` port only becomes *useful* once a repo carries `@todo #N` markers (deferred for pycats).
- Plan C's migration produces the issues Plan B's skill triages; running the skill end-to-end on pycats is the final verification step in Plan C.
