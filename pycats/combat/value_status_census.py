"""Authored-value census (#1151) over the two value-status loci.

A pure, headless reader that counts value status across BOTH places status lives,
returning per-area buckets. It **reads** both registries; it does not merge them
(ratified #1125 Q1 — composition, not a merged store). The counts feed:

  1. a human table (``python -m pycats.combat.value_status_census`` / ``make census``);
  2. the ratchet regression (``tests/test_authored_value_ratchet.py``), which reds
     when the authored + undeclared count grows above ``tests/authored_value_baseline.json``.

The two loci (design doc ``docs/research/authored-value-ratchet-findings.md`` §2):

  * ``combat/provenance.py`` → ``TUNING_PROVENANCE`` — config/physics **scalars**;
    ``status`` is a plain string ∈ {FOUND, GUESS, TUNED, DIVERGENCE}. Area key
    ``"physics_config"``. Its keyset is drift-guarded to equal the curated constant
    set (``test_tuning_provenance.py``), so every in-scope scalar carries a status —
    this locus has **no undeclared** by construction.
  * the #1133 seam (``combat/data.py``) → ``status: StatusMap`` on ``Circle`` /
    ``Hitbox`` / ``MoveData`` / ``VelocityPhase`` / ``LandingSpawn``, hydrated from
    ``characters/data/*.json``. Per-fighter **move data**. Area key ``"fighter:<stem>"``.
    Adds ``PLACEHOLDER`` to the vocabulary, and — unlike the config side — most
    authored values carry **no** status yet, so ``undeclared`` is the crux (§5).

Status → bucket (design §2):

  * ``authored``  = GUESS + PLACEHOLDER (sub-tallied; the two debts are different —
                    a GUESS is a real number to source, a PLACEHOLDER a hole to fill).
  * ``sourced``   = FOUND.
  * ``decided``   = TUNED + DIVERGENCE.
  * ``undeclared``= authored value-slots that carry no status entry (§5, ratified
                    option b). This needs a **denominator**: how many authored value
                    slots a fighter *has*.

The denominator — what a "value slot" is (§5, the one piece of new machinery):
a value slot is one **authored scalar field** on one of the five status-carrying
dataclasses whose value is **present** — i.e. the field is required, or its value
differs from its dataclass default (the same "omit == default" rule the serializer
uses, ``combat.data._nondefault_scalars``). Structural fields (nested objects, the
status map itself), identity/display fields (``name``/``label``), behavioural flags
(``in_air``/``chargeable``/…), and tag fields (``set_id``) are **not** value slots —
they are not authored quantities a sourcing pass would resolve. The per-class
partition lives in ``VALUE_FIELDS`` / ``NON_VALUE_FIELDS`` below and is drift-guarded
(``test_authored_value_ratchet.test_field_partition_covers_every_field``) so adding
a field to a dataclass without classifying it reds the suite.

The ratchet gates the ``authored`` bucket (guess + placeholder) and the
``undeclared`` bucket **independently** per area (design §6 Q3): each may only fall,
never rise, without a deliberate baseline re-bless. ``sourced`` and ``decided`` are
reported, not gated.
"""

from __future__ import annotations

from dataclasses import MISSING, fields

from .data import (
    Circle,
    FighterData,
    Hitbox,
    Hurtbox,
    LandingSpawn,
    MoveData,
    VelocityPhase,
    fighter_json_paths,
    load_fighter_data,
)
from .provenance import TUNING_PROVENANCE

# ---------------------------------------------------------------------------
# Value-slot classification (the undeclared denominator)
# ---------------------------------------------------------------------------
# Per status-carrying dataclass, the field names that are authored VALUE slots.
# A value slot is a numeric authored quantity eligible for a status (and therefore
# for the sourcing pass). NON_VALUE_FIELDS is the complement — structural (nested
# objects + the `status` map), identity/display (name/label), flags (bools), and
# tags (set_id). The two sets partition every field of each class; the partition is
# asserted in the ratchet test so a new dataclass field must be classified here.
VALUE_FIELDS: dict[type, frozenset[str]] = {
    Circle: frozenset({"dx", "dy", "r"}),
    Hitbox: frozenset(
        {"damage", "angle", "base_knockback", "knockback_growth", "active_start", "active_end", "set_knockback"}
    ),
    VelocityPhase: frozenset({"frame", "vx", "vy"}),
    LandingSpawn: frozenset({"speed", "lifetime", "landing_lag", "gravity"}),
    MoveData: frozenset(
        {
            "startup",
            "active",
            "recovery",
            "rehit_rate",
            "projectile_speed",
            "projectile_lifetime",
            "recovery_vy",
            "recovery_vx",
        }
    ),
}

