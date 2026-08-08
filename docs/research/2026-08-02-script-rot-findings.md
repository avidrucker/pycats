# Script-rot audit — which scripts need test coverage (#1109)

**Role:** RESEARCH — findings + option space only. No guard test or script repair lands here;
those are downstream DEV children, filed one-at-a-time.
**As-of:** 2026-08-02, `main` @ `0023baf`.
**Trigger:** #1091 found `scripts/profile_frame_budget.py` no longer imports on `main` — the
`pycats/shell/` + `pycats/storage/` reorg relocated the modules it imports, and because no test
imports the script, the suite stayed green through the break. This ticket asks: how many other
scripts are in that state, and what is the smallest guard that would have caught it.

---

## §0 — TL;DR

- The runnable-script surface outside `pycats/` and `tests/` is **8 scripts** (4 in `scripts/`,
  4 at repo root; `conftest.py` is pytest's own and is exercised every run).
- **3 have zero import coverage and import `pycats`, so they can rot with a green suite:**
  `scripts/profile_frame_budget.py` (**already broken** — the #1091 finding),
  `bench_render.py`, and `scripts/regen_character_json.py` (its *output* is guarded, the *script*
  is not).
- **1 more is uncovered but rot-immune:** `scripts/datamine_stage_bounds.py` is pure-stdlib
  (no `pycats` import), so a package refactor can't break it.
- **4 are already covered** by a test that imports them top-level (`bench.py`, `parity_report.py`,
  `watch.py`) or loads them by path (`run_cmd.py`) — a refactor that breaks their imports reddens
  the suite today.
- **Recommended bar:** a single parametrized, auto-discovering **smoke-import** test
  (`tests/test_scripts_import.py`) that globs both script dirs and imports each module under
  `SDL_VIDEODRIVER=dummy`. Cheap, catches the whole class of refactor rot, and a new script is
  covered without editing the test. Behavior/output checks stay where they already are (bench,
  watch, parity, run_cmd, the JSON-drift guard) — the smoke test does not replace them.
- **Downstream children (filed):** #1112 add `tests/test_scripts_import.py`; #1113 repair
  `scripts/profile_frame_budget.py`'s imports (or fold #1113 into the GPU-present impl child of
  #1090/#1091, which owns the harness).

---

## §1 — The rot mechanism

The test suite imports `pycats/` (via the tests) and `tests/`. It does **not** import
`scripts/*.py` or the root-level `bench.py` / `bench_render.py` / `watch.py` /
`parity_report.py` **unless a specific test names them**. So any script that both

1. imports `pycats`, and
2. is not imported (directly or by-path) by a test,

can be broken by a package refactor while every test stays green. The break is invisible until a
human runs the script. That is exactly what happened to `profile_frame_budget.py`: `3036a02`
(the #1077 merge) shipped it importing `from pycats import runtime_settings` /
`from pycats.app import …`; the later `shell/`+`storage/` reorg moved those modules, and nothing
went red.

`pytest` puts the repo root on `sys.path` (rootdir prepend-import mode, because `conftest.py`
sits at the repo root), which is why the covered root scripts (`import watch`, `import
parity_report`, `from bench import …`) import cleanly inside a test. A guard can rely on the same
path setup.

---

## §2 — Inventory (the answer to Q1–Q3)

| Script | Imports `pycats`? | Covered by a test? | How it's covered | Category | Rot-prone? |
|---|---|---|---|---|---|
| `scripts/profile_frame_budget.py` | **yes** | **no** | — | profiling harness (#1077) | **YES — broken now** |
| `bench_render.py` | **yes** | **no** | — | profiling harness | **YES** |
| `scripts/regen_character_json.py` | **yes** | **no** (script) | *output* guarded by `test_hitbox_label_migration.py` via `combat.data`; the script is never imported | codegen | **YES (script)** |
| `scripts/datamine_stage_bounds.py` | no (stdlib `re`/`struct`/`sys`) | no | — | dev tooling (datamine) | no — stdlib-only |
| `scripts/run_cmd.py` | no (stdlib + `git` subprocess) | yes | `test_run_cmd.py` loads by path (`spec_from_file_location`) + behavior | dev tooling | covered |
| `bench.py` | yes | yes | `test_benchmark.py` — `from bench import benchmark, bucketed`, runs it | profiling harness | covered |
| `parity_report.py` | yes | yes | `test_parity_status_report.py` — `import parity_report` + regen/verify behavior | reporting tool | covered |
| `watch.py` | yes | yes | heavy — `import watch` across ~12 tests (CLI, demo, replay) | dev/replay tool | covered |

`conftest.py` (repo root) is excluded — pytest imports it every run by construction.

**Gaps (rot-prone AND uncovered): 3** — `profile_frame_budget.py`, `bench_render.py`,
`regen_character_json.py`.

### The codegen nuance (`regen_character_json.py`)

`test_hitbox_label_migration.py` guards that the committed `pycats/characters/data/<stem>.json`
matches a fresh oracle serialization — but it does so via `pycats.combat.data.fighter_to_json`,
**not** by running the script. So a rename in the character oracles reddens the drift guard, but a
break localized to `regen_character_json.py` itself (a removed collaborator it imports, a bug in
its own serialization helpers) leaves the suite green while the regeneration path is dead. The
script's *output* is guarded; the *script* is not.

---

## §3 — What "tested" should mean, per category (Q4)

The right bar differs by category. Do **not** over-test throwaway or behavior-owned scripts.

| Category | Scripts | Recommended bar | Why |
|---|---|---|---|
| Profiling/measurement harness | `profile_frame_budget.py`, `bench_render.py`, `bench.py` | **smoke-import** (bench also keeps its behavior test) | Output is timings, not committed artifacts — nothing to assert on. Smoke-import catches refactor rot, which is the only failure mode that hides. |
| Codegen (committed output) | `regen_character_json.py` | **smoke-import** + keep the existing JSON-drift guard | Two independent failure modes: the *script* can break (smoke-import catches) and the *output* can drift (drift guard catches). Neither subsumes the other. |
| Dev tooling with real logic | `run_cmd.py`, `parity_report.py`, `watch.py` | **behavior test** (already present) — smoke-import is a free subset | These have parseable outputs and branching logic worth asserting; they already have behavior tests, and a smoke-import adds nothing they don't already get. |
| Pure-stdlib datamine | `datamine_stage_bounds.py` | **none required** (smoke-import is harmless if the glob picks it up) | No `pycats` import ⇒ no refactor-rot surface. A behavior test would need a `.pac` fixture — not worth it for a run-once datamine. |

The through-line: **smoke-import is the floor for any script that imports `pycats`**; behavior
tests are added only where output is committed or logic is branchy, and those already exist.

---

## §4 — Guard mechanism (Q5)

Recommended: one parametrized, auto-discovering test at `tests/test_scripts_import.py`.

**Shape (spec, not final code — that's the DEV child):**

- Glob the two script homes: `scripts/*.py` and the root-level runnable scripts
  (`bench.py`, `bench_render.py`, `parity_report.py`, `watch.py`) — a small explicit allowlist for
  root, since the repo root also holds `conftest.py` and future non-script `.py`. `scripts/` can be
  a bare glob.
- `@pytest.mark.parametrize` over the discovered paths so **each script is its own test node** —
  a new script dropped into `scripts/` is covered with no edit, and one broken script names itself
  in the failure rather than aborting the module.
- Import by **path** (`importlib.util.spec_from_file_location`, the pattern `test_run_cmd.py`
  already uses) so it works uniformly for `scripts/` (no `__init__.py`) and root scripts.
- Set `SDL_VIDEODRIVER=dummy` for the import (several scripts import `pygame`). Verified this run:
  **no script opens a window at import time** — all window creation is behind `main()`/helpers and
  `if __name__ == "__main__"` guards, so a bare import is headless-safe. The DEV child should keep
  a guard-comment noting that invariant (a future script that calls `set_mode` at module top-level
  would hang the test — that's the signal to move the call into `main()`).

**Where it lives:** `tests/` (runs in the default `make test` suite, no new target needed). It
does not need `PYTHONPATH=.` — pytest already prepends the repo root.

**Alternatives considered:**

- *A Makefile/CI-only target* (import every script outside pytest): rejected — it would run only in
  CI, not in the local `make test` loop, so the fast feedback that catches a refactor mid-edit is
  lost. In-suite is strictly better here.
- *A per-script hand-written import test*: rejected — not auto-discovering, so it rots the opposite
  way (a new script silently uncovered). The parametrized glob is the point.

---

## §5 — Rot vectors beyond imports (Q6 — named, not chased)

Flagged cheap, deferred deep:

- **Stale in-script path/module references in docstrings** — e.g. `profile_frame_budget.py`'s
  header still describes the pre-reorg import layout. Cosmetic; a smoke-import won't catch it.
  Defer to whoever repairs the script.
- **Docs referencing scripts that moved/were removed** — a `grep -r 'scripts/' docs/` sweep would
  find dangling references. Cheap but out of scope for this audit; file separately if wanted.
- **Behavioral drift under a green import** — a script that imports fine but produces wrong output
  after a refactor. Only the behavior-tested scripts (bench/watch/parity/run_cmd) are guarded here;
  the harnesses are output-by-inspection by nature. Not worth synthetic behavior tests — the
  smoke-import floor is the right ROI.

---

## §6 — Downstream DEV children (hand-off — file one-at-a-time)

1. **#1112 — `DEV(test): add tests/test_scripts_import.py`** — the parametrized auto-discovering
   smoke-import guard per §4. Landing it will go **red on `profile_frame_budget.py`** immediately
   (that's the guard working) — so it must land together with, or immediately before, #1113.
2. **#1113 — `DEV(display): repair scripts/profile_frame_budget.py imports`** — repoint to
   `pycats.storage.runtime_settings`, `pycats.shell.app`, `pycats.shell.display`,
   `pycats.shell.display_manager`, and drop the removed `screen_render` import. Alternatively fold
   into the GPU-present impl child of #1090/#1091, which already owns re-running the harness — the
   findings doc `docs/research/2026-08-02-gpu-present-spike-findings.md` §7 flags this.

Sequencing note: because #1112 reddens on #1113's target, either bundle them or land #1113 first
and #1112 second. The RULES "able-to-fail regression test in the same commit" discipline is
naturally satisfied — #1112 *is* the red-without-the-fix proof for #1113.

Out of scope for #1109 (this doc): writing either child, and the docs-reference sweep in §5.

---

## §7 — References

- #1091 — surfaced the harness bit-rot; `docs/research/2026-08-02-gpu-present-spike-findings.md` §7.
- #1077 — the profiling harness (`scripts/profile_frame_budget.py`), last-touched `3036a02`.
- `scripts/`, `Makefile` (`make bench`, `make run-cmd` targets), `tests/test_run_cmd.py`
  (the by-path import pattern to reuse), `tests/test_hitbox_label_migration.py` (the JSON-drift guard).
