# PM Phase 0 — move/hitbox data schema & fighter statechart regions (design)

> Phase 0 of the Project-M mechanics roadmap: the foundation the rest of the
> roadmap parameterizes off — the move/hitbox **data schema** and the fighter
> statechart's **region decomposition**.
>
> Inputs: [pm-mechanics-implementation-analysis.md](../../research/pm-mechanics-implementation-analysis.md),
> [pm-framerate-fidelity.md](../../research/pm-framerate-fidelity.md),
> [brawl-projectm-fighter-states.md](../../research/brawl-projectm-fighter-states.md),
> [BACKLOG.md](../../research/BACKLOG.md), and the statecharts benchmark
> [spec](./2026-06-21-statecharts-benchmark-design.md).
> Date: 2026-06-21.

## Guiding principle (north star)

pycats aims to become **progressively more faithful to Super Smash Bros. Project
M** over time. The intent is explicitly to **add mechanics and interactions that
are not possible in the current app** — not merely to re-express existing
behavior in a new structure. Therefore:

- **Behavior will intentionally diverge** from the current/legacy app as PM
  mechanics land. We design for that, not against it.
- The **statechart (statecharts-py) becomes the primary fighter engine.** The
  legacy hand-rolled FSM is **frozen** as a "classic mode" + performance baseline.
- Strict cross-backend (legacy-vs-statechart) byte-identical parity **ends at
  Phase 0**; the regression oracle becomes **golden snapshots** of the statechart
  engine (same headless runner/harness, different oracle).
- The data schema and chart are designed to **grow additively** toward PM
  fidelity (minimal-now, grow-by-phase) so each later mechanic is a cheap,
  non-migrating extension.

Phase 0 itself adds no new *gameplay* mechanic; it builds the structure that makes
adding them cheap, and takes the one irreversible step (the oracle flip + circle
geometry) that the rest of the roadmap depends on.

## Decisions (from brainstorming)

| # | Decision | Choice |
| - | -------- | ------ |
| 1 | Schema fidelity | **Minimal now, grow additively by phase** (every field real & used) |
| 2 | Where data lives | **Python frozen dataclasses** as literals, behind a single `load_fighter_data()` seam (files possible later) |
| 3 | Combat geometry | **Circles** for hit/hurt/shield; **rects** unchanged for body↔terrain physics |
| 4 | Body hurtbox | **`list[Circle]`**, default a **2-circle body stack**; tails excluded |
| 5 | Statechart regions | **Two parallel regions: `action` + `defensive_status`**; jumps/shieldHP/percent/timers stay datamodel scalars |

## 1. Data schema

Frozen dataclasses; all timing in **integer frames**; circle offsets are
facing-RIGHT-relative and mirrored when the fighter faces left.

```python
# pycats/combat/data.py  (new)

@dataclass(frozen=True)
class Circle:
    dx: int      # offset from fighter origin (facing-right relative; mirrored if facing left)
    dy: int
    r: int

@dataclass(frozen=True)
class Hitbox:
    circle: Circle
    damage: float
    angle: int               # launch angle, degrees (Sakurai-angle handling: later phase)
    base_knockback: float
    knockback_growth: float

@dataclass(frozen=True)
class MoveData:
    name: str
    in_air: bool             # ground vs air variant
    startup: int             # frames before first active frame
    active: int              # frames hitboxes are live
    recovery: int            # frames after active until actionable
    hitboxes: tuple[Hitbox, ...]   # live during the active window

@dataclass(frozen=True)
class Hurtbox:
    circles: tuple[Circle, ...]    # default: 2-circle body stack

@dataclass(frozen=True)
class FighterData:
    hurtbox: Hurtbox
    moves: dict[str, MoveData]      # move_id -> data

def load_fighter_data(character: str) -> FighterData: ...   # single swap-to-files seam
```

- **Minimal core only** (Phase 0–1). Later phases add **defaulted** fields
  additively — e.g. `hitlag`, `shieldstun_mult`, `landing_lag`, charge frames,
  multiple/per-hitbox active windows, hitbox id/priority/clank, stale-move state.
  No migration of existing call sites.
- Deliberate "not yet" simplifications: one active window per move; no per-hitbox
  id/priority/clank; no Sakurai-angle special-casing.
- **Research-blocked fields are intentionally absent** until threads b/c resolve:
  shield pushback magnitudes, powershield/parry data.

## 2. Statechart regions

Two parallel regions advance each `send("tick")`.

### Region `action` (hierarchical fighter FSM)

