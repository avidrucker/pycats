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

.PHONY: help test run lint format bench goldens

help:
	@echo "pycats — command SSOT (see #724). Targets:"
	@echo "  make test [ARGS=\"-k expr\"]   full suite headless (subset via ARGS)"
	@echo "  make run                      play: python -m pycats.game"
	@echo "  make lint                     ruff format --check + check on pycats/ (close-gate)"
	@echo "  make format                   ruff format pycats/ (write; lint is its --check twin)"
	@echo "  make bench [ARGS=\"...\"]        bench.py headless (extra flags via ARGS)"
	@echo "  make goldens                  regen file-based goldens (3 modules); review sidecars — see tests/golden/REGEN_PROTOCOL.md"

# full suite headless; subset via ARGS="-k expr"
test:
	$(HEADLESS) "$(PY)" -m pytest -q $(ARGS)

# play the game
run:
	PYTHONPATH=. "$(PY)" -m pycats.game

# ruff format --check + ruff check on pycats/ (mirrors the close-gate)
lint:
	"$(RUFF)" format --check pycats/
	"$(RUFF)" check pycats/

# apply ruff formatting (write-twin of lint's --check)
format:
	"$(RUFF)" format pycats/

# bench.py headless; extra flags via ARGS
bench:
	SDL_VIDEODRIVER=dummy PYTHONPATH=. "$(PY)" bench.py $(ARGS)

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
