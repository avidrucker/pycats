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

Run tests:        .venv/bin/python -m pytest
Run benchmark:    .venv/bin/python bench.py
Watch a replay:   .venv/bin/python watch.py --backend statechart

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