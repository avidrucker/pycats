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