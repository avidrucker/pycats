"""
tests/test_fighter_to_json.py

R5 (#847, child of #792 editor): the migration dump — FighterData -> minimal
thin-mirror dict (docs/pycats-editor-data-schema-design.md §2.4 + §1).

`fighter_to_json` is the inverse of `_fighter_from_json` (R3, #838). The core
guarantee is a round-trip THROUGH JSON (mirroring the real §2.2 write->reload
cycle: dict -> json.dumps -> json.loads -> hydrate): every shipped fighter
survives serialize->reload byte-equal. A serializer bug (wrong key, a dropped
non-default, a list/tuple slip) breaks that equality.

Two schema rules are also asserted directly (§1):
  1. Omit == default — no field equal to its dataclass default appears.
  2. Circles are inline [dx, dy, r] arrays.

R5 ships the serializer + these tests ONLY and commits ZERO live <character>.json
(ruling on #847). No real fighter is flipped onto the R4 JSON reader, so goldens
cannot move — the round-trip here is an in-memory equality check, not a file.
"""

import json
from dataclasses import replace

import pytest

from pycats.combat.data import (
    GETUP_ATTACK,
    SCHEMA_VERSION,
    Circle,
    FieldStatus,
    FighterData,
    Hitbox,
    Hurtbox,
    MoveData,
    Status,
    _fighter_from_json,
    _move_from_json,
    _move_to_json,
    fighter_to_json,
    load_fighter_data,
)

# Every fighter key the Python switch resolves to a distinct definition, plus the
# default cat. "default" is an unknown key -> DEFAULT_FIGHTER_DATA (§2.4 names
# nalio/birky/narz/default; gnok is the fourth archetype and rides along).
FIGHTER_KEYS = ["nalio", "birky", "narz", "gnok", "default"]


def _through_json(doc: dict) -> dict:
    """Round the dict through the real JSON text boundary (§2.2 reload)."""
    return json.loads(json.dumps(doc))


# ---------------------------------------------------------------------------
# Round-trip equality (able-to-fail) — the load-bearing guarantee
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", FIGHTER_KEYS)
def test_roundtrip_through_json_equals_source(key):
    fd = load_fighter_data(key)
    rebuilt = _fighter_from_json(_through_json(fighter_to_json(fd)))
    assert rebuilt == fd


def test_getup_attack_move_roundtrips():
    # The module-level bare MoveData (not attached to a fighter) round-trips at
    # the move level: it carries non-default BKB/KBG so it also proves the
    # non-default tail survives.
    rebuilt = _move_from_json(_through_json(_move_to_json(GETUP_ATTACK)))
    assert rebuilt == GETUP_ATTACK


@pytest.mark.parametrize("key", FIGHTER_KEYS)
def test_output_is_json_serializable(key):
    # No tuples/sets/dataclasses leak into the dump — json.dumps must not raise.
    json.dumps(fighter_to_json(load_fighter_data(key)))


# ---------------------------------------------------------------------------
# Schema rule 1 — omit == default (thin output)
# ---------------------------------------------------------------------------


def test_nalio_jab_is_thin_matches_worked_example():
    # §1.1: the Nalio jab dumps to exactly the collapsed hitboxes, no default
    # keys. Grounded in nalio_cat.py _JAB, not the design prose. Each box also
    # carries its dense `label` (#1041) — A, B, C in box order.
    doc = fighter_to_json(load_fighter_data("nalio"))
    jab = doc["moves"]["jab"]
    assert jab["hitboxes"] == [
        {
            "circle": [54, 27, 19],
            "damage": 3.0,
            "angle": 83,
            "knockback_growth": 100.0,
            "set_knockback": 20,
            "label": "A",
        },
        {
            "circle": [44, 28, 13],
            "damage": 3.0,
            "angle": 83,
            "knockback_growth": 100.0,
            "set_knockback": 20,
            "label": "B",
        },
        {
            "circle": [34, 29, 15],
            "damage": 3.0,
            "angle": 85,
            "knockback_growth": 100.0,
            "set_knockback": 20,
            "label": "C",
        },
    ]
    # base_knockback (0.0) and the default window resolve to None -> all dropped.
    for hb in jab["hitboxes"]:
        assert "base_knockback" not in hb
        assert "active_start" not in hb
        assert "active_end" not in hb


