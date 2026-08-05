"""
pycats/combat/data.py

Purpose: Frozen dataclass schema for fighter move/hitbox data, plus the
load_fighter_data() seam used by all consumers.

Contents:
- Circle      — 2-D collision circle, offset relative to fighter origin (facing right)
- Hitbox      — one active hitbox: a circle, damage amount, and launch angle
- MoveData    — one move: timing (frames) + one or more hitboxes
- Hurtbox     — the fighter's vulnerable body: one or more circles
- FighterData — full fighter data: hurtbox + named moves dict
- load_fighter_data(character) -> FighterData

Design notes:
- All timing values are integer frames.
- Circle offsets are facing-RIGHT-relative; consumers mirror for left-facing.
- Phase 0: load_fighter_data returns the same default for every character key.
  Phase 1+ will branch per character to TOML/JSON files.
- dict[str, MoveData] on a frozen dataclass is legal: the field holds a dict
  reference, we just never reassign the field.  Callers must not mutate it.
"""

from __future__ import annotations

import json
from dataclasses import MISSING, dataclass, field, fields, replace
from enum import Enum
from pathlib import Path

# Movement-constant defaults live in config; FighterData uses them as field
# defaults so any data that doesn't specify movement == today's globals (the
# default cat / golden sim is unchanged). #126.
from ..config import DASH_SPEED, GRAVITY, JUMP_VEL, MAX_FALL_SPEED, MAX_JUMPS, MOVE_SPEED

# ---------------------------------------------------------------------------
# Per-fighter value status (#1133, O3+O2 seam ratified in #1129)
# ---------------------------------------------------------------------------
# The machine-readable authored-vs-sourced status of each per-fighter move value,
# the fighter-data counterpart of the config-scalar `Provenance` registry
# (combat/provenance.py, ADR-0003). That registry covers config/physics scalars;
# this seam covers the per-move data in `characters/*_cat.py` that flips to
# `characters/data/*.json` — the gap #1124 found (G1/G2). Granularity is per-VALUE
# (#1129 Q5): a `status` map on each authored dataclass keys the dataclass's OWN
# field names, so a box's radius can be FOUND while its damage is PLACEHOLDER (the
# mixed-box case, e.g. Final Cutter's datamined blade radius + playtest position).
# CPU controller constants are OUT of this seam (#1129 Q4, ruling #704).


class Status(Enum):
    """Authored-vs-sourced status of one per-fighter value (#1129 Q3).

    FOUND       — traced to a cited canon value (datamine / SmashWiki / decomp);
                  MEASURED body geometry is FOUND with `source="datamine"` (there is
                  no separate MEASURED status — #1129 Q3).
    GUESS       — unsourced / playtest starting point that IS seeking canon; a
                  grounding DEBT the #319-style sourcing pass resolves.
    TUNED       — a deliberate design value, not seeking canon (pycats flavor).
    DIVERGENCE  — an intentional departure from a known canon value.
    PLACEHOLDER — a deliberate V1 no-parity-claim stand-in (#1129 Q3): the value
                  makes NO parity claim and is not a grounding debt (distinct from
                  GUESS), e.g. the #893-flattened sex-kick aerials, Final Cutter's
                  phase-2/3 numbers. The #1125 ratchet counts these apart from GUESS.
    """

    FOUND = "FOUND"
    GUESS = "GUESS"
    TUNED = "TUNED"
    DIVERGENCE = "DIVERGENCE"
    PLACEHOLDER = "PLACEHOLDER"


@dataclass(frozen=True)
class FieldStatus:
    """The status of one authored value, plus an optional citation `source`.

    `source` is the machine-readable provenance string for a FOUND value —
    "datamine" for brawllib_rs / rukaidata geometry, a SmashWiki page, a decomp
    path — mirroring `Provenance.source`. None when a bare status carries no
    citation (a PLACEHOLDER/GUESS makes no claim to cite). Serializes compactly:
    a bare status string when `source is None` (`"PLACEHOLDER"`), else an object
    (`{"status": "FOUND", "source": "datamine"}`) — the same lenient union the
    hurt-circle label form uses (#1036).
    """

    status: Status
    source: str | None = None


# A per-value status map: field-name (of the owning dataclass) -> FieldStatus.
# Empty by default on every authored dataclass, so the serializer omits it and all
# existing data stays byte-identical (golden-safe). `dict` (unhashable) follows the
# `FighterData.moves` precedent — nothing hashes these frozen dataclasses.
StatusMap = dict[str, "FieldStatus"]


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Circle:
    """A 2-D circle, offset (dx, dy) from the fighter origin, radius r.

    All values in pixels. Offsets are facing-RIGHT-relative.

    `label` is an optional stable per-circle display id (#1036): a letter A–Z
    the editor (and a JSON reader) uses to tell which HURT circle is which, the
    hurt-side counterpart of `Hitbox.label`. It carries the same leniency —
    assigned editor-side, preserved across save→load, `None` for unlabeled
    (migrated/hand-written) data so the serializer omits it and existing data is
    byte-identical (golden-safe). Hit circles keep `None` here; a hitbox's letter
    lives on `Hitbox.label`, not on its `Circle`.
    """

    dx: int
    dy: int
    r: int
    label: str | None = None
    # Per-value status (#1133), keyed by this Circle's own field names ("r"/"dx"/
    # "dy"). Empty by default → omitted from JSON → existing data byte-identical.
    # A hit circle's status serializes as a `circle_status` sibling of its inlined
    # `circle` triple; a hurt circle's rides inside its labeled dict form (#1036).
    status: StatusMap = field(default_factory=dict)


