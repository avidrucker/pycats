"""
tests/test_hitbox_v1_fields.py

#1213 (child of #1147, ruled by ADR-0021 / #1150): the ADR-0018 (#1161) V1-in
per-hitbox fields land on the `Hitbox` dataclass as five flat, optional,
defaulted scalars — peers of `base_knockback`/`set_id`/`label`:

    | field          | type         | default |
    | hitlag_mult    | float        | 1.0     |
    | shield_damage  | int          | 0       |
    | ground         | bool         | True    |
    | aerial         | bool         | True    |
    | hitbox_id      | int | None    | None    |

Two guarantees, both able-to-fail:

  1. **Byte-identical (omit == default).** A box left at the new defaults emits
     none of the five keys, so every shipped `<cat>.json` and every golden is
     unchanged and `schema_version` stays 1. Guarded here directly on
     `_hitbox_to_json`; the whole-fighter round-trip in test_fighter_to_json.py
     (`test_roundtrip_through_json_equals_source`) is the corpus-wide backstop.

  2. **Non-default survives.** A box authored with any of the five set away from
     its default serializes that sibling key and hydrates it back faithfully
     through the real JSON text boundary.

This DEV is representation + serialization + editor round-trip preservation ONLY
(ADR-0021 scope). Engine consumption (hitlag_frames / shield.py / target-state
gate) and the `max(damage)->min(hitbox_id)` box-selection swap are separate
downstream DEVs (#1214 for the swap).
"""

import json

import pytest

from pycats.combat.data import (
    Circle,
    FieldStatus,
    Hitbox,
    MoveData,
    Status,
    _hitbox_from_json,
    _hitbox_to_json,
    _move_from_json,
    _move_to_json,
)

# The five V1-in fields and a value DISTINCT from each default (ADR-0021 table).
_DEFAULTS = {
    "hitlag_mult": 1.0,
    "shield_damage": 0,
    "ground": True,
    "aerial": True,
    "hitbox_id": None,
}
_NONDEFAULT = {
    "hitlag_mult": 1.5,
    "shield_damage": 6,
    "ground": False,
    "aerial": False,
    "hitbox_id": 2,
}


def _base_box(**extra) -> Hitbox:
    return Hitbox(circle=Circle(30, 20, 10), damage=4.0, angle=45, **extra)


def _through_json_box(hb: Hitbox) -> Hitbox:
    """Round one hitbox through the real JSON text boundary (§2.2 reload)."""
    return _hitbox_from_json(json.loads(json.dumps(_hitbox_to_json(hb))))


# ---------------------------------------------------------------------------
# Defaults are today's behaviour
# ---------------------------------------------------------------------------


def test_new_fields_default_to_todays_values():
    hb = _base_box()
    assert hb.hitlag_mult == 1.0
    assert hb.shield_damage == 0
    assert hb.ground is True
    assert hb.aerial is True
    assert hb.hitbox_id is None


# ---------------------------------------------------------------------------
# Guarantee 1 — omit == default (byte-identical)
# ---------------------------------------------------------------------------


def test_default_new_fields_are_omitted():
    # A box at all-defaults emits none of the five keys -> existing data is
    # byte-identical and schema_version stays 1.
    out = _hitbox_to_json(_base_box())
    for name in _DEFAULTS:
        assert name not in out, f"{name} at its default must be omitted (byte-identical)"


# ---------------------------------------------------------------------------
# Guarantee 2 — non-default survives serialize -> reload
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field_name", list(_NONDEFAULT))
def test_each_new_field_emitted_and_roundtrips(field_name):
    value = _NONDEFAULT[field_name]
    hb = _base_box(**{field_name: value})
    out = _hitbox_to_json(hb)
    assert out[field_name] == value, f"{field_name} set away from default must be emitted"
    assert getattr(_through_json_box(hb), field_name) == value


def test_all_new_fields_together_roundtrip():
    hb = _base_box(**_NONDEFAULT)
    assert _through_json_box(hb) == hb


def test_new_fields_roundtrip_inside_a_move():
    # The real write path is per-move: a box carrying the fields inside a MoveData
    # survives the move-level serialize->reload (the shape <cat>.json actually uses).
    move = MoveData(
        name="poke",
        in_air=False,
        startup=2,
        active=2,
        recovery=6,
        hitboxes=(_base_box(**_NONDEFAULT),),
    )
    rebuilt = _move_from_json(json.loads(json.dumps(_move_to_json(move))))
    assert rebuilt == move


# ---------------------------------------------------------------------------
# FOUND provenance rides along (ADR-0021 / #1133 StatusMap)
# ---------------------------------------------------------------------------


def test_new_field_carries_found_provenance():
    # A datamined value annotates its provenance via the existing per-value
    # StatusMap keyed by the box's own field name.
    hb = _base_box(
        shield_damage=6,
        status={"shield_damage": FieldStatus(Status.FOUND, "datamine")},
    )
    rebuilt = _through_json_box(hb)
    assert rebuilt.status["shield_damage"] == FieldStatus(Status.FOUND, "datamine")
    assert rebuilt.shield_damage == 6
