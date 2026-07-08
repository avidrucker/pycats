# PyCats

A local 2-player cat fighter for the keyboard, written in Python with Pygame and
inspired by **Project M** (the *Super Smash Bros. Brawl* mod). Two cats knock each
other off a stage; damage builds knockback, and a launched fighter that flies past
the blast line loses a stock.

## What it is (and isn't)

pycats is a **personal learning project**, so its goals are shaped by that:

- **Project-M-at-heart, not a clone.** The *feel* — movement, knockback, shield,
  dodges, ledges — follows Project M; where pycats deliberately diverges is written
  down in [docs/project-m-parity.md](./docs/project-m-parity.md).
- **Deterministic and headless-first.** The simulation is frame-counted, RNG-free at
  its core, and runs without a display, so recorded "golden" snapshots reproduce a
  fight exactly and act as the regression oracle. This constraint is load-bearing —
  see the determinism/headless contract in [CONTEXT.md](./CONTEXT.md).
- **Local, keyboard, two players.** Two humans on one keyboard, or a human against a
  computer-controlled cat (see [Play against the computer](#play-against-the-computer)).

**Not** goals of this project: online / netplay, and a large character roster.
Play is keyboard-first; a game-controller backend is only exploratory, not part of
the current game.

## Quickstart

Requires Python 3.10+. These steps use a project virtualenv (`.venv`), which works
everywhere — including Debian/Ubuntu/Mint, where a bare `pip install` is refused with
`externally-managed-environment` (PEP 668).

```bash
git clone https://github.com/avidrucker/pycats.git
cd pycats
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # pygame-ce + the statechart engine
.venv/bin/python -m pycats.game                       # play
```

`requirements.txt` pulls both runtime dependencies: **pygame-ce**, and **statecharts**
— the statechart engine that drives every fighter and screen (ADR-0002). The engine
isn't on PyPI, so it's pinned there to a git release tag; nothing else to clone.

(If your `python` already points at a writable environment, you can skip the `.venv`
and drop the `.venv/bin/` prefixes.)

## Controls

Two players share the keyboard. Every key below is **rebindable in the in-game Options
screen** (the defaults are what "reset to defaults" restores).

| Action  | Player 1 | Player 2 |
| ------- | -------- | -------- |
| Move    | `W` `A` `S` `D` | Arrow keys |
| Attack  | `V` | `/` |
| Special | `C` | `.` |
| Shield  | `X` | `,` |
| Smash   | `B` | `'` |

Jump is *up* (`W` / `Up`); hold *down* to crouch and to drop through / off ledges.
Attack is the standard A-button; **Special** is the B-button (e.g. Nalio's fireball);
**Smash** is a dedicated strong-attack input.

## Play against the computer

A cat can be driven by the computer along **two independent axes** — don't confuse them:

**CPU difficulty — `--p1-level` / `--p2-level`, a level from 1 to 9.** This is the
Smash-style **CPU** opponent: higher levels react faster, attack and shield more, and
at the top levels throw specials (fireballs). Turning on a level makes that player a
CPU.

```bash
# Two Nalios: a level-5 CPU (P1) versus a level-9 CPU (P2), reproducible with a seed.
.venv/bin/python watch.py --p1-char nalio --p1-level 5 --p2-char nalio --p2-level 9 --seed 42
```

**Behavior variants — `--vs {idle,chase,idler,follower}`.** A *separate* axis: these
are scripted-controller personalities for P2 (idle = no controller, chase = pursue,
idler = baseline, follower = shadow P1), used for demos and testing. They are **not**
CPU difficulty levels — a "follower" is not "harder" than an "idler", just different.

```bash
.venv/bin/python watch.py --vs chase --seed 42   # P1 attacker vs a P2 that chases
```

Other `watch.py` modes: `--match` plays a full match to a KO, `--demo showcase` plays
the captioned feature demo, and `--video out.mp4` records instead of showing a live
window (recording needs `imageio` + `imageio-ffmpeg`). Run `watch.py --help` for the
full flag list. Omit `--seed` for a clocktime seed so a computer match varies
run-to-run; pass an int for a reproducible one.

---

## For contributors

### Running the tests

The suite runs headless (no display) and is the regression oracle. One canonical
command, run from the repo root:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. .venv/bin/python -m pytest -q
```

A green run with some skips is expected. Add `-m "not slow"` to skip the benchmark
tests. Golden snapshots live in `tests/golden/`; regenerate them intentionally with
`PYCATS_UPDATE_GOLDENS=1`.

### Development setup

The tests, linter, benchmark, and video recording need a few more packages, in
`requirements-dev.txt` (pytest, ruff, pre-commit, imageio) — install alongside the
runtime deps (see [ADR-0006](./docs/adr/) for the lint setup):

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
```

**Hacking on the engine?** To develop `statecharts-py` alongside pycats, clone it as a
sibling and install it editable *instead of* the pinned line in `requirements.txt`
(see [ADR-0002](./docs/adr/) for why it is the sole state engine):

```bash
git clone https://github.com/avidrucker/statecharts-py.git   # ../statecharts-py
.venv/bin/python -m pip install -e ../statecharts-py          # overrides the pinned tag
```

Lint + format (ruff; config in `ruff.toml` and `.pre-commit-config.yaml`):

```bash
.venv/bin/ruff check --select F,I,E722,E702,E402,UP pycats/   # lint (some findings: add --fix)
.venv/bin/ruff format --check pycats/                         # formatting
.venv/bin/pre-commit install                                  # one-time: run both on each commit
```

The lint hook is ruff-only so it stays fast; `pytest` remains the on-demand source of
truth (there is no CI gate). Legacy debug scripts that once masqueraded as tests now
live in `scripts/`, so a bare `pytest` collects only real assert-based tests.

### Benchmark

```bash
SDL_VIDEODRIVER=dummy .venv/bin/python bench.py                                   # quick run
SDL_VIDEODRIVER=dummy .venv/bin/python bench.py --frames 20000 --json bench_results/run.json
```

### Project layout

The `pycats/` package is split into a **display-free rules core** and a separate
**present layer** (rendering, input polling, `game.py`). The core sub-packages:

| Package | Holds |
| ------- | ----- |
| `pycats/core/` | input frames, rebindable keymaps, low-level physics |
| `pycats/entities/` | `Fighter` (pure state/rules), the `Player` sprite adapter, platforms, ledges |
| `pycats/combat/` | the data-driven attack system — hitboxes, knockback, shield, move selection |
| `pycats/characters/` | per-archetype fighter data + skins (Nalio, Birky, Narz, the default cat) |
| `pycats/charts/` + `pycats/systems/` | the statechart definitions and state engines |
| `pycats/sim/` | the headless battle runner, AI controllers, demos, and the captioned showcase |

Entry points are modules, **not** a `main.py`: `python -m pycats.game` (the game),
`watch.py` (replays / demos / CPU battles), and `bench.py` (benchmark). The
architecture layer map lives in [CONTEXT.md](./CONTEXT.md).

## Project docs

New here (human or agent)? Start with these:

- [CONTEXT.md](./CONTEXT.md) — domain vocabulary + the determinism/headless contract.
- [docs/glossary.md](./docs/glossary.md) — one-line definitions of every PM/Smash mechanic + project term, linked to the authoritative doc.
- [docs/adr/](./docs/adr/) — architecture decision records (the *why* behind design calls).
- [docs/project-m-parity.md](./docs/project-m-parity.md) — where pycats deliberately diverges from Project M.
- [docs/pygame-fonts.md](./docs/pygame-fonts.md) — working with the font/text stack: sizes, scaling, mixed text, per-frame `SysFont` and test-isolation gotchas.
- [RULES.md](./RULES.md) — project conventions (labels, filing, closing work).
