"""
pycats/loadout/modifiers.py

Purpose: the ROUNDS v1 modifier apply-layer — turn drafted cards into a patched
FighterData. This is the keystone the draft and every downstream slice build on.

Spec: docs/adr/0014-rounds-v1-modifier-apply-layer.md (ADR-0014). Seam shapes:
docs/adr/0013-rounds-v1-fighter-seam-modifier-contract.md (ADR-0013). Card model:
docs/adr/0020-rounds-v1-card-modifier-catalog.md (ADR-0020) / loadout/cards.py.

Contents:
- Modifier            — a bare (seam, op, value) record (ADR-0014 §2: no provenance).
- card_to_modifiers   — one Modifier per card delta (pure derivation).
- apply(baseline, cards) -> FighterData — functional patch; never mutates baseline.

Design notes:
- FUNCTIONAL (ADR-0014 §3): apply builds a NEW FighterData via dataclasses.replace
  (and nested replace over moves / hitboxes / circles); it never mutates `baseline`.
  That invariant is what makes card deletion reversible — recompute from the pristine
  baseline (model C1) and the result is exact regardless of prior apply() calls.
- No RNG (ADR-0014 / #1099): the draft owns the seed; apply is deterministic.
- Multi-modifier combine = compound factors, flats after (owner ruling 2026-08-04):
      effective(seam) = round_if_int( base × Π(1 + pct_i/100) + Σ add_n_j )
  then apply the ADR-0013 floor. Each mult_pct is its own factor (a product, NOT
  summed percents); all add_n sum and land after the scaled base. Order-independent
  within each op class.
- Int-contracted seams (velocities, weight, reach, body geometry, max_jumps) round;
  gravity / damage / knockback are genuine floats and are NOT rounded (ADR-0013).
- Stocks (ADR-0013 seam 10, Phoenix) is OUT of this layer: `fighter.lives` is a
  match-level value, not a FighterData field, so a stocks delta is simply not
  consumed here — it needs its own match-setup hook (a follow-up DEV). A card that
  carries only a stocks delta therefore leaves the FighterData unchanged.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from ..combat.data import FighterData
    from .cards import Card


class Modifier(NamedTuple):
    """One fighter-seam patch: which `seam`, which `op`, by how much (`value`).

    A bare record — ADR-0014 §2 keeps no provenance sidecar; a drafted card's
    "why" is the player's pick + the catalog id, not a canon citation.
    """

    seam: str
    op: str
    value: float


def card_to_modifiers(card: Card) -> list[Modifier]:
    """Derive one Modifier per card delta (pure; order preserved)."""
    return [Modifier(d["seam"], d["op"], d["value"]) for d in card.deltas]


# ---------------------------------------------------------------------------
# Combine — compound factors, flats after (owner ruling 2026-08-04)
# ---------------------------------------------------------------------------
def _combine(mods: list[Modifier]) -> tuple[float, float]:
    """Fold one seam's modifiers into (pct_product, add_sum).

    `mult_pct` values compound as independent factors Π(1 + v/100); `add_n` values
    sum. effective = base × pct_product + add_sum. Order-independent within each op.
    """
    product = 1.0
    add = 0.0
    for m in mods:
        if m.op == "mult_pct":
            product *= 1 + m.value / 100
        else:  # add_n
            add += m.value
    return product, add


def _coerce(raw: float, *, rounds: bool, floor: int | None) -> float | int:
    """Apply the seam's int-contract (round) and ADR-0013 floor, in that order."""
    value = round(raw) if rounds else raw
    if floor is not None and value < floor:
        value = floor
    return value


def _effective(base: float, mods: list[Modifier], *, rounds: bool, floor: int | None) -> float | int:
    """The combine rule end-to-end: base × Π(pct) + Σ(add_n), then coerce."""
    product, add = _combine(mods)
    return _coerce(base * product + add, rounds=rounds, floor=floor)


# Top-level FighterData scalar seams -> (field, rounds, floor). ADR-0013:
# velocities & weight are int-contracted (round); gravity is the sole genuine float
# (no round). weight and max_jumps floor at 1; the others have no floor. jump_vel
# is negative, so it has no lower floor (a stronger jump is a larger magnitude).
#
# Walk/dash/run (#1209, ADR-0011): the move_speed/dash_speed/run_speed CARD seams now
# target the raw-unit fields walk/dash/run (move_speed/etc. are read-only derived-px
# properties — nothing to replace()). rounds=False: the scaled UNIT stays a float; the
# integer px contract is honored downstream by the u() conversion in the property (a
# fractional walk speed is meaningless — pygame.Rect truncates each frame). All shipped
# speed cards are mult_pct (ratio, unit-agnostic); an additive speed delta would now be
# in unit-space, not px.
_SCALAR_SEAMS: dict[str, tuple[str, bool, int | None]] = {
    "weight": ("weight", True, 1),
    "jump_vel": ("jump_vel", True, None),
    "move_speed": ("walk", False, None),
    "dash_speed": ("dash", False, None),
    "run_speed": ("run", False, None),
    "max_fall_speed": ("max_fall_speed", True, None),
    "gravity": ("gravity", False, None),
    "max_jumps": ("max_jumps", True, 1),
    # ROUNDS Leech knobs (#1208, ADR-0019/ADR-0020). lifesteal_fraction & regen_rate
    # are genuine floats (a fraction / a percent) — no round, like gravity. All three
    # floor at 0: no negative lifesteal or regen in v1. regen_interval is a frame count
    # (int-contracted → round); its floor stays 0 (0 = off), deferring the divide/modulo
    # guard to DEV 4's over_time.py tick (#1208 /decomplect ruling).
    "lifesteal_fraction": ("lifesteal_fraction", False, 0),
    "regen_rate": ("regen_rate", False, 0),
    "regen_interval": ("regen_interval", True, 0),
}