NON_VALUE_FIELDS: dict[type, frozenset[str]] = {
    Circle: frozenset({"label", "status"}),
    Hitbox: frozenset({"circle", "set_id", "label", "status"}),
    VelocityPhase: frozenset({"status"}),
    LandingSpawn: frozenset({"hitboxes", "both_directions", "status"}),
    MoveData: frozenset(
        {
            "name",
            "in_air",
            "hitboxes",
            "chargeable",
            "grants_recovery",
            "velocity_phases",
            "hurtbox",
            "landing_spawn",
            "is_counter",  # #1199: behavioural flag (counter-detect stance), not a value slot
            "counter_riposte_key",  # #1199: sibling move key for the riposte, not a value slot
            "status",
        }
    ),
}

# The five status-carrying dataclasses, in a stable order.
STATUS_CARRIERS: tuple[type, ...] = (Circle, Hitbox, VelocityPhase, LandingSpawn, MoveData)


def _field_default(cls: type, name: str):
    """The default value of dataclass field `name` on `cls`, or MISSING if required."""
    for f in fields(cls):
        if f.name == name:
            if f.default is not MISSING:
                return f.default
            if f.default_factory is not MISSING:  # type: ignore[misc]
                return f.default_factory()
            return MISSING
    raise KeyError(name)  # pragma: no cover — name is always a real field


def _is_present(instance, name: str) -> bool:
    """True when field `name` carries an authored value on `instance`.

    Required fields (no default) are always present; an optional field is present
    only when its value differs from the dataclass default — the same "omit ==
    default" rule the JSON serializer uses (``combat.data._nondefault_scalars``),
    so the denominator equals the count of authored scalars in the fighter's JSON.
    """
    default = _field_default(type(instance), name)
    if default is MISSING:
        return True
    return getattr(instance, name) != default


# ---------------------------------------------------------------------------
# Bucket accumulator
# ---------------------------------------------------------------------------
def _empty_bucket() -> dict:
    return {"authored": {"guess": 0, "placeholder": 0}, "sourced": 0, "decided": 0, "undeclared": 0}


# Status token (enum value or provenance string) -> where it lands in a bucket.
_SOURCED = frozenset({"FOUND"})
_DECIDED = frozenset({"TUNED", "DIVERGENCE"})


def _tally_status(bucket: dict, status_value: str) -> None:
    """Fold one declared status token into `bucket` (does NOT touch undeclared)."""
    if status_value == "GUESS":
        bucket["authored"]["guess"] += 1
    elif status_value == "PLACEHOLDER":
        bucket["authored"]["placeholder"] += 1
    elif status_value in _SOURCED:
        bucket["sourced"] += 1
    elif status_value in _DECIDED:
        bucket["decided"] += 1
    else:  # pragma: no cover — an unknown token means a new Status was not mapped
        raise ValueError(f"unmapped value status {status_value!r}")


def authored(bucket: dict) -> int:
    """The authored count for a bucket: GUESS + PLACEHOLDER."""
    return bucket["authored"]["guess"] + bucket["authored"]["placeholder"]


def ratcheted(bucket: dict) -> int:
    """A human "total debt" figure: authored + undeclared.

    The ratchet test gates ``authored`` and ``undeclared`` **independently** per
    area (design §6 Q3 — each may only fall); this sum is only a convenience column
    for the printed table, not the gate. ``sourced`` and ``decided`` are reported,
    never gated.
    """
    return authored(bucket) + bucket["undeclared"]


# ---------------------------------------------------------------------------
# Locus 1 — config/physics scalars (provenance.py)
# ---------------------------------------------------------------------------
def _physics_config_bucket() -> dict:
    bucket = _empty_bucket()
    for prov in TUNING_PROVENANCE.values():
        _tally_status(bucket, prov.status)
    # No undeclared: the registry keyset == the curated constant set (drift-guarded
    # in test_tuning_provenance), so every in-scope scalar carries a status.
    return bucket