@dataclass(frozen=True)
class Hitbox:
    """One active hitbox for a move.

    Fields:
        circle           — position and size (facing-right coords)
        damage           — percentage damage dealt on hit
        angle            — launch angle in degrees (0 = directly right, 90 = up)
        base_knockback   — BKB: knockback at 0% (Phase 1)
        knockback_growth — KBG: how knockback scales with percent (Phase 1)
        active_start     — per-hitbox temporal window (#204): inclusive START
                           frame in the MoveClock 1-indexed frame coordinate.
                           None = use the move's window [startup+1, startup+active]
                           (today's behavior — the box spawns with the move's
                           default group). Sequential multi-hit moves give boxes
                           different windows so they fire on different frames.
        active_end       — inclusive END frame of the window. Paired with
                           active_start: set both or neither.
        set_knockback    — weight-dependent SET knockback (WDSK, #211). When set
                           to the WDSK value, this hit's launch ignores the
                           victim's percent (a "set" hit) but still scales with the
                           victim's weight + KBG/BKB. None = normal percent-scaling
                           (today's behavior). The hit still deals its `damage` %;
                           only the knockback is set.
        set_id           — hitbox-SET tag for B-full hit resolution (#888, mirrors
                           Brawl's `set_id` + `hitbox_sets_rehit`). Boxes across a
                           move's temporal windows (#204) that share a set_id share
                           a per-target hit-list within one move-instance → a
                           stationary target is hit ONCE by the set (the fix for a
                           two-window clean/late move over-hitting). A DIFFERENT
                           set_id re-hits. None = no set (today's behavior: each
                           window's Attack is independent → multi-hit), so every
                           existing move is byte-identical (golden-safe). The tag
                           is per-move-instance: the registry clears on move start,
                           so the same small integer may be reused across moves.
        label            — a stable per-hitbox display id (#958, #1029): a letter
                           A–Z the editor (and a JSON reader) uses to tell which
                           hitbox is which across a move's temporal windows. The
                           letter is a preserved identity — assigned once at box
                           creation editor-side (#1030) and carried through
                           save→load; `collapse` PRESERVES the source box's `label`
                           rather than recomputing a rank, so deleting a *middle*
                           box does not re-letter the survivors, and a box spanning
                           several windows keeps ONE letter. None = unlabeled
                           (migrated/hand-written data, or a box with no assigned
                           letter), so every existing move is byte-identical (the
                           serializer omits it) — golden-safe.
        hitlag_mult      — per-hitbox hitlag multiplier (ADR-0018 #1161, ruled
                           into V1 by ADR-0021 #1150). Scales this box's hitlag
                           (freeze) frames. 1.0 = the move's default hitlag
                           (today's behavior). Consumer wiring (-> hitlag_frames)
                           is a downstream DEV; this DEV stores it only.
        shield_damage    — extra damage this box deals to a shield beyond its %
                           (ADR-0018). 0 = no bonus (today's behavior). Consumer
                           wiring (-> shield.py depletion) is downstream.
        ground / aerial  — target-state gate: whether this box can hit a grounded
                           / airborne target (ADR-0018). Both True = hits either
                           (today's behavior). Mirrors the datamine's two
                           independent flags 1:1 (not one enum). Consumer wiring
                           (target-state gate in hit_resolution) is downstream.
        hitbox_id        — the raw datamined per-box id (ADR-0018), authored in
                           priority order. None = no id (today's behavior). The
                           `max(damage)->min(hitbox_id)` same-frame box-selection
                           swap is a separate downstream DEV (#1214); this DEV
                           stores the field only, so all data stays byte-identical.
    All five default to today's behavior -> the serializer omits them at their
    default (§1 omit == default) -> every existing move is byte-identical and
    schema_version stays 1 (ADR-0021).
    """

    circle: Circle
    damage: float
    angle: int
    base_knockback: float = 0.0
    knockback_growth: float = 0.0
    active_start: int | None = None
    active_end: int | None = None
    set_knockback: int | None = None
    set_id: int | None = None
    label: str | None = None
    hitlag_mult: float = 1.0
    shield_damage: int = 0
    ground: bool = True
    aerial: bool = True
    hitbox_id: int | None = None
    # Per-value status (#1133), keyed by this Hitbox's own field names ("damage"/
    # "angle"/"base_knockback"/...). Empty by default → omitted → byte-identical.
    # The owning circle's radius/offset status lives on `circle.status`, not here,
    # so the mixed box (sourced radius + authored scalars, #1124) is expressed by
    # the two maps together.
    status: StatusMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        s, e = self.active_start, self.active_end
        if (s is None) != (e is None):
            raise ValueError(f"Hitbox active_start/active_end must be set together (got start={s!r}, end={e!r})")
        if s is not None:
            if s < 1:
                raise ValueError(f"Hitbox active_start {s} must be >= 1")
            if s > e:
                raise ValueError(f"Hitbox window start {s} is after its end {e}")


@dataclass(frozen=True)
class VelocityPhase:
    """A scripted mid-move velocity SET (#973, B1 of #566 Final Cutter).

    On the frame the move clock's (post-increment) `move_frame` reaches `frame`,
    the engine SETs the fighter's velocity to (`vx` facing-relative, `vy`) —
    replacing, not adding to, the current velocity. This is the generalized
    counterpart of the recovery hook's single start-of-move burst (#578): a move
    may declare an ORDERED LIST of these to model multi-phase specials (Final
    Cutter's rise->plunge flip; a future Dolphin-Slash-style special).

    The trigger is a fixed integer frame (deterministic, a pure function of
    `move_frame`) — NOT apex-velocity detection, which #1066 Q2 ruled out because
    it couples the boundary to `vy` history (a mid-rise hit fires it on the wrong
    trajectory). `vy` is screen-space (negative = up, like `recovery_vy`); `vx` is
    mirrored by facing at apply time (like `recovery_vx`).
    """

    frame: int
    vx: float = 0.0
    vy: float = 0.0
    # Per-value status (#1133), keyed by this phase's own field names ("frame"/
    # "vx"/"vy"). Empty by default → the phase serializes as its compact
    # [frame, vx, vy] triple (byte-identical); a non-empty map expands it to the
    # object form so status can ride along.
    status: StatusMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.frame < 1:
            raise ValueError(f"VelocityPhase frame {self.frame} must be >= 1 (post-increment move_frame)")


