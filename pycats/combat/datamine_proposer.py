"""
pycats/combat/datamine_proposer.py

Purpose: Turn a datamined hitbox table (I.1a's HitboxTable, #1207) into pycats-px
box CANDIDATES a human accepts/tweaks in the editor (I.1b, slice of #1206). A
candidate is a suggestion only — box position is a feel quantity (#782/#310), so
this proposes; it never writes cat data.

Contents:
- RepresentativeFrame — which frame of a MOVING hitbox represents its static Circle
- HitboxCandidate     — one proposed box: id, circle, damage/angle, window, source
- propose(table, strategy) -> list[HitboxCandidate]

Design notes:
- Scale (ADR-0011 / #1210 ruling): world units -> px goes through the named seam
  units.py::u() = round(PX_PER_UNIT * unit), NOT an inline multiply. The GIF
  orthographic `k` #1206's ruling assumed does NOT exist — brawllib renders the
  reference GIFs via a per-subaction perspective auto-fit camera
  (brawllib_rs/src/renderer/camera.rs::new_from_extent), and #120 established
  there is no fixed world->px POSITION scale
  (docs/research/parity-notes-regarding-hurtbox-values.md). So the RADIUS
  conversion is well-grounded — pycats already ships datamined radii through this
  same 5.4 factor (#1124) — but the OFFSET is an APPROXIMATION: u() is a
  playtest-chosen radius factor pressed into service as a position scale
  (#120/#195). That is acceptable because a candidate is only a starting point a
  human nudges in the editor, never a parity claim about the offset.
- Axis mapping (datamine world -> pycats facing-right px): the datamine pos is
  (x=depth, y=vertical up+, z=horizontal) — see DatamineHitBox. pycats Circle
  offsets are screen-space (y grows DOWN). So dx <- u(z), dy <- -u(y); x=depth is
  dropped (pycats is 2-D).
- Moving box (#1210 open choice, DEFERRED to cross-comparison ticket #1217): a
  datamined hitbox moves per frame but a Circle is one static offset. `strategy`
  selects the representative frame; FIRST_ACTIVE is the PROVISIONAL default
  pending #1217 (render each over the reference animation, eyeball the winner) —
  do not read it as the settled choice.
- Frame index: `window` is in the datamine's own 0-based frame-index space, NOT
  the MoveClock 1-indexed coordinate Hitbox.active_start uses. Mapping to a
  MoveClock window is the editor/accept step's job (I.1c), not this slice.
- FOUND/datamine: every candidate value is sourced geometry, so its Circle's
  dx/dy/r carry FieldStatus(FOUND, "datamine") (Status.FOUND is how MEASURED
  geometry is tagged, #1129) and the candidate's `source` is "datamine". The
  position-scale approximation lives in PX_PER_UNIT itself (tracked #195/#120),
  not in whether the coordinate is sourced.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .data import Circle, FieldStatus, Status
from .datamine_hitboxes import DatamineHitBox, HitboxTable
from .units import u

# Shared frozen provenance tag: every proposed geometry value is sourced datamine.
_DATAMINE = FieldStatus(Status.FOUND, "datamine")


class RepresentativeFrame(Enum):
    """Which frame of a moving hitbox represents its single static Circle (#1210).

    A datamined hitbox moves per frame; a pycats Circle is one static offset, so a
    representative frame must be chosen. Which one is best is an OPEN question,
    deferred to cross-comparison ticket #1217 (render each and eyeball against
    the reference animation) — FIRST_ACTIVE is only the provisional default here.

    FIRST_ACTIVE   — the first frame the box is live (the moment it connects).
    MID_WINDOW     — the middle active frame (index len // 2 of the active frames;
                     for an even count this rounds toward the later frame).
    WINDOW_AVERAGE — the centroid position averaged across all active frames.
    """

    FIRST_ACTIVE = "first_active"
    MID_WINDOW = "mid_window"
    WINDOW_AVERAGE = "window_average"


@dataclass(frozen=True)
class HitboxCandidate:
    """One proposed hitbox in pycats px — a suggestion the editor draws as a ghost.

    Fields:
        hitbox_id — the datamine id this candidate came from.
        circle    — facing-right Circle (dx/dy/r px), every value FOUND/datamine.
        damage    — the datamine Hit damage; None for a grab box.
        angle     — the datamine Hit launch angle; None for a grab box.
        window    — inclusive (start, end) active span in DATAMINE frame-index
                    space (0-based), NOT MoveClock coordinates.
        source    — provenance tag; "datamine" for every candidate this emits.
    """

    hitbox_id: int
    circle: Circle
    damage: float | None
    angle: int | None
    window: tuple[int, int]
    source: str = "datamine"


def _active_boxes(table: HitboxTable, hid: int) -> list[tuple[int, DatamineHitBox]]:
    """(frame_index, box) for every frame `hid` is live, ascending by frame index."""
    out = [(frame.index, box) for frame in table.frames for box in frame.boxes if box.hitbox_id == hid]
    out.sort(key=lambda pair: pair[0])
    return out


def _circle_from_world(z: float, y: float, size: float) -> Circle:
    """World (z=horizontal, y=up+) + radius -> facing-right pycats Circle via u().

    dx <- u(z), dy <- -u(y) (pycats screen-y grows down), r <- u(size). Every value
    is routed through the named units.py::u() seam (ADR-0011) — never an inline
    `* PX_PER_UNIT` / `* 5.4`.
    """
    return Circle(
        dx=u(z),
        dy=-u(y),
        r=u(size),
        status={"dx": _DATAMINE, "dy": _DATAMINE, "r": _DATAMINE},
    )


def propose(
    table: HitboxTable,
    strategy: RepresentativeFrame = RepresentativeFrame.FIRST_ACTIVE,
) -> list[HitboxCandidate]:
    """Propose one HitboxCandidate per distinct hitbox id in `table`, in id order.

    For each distinct `hitbox_id`, gather every frame the box is live on and reduce
    its per-frame motion to a single static Circle by `strategy` (see
    RepresentativeFrame). The Circle's dx/dy/r are the world position/radius scaled
    through units.py::u() (ADR-0011 named seam); damage/angle ride along from the
    datamine (None for a grab box); `window` is the box's inclusive active span in
    the datamine's own 0-based frame-index space.

    Deterministic and pure — given a HitboxTable it returns the same candidates, so
    it unit-tests off #1207's committed fixture with no datamine env.
    """
    candidates: list[HitboxCandidate] = []
    for hid in table.distinct_ids():
        active = _active_boxes(table, hid)
        indices = [idx for idx, _ in active]
        boxes = [box for _, box in active]
        window = (indices[0], indices[-1])

        if strategy is RepresentativeFrame.WINDOW_AVERAGE:
            n = len(boxes)
            z = sum(b.pos[2] for b in boxes) / n
            y = sum(b.pos[1] for b in boxes) / n
            size = sum(b.size for b in boxes) / n
            # damage/angle are move properties (constant across an id's frames), so
            # the averaged-position candidate still carries the first frame's pair.
            meta = boxes[0]
        else:
            if strategy is RepresentativeFrame.MID_WINDOW:
                meta = boxes[len(boxes) // 2]
            else:  # FIRST_ACTIVE (default)
                meta = boxes[0]
            z, y, size = meta.pos[2], meta.pos[1], meta.size

        candidates.append(
            HitboxCandidate(
                hitbox_id=hid,
                circle=_circle_from_world(z, y, size),
                damage=meta.damage,
                angle=meta.angle,
                window=window,
                source="datamine",
            )
        )
    return candidates
