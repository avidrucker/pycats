# Ledge-hang state — design (#14, v1 slice)

- **Status:** Approved (brainstorm 2026-06-30, DRAGONFRUIT)
- **Issue:** #14 "Add ledge-hang state" · area:entities · enhancement
- **Refs:** `docs/pm-reference/ledge-mechanics.md`, `docs/pm-reference/fighter-states.md`,
  `pycats/charts/fighter_chart.py` (FSM), prone slice precedent (#13/#146/#225).

## Scope

### In (v1)
Automatic ledge **grab** at a solid stage edge → **ledge-hang** (timed intangibility
window, input-locked) → **neutral getup** (up → climb onto stage) OR **drop**
(down/away → release into fall, with a regrab lockout) OR **timeout** (auto-release →
fall). **One-occupant lockout** per edge (a held edge blocks a second grab; no trump).

### Out (deferred → follow-up tickets filed on close)
Ledge **roll**, ledge **attack**, ledge **jump** (the other three getup options — slice
them like prone's #146/#225); **intangibility decay** on repeated grabs; **ledge-trump**
(later flips the one-occupant lockout into a trump); the **"2-frame"** grab-vulnerability;
**teching**; **up-B sweetspot** recovery (needs specials first); **hold-away-to-decline**
the grab + a **frame-accurate getup window** (v1 getup is instant).

### Decisions locked in brainstorming
1. **Solid edges only** — thin/pass-through platforms are not grabbable (owner ruling on
   #14, `docs/pm-reference/stages-and-environment.md`).
2. **Automatic grab** (PM-faithful, geometry-only — no button). Golden impact is measured
   during TDD; any shift lands a reviewed semantic regen per `tests/golden/REGEN_PROTOCOL.md`.
3. **One-occupant lockout** per edge (no trump in v1).
4. **Architecture A** — ledge-hang is a self-contained fighter behavior driven in
   `player.update` (like prone/crouch/dodge); per-edge occupancy lives on a small shared
   `Ledge` value, not in the match engine.

## Architecture

### Ledge model (new)
A small value object (e.g. `pycats/entities/ledge.py`, `Ledge`):
- `side`: `LEFT` | `RIGHT`.
- `anchor`: the corner point `(x, y)` = the thick platform's top-left / top-right.
- `catch_rect`: a `pygame.Rect` hanging just **outside and below** the corner
  (`LEDGE_CATCH_W × LEDGE_CATCH_H`); for LEFT it extends left+down of the anchor, for
  RIGHT right+down.
- `occupied_by`: the `Fighter`/`Player` currently hanging, or `None`.
- `hang_pos(player_size)`: the Rect top-left a hanging fighter snaps to (corner minus a
  body-relative hang offset, on the off-stage side).
- `getup_pos(player_size)`: the Rect top-left for standing on the stage at the corner.

Ledges are derived from each **thick** platform at **stage-construction time** (where the
`Platform`s are built) and carried with the stage so both the live game (`game.py`) and the
deterministic sim (`sim/runner.py`) build them identically. They are threaded into
`Player.update`.

### `Player.update` signature
`update(self, input_frame, platforms, attack_group, ledges=())` — `ledges` defaults to an
empty tuple so existing callers/tests compile unchanged; the live game and sim pass the real
list. (Callers to update: `game.py`, `sim/runner.py`, `watch.py`, and any test harness.)

### Fighter state (new fields, `entities/fighter.py`)
- `ledge_hang_timer: int` — counts down each hang frame; the **hang-timeout** window. For
  v1 it is also the **intangibility** window (decay-on-regrab deferred ⇒ `invulnerable`
  stays `True` for the whole hang).
- `grabbed_ledge` — the `Ledge` being held, or `None`. The presence/absence of this is the
  authoritative "am I hanging" signal the statechart reads.
- `ledge_regrab_lockout_timer: int` — set on release; while `> 0`, grab detection is
  suppressed (prevents instant regrab / infinite hang).
- Intangibility **reuses** the existing `invulnerable` flag (no new flag).

### Driving logic (`Player.update`, after `step_physics`, mirroring the prone/getup blocks)
1. **Regrab lockout decay:** if `ledge_regrab_lockout_timer > 0`, decrement.
2. **Grab detection** (only if `grabbed_ledge is None` and `ledge_regrab_lockout_timer == 0`):
   - Conditions: `not on_ground` AND `vel.y >= 0` (descending/level, not rising) AND the
     fighter's catch-point overlaps some `ledge.catch_rect` AND `ledge.occupied_by is None`.
   - On grab: set Rect to `ledge.hang_pos(...)`; `vel = (0, 0)`; `ledge_hang_timer =
     LEDGE_HANG_FRAMES`; `invulnerable = True`; `grabbed_ledge = ledge`;
     `ledge.occupied_by = self`; face toward the stage; send `force_ledge_grab` to the
     engine.
3. **While hanging** (`grabbed_ledge is not None`):
   - Pin position (suppress gravity — the fighter does not integrate physics while hanging);
     decrement `ledge_hang_timer`.
   - Read locked input (see Input):
     - **getup** (up held): Rect → `getup_pos(...)`; release (`occupied_by=None`,
       `grabbed_ledge=None`); `invulnerable=False`. (Now on the stage ⇒ statechart → idle.)
     - **drop** (down held, or holding away from the stage): release;
       `ledge_regrab_lockout_timer = LEDGE_REGRAB_LOCKOUT_FRAMES`; `invulnerable=False`; a
       small downward nudge so the next frame is clearly airborne (⇒ → fall).
     - else: stay hung.
   - **Timeout:** when `ledge_hang_timer` reaches 0 while still hanging, auto-release exactly
     like a drop (set the lockout) ⇒ fall.

Release in all paths clears `ledge.occupied_by` so the one-occupant lockout frees the edge.

### Statechart (`charts/fighter_chart.py`) — isomorphic to the prone leaf
- New leaf `ledge_hang` hoisted under the `action` compound, beside `prone`/`getup_*`.
- **Entry:** a hoisted `on("force_ledge_grab", "ledge_hang")` on `action` (beside
  `force_prone`). `Player.update` triggers it via the existing engine seam
  `self._engine.force("ledge_grab")` → `session.send("force_ledge_grab")`
  (`systems/state_engine_sc.py:37`).
- **Exits** (`_tick` guards reading the released state):
  ```python
  _tick(lambda e, d: p.fighter.grabbed_ledge is None and p.fighter.on_ground, "idle")
  _tick(lambda e, d: p.fighter.grabbed_ledge is None and not p.fighter.on_ground, "fall")
  ```
- `defensive_status` is **unchanged** — it flips to `intangible` whenever `invulnerable`,
  so ledge intangibility is reflected automatically.
- `StatechartEngine.state` resolves the active leaf by scanning a `LABELS` list
  (`systems/state_engine_sc.py`); **add `"ledge_hang"` to `LABELS`** so the new flat label
  resolves. Audit consumers that switch on a state label (render, stats) for a closed-set
  assumption and add a branch where needed.

### Input (`entities/fighter_input.py`)
While `grabbed_ledge is not None`, lock normal move / jump / attack / shield (like
`helpless`/`prone`/`landing_lag`); only the getup (up) and drop (down or away-from-stage)
reads are consulted. "Away from stage" = the horizontal direction pointing off the edge
(opposite the stage for the held `side`).

### Constants (`config.py`) — ⚠ playtest starting points, provenance-commented
- `LEDGE_HANG_FRAMES` — hang timeout = intangibility window (⚠ PM ledge intangibility is
  per-character; v1 single starting value).
- `LEDGE_REGRAB_LOCKOUT_FRAMES` — post-release regrab suppression (⚠ playtest).
- `LEDGE_CATCH_W`, `LEDGE_CATCH_H` — catch-region px size (⚠ playtest).
- Hang offset — derived from `PLAYER_SIZE` (how the body sits relative to the corner).

These are exactly the tuning constants the (blocked) #233 provenance registry will track;
for now comment them `⚠ playtest` per the existing `config.py` convention.

## Testing (TDD — every test must be able to fail)

- **Detection (unit):** descending into a LEFT/RIGHT catch region grabs; rising (`vel.y<0`)
  does **not**; a **thin** platform yields no grabbable edge; an **occupied** edge blocks a
  second grabber (one-occupant); a non-zero **regrab lockout** blocks an immediate regrab.
- **State (statechart):** from `fall`, `force_ledge_grab` ⇒ `state == "ledge_hang"`;
  `invulnerable` is `True` while hanging (and `defensive_status` reads `intangible`); up ⇒
  `idle`; down/away ⇒ `fall` and lockout set; timeout ⇒ `fall`.
- **Integration (`Player.update`):** a full grab→hang→getup cycle with a thick platform +
  synthetic input frames; a two-fighter same-edge occupancy test (second fighter keeps
  falling).
- **Golden:** run the full suite. If any golden shifts, follow `REGEN_PROTOCOL.md` — confirm
  every changed sidecar field is a genuine ledge-grab consequence, explain it in the commit,
  and land a reviewed semantic regen. Report the measured blast radius (ideally: none).

## Out-of-scope follow-ups to file on close
Ledge roll / attack / jump; intangibility decay-on-regrab; ledge-trump (flips the
one-occupant lockout); the "2-frame"; teching; up-B sweetspot; hold-away-to-decline +
frame-accurate getup window. (Coyote-time `game.py:17` is related but separately tracked.)