@dataclass(frozen=True)
class LandingSpawn:
    """A projectile spawned when a move's fighter touches the ground (#974, B-cluster
    of #566 Final Cutter — the up-B's ground shockwave beam).

    Unlike the mid-move projectile (spawned on an active move-clock frame in
    `Player._spawn_move_hitbox` when `projectile_speed` is set), this fires on the
    touchdown EVENT (`Player._step_physics` detects the airborne->ground frame). The
    event trigger is canon-required, not a preference: the descent-to-floor distance
    varies (off a ledge, on a taller stage), so a fixed move-clock frame would desync
    the beam (#1066 Q2 — the Melee decomp fires the landing phase in a ground-contact
    callback, meleelight in `land()`). By touchdown the move has usually ended
    (`current_move is None`, routed to `helpless`), so the spawn keys off a descriptor
    stashed at move start (`Player._pending_landing_spawn`), not off the move clock.

    Reuses the #223/#266 `Projectile` primitive — only the trigger (on-land) and the
    spawn position are new. The projectile resolves its circles against the fighter's
    grounded rect at touchdown, so author the hitbox circle at the feet offset. It
    travels outward at `speed` px/frame along the facing direction; `both_directions`
    emits a mirrored pair for a symmetric shockwave (assumes a body-centred box, dx≈0,
    since the circle is resolved against the same facing for both). `landing_lag` is
    the grounded action-lock applied on touchdown (routed via the existing
    `landing_lag` chart state, #202); 0 recovers straight to idle. Generalizes to any
    special's landing effect (#1066 Q4), not Birky-only.
    """

    hitboxes: tuple[Hitbox, ...]
    speed: float
    lifetime: int
    landing_lag: int = 0
    both_directions: bool = False
    gravity: float = 0.0
    # Per-value status (#1133), keyed by this spawn's own field names ("speed"/
    # "lifetime"/"landing_lag"/...). The spawn's hitboxes carry their own maps.
    # Empty by default → omitted → byte-identical.
    status: StatusMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hitboxes:
            raise ValueError("LandingSpawn requires at least one hitbox")
        if self.lifetime < 1:
            raise ValueError(f"LandingSpawn lifetime {self.lifetime} must be >= 1")
        if self.speed < 0:
            raise ValueError(f"LandingSpawn speed {self.speed} must be >= 0")
        if self.landing_lag < 0:
            raise ValueError(f"LandingSpawn landing_lag {self.landing_lag} must be >= 0")


