# PyCats

A game inspired by Super Smash Bros, written in Python using Pygame.

# How to Run

1. Clone the repository:
   ```bash
   git clone
   ```

2. Navigate to the project root directory:
   ```bash
   cd pycats
   ```

3. Install the required dependencies:
   ```bash
   pip install pygame-ce
   ```

4. Run the game:
   ```bash
   python -m pycats.game
   ```

# Project docs

New here (human or agent)? Start with these:

- [CONTEXT.md](./CONTEXT.md) — domain vocabulary + the determinism/headless contract.
- [docs/adr/](./docs/adr/) — architecture decision records (the *why* behind design calls).
- [docs/project-m-parity.md](./docs/project-m-parity.md) — where pycats deliberately diverges from Project M.
- [RULES.md](./RULES.md) — project conventions (labels, filing, closing work).

## Development / benchmarking

Headless tests and the battle benchmark need pytest, pygame-ce, and the sibling
`statecharts-py` repo. On Debian/Mint (PEP 668 "externally-managed-environment")
use a project virtualenv:

    python3 -m venv .venv
    .venv/bin/python -m pip install pytest pygame-ce
    .venv/bin/python -m pip install -e ../statecharts-py   # sibling repo

**The statechart engine is the sole state engine** for the live game, `watch.py`,
and the benchmarks (ADR-0002: the legacy backend and its `--backend` /
`PYCATS_STATE_BACKEND` selection were removed in #178/#183).

Phase-0 introduced a **data-driven attack system** with circle hitboxes (see
`pycats/combat/` and `pycats/characters/`). Golden snapshots in `tests/golden/`
are the regression oracle — regenerate them with `PYCATS_UPDATE_GOLDENS=1`.

Run tests:        SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. .venv/bin/python -m pytest -q
                      # bare pytest is the source of truth — collects & runs the whole suite
                      # green (skips OK). Add -m "not slow" to skip the benchmark tests.

Copy-paste one-liner (absolute paths, runs from anywhere):

    cd /home/avi/Documents/Study/Python/pycats && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. /home/avi/Documents/Study/Python/pycats/.venv/bin/python -m pytest -q

The `cd <repo> && <test cmd>` form keeps `cd` a separate command from the test run
(the `&&` is the separator), so the whole thing still pastes as one line — without
it, `cd` plus the env vars on one line trips `bash: cd: too many arguments`, and a
line-break after `-m` makes Python report `Argument expected for the -m option`.
Run benchmark:    SDL_VIDEODRIVER=dummy .venv/bin/python bench.py
Store results:    SDL_VIDEODRIVER=dummy .venv/bin/python bench.py --frames 20000 --json bench_results/run.json
Watch a replay:   .venv/bin/python watch.py                    # scripted replay
Watch full match: .venv/bin/python watch.py --match            # P1 defeats P2 (3 stocks)
  ...uncapped:    .venv/bin/python watch.py --match --uncapped  # FPS readout = true rate
Record a video:   .venv/bin/python watch.py --match --video media/full_battle.mp4
NPC battle (--vs): .venv/bin/python watch.py --vs chase            # P1 vs NPC: idle|chase|idler|follower (#61)
  ...reproducible:  .venv/bin/python watch.py --vs chase --seed 42 # same seed + backend → same outcome (#166)
                      # omit --seed for a clocktime seed → the NPC battle varies run-to-run
                      # video needs: .venv/bin/python -m pip install imageio imageio-ffmpeg

The live window shows an FPS counter + each fighter's stocks/damage (hide with
--no-overlay). It paces to 60 FPS by default; --uncapped shows the true rate.

(Legacy debug/diagnostic scripts that once masqueraded as tests now live in
`scripts/`, so bare `pytest` is clean. `tests/` holds only real assert-based tests.)

(If your `python` already resolves to a writable environment, drop the
`.venv/bin/` prefix.)

# Controls

- **Player 1**:
  - Move: WASD keys
  - A Attack: v
  - B Attack: c
  - Shield: x

- **Player 2**:
  - Move: Arrow keys
  - A Attack: /
  - B Attack: .
  - Shield: ,

# File Structure
```
pycats/                 ← top-level package  (must contain __init__.py)
├── __init__.py
├── config.py
├── entities/
│   ├── __init__.py
│   ├── platform.py
│   ├── attack.py
│   └── player.py
└── game.py             ← tiny entry-point / game loop
```