def test_default_valued_move_tail_omitted():
    jab = fighter_to_json(load_fighter_data("nalio"))["moves"]["jab"]
    for defaulted in (
        "rehit_rate",
        "projectile_speed",
        "projectile_lifetime",
        "chargeable",
        "grants_recovery",
        "recovery_vy",
        "recovery_vx",
        "hurtbox",
    ):
        assert defaulted not in jab


def test_default_valued_fighter_fields_omitted():
    # Nalio uses weight 100 (the default) and the config movement globals -> none
    # of those keys appear. (Nalio DOES set crouch geometry, so *_size/*_hurtbox
    # are intentionally not asserted here — see test_optional_geometry_roundtrips.)
    doc = fighter_to_json(load_fighter_data("nalio"))
    for defaulted in (
        "weight",
        "gravity",
        "max_fall_speed",
        "move_speed",
        "dash_speed",
        "jump_vel",
        "max_jumps",
    ):
        assert defaulted not in doc, f"{defaulted} equals its default and must be omitted"


def test_nondefault_scalar_is_emitted_and_roundtrips():
    # Sharpener: a field set AWAY from its default must survive (guards the drop
    # logic from over-dropping). weight 123 != 100 -> present.
    base = load_fighter_data("nalio")
    heavy = FighterData(
        hurtbox=base.hurtbox,
        moves=base.moves,
        weight=123,
    )
    doc = fighter_to_json(heavy)
    assert doc["weight"] == 123
    assert _fighter_from_json(_through_json(doc)).weight == 123


# ---------------------------------------------------------------------------
# Schema rule 2 — inline circles; schema envelope
# ---------------------------------------------------------------------------


def test_circles_are_inline_arrays():
    doc = fighter_to_json(load_fighter_data("nalio"))
    assert doc["hurtbox"]["circles"] == [[20, 15, 14], [20, 45, 14]]
    assert doc["moves"]["jab"]["hitboxes"][0]["circle"] == [54, 27, 19]


def test_schema_version_present():
    assert fighter_to_json(load_fighter_data("nalio"))["schema_version"] == SCHEMA_VERSION


def test_character_key_present_only_when_named():
    fd = load_fighter_data("nalio")
    assert fighter_to_json(fd, "nalio")["character"] == "nalio"
    assert "character" not in fighter_to_json(fd)


def test_fighter_level_status_map_roundtrips():
    # #1216: FighterData carries its own per-value status map (the fighter-scalar
    # provenance seam), like the five #1133 carriers. A non-empty map survives
    # serialize->reload, and serializes in the same lenient union form (an object
    # when a source rides along). Able-to-fail: without the field + serializer
    # wiring the map is dropped and rebuilt.status != tagged.status.
    base = load_fighter_data("nalio")
    tagged = replace(base, status={"weight": FieldStatus(Status.FOUND, "datamine")})
    doc = fighter_to_json(tagged)
    assert doc["status"] == {"weight": {"status": "FOUND", "source": "datamine"}}
    rebuilt = _fighter_from_json(_through_json(doc))
    assert rebuilt.status == tagged.status


def test_fighter_level_status_omitted_when_empty():
    # Every shipped cat authors no fighter-level status today -> the key is omitted
    # -> existing <cat>.json stay byte-identical (golden-neutral), mirroring the
    # omit-when-empty leniency the other #1133 carriers already have.
    doc = fighter_to_json(load_fighter_data("nalio"))
    assert "status" not in doc


def test_optional_geometry_roundtrips():
    # A fighter with crouch/prone geometry + a per-move hurtbox override must
    # round-trip those optional structural fields (not just the movement globals).
    hb = Hurtbox(circles=(Circle(10, 20, 8),))
    move = MoveData(
        name="poke",
        in_air=False,
        startup=2,
        active=2,
        recovery=6,
        hitboxes=(Hitbox(circle=Circle(30, 20, 10), damage=4.0, angle=45),),
        hurtbox=Hurtbox(circles=(Circle(12, 22, 9),)),
    )
    fd = FighterData(
        hurtbox=hb,
        moves={"poke": move},
        stand_size=(40, 60),
        crouch_size=(40, 40),
        crouch_hurtbox=Hurtbox(circles=(Circle(10, 30, 8),)),
        prone_size=(40, 24),
        prone_hurtbox=Hurtbox(circles=(Circle(10, 40, 8),)),
    )
    assert _fighter_from_json(_through_json(fighter_to_json(fd))) == fd