@dataclass(frozen=True)
class MoveData:
    """Timing and hitbox data for a single move.

    Fields:
        name      — human-readable move name
        in_air    — True if this is an aerial move, False for ground moves
        startup   — frames before hitbox becomes active
        active    — frames the hitbox is present
        recovery  — frames after the hitbox disappears before the fighter is free
        hitboxes  — one or more Hitbox instances (tuple, immutable)

    Total move duration = startup + active + recovery frames.
    """

    name: str
    in_air: bool
    startup: int
    active: int
    recovery: int
    hitboxes: tuple[Hitbox, ...]
    # Rehit-rate (#213): frames between re-hits of the same target for a LOOPING
    # multi-hit move (the d-air drill). None = single hit per move-instance
    # (today's behavior, the #130 guarantee). A number N = the spawned hitbox
    # re-hits an overlapping target every N frames across its active window.
    rehit_rate: int | None = None
    # Projectile special (#223): when projectile_speed is set, the move spawns a
    # MOVING projectile (an Attack with velocity = facing * projectile_speed) that
    # lives projectile_lifetime frames, detached from the owner. None = a normal
    # static-hitbox move. projectile_speed is a ⚠🔬 GUESS in px/frame (derive via
    # rukaidata units/frame × PX_PER_UNIT / playtest — tracked like #192).
    projectile_speed: int | None = None
    projectile_lifetime: int | None = None
    # Smash charge (#327 slice 3a): a chargeable move is HELD to charge and
    # released to fire (the charge state). Defaults False, so every existing
    # move is byte-identical (golden-safe); slice 3b scales a charged hit's output.
    chargeable: bool = False
    # Special-recovery / up-B (#578, B1 of #566): a recovery move applies an upward
    # velocity burst on start (SET, not add) and routes the fighter into `helpless`
    # (#184) when it ends airborne. `grants_recovery` gates the behavior;
    # `recovery_vy` is the vertical burst (negative = up, like jump_vel);
    # `recovery_vx` is an optional facing-relative horizontal component (arc).
    # Defaults off / zero → every existing move is byte-identical (golden-safe).
    # NOTE: distinct from `recovery` above, which is this move's END-LAG frame count.
    grants_recovery: bool = False
    recovery_vy: float = 0.0
    recovery_vx: float = 0.0
    # Scripted mid-move velocity phases (#973, B1 of #566): an ordered list of
    # VelocityPhase, each SETting velocity at its integer `move_frame` (see
    # VelocityPhase). The engine hook (`Player._apply_velocity_phases`) is what
    # models Final Cutter's rise->plunge flip; the rise burst stays the #578
    # `recovery_vy` start SET, these are the AFTER-rise re-sets. Empty by default
    # → every existing move is byte-identical (golden-safe); the serializer omits
    # it (omit == default). Generalizes the recovery hook rather than bolting on a
    # one-off plunge_frame/plunge_vy pair (Nalio SJP #956 / Narz can reuse it).
    velocity_phases: tuple[VelocityPhase, ...] = ()
    # Per-move hurtbox override (#831, R1 of the #792 editor). None = use the
    # fighter-posture hurtbox (FighterData.hurtbox / crouch_hurtbox / prone_hurtbox
    # — today's behavior). A move that sets this carries its own always-active
    # Hurtbox, letting the editor author per-move hurtboxes (per-frame edits are
    # collapsed to one static override by union, #809 §1.2). Defaults None → every
    # existing move is byte-identical (golden-safe). INERT until a consumer resolves
    # `move.hurtbox or fighter.hurtbox` — that's R2 (#792), not this slice.
    # Forward ref (Hurtbox is defined below): safe under `from __future__ import
    # annotations`, which stringifies all annotations.
    hurtbox: Hurtbox | None = None
    # Landing-triggered shockwave (#974, B-cluster of #566): a LandingSpawn spawned
    # the frame the fighter touches down (the engine hook is
    # `Player._spawn_landing_shockwave`), modelling Final Cutter's ground beam. The
    # trigger is the touchdown EVENT (not a move-clock frame), so a varying
    # descent-to-floor distance can't desync it (#1066 Q2 / see LandingSpawn).
    # Defaults None → every existing move is byte-identical (golden-safe); the
    # serializer omits it (omit == default). Generalizes to any special's landing
    # effect (#1066 Q4), reusing the #223/#266 Projectile primitive.
    landing_spawn: LandingSpawn | None = None
    # Counter special (#1199, ruled #1194 D5): Narz's down-B. `is_counter` marks a
    # move as a counter-DETECT stance — it is NOT run on the move clock (it arms the
    # `counter` fighter state instead, via Fighter.start_counter), so its startup /
    # active / recovery describe the DETECT window (active sub-window = the ruled
    # detect frames) rather than a hitbox window, and its `hitboxes` are empty. On a
    # successful counter, the move keyed by `counter_riposte_key` is spawned as the
    # riposte (a normal clocked move — the fixed-7% SpecialLwHit). Both default
    # off/None → every existing move is byte-identical (golden-safe); the serializer
    # omits them (omit == default). Behavioural flags, not authored value slots
    # (classified NON_VALUE in value_status_census).
    is_counter: bool = False
    counter_riposte_key: str | None = None
    # Per-value status (#1133), keyed by this move's own scalar field names
    # ("recovery_vy"/"startup"/...). Per-box status lives on each Hitbox; this map
    # is for the MOVE-level scalars. Empty by default → omitted → byte-identical.
    status: StatusMap = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Per-hitbox temporal-window cross-check (#204). Per-box shape (paired,
        # non-inverted, start >= 1) is enforced on Hitbox; here we need the move's
        # duration: a window must end within the move. Design B (#951): boxes
        # sharing a start frame may hold DIFFERENT windows (each its own Attack;
        # see move_clock._compute_windows) — the v1 same-start/same-window
        # rejection is lifted, so per-frame authored divergence is representable.
        total = self.startup + self.active + self.recovery
        for hb in self.hitboxes:
            if hb.active_start is None:
                continue
            if hb.active_end > total:
                raise ValueError(
                    f"Hitbox window [{hb.active_start}, {hb.active_end}] exceeds move '{self.name}' duration {total}"
                )
        # A velocity phase past the move's last frame would never fire (the clock
        # clears the move on completion) — reject it as authoring error (#973).
        for vp in self.velocity_phases:
            if vp.frame > total:
                raise ValueError(f"VelocityPhase frame {vp.frame} exceeds move '{self.name}' duration {total}")


# ---------------------------------------------------------------------------
# Fighter-level data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Hurtbox:
    """The fighter's vulnerable body, represented as a tuple of Circles.

    Circles are in facing-RIGHT-relative coords; consumers mirror for left.
    """

    circles: tuple[Circle, ...]


@dataclass(frozen=True)
class FighterData:
    """Complete data definition for one fighter character.

    Fields:
        hurtbox — the fighter's vulnerable body
        moves   — mapping of move key (e.g. "attack") to MoveData
        weight  — fighter weight fed to the knockback formula (#117/#123). The
                  Smash convention is Mario = 100; defaults to 100 so existing
                  data (the default cat) is unchanged and stays the baseline.
        gravity / max_fall_speed / move_speed / jump_vel / max_jumps —
                  per-character movement constants (#126), read per-fighter by
                  the physics/input layer. Each defaults to the matching config
                  global, so data that omits them behaves exactly as before.
        crouch_size / crouch_hurtbox — per-character crouch geometry (#124): the
                  (w, h) the body Rect resizes to when crouching (feet planted)
                  and the shorter/lower hurtbox used while crouched. Both default
                  to None = this fighter cannot crouch. Crouch effectiveness is
                  deliberately per-character (PM: Kirby hugs the ground, DK barely
                  lowers) — see docs and the #124 research notes.
        prone_size / prone_hurtbox — per-character prone/knockdown geometry (#173):
                  the lying-down counterpart of the crouch pair. While prone the
                  body Rect lowers further than crouch (a downed fighter lies flat)
                  and the hurtbox drops with it so high attacks whiff. Both default
                  to None = this fighter has no prone posture (it keeps the stand
                  box while prone). New fields, NOT reused crouch fields: prone is a
                  lower posture than crouch.

    The dict is not frozen; callers must not mutate it.
    """

    hurtbox: Hurtbox
    moves: dict[str, MoveData]
    weight: int = 100
    gravity: float = GRAVITY
    max_fall_speed: float = MAX_FALL_SPEED
    move_speed: float = MOVE_SPEED
    # Walk/dash/run (#388): `move_speed` is the WALK; `dash_speed` is the faster
    # tap-burst (#374 design). Defaults to the config global so existing data is
    # unchanged; the dash is only reached via `_start_dash` (slice 2b's double-tap).
    dash_speed: float = DASH_SPEED
    # `run_speed` (#967, slice 3): the SUSTAINED speed after the dash burst, held by
    # keeping the dash direction pressed past the burst window (the `run` leaf).
    # Provisional home mirroring move_speed/dash_speed until the ADR-0011 re-pin folds
    # all three into the raw-unit per-character JSON schema (no config fallback); this
    # slice adds NO new run global, so it defaults to DASH_SPEED. dash != run is a
    # STATE distinction (sustained vs. decay), not a pixel one (ADR-0011 §Decision 4):
    # for nalio run == dash == round(mod_factor(1.5)) == 8, an equal pixel that is
    # correct and intended, not a value to force apart.
    run_speed: float = DASH_SPEED
    jump_vel: float = JUMP_VEL
    max_jumps: int = MAX_JUMPS
    # ROUNDS Leech knob-fields (#1208, ADR-0019 §2) — the cached patch targets for
    # the two Leech cards, all defaulted OFF so every existing cat is byte-identical
    # (missing JSON keys hydrate to these defaults, #1196 precedent). This slice adds
    # the fields + their seams only; nothing reads them yet — Vampire's on-hit
    # lifesteal is DEV 5 (process_hits), Health Regen's per-interval tick is DEV 4
    # (systems/over_time.py). Kept as three flat scalars (the #1208 /decomplect ruling
    # — Option A), matching the top-level scalar seams above; grouping deferred until a
    # consumer needs it.
    lifesteal_fraction: float = 0.0  # Vampire: fraction of damage dealt healed (e.g. 0.3)
    regen_rate: float = 0.0  # Health Regen: heal chunk per interval (percent)
    regen_interval: int = 0  # Health Regen: frames between heals (0 = off)
    # Per-fighter standing body box (#275). None = the global config.PLAYER_SIZE
    # (via owner.SIZE), so the default cat / sim path is unchanged. Symmetric with
    # crouch_size/prone_size; a small archetype (Kirby) sets a shorter box here.
    stand_size: tuple[int, int] | None = None
    crouch_size: tuple[int, int] | None = None
    crouch_hurtbox: Hurtbox | None = None
    prone_size: tuple[int, int] | None = None
    prone_hurtbox: Hurtbox | None = None
    # Per-value status (#1216), keyed by this FighterData's OWN scalar field names
    # ("weight"/"gravity"/… and the incoming per-character walk/dash/run, #1209).
    # The fighter-LEVEL counterpart of the five #1133 carriers (Circle/Hitbox/
    # MoveData/VelocityPhase/LandingSpawn), which the seam originally skipped
    # (value_status_census: "Hurtbox and FighterData themselves carry no status
    # map"). Empty by default → omitted from JSON → existing data byte-identical.
    status: StatusMap = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loader seam
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# JSON hydrate (#838, R3 of the #792 editor) — dict -> FighterData
# ---------------------------------------------------------------------------
# A PURE, mechanical hydrate of the thin-mirror schema
# (docs/pycats-editor-data-schema-design.md §1 + §2.1). No reshaping, no window
# synthesis, no unit scaling — values are already px/frames as authored.
#
# Rules (§2.1):
#   - inline [dx, dy, r] -> Circle(*triple); {"circles": [...]} -> Hurtbox.
#   - Hitbox/MoveData/FighterData get ONLY the keys present in the doc — the
#     frozen dataclass supplies every default, so the loader keeps a SINGLE
#     default table and cannot drift from it. "Omit == default" (§1).
#   - JSON arrays deserialize to lists -> re-tuple() every collection (hitboxes,
#     circles, *_size) because the dataclasses are frozen and goldens depend on
#     tuple identity.
#   - Validation is DELEGATED to the existing __post_init__ checks (paired
#     window, window-in-duration, same-start-same-window); the loader adds only
#     the schema_version guard below.
#   - doc["provenance"] is NEVER read here (the drift-guard test consumes it, R7).
#
# This slice is the function ONLY — it is not wired into load_fighter_data yet
# (that's R4), so nothing calls it and no golden is touched.
SCHEMA_VERSION = 1


def _select(node: dict, cls) -> dict:
    """Keep only the keys of `node` that are real fields of dataclass `cls`.

    Drops schema-level keys (schema_version, character, provenance) and any
    editor-added extras so the frozen dataclass never sees an unknown kwarg. The
    structured fields (circle/hitboxes/hurtbox/moves/*_size) survive this filter
    and are converted by the callers below.
    """
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in node.items() if k in names}


