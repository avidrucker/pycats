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
from dataclasses import MISSING, dataclass, fields, replace
from pathlib import Path

# Movement-constant defaults live in config; FighterData uses them as field
# defaults so any data that doesn't specify movement == today's globals (the
# default cat / golden sim is unchanged). #126.
from ..config import DASH_SPEED, GRAVITY, JUMP_VEL, MAX_FALL_SPEED, MAX_JUMPS, MOVE_SPEED

# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Circle:
    """A 2-D circle, offset (dx, dy) from the fighter origin, radius r.

    All values in pixels. Offsets are facing-RIGHT-relative.
    """

    dx: int
    dy: int
    r: int


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

    def __post_init__(self) -> None:
        if self.frame < 1:
            raise ValueError(f"VelocityPhase frame {self.frame} must be >= 1 (post-increment move_frame)")


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
    # released to fire (the smash_charge state). Defaults False, so every existing
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
    # Per-fighter standing body box (#275). None = the global config.PLAYER_SIZE
    # (via owner.SIZE), so the default cat / sim path is unchanged. Symmetric with
    # crouch_size/prone_size; a small archetype (Kirby) sets a shorter box here.
    stand_size: tuple[int, int] | None = None
    crouch_size: tuple[int, int] | None = None
    crouch_hurtbox: Hurtbox | None = None
    prone_size: tuple[int, int] | None = None
    prone_hurtbox: Hurtbox | None = None


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


def _hurtbox_from_json(node: dict) -> Hurtbox:
    return Hurtbox(circles=tuple(Circle(*triple) for triple in node["circles"]))


def _hitbox_from_json(node: dict) -> Hitbox:
    kw = _select(node, Hitbox)
    kw["circle"] = Circle(*node["circle"])
    return Hitbox(**kw)  # __post_init__ validates the window pairing


def _move_from_json(node: dict) -> MoveData:
    kw = _select(node, MoveData)
    kw["hitboxes"] = tuple(_hitbox_from_json(h) for h in node["hitboxes"])
    if node.get("hurtbox") is not None:  # optional per-move override (#831)
        kw["hurtbox"] = _hurtbox_from_json(node["hurtbox"])
    if node.get("velocity_phases"):  # scripted mid-move velocity SETs (#973)
        kw["velocity_phases"] = tuple(VelocityPhase(*triple) for triple in node["velocity_phases"])
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
_HITBOX_STRUCTURAL = frozenset({"circle"})
_MOVE_STRUCTURAL = frozenset({"hitboxes", "hurtbox", "velocity_phases"})
_FIGHTER_STRUCTURAL = frozenset(
    {"hurtbox", "moves", "stand_size", "crouch_size", "crouch_hurtbox", "prone_size", "prone_hurtbox"}
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


def _circle_to_json(c: Circle) -> list:
    return [c.dx, c.dy, c.r]


def _hurtbox_to_json(h: Hurtbox) -> dict:
    return {"circles": [_circle_to_json(c) for c in h.circles]}


def _hitbox_to_json(hb: Hitbox) -> dict:
    out = _nondefault_scalars(hb, _HITBOX_STRUCTURAL)
    out["circle"] = _circle_to_json(hb.circle)
    return out


def _move_to_json(m: MoveData) -> dict:
    out = _nondefault_scalars(m, _MOVE_STRUCTURAL)
    out["hitboxes"] = [_hitbox_to_json(hb) for hb in m.hitboxes]
    if m.hurtbox is not None:  # optional per-move override (#831)
        out["hurtbox"] = _hurtbox_to_json(m.hurtbox)
    if m.velocity_phases:  # scripted mid-move velocity SETs (#973); omit when empty
        out["velocity_phases"] = [[vp.frame, vp.vx, vp.vy] for vp in m.velocity_phases]
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
    return out


def with_dense_hit_labels(fd: FighterData) -> FighterData:
    """Return a copy of `fd` with every move's hit boxes labeled dense `A, B, C…`
    in tuple order — the canonical baseline labeling for *authored* fighter data
    (#1041).

    Authored (pristine) moves always carry a full, hole-free letter run in box
    order, so deriving it here and baking it into the shipped `Hitbox.label`
    gives the editor real letters to adopt (#1030) instead of none. It is NOT the
    editor auto-assigning at load — that stays banned; this is the one-time
    migration baseline the oracles apply so the JSON ships stored labels a human
    can review and a validator can check. Idempotent (dense in → dense out).

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
# it when present. NO <character>.json ships today, so the branch never fires for
# a real character and the Python switch below is authoritative (golden-safe).
# The migration dump that populates this dir is R5 (#792). Tests monkeypatch this
# constant to exercise the branch without touching the repo.
CHARACTER_DATA_DIR = Path(__file__).parent.parent / "characters" / "data"


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
    """Hydrate the default cat from its shipped JSON — never the Python literal.

    Since #881 default.json is the sole runtime source: the Python
    DEFAULT_FIGHTER_DATA survives only as gnok/narz's construction base and the
    R8 drift-guard oracle (#877), never a runtime path. A missing or malformed
    default.json is therefore a hard, loud failure by design (no quiet floor).
    """
    return _fighter_from_json(json.loads((CHARACTER_DATA_DIR / "default.json").read_text()))


def load_fighter_data(character: str) -> FighterData:
    """Return FighterData for the named character.

    Resolution order (#844, R4): a `CHARACTER_DATA_DIR/<character>.json` thin
    mirror is preferred when present (hydrated via `_fighter_from_json`, #809
    §2.1). The four archetypes and the default cat all ship JSON, so they resolve
    through that branch; the Python archetype arms below are dead (kept as the R8
    oracles + gnok/narz's construction base — O1 "demote, don't delete", #881).

    The intended-default keys (`_DEFAULT_KEYS` = `{"default", "P1", "P2",
    "testcat"}`) resolve to the default cat loaded from default.json (a fresh
    hydrated instance, never the Python literal). Every OTHER key is a programming
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

    # Dead archetype arms (O1, #881): each archetype ships JSON, so the branch
    # above already returned. Kept because the Python literals remain the R8
    # drift-guard oracles; deleting them is a deferred follow-up.
    if character == "nalio":
        from pycats.characters.nalio_cat import NALIO_FIGHTER_DATA

        return NALIO_FIGHTER_DATA
    if character == "birky":
        from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA

        return BIRKY_FIGHTER_DATA
    if character == "narz":
        from pycats.characters.narz_cat import NARZ_FIGHTER_DATA

        return NARZ_FIGHTER_DATA
    if character == "gnok":
        from pycats.characters.gnok_cat import GNOK_FIGHTER_DATA

        return GNOK_FIGHTER_DATA

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
# ---------------------------------------------------------------------------
GETUP_ATTACK = MoveData(
    name="getup attack",
    in_air=False,
    startup=4,
    active=3,
    recovery=14,
    hitboxes=(
        Hitbox(circle=Circle(dx=28, dy=42, r=24), damage=8.0, angle=70, base_knockback=40.0, knockback_growth=70.0),
    ),
)
