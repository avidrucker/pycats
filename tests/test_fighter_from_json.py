"""
Tests for _fighter_from_json — the pure dict -> FighterData hydrate (#838, R3 of
the #792 editor; design docs/pycats-editor-data-schema-design.md §2.1).

The hydrate is mechanical: inline [dx,dy,r] -> Circle, lists -> tuples, only the
keys present are passed (the frozen dataclasses own every default), validation is
delegated to __post_init__, and `provenance` is never read. It is NOT wired into
load_fighter_data yet (that is R4) — nothing shipped calls it, so goldens are
untouched. Round-trip acceptance pins it against load_fighter_data("nalio").
"""

import pytest

from pycats.combat.data import (
    Circle,
    FighterData,
    Hurtbox,
    MoveData,
    _fighter_from_json,
    load_fighter_data,
)


def _jab_doc():
    """A hand-written document mirroring the real Nalio jab + posture hurtbox
    (pycats/characters/nalio_cat.py `_JAB` / `_HURTBOX`), thin per §1 (every
    default-valued field omitted)."""
    return {
        "schema_version": 1,
        "character": "nalio",
        "weight": 100,
        "hurtbox": {"circles": [[20, 15, 14], [20, 45, 14]]},
        "moves": {
            "jab": {
                "name": "jab",
                "in_air": False,
                "startup": 1,
                "active": 2,
                "recovery": 13,
                "hitboxes": [
                    {
                        "circle": [54, 27, 19],
                        "damage": 3.0,
                        "angle": 83,
                        "knockback_growth": 100.0,
                        "set_knockback": 20,
                    },
                    {
                        "circle": [44, 28, 13],
                        "damage": 3.0,
                        "angle": 83,
                        "knockback_growth": 100.0,
                        "set_knockback": 20,
                    },
                    {
                        "circle": [34, 29, 15],
                        "damage": 3.0,
                        "angle": 85,
                        "knockback_growth": 100.0,
                        "set_knockback": 20,
                    },
                ],
            }
        },
        # provenance present but never read by the loader:
        "provenance": {"jab": {"note": "should be ignored by the hydrate"}},
    }


# --- Tracer bullet: the hydrate builds the frozen dataclasses ----------------


def test_hydrate_returns_fighterdata():
    fd = _fighter_from_json(_jab_doc())
    assert isinstance(fd, FighterData)


# --- Round-trip acceptance: hydrated jab == the real Nalio jab ---------------


def test_hydrated_jab_equals_nalio():
    """The hand-written jab doc hydrates to dataclasses EQUAL to the shipped
    Python (moves/hurtbox/weight) — the §2.4 round-trip acceptance."""
    fd = _fighter_from_json(_jab_doc())
    nalio = load_fighter_data("nalio")
    assert fd.weight == nalio.weight
    assert fd.hurtbox == nalio.hurtbox
    assert fd.moves["jab"] == nalio.moves["jab"]


def test_hydrated_jab_preserves_hitbox_order_and_scalars():
    fd = _fighter_from_json(_jab_doc())
    jab = fd.moves["jab"]
    assert isinstance(jab, MoveData)
    # first box is the outermost fist at dx=54 (priority/list order preserved)
    assert jab.hitboxes[0].circle == Circle(54, 27, 19)
    assert jab.hitboxes[0].set_knockback == 20
    assert jab.hitboxes[0].knockback_growth == 100.0


# --- Collections re-tupled (frozen dataclasses + golden tuple identity) ------


def test_collections_are_tuples_not_lists():
    fd = _fighter_from_json(_jab_doc())
    assert isinstance(fd.hurtbox.circles, tuple)
    assert isinstance(fd.moves["jab"].hitboxes, tuple)
    assert all(isinstance(hb.circle, Circle) for hb in fd.moves["jab"].hitboxes)


def test_sizes_hydrate_to_tuples():
    doc = _jab_doc()
    doc["crouch_size"] = [40, 40]
    doc["crouch_hurtbox"] = {"circles": [[20, 20, 14], [20, 32, 12]]}
    fd = _fighter_from_json(doc)
    assert fd.crouch_size == (40, 40)
    assert isinstance(fd.crouch_size, tuple)
    assert fd.crouch_hurtbox == Hurtbox(circles=(Circle(20, 20, 14), Circle(20, 32, 12)))


# --- Omission == the dataclass default (§1) ----------------------------------


def test_omitted_fields_take_dataclass_defaults():
    fd = _fighter_from_json(_jab_doc())
    jab = fd.moves["jab"]
    # omitted MoveData tail -> defaults
    assert jab.hurtbox is None  # no per-move override in the doc
    assert jab.rehit_rate is None
    assert jab.chargeable is False
    # omitted Hitbox fields -> defaults
    assert jab.hitboxes[0].base_knockback == 0.0
    assert jab.hitboxes[0].active_start is None
    assert jab.hitboxes[0].active_end is None
    # omitted FighterData movement fields -> config globals (== the default cat)
    default = load_fighter_data("nalio")
    assert fd.gravity == default.gravity
    assert fd.crouch_size is None  # omitted -> cannot crouch


def test_per_move_hurtbox_override_hydrates():
    doc = _jab_doc()
    doc["moves"]["jab"]["hurtbox"] = {"circles": [[20, 10, 16], [20, 40, 16]]}
    fd = _fighter_from_json(doc)
    assert fd.moves["jab"].hurtbox == Hurtbox(circles=(Circle(20, 10, 16), Circle(20, 40, 16)))


def test_provenance_is_never_read():
    doc = _jab_doc()
    doc["provenance"] = {"jab": {"garbage": object()}}  # unserializable junk; loader must ignore it
    fd = _fighter_from_json(doc)  # must not raise
    assert isinstance(fd, FighterData)


# --- Able-to-fail: validation is delegated, not re-implemented ---------------


def test_schema_version_mismatch_rejected():
    doc = _jab_doc()
    doc["schema_version"] = 2
    with pytest.raises(ValueError):
        _fighter_from_json(doc)


def test_missing_schema_version_rejected():
    doc = _jab_doc()
    del doc["schema_version"]
    with pytest.raises(ValueError):
        _fighter_from_json(doc)


def test_invalid_window_raises_via_post_init():
    """active_start without active_end -> ValueError from Hitbox.__post_init__,
    proving the loader delegates validation rather than re-implementing it."""
    doc = _jab_doc()
    doc["moves"]["jab"]["hitboxes"][0]["active_start"] = 2  # no active_end
    with pytest.raises(ValueError):
        _fighter_from_json(doc)


def test_window_exceeding_duration_raises_via_post_init():
    """A window past the move's total duration -> ValueError from
    MoveData.__post_init__ (window-in-duration check)."""
    doc = _jab_doc()
    # jab total = 1+2+13 = 16; a [17,18] window overflows.
    doc["moves"]["jab"]["hitboxes"][0]["active_start"] = 17
    doc["moves"]["jab"]["hitboxes"][0]["active_end"] = 18
    with pytest.raises(ValueError):
        _fighter_from_json(doc)