def _field_status_from_json(value) -> FieldStatus:
    """One serialized value-status -> FieldStatus (#1133). Lenient union (mirrors
    the hurt-circle label form): a bare string ``"PLACEHOLDER"`` -> source-less;
    an object ``{"status": "FOUND", "source": "datamine"}`` -> with a citation."""
    if isinstance(value, dict):
        return FieldStatus(Status(value["status"]), value.get("source"))
    return FieldStatus(Status(value))


def _status_map_from_json(node: dict) -> StatusMap:
    """A serialized ``{field: value-status}`` map -> ``{field: FieldStatus}``. An
    absent/empty map hydrates to ``{}`` (the dataclass default), so unannotated
    data is byte-identical."""
    return {name: _field_status_from_json(v) for name, v in node.items()}


def _hurt_circle_from_json(entry) -> Circle:
    """One serialized hurt circle -> Circle (#1036). Accepts BOTH the old bare
    triple ``[dx, dy, r]`` (label absent -> ``None``) and the labeled entry
    ``{"circle": [dx, dy, r], "label": "A"}`` — the same optional-label leniency
    ``Hitbox.label`` has, so old and new ``<char>.json`` both hydrate."""
    if isinstance(entry, dict):
        return Circle(
            *entry["circle"],
            label=entry.get("label"),
            status=_status_map_from_json(entry.get("status", {})),  # per-value status (#1133)
        )
    return Circle(*entry)


def _velocity_phase_from_json(entry) -> VelocityPhase:
    """One serialized velocity phase -> VelocityPhase (#1133). Lenient union: the
    compact ``[frame, vx, vy]`` triple (no status) or the object form
    ``{"frame":.., "vx":.., "vy":.., "status": {...}}`` that carries a status map."""
    if isinstance(entry, dict):
        kw = {k: entry[k] for k in ("frame", "vx", "vy") if k in entry}
        kw["status"] = _status_map_from_json(entry.get("status", {}))
        return VelocityPhase(**kw)
    return VelocityPhase(*entry)


def _hurtbox_from_json(node: dict) -> Hurtbox:
    return Hurtbox(circles=tuple(_hurt_circle_from_json(e) for e in node["circles"]))


def _hitbox_from_json(node: dict) -> Hitbox:
    kw = _select(node, Hitbox)
    kw["circle"] = Circle(*node["circle"], status=_status_map_from_json(node.get("circle_status", {})))
    if "status" in node:  # per-value status map (#1133)
        kw["status"] = _status_map_from_json(node["status"])
    return Hitbox(**kw)  # __post_init__ validates the window pairing


def _landing_spawn_from_json(node: dict) -> LandingSpawn:
    kw = _select(node, LandingSpawn)
    kw["hitboxes"] = tuple(_hitbox_from_json(h) for h in node["hitboxes"])
    if "status" in node:  # per-value status map (#1133)
        kw["status"] = _status_map_from_json(node["status"])
    return LandingSpawn(**kw)  # __post_init__ validates lifetime/speed/lag


