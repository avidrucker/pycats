# Command SSOT for pycats (#725, Wave 1 of #724). Every target resolves the
# main-repo venv depth-independently, so it works from the main checkout AND
# from any .claude/worktrees/wt-* cwd (worktrees have no .venv — repo convention):
# from main, --git-common-dir -> .git, so ../.venv = .venv; from a worktree it
# -> the main repo's .git, so ../.venv resolves to main's venv.
GIT_COMMON := $(shell git rev-parse --path-format=absolute --git-common-dir)
VENV := $(GIT_COMMON)/../.venv/bin
PY := $(VENV)/python
RUFF := $(VENV)/ruff
HEADLESS := SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=.
ARGS ?=

.PHONY: help test test-isolated test-shuffle run run-cmd lint format bench profile goldens census

help:
	@echo "pycats — command SSOT (see #724). Targets:"
	@echo "  make test [ARGS=\"-k expr\"]   full suite headless (subset via ARGS)"
	@echo "  make test-isolated            per-file isolation sweep: each test_*.py alone in its own process (#1259)"
	@echo "  make test-shuffle             whole suite under pytest-randomly seeds — catches inter-test order-dependence (#1259)"
	@echo "  make run                      play: python -m pycats.game"
	@echo "  make run-cmd WHAT=<issue|branch|path>  print the run block for an UNMERGED worktree change (#859)"
	@echo "  make lint                     ruff format --check + check on pycats/ (close-gate)"
	@echo "  make format                   ruff format pycats/ (write; lint is its --check twin)"
	@echo "  make bench [ARGS=\"...\"]        bench.py headless (extra flags via ARGS)"
	@echo "  make profile [ARGS=\"...\"]      profile_loop.py cProfile hot-function harness (#1247; --state/--frames/--top via ARGS)"
	@echo "  make goldens                  regen file-based goldens (3 modules); review sidecars — see tests/golden/REGEN_PROTOCOL.md"
	@echo "  make census                   print the authored-vs-sourced value census (#1151); re-bless its ratchet baseline with PYCATS_UPDATE_AUTHORED_BASELINE=1"
	@echo ""
	@echo "SIM (run: python -m pycats.game):"
	@echo "  python -m pycats.game                   play the game (same as make run)"
	@echo "  SDL_VIDEODRIVER=dummy python bench.py   headless state-engine benchmark (same as make bench)"
	@echo "  SDL_VIDEODRIVER=dummy python profile_loop.py  cProfile App.step() hot-function harness (same as make profile)"
	@echo ""
	@"$(PY)" scripts/help_scripts.py

# full suite headless; subset via ARGS="-k expr"
test:
	$(HEADLESS) "$(PY)" -m pytest -q $(ARGS)

# per-file isolation sweep — each tests/test_*.py alone in its own process (#1259).
# Surfaces a test that only greens because a neighbor set up global state; exit-5
# ("no tests collected") is filtered, not treated as a failure.
test-isolated:
	$(HEADLESS) "$(PY)" scripts/isolation_sweep.py $(ARGS)

# shuffle-order run — the whole suite under pytest-randomly seeds (#1258 dep, #1259).
# Catches inter-test order-dependence rather than single-file isolation. Seeds via
# ARGS="--seed 42 --seed 7"; defaults to 0 and 1259.
test-shuffle:
	$(HEADLESS) "$(PY)" scripts/isolation_sweep.py --shuffle $(ARGS)

# play the game
run:
	PYTHONPATH=. "$(PY)" -m pycats.game

# Print the mistake-proof run block for an UNMERGED (worktree) change, resolving
# an issue number / branch name / worktree path -> `cd <worktree> && make run`
# (#859). Fails loudly if nothing matches — never falls back to main.
#   make run-cmd WHAT=859   |   make run-cmd WHAT=br-fig/pycats-882-...
run-cmd:
	@test -n "$(WHAT)" || { echo "usage: make run-cmd WHAT=<issue|branch|worktree-path>" >&2; exit 2; }
	@"$(PY)" scripts/run_cmd.py "$(WHAT)"

# ruff format --check + ruff check on pycats/ (mirrors the close-gate)
lint:
	"$(RUFF)" format --check pycats/ tests/
	"$(RUFF)" check pycats/ tests/

# apply ruff formatting (write-twin of lint's --check)
format:
	"$(RUFF)" format pycats/ tests/

# bench.py headless; extra flags via ARGS
bench:
	SDL_VIDEODRIVER=dummy PYTHONPATH=. "$(PY)" bench.py $(ARGS)

# profile_loop.py — cProfile App.step() hot-function harness (#1247); flags via ARGS
# e.g. make profile ARGS="--state playing --frames 900 --top 40"
profile:
	SDL_VIDEODRIVER=dummy PYTHONPATH=. "$(PY)" profile_loop.py $(ARGS)

# regenerate the file-based goldens — the three modules that honor
# PYCATS_UPDATE_GOLDENS (not the full suite; the flag is read only by these).
# A regen is REVIEWED, not rubber-stamped: diff the .summary.json sidecars and
# trace every change to an intended code change before committing.
# See tests/golden/REGEN_PROTOCOL.md.
goldens:
	PYCATS_UPDATE_GOLDENS=1 $(HEADLESS) "$(PY)" -m pytest -q \
	  tests/test_golden.py tests/test_golden_summary.py tests/test_screen_parity.py
	@echo
	@echo "goldens regenerated — REVIEW before committing:"
	@echo "  git diff tests/golden/*.summary.json   # read the semantic sidecar diffs"
	@echo "  every change must trace to an intended code change (tests/golden/REGEN_PROTOCOL.md)"

# print the authored-vs-sourced value census across both status loci (#1151):
# provenance.py config scalars + the per-fighter #1133 seam. Re-bless the ratchet
# baseline (tests/authored_value_baseline.json) with the env var below (reviewed).
census:
	$(HEADLESS) "$(PY)" -m pycats.combat.value_status_census