# Nested per-hitbox scalar seams -> (field, rounds), applied to EVERY hitbox of
# every move. damage / knockback are genuine floats (no round); `reach` is handled
# separately because it lives on the hitbox's Circle (int radius, round).
_HITBOX_SCALAR_SEAMS: dict[str, tuple[str, bool]] = {
    "damage": ("damage", False),
    "base_knockback": ("base_knockback", False),
    "knockback_growth": ("knockback_growth", False),
}


def _map_hitboxes(
    fd: FighterData,
    hitbox_edits: list[tuple[str, float, float, bool]],
    reach_pa: tuple[float, float] | None,
) -> FighterData:
    """Return `fd` with the given edits applied to every hitbox across all moves.

    `hitbox_edits` is a list of (field, pct_product, add_sum, rounds) for the
    per-hitbox scalar seams; `reach_pa` is the (product, add) for the reach seam
    (the Circle radius) or None. Both walk the same hitbox tuples so the moves dict
    is rebuilt once.
    """

    def edit(hb):
        changes: dict[str, object] = {}
        for field, product, add, rounds in hitbox_edits:
            changes[field] = _coerce(getattr(hb, field) * product + add, rounds=rounds, floor=None)
        if reach_pa is not None:
            product, add = reach_pa
            changes["circle"] = replace(hb.circle, r=_coerce(hb.circle.r * product + add, rounds=True, floor=None))
        return replace(hb, **changes) if changes else hb

    new_moves = {key: replace(move, hitboxes=tuple(edit(hb) for hb in move.hitboxes)) for key, move in fd.moves.items()}
    return replace(fd, moves=new_moves)


def _scale_body(fd: FighterData, product: float, add: float) -> FighterData:
    """Scale the fighter body (body_size seam): every hurtbox Circle's geometry
    (dx/dy/r, a uniform scale about the origin) plus `stand_size` if present. Ints,
    rounded. Scoped to stand_size + hurtbox per ADR-0014's acceptance; crouch/prone
    geometry is left to a follow-up."""

    def s(v: int) -> int:
        return _coerce(v * product + add, rounds=True, floor=None)

    new_hurtbox = replace(
        fd.hurtbox,
        circles=tuple(replace(c, dx=s(c.dx), dy=s(c.dy), r=s(c.r)) for c in fd.hurtbox.circles),
    )
    changes: dict[str, object] = {"hurtbox": new_hurtbox}
    if fd.stand_size is not None:
        changes["stand_size"] = (s(fd.stand_size[0]), s(fd.stand_size[1]))
    return replace(fd, **changes)


def apply(baseline: FighterData, cards: Iterable[Card]) -> FighterData:
    """Return a NEW FighterData with every card's modifiers applied to `baseline`.

    Functional (ADR-0014 §3): `baseline` is never mutated. `apply(baseline, ())`
    returns `baseline` unchanged (the inert path → byte-identical to today), so a
    default Selection stays golden-safe.
    """
    by_seam: dict[str, list[Modifier]] = defaultdict(list)
    for card in cards:
        for m in card_to_modifiers(card):
            by_seam[m.seam].append(m)
    if not by_seam:
        return baseline

    fd = baseline
    changes: dict[str, float | int] = {}
    for seam, (field, rounds, floor) in _SCALAR_SEAMS.items():
        if seam in by_seam:
            changes[field] = _effective(getattr(fd, field), by_seam[seam], rounds=rounds, floor=floor)
    if changes:
        fd = replace(fd, **changes)

    # Nested per-hitbox seams (damage / knockback / reach) — one walk over the moves.
    hitbox_edits: list[tuple[str, float, float, bool]] = []
    for seam, (field, rounds) in _HITBOX_SCALAR_SEAMS.items():
        if seam in by_seam:
            product, add = _combine(by_seam[seam])
            hitbox_edits.append((field, product, add, rounds))
    reach_pa = _combine(by_seam["reach"]) if "reach" in by_seam else None
    if hitbox_edits or reach_pa is not None:
        fd = _map_hitboxes(fd, hitbox_edits, reach_pa)

    # body_size: stand_size + hurtbox geometry.
    if "body_size" in by_seam:
        fd = _scale_body(fd, *_combine(by_seam["body_size"]))
    return fd