def _move_from_json(node: dict) -> MoveData:
    kw = _select(node, MoveData)
    kw["hitboxes"] = tuple(_hitbox_from_json(h) for h in node["hitboxes"])
    if node.get("hurtbox") is not None:  # optional per-move override (#831)
        kw["hurtbox"] = _hurtbox_from_json(node["hurtbox"])
    if node.get("velocity_phases"):  # scripted mid-move velocity SETs (#973)
        kw["velocity_phases"] = tuple(_velocity_phase_from_json(vp) for vp in node["velocity_phases"])
    if node.get("landing_spawn") is not None:  # touchdown shockwave (#974)
        kw["landing_spawn"] = _landing_spawn_from_json(node["landing_spawn"])
    if "status" in node:  # per-value MOVE-level status map (#1133)
        kw["status"] = _status_map_from_json(node["status"])
    return MoveData(**kw)  # __post_init__ validates windows + phases vs duration


def _fighter_from_json(doc: dict) -> FighterData:
    """Hydrate a full FighterData from a parsed thin-mirror document."""
    version = doc.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version {version!r} (expected {SCHEMA_VERSION})")
    kw = _select(doc, FighterData)
    kw["hurtbox"] = _hurtbox_from_json(doc["hurtbox"])
    kw["moves"] = {key: _move_from_json(m) for key, m in doc["moves"].items()}
    for key in ("crouch_hurtbox", "prone_hurtbox"):
        if doc.get(key) is not None:
            kw[key] = _hurtbox_from_json(doc[key])
    for key in ("stand_size", "crouch_size", "prone_size"):
        if doc.get(key) is not None:
            kw[key] = tuple(doc[key])
    if "status" in doc:  # per-value fighter-LEVEL status map (#1216)
        kw["status"] = _status_map_from_json(doc["status"])
    return FighterData(**kw)


# ---------------------------------------------------------------------------
# JSON dump (#847, R5 of the #792 editor) — FighterData -> minimal dict
# ---------------------------------------------------------------------------
# The mechanical inverse of _fighter_from_json (design §2.4 + §1). Two schema
# rules keep the output thin and golden-safe:
#   1. Omit == default. Any field equal to its dataclass default is dropped, via
#      dataclasses.fields() + a default comparison — so the dump reads the SAME
#      single default table the hydrate does and the two cannot drift.
#   2. Inline circles. Every Circle serializes to [dx, dy, r]; everything else
#      keeps its dataclass field name.
# Structured fields (circle/hitboxes/hurtbox/moves/*_size/*_hurtbox) are walked
# explicitly, mirroring the hydrate; the plain scalar tail of each dataclass is
# emitted by _nondefault_scalars. `provenance` is never written (migrated data
# has no per-frame trace — §2.4; the editor seeds it on first open).
#
# R5 ships this function + its round-trip test ONLY and commits ZERO live
# <character>.json (ruling on #847): no real fighter is flipped onto the R4 JSON
# reader, so the dump is inert and goldens cannot move. The per-fighter flip is
# deferred to follow-up DEV tickets, filed one-at-a-time once the dumper is proven.

# Structural fields handled explicitly per dataclass (excluded from the generic
# scalar sweep). Circles go inline; hurtboxes/moves/sizes get their own walk.
_HITBOX_STRUCTURAL = frozenset({"circle", "status"})
_LANDING_SPAWN_STRUCTURAL = frozenset({"hitboxes", "status"})
_MOVE_STRUCTURAL = frozenset({"hitboxes", "hurtbox", "velocity_phases", "landing_spawn", "status"})
_FIGHTER_STRUCTURAL = frozenset(
    {"hurtbox", "moves", "stand_size", "crouch_size", "crouch_hurtbox", "prone_size", "prone_hurtbox", "status"}
)


# Sentinel: field has no default (required) -> always emitted.
_NO_DEFAULT = object()


def _field_default(f):
    """The default value of dataclass field `f`, or _NO_DEFAULT if it is required."""
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:  # type: ignore[misc]
        return f.default_factory()
    return _NO_DEFAULT


def _nondefault_scalars(obj, structural: frozenset) -> dict:
    """Emit each non-structural field whose value differs from its default.

    Required fields (no default) are always emitted. This is the "omit ==
    default" rule (§1): it drives off dataclasses.fields(), the same default
    table _fighter_from_json relies on, so serialize and hydrate cannot drift.
    """
    out = {}
    for f in fields(obj):
        if f.name in structural:
            continue
        value = getattr(obj, f.name)
        default = _field_default(f)
        if default is _NO_DEFAULT or value != default:
            out[f.name] = value
    return out


def _field_status_to_json(fs: FieldStatus):
    """One FieldStatus -> its serialized form (#1133). Source-less -> the bare
    status string; with a citation -> ``{"status": .., "source": ..}`` — the same
    lenient union ``_field_status_from_json`` reads back."""
    if fs.source is None:
        return fs.status.value
    return {"status": fs.status.value, "source": fs.source}


def _status_map_to_json(m: StatusMap) -> dict:
    """A ``{field: FieldStatus}`` map -> its serialized ``{field: value-status}``."""
    return {name: _field_status_to_json(fs) for name, fs in m.items()}


def _circle_to_json(c: Circle) -> list:
    return [c.dx, c.dy, c.r]


def _hurt_circle_to_json(c: Circle):
    """One hurt circle -> its serialized form (#1036, #1133). Unlabeled + no status
    -> the old bare triple ``[dx, dy, r]`` (so existing files don't churn);
    otherwise a dict entry ``{"circle": [dx, dy, r], "label": "A", "status": {...}}``
    (not a parallel list, which would reintroduce the index-coupling #1024 fixed).
    Mirrors the omit-when-empty leniency of ``Hitbox.label``."""
    if c.label is None and not c.status:
        return _circle_to_json(c)
    out: dict = {"circle": _circle_to_json(c)}
    if c.label is not None:
        out["label"] = c.label
    if c.status:  # per-value status (#1133)
        out["status"] = _status_map_to_json(c.status)
    return out


