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

## Development / benchmarking

Headless tests and the battle benchmark need pytest, pygame-ce, and the sibling
`statecharts-py` repo. On Debian/Mint (PEP 668 "externally-managed-environment")
use a project virtualenv:

    python3 -m venv .venv
    .venv/bin/python -m pip install pytest pygame-ce
    .venv/bin/python -m pip install -e ../statecharts-py   # sibling repo

**The statechart engine is now the default** for the live game, `watch.py`, and
`bench_render.py`. Pass `--backend legacy` (or set `PYCATS_STATE_BACKEND=legacy`)
to run the frozen classic baseline instead.

Phase-0 introduced a **data-driven attack system** with circle hitboxes (see
`pycats/combat/` and `pycats/characters/`). Golden snapshots in `tests/golden/`
are the regression oracle — regenerate them with `PYCATS_UPDATE_GOLDENS=1`.

Run tests:        .venv/bin/python -m pytest tests/test_smoke.py tests/test_state_engine.py \
                      tests/test_player_seam.py tests/test_input_script.py tests/test_fighter_chart.py \
                      tests/test_match_engine.py tests/test_runner.py tests/test_parity.py \
                      tests/test_full_match.py tests/test_render_battle.py tests/test_render_cache.py \
                      tests/test_benchmark.py tests/test_combat_data.py tests/test_geometry.py \
                      tests/test_player_move.py tests/test_combat.py tests/test_golden.py
Run benchmark:    SDL_VIDEODRIVER=dummy .venv/bin/python bench.py
Store results:    SDL_VIDEODRIVER=dummy .venv/bin/python bench.py --frames 20000 --json bench_results/run.json
Watch a replay:   .venv/bin/python watch.py                    # statechart (default)
  ...legacy:      .venv/bin/python watch.py --backend legacy   # frozen classic baseline
Watch full match: .venv/bin/python watch.py --match            # P1 defeats P2 (3 stocks)
  ...uncapped:    .venv/bin/python watch.py --match --uncapped  # FPS readout = true rate
Record a video:   .venv/bin/python watch.py --match --video media/full_battle.mp4
                      # video needs: .venv/bin/python -m pip install imageio imageio-ffmpeg

The live window shows an FPS counter + each fighter's stocks/damage (hide with
--no-overlay). It paces to 60 FPS by default; --uncapped shows the true rate.

(The benchmark suite is the test_*.py list above. Bare `pytest` also picks up
pre-existing legacy debug scripts in tests/ that have unrelated collection issues.)

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