# ---------------------------------------------------------------------------
# Locus 2 — per-fighter move data (the #1133 seam)
# ---------------------------------------------------------------------------
def _iter_status_carriers(fd: FighterData):
    """Yield every status-carrying instance reachable in a fighter's data.

    The five carriers are Circle / Hitbox / VelocityPhase / LandingSpawn / MoveData
    (Hurtbox and FighterData themselves carry no ``status`` map). Circles are reached
    through hurtboxes and through each Hitbox's ``circle``; the rest hang off moves.
    """

    def circles_of(hb: Hurtbox):
        yield from hb.circles

    def hitboxes_of(boxes):
        for box in boxes:
            yield box
            yield box.circle  # the box's radius/offset status lives on its Circle

    yield from circles_of(fd.hurtbox)
    for hb in (fd.crouch_hurtbox, fd.prone_hurtbox):
        if hb is not None:
            yield from circles_of(hb)

    for move in fd.moves.values():
        yield move
        if move.hurtbox is not None:
            yield from circles_of(move.hurtbox)
        yield from hitboxes_of(move.hitboxes)
        yield from move.velocity_phases
        if move.landing_spawn is not None:
            ls = move.landing_spawn
            yield ls
            yield from hitboxes_of(ls.hitboxes)


def _fighter_bucket(fd: FighterData) -> dict:
    bucket = _empty_bucket()
    for instance in _iter_status_carriers(fd):
        value_fields = VALUE_FIELDS[type(instance)]
        status_map = instance.status
        for name in value_fields:
            if name in status_map:
                _tally_status(bucket, status_map[name].status.value)
            elif _is_present(instance, name):
                # An authored value with no status entry — the invisible debt (§5).
                bucket["undeclared"] += 1
    return bucket


def _fighter_stems() -> list[str]:
    """The fighter data files to census, by JSON stem (sorted, self-updating).

    Uses `fighter_json_paths()` so a co-located non-fighter file (e.g. the ROUNDS
    card catalog cards.json, ADR-0020 §1) is never censused as a fighter.
    """
    return [p.stem for p in fighter_json_paths()]


# ---------------------------------------------------------------------------
# The census
# ---------------------------------------------------------------------------
def _sum_into(total: dict, bucket: dict) -> None:
    total["authored"]["guess"] += bucket["authored"]["guess"]
    total["authored"]["placeholder"] += bucket["authored"]["placeholder"]
    total["sourced"] += bucket["sourced"]
    total["decided"] += bucket["decided"]
    total["undeclared"] += bucket["undeclared"]


def census() -> dict[str, dict]:
    """Per-area value-status buckets across both loci, plus a ``"TOTAL"`` roll-up.

    Areas: ``"physics_config"`` (the config scalars) and ``"fighter:<stem>"`` for
    each ``characters/data/<stem>.json``. Each value is a bucket dict:
    ``{"authored": {"guess": N, "placeholder": M}, "sourced": N, "decided": N,
    "undeclared": N}``. Pure and headless — safe to call from a test.
    """
    areas: dict[str, dict] = {"physics_config": _physics_config_bucket()}
    for stem in _fighter_stems():
        areas[f"fighter:{stem}"] = _fighter_bucket(load_fighter_data(stem))

    total = _empty_bucket()
    for bucket in areas.values():
        _sum_into(total, bucket)
    areas["TOTAL"] = total
    return areas


# ---------------------------------------------------------------------------
# Human-readable table (__main__ / `make census`)
# ---------------------------------------------------------------------------
def format_table(data: dict[str, dict] | None = None) -> str:
    """A fixed-width table of the census, one row per area, TOTAL last."""
    data = census() if data is None else data
    header = f"{'area':22} {'guess':>6} {'placehldr':>9} {'sourced':>8} {'decided':>8} {'undecl':>7} {'RATCHET':>8}"
    lines = [header, "-" * len(header)]
    ordered = [k for k in data if k != "TOTAL"] + ["TOTAL"]
    for area in ordered:
        b = data[area]
        row = (
            f"{area:22} {b['authored']['guess']:>6} {b['authored']['placeholder']:>9} "
            f"{b['sourced']:>8} {b['decided']:>8} {b['undeclared']:>7} {ratcheted(b):>8}"
        )
        if area == "TOTAL":
            lines.append("-" * len(header))
        lines.append(row)
    lines.append("")
    lines.append("RATCHET = guess + placeholder + undeclared (total value debt). The #1151 ratchet gates")
    lines.append("  authored (guess+placeholder) and undeclared INDEPENDENTLY per area — each may only fall.")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — human entry point
    print(format_table())