def _hurtbox_to_json(h: Hurtbox) -> dict:
    return {"circles": [_hurt_circle_to_json(c) for c in h.circles]}


def _hitbox_to_json(hb: Hitbox) -> dict:
    out = _nondefault_scalars(hb, _HITBOX_STRUCTURAL)
    out["circle"] = _circle_to_json(hb.circle)
    if hb.circle.status:  # the box's radius/offset status (#1133), sibling of `circle`
        out["circle_status"] = _status_map_to_json(hb.circle.status)
    if hb.status:  # the box's scalar status (#1133)
        out["status"] = _status_map_to_json(hb.status)
    return out


def _velocity_phase_to_json(vp: VelocityPhase):
    """One VelocityPhase -> its serialized form (#973, #1133). No status -> the
    compact ``[frame, vx, vy]`` triple (byte-identical); with status -> the object
    form so the map can ride along."""
    if not vp.status:
        return [vp.frame, vp.vx, vp.vy]
    return {"frame": vp.frame, "vx": vp.vx, "vy": vp.vy, "status": _status_map_to_json(vp.status)}


def _landing_spawn_to_json(ls: LandingSpawn) -> dict:
    out = _nondefault_scalars(ls, _LANDING_SPAWN_STRUCTURAL)
    out["hitboxes"] = [_hitbox_to_json(hb) for hb in ls.hitboxes]
    if ls.status:  # per-value status (#1133)
        out["status"] = _status_map_to_json(ls.status)
    return out


def _move_to_json(m: MoveData) -> dict:
    out = _nondefault_scalars(m, _MOVE_STRUCTURAL)
    out["hitboxes"] = [_hitbox_to_json(hb) for hb in m.hitboxes]
    if m.hurtbox is not None:  # optional per-move override (#831)
        out["hurtbox"] = _hurtbox_to_json(m.hurtbox)
    if m.velocity_phases:  # scripted mid-move velocity SETs (#973); omit when empty
        out["velocity_phases"] = [_velocity_phase_to_json(vp) for vp in m.velocity_phases]
    if m.landing_spawn is not None:  # touchdown shockwave (#974); omit when absent
        out["landing_spawn"] = _landing_spawn_to_json(m.landing_spawn)
    if m.status:  # per-value MOVE-level status (#1133); omit when empty
        out["status"] = _status_map_to_json(m.status)
    return out


def fighter_to_json(fd: FighterData, character: str | None = None) -> dict:
    """Serialize a FighterData to the minimal thin-mirror dict (inverse hydrate).

    Pass `character` to emit the schema's `character` key (the file stem); it is
    metadata the hydrate ignores, so the round-trip does not depend on it. Absent
    -> the key is omitted. `schema_version` is always emitted (the hydrate asserts
    it). The result is JSON-serializable (no tuples/dataclasses leak).
    """
    out: dict = {"schema_version": SCHEMA_VERSION}
    if character is not None:
        out["character"] = character
    out.update(_nondefault_scalars(fd, _FIGHTER_STRUCTURAL))
    out["hurtbox"] = _hurtbox_to_json(fd.hurtbox)
    out["moves"] = {key: _move_to_json(m) for key, m in fd.moves.items()}
    for key in ("crouch_hurtbox", "prone_hurtbox"):
        hb = getattr(fd, key)
        if hb is not None:
            out[key] = _hurtbox_to_json(hb)
    for key in ("stand_size", "crouch_size", "prone_size"):
        size = getattr(fd, key)
        if size is not None:
            out[key] = list(size)
    if fd.status:  # per-value fighter-LEVEL status map (#1216); omit when empty
        out["status"] = _status_map_to_json(fd.status)
    return out


def with_dense_hit_labels(fd: FighterData) -> FighterData:
    """Return a copy of `fd` with every move's hit boxes labeled dense `A, B, C…`
    in tuple order — the canonical baseline labeling for *authored* fighter data
    (#1041).

    Authored (pristine) moves always carry a full, hole-free letter run in box
    order, so deriving it here and baking it into the shipped `Hitbox.label`
    gives the editor real letters to adopt (#1030) instead of none. It is NOT the
    editor auto-assigning at load — that stays banned; this is the one-time
    migration baseline applied when the JSON was generated, so it ships stored
    labels a human can review and a validator can check. Idempotent (dense in →
    dense out).

    Hit boxes only — hurt-box labels need the `Circle`/`Hurtbox` schema change in
    #1036. Assumes ≤26 hit boxes per move (max shipped is 8); a 27th would run
    past `Z`.
    """
    new_moves = {
        key: replace(
            move,
            hitboxes=tuple(replace(hb, label=chr(ord("A") + i)) for i, hb in enumerate(move.hitboxes)),
        )
        for key, move in fd.moves.items()
    }
    return replace(fd, moves=new_moves)


# Per-fighter JSON data directory (#844, R4 of the #792 editor; design §1). The
# editor writes one thin-mirror file per fighter here; load_fighter_data prefers
# it when present. The four archetypes + default ship JSON here, and since #1141
# it is the sole source (the Python oracles are retired). Tests monkeypatch this
# constant to exercise the branch without touching the repo.
CHARACTER_DATA_DIR = Path(__file__).parent.parent / "characters" / "data"

# Files in CHARACTER_DATA_DIR that are NOT per-fighter data, so fighter-JSON
# discovery must skip them. cards.json is the ROUNDS card catalog (ADR-0020 §1):
# co-located with fighter data by design, but hydrated by loadout/cards.py, not by
# this seam. Fighter-file consumers glob via fighter_json_paths(), never a bare
# CHARACTER_DATA_DIR.glob("*.json").
NON_FIGHTER_DATA_FILES = frozenset({"cards.json"})


def fighter_json_paths() -> list[Path]:
    """Sorted per-fighter ``<character>.json`` paths in CHARACTER_DATA_DIR.

    Excludes non-fighter data files (NON_FIGHTER_DATA_FILES, e.g. the ROUNDS card
    catalog) so a co-located catalog file is never mistaken for a fighter mirror.
    """
    return sorted(p for p in CHARACTER_DATA_DIR.glob("*.json") if p.name not in NON_FIGHTER_DATA_FILES)