```
action
├── actionable
│   ├── grounded
│   │   ├── idle
│   │   ├── run                 (current "run"/walk)
│   │   ├── crouch              (later phase)
│   │   └── shield              (sub: guard_on -> guard -> guard_off; shieldstun later)
│   └── airborne
│       ├── jump                (rising)
│       └── fall
├── attacking                   (ONE generic, data-driven move sub-chart)
│   ├── startup                 (frame budget = MoveData.startup)
│   ├── active                  (entry: spawn hitboxes from MoveData; lasts .active)
│   └── recovery                (lasts .recovery -> return to grounded/airborne)
├── dodging                     (spot / air / roll)
├── hitstun
│   └── hurt                    (later: tumble, knockdown, getup, shieldstun)
└── ko
```

Shared transitions ("from any actionable state you may jump/shield/attack") live
at the `actionable` parent rather than being repeated per leaf (the current flat
chart repeats them). `attacking` is a **single generic sub-chart** parameterized
by a `MoveData` row; Phase 0 wires exactly one move (the existing basic attack),
proving the data-driven path end-to-end.

### Region `defensive_status` (thin, concurrent)

```
defensive_status
├── vulnerable        (default)
├── intangible        (while the intangibility timer > 0)
└── armored           (placeholder, later phase)
```

### Cross-region coordination — via datamodel scalars, not emitted events

Regions stay decoupled. The `action` region owns *what the fighter is doing* and
sets an `intangibility` frame timer on the player when entering `dodging` (later:
respawn, ledge-grab). The `defensive_status` region only **observes** that scalar:
`vulnerable → intangible` while timer > 0, back when it reaches 0. Rendering and
hit-resolution read `defensive_status` / the timer.

### Frame mechanics

Consistent with the fixed-timestep model and the existing one-hop-per-`tick`
rule: every state entry sets a frame counter; `tick` increments it; transitions
fire on integer thresholds from `MoveData`/timers. No eventless transitions.

### Current → new mapping (golden baseline)

idle/run/jump/fall/shield/dodge/attack/hurt/ko all map into the tree above.
`stun` stays unreachable for now (later becomes shieldstun/shield-break under
`hitstun`). `StatechartEngine.state` keeps returning the single `action`-region
leaf label so existing `player.state` reads keep working; `defensive_status` is
read separately.

## 3. Integration, code layout, oracle flip

**Code layout**
- `pycats/combat/data.py` — schema + `load_fighter_data()` seam.
- `pycats/characters/<name>.py` — per-character `FighterData` literals (Phase 0:
  one cat, one move, the 2-circle hurtbox).
- `pycats/combat/geometry.py` — circle / circle-list overlap helpers
  (hit-vs-hurt, shield-vs-hit).
- `pycats/statecharts/fighter_chart.py` — grows from flat to hierarchical +
  two-parallel-region chart; the generic `attacking` sub-chart reads a `MoveData`.
- `StatechartEngine` — `state` returns the `action` leaf (back-compat); exposes
  `defensive_status` separately.

**Parity-oracle flip (the one irreversible step)**
- Circle geometry changes hit detection, so the data-driven attack is **not**
  byte-identical to the legacy rect attack. Strict cross-backend parity ends.
- `legacy` is frozen (classic mode + perf baseline). The oracle becomes
  **golden snapshots**: the existing headless runner + scripted timelines record
  golden per-frame snapshots of the *statechart* engine; tests assert future
  refactors reproduce them. Goldens are committed; a deliberate `--update-goldens`
  path regenerates them.

## Scope

**In scope (Phase 0):** the schema; the hierarchical + 2-region chart; circle
geometry + overlap helpers for the single existing attack; the load seam; the
oracle flip to golden snapshots; mapping current behavior into the new structure.

**Out of scope (later phases):** real knockback formula, hitstun-from-knockback,
shieldstun, multi-move movesets, DI/SDI, grabs/throws, tumble/knockdown/getup,
ledges, dash-dance/pivot/fast-fall, and the research-blocked PM signatures
(shield pushback, powershield/parry, wavedash, L-cancel — threads b/c).

## Testing

- **Unit:** `load_fighter_data` returns expected `FighterData`; geometry overlap
  helpers (circle–circle, circle-list); `attacking` sub-chart frame timing
  (hitboxes spawn on `active` entry, clear on exit); `defensive_status` follows
  the intangibility timer; hierarchical shared-transition behavior.
- **Regression:** golden-snapshot tests over the scripted timelines (including the
  full match-to-defeat). The per-frame snapshot is extended to capture the new
  observable state — the `action` leaf label (as today) **plus** `defensive_status`
  and the intangibility timer — so regressions in either region are caught.
- **Performance:** re-run `bench.py` / `bench_render.py` to confirm the richer
  chart stays cheap.

## Open / evolution notes

- As PM mechanics land, the `action` hierarchy and schema grow; the golden
  snapshots are updated deliberately at each behavior change.
- The move data may move from Python literals to data files later; the
  `load_fighter_data()` seam makes that a one-function change.
- Research threads b/c must resolve before the gated mechanics (shield pushback,
  powershield/parry, wavedash, L-cancel) can be implemented faithfully.