# Keys that resolve to the default cat rather than a distinct archetype: the sim
# seats "P1"/"P2" (sim/runner.py, game.py), the migration key "default", and the
# "testcat" minimal fixture (#591). Separate from the archetypes so a consumer can
# tell an intended-default key from a real character key (#894).
_DEFAULT_KEYS = frozenset({"default", "P1", "P2", "testcat"})


def known_character_keys() -> frozenset[str]:
    """The character keys `load_fighter_data` resolves to a fighter.

    The playable archetypes (`ARCHETYPE_ROSTER`) plus the intended-default seats
    (`_DEFAULT_KEYS`). Consumers use this to distinguish a real character key from
    a display label — e.g. `Player.__init__` treats a `char_name` outside this set
    as a label, not a key (#894). Kept a function (lazy `ARCHETYPE_ROSTER` import)
    to avoid a module-load cycle, mirroring the lazy import inside
    `load_fighter_data`.
    """
    from pycats.characters.roster import ARCHETYPE_ROSTER

    return frozenset(ARCHETYPE_ROSTER) | _DEFAULT_KEYS


def _default_fighter() -> FighterData:
    """Hydrate the default cat from its shipped JSON.

    Since #881 default.json is the sole runtime source; #1141 retired the Python
    DEFAULT_FIGHTER_DATA oracle entirely, so there is no literal to fall back to.
    A missing or malformed default.json is therefore a hard, loud failure by
    design (no quiet floor).
    """
    return _fighter_from_json(json.loads((CHARACTER_DATA_DIR / "default.json").read_text()))


def load_fighter_data(character: str) -> FighterData:
    """Return FighterData for the named character.

    Resolution order (#844, R4): a `CHARACTER_DATA_DIR/<character>.json` thin
    mirror is preferred when present (hydrated via `_fighter_from_json`, #809
    §2.1). The four archetypes and the default cat all ship JSON, so they resolve
    through that branch; #1141 retired the Python archetype arms (and the oracle
    modules) entirely, so the JSON mirror is the only source.

    The intended-default keys (`_DEFAULT_KEYS` = `{"default", "P1", "P2",
    "testcat"}`) resolve to the default cat loaded from default.json (a fresh
    hydrated instance). Every OTHER key is a programming
    error and raises `UnknownCharacter` (#887/#881). Production never reaches the
    raise: the #672 domain layer folds an unknown/None selection into the
    `testcat` placeholder before this seam, and `Player.__init__` resolves a
    non-key `char_name` to `"testcat"` (#894), so the raise is defense-in-depth
    for a programming error and cannot move goldens.

    Args:
        character: an archetype key (e.g. "nalio"), an intended-default key
            (`"default"`, `"P1"`, `"P2"`, `"testcat"`), or an unknown key (raises).

    Returns:
        FighterData instance (frozen, deterministic, no RNG).

    Raises:
        UnknownCharacter: the key is neither an archetype nor an intended-default
            key (a typo / programming error).
    """
    # JSON branch (#844): a per-fighter thin-mirror file wins over the Python
    # switch. The four archetypes + default ship JSON, so this fires for them;
    # algorithm-free hydrate (§2.1), provenance left untouched.
    path = CHARACTER_DATA_DIR / f"{character}.json"
    if path.exists():
        return _fighter_from_json(json.loads(path.read_text()))

    # The four archetypes ship JSON, so the branch above returns for them. Their
    # Python-literal fallback arms were retired with the oracles (#1141, #1078
    # Q1/G1): the JSON mirror is the sole source, so a missing <archetype>.json is
    # now a loud UnknownCharacter below rather than a quiet Python floor.
    if character in _DEFAULT_KEYS:
        # Intended-default seats ("default"/"P1"/"P2"/"testcat"). "default" also
        # resolves via the JSON branch above once default.json ships; "P1"/"P2"
        # (sim seats) and "testcat" (#591 minimal fixture) have no JSON of their
        # own, so they hydrate the default cat here — a fresh instance, never the
        # Python literal.
        return _default_fighter()

    # Unknown key → loud programming-error raise (#887/#881). The valid set is
    # derived at raise time (roster + allow-list), so it self-updates as cats are
    # added.
    from .errors import UnknownCharacter

    raise UnknownCharacter(character, sorted(known_character_keys()))


# ---------------------------------------------------------------------------
# Getup-attack (#225 / #146 slice 2): a generic wake-up attack out of `prone`.
# Started directly on the move clock from the getup transition (player.update),
# not via the move-selection seam — so the existing Attack/clank/multi-hit
# plumbing is reused. One low front hitbox for v1; a back hitbox (PM hits both
# sides) is a documented refinement. Frames/box are ⚠ playtest starting points.
#
# Provenance (#1135): every value here is an unsourced playtest starting point that
# IS seeking canon (PM has a real getup attack) — a grounding DEBT, so GUESS at
# per-VALUE granularity via the #1133 status seam. GETUP_ATTACK is a standalone
# module move (not part of any FighterData / <char>.json), so the maps annotate it in
# place; the round-trip test (test_fighter_to_json) carries the maps through unchanged.
# ---------------------------------------------------------------------------
_GETUP_GUESS = FieldStatus(Status.GUESS)  # shared frozen tag: every GETUP_ATTACK value is GUESS
GETUP_ATTACK = MoveData(
    name="getup attack",
    in_air=False,
    startup=4,
    active=3,
    recovery=14,
    hitboxes=(
        Hitbox(
            circle=Circle(
                dx=28,
                dy=42,
                r=24,
                status={"dx": _GETUP_GUESS, "dy": _GETUP_GUESS, "r": _GETUP_GUESS},
            ),
            damage=8.0,
            angle=70,
            base_knockback=40.0,
            knockback_growth=70.0,
            status={
                "damage": _GETUP_GUESS,
                "angle": _GETUP_GUESS,
                "base_knockback": _GETUP_GUESS,
                "knockback_growth": _GETUP_GUESS,
            },
        ),
    ),
    status={"startup": _GETUP_GUESS, "active": _GETUP_GUESS, "recovery": _GETUP_GUESS},
)
