"""
tests/test_value_status_seam.py

The per-fighter value-status seam (#1133, O3+O2 ratified in #1129). A typed
`status` map on the authored dataclasses (Circle / Hitbox / MoveData /
VelocityPhase / LandingSpawn) records each value's authored-vs-sourced status
(FOUND / GUESS / TUNED / DIVERGENCE / PLACEHOLDER, #1129 Q3) at per-VALUE
granularity (#1129 Q5), and the flip carries it into `characters/data/*.json`
(O2) — closing the #1124 G1/G2 gap where the shipped JSON carried no status.

The able-to-fail anchor is `test_shipped_birky_json_carries_placeholder_*`:
before the seam the compiled birky.json had no `status` key at all, so reading
Final Cutter's plunge-spike `damage` status KeyErrors — red today, green once
the seam ships and birky.json is regenerated. Birky's Final Cutter is the
exemplar (the #1110 case): phase-2/3 numbers are PLACEHOLDER, the datamined
phase-1 blade is the mixed box (sourced radius + authored position).
"""

import json

from pycats.characters.birky_cat import BIRKY_FIGHTER_DATA
from pycats.combat.data import (
    CHARACTER_DATA_DIR,
    Circle,
    FieldStatus,
    FighterData,
    Hitbox,
    Hurtbox,
    LandingSpawn,
    MoveData,
    Status,
    VelocityPhase,
    _field_status_to_json,
    _fighter_from_json,
    _hitbox_to_json,
    _velocity_phase_to_json,
    fighter_to_json,
    load_fighter_data,
)


def _final_cutter_boxes():
    return BIRKY_FIGHTER_DATA.moves["up_b"].hitboxes


def _spike(boxes):
    # The phase-2 plunge spike: the #1110 authored meteor (damage 6, angle 270).
    return next(b for b in boxes if b.angle == 270 and b.damage == 6.0)


def _blade(boxes):
    # A phase-1 rising-slash blade (active f3-4): the datamined mixed box.
    return next(b for b in boxes if b.active_start == 3)


# --- Able-to-fail anchor: the shipped JSON carries the status ------------------


def test_shipped_birky_json_carries_placeholder_on_final_cutter_spike():
    # Reads the COMPILED file (not the oracle): before the seam the box has no
    # "status" key, so this KeyErrors — red today, green after the flip.
    doc = json.loads((CHARACTER_DATA_DIR / "birky.json").read_text())
    boxes = doc["moves"]["up_b"]["hitboxes"]
    spike = next(b for b in boxes if b.get("angle") == 270 and b.get("damage") == 6.0)
    assert spike["status"]["damage"] == "PLACEHOLDER"


def test_loaded_birky_final_cutter_spike_is_all_placeholder():
    # The same value hydrated back through load_fighter_data (the JSON branch).
    spike = _spike(load_fighter_data("birky").moves["up_b"].hitboxes)
    assert spike.status["damage"] == FieldStatus(Status.PLACEHOLDER)
    assert spike.status["angle"] == FieldStatus(Status.PLACEHOLDER)
    assert spike.circle.status["r"] == FieldStatus(Status.PLACEHOLDER)


# --- Per-value granularity: the mixed box (#1129 Q5, #1124) --------------------


def test_final_cutter_blade_mixes_sourced_radius_with_authored_position():
    # Within ONE box: the circle's radius is FOUND (datamine) while its dx/dy are
    # PLACEHOLDER (body-fit playtest) — the per-value granularity the seam exists
    # for. This can't be expressed at per-box granularity.
    blade = _blade(load_fighter_data("birky").moves["up_b"].hitboxes)
    assert blade.circle.status["r"] == FieldStatus(Status.FOUND, "datamine")
    assert blade.circle.status["dx"] == FieldStatus(Status.PLACEHOLDER)
    assert blade.status["damage"] == FieldStatus(Status.FOUND, "datamine")


def test_final_cutter_move_level_recovery_vy_is_found():
    move = load_fighter_data("birky").moves["up_b"]
    assert move.status["recovery_vy"] == FieldStatus(Status.FOUND, "datamine")


# --- Serialized shape: compact vs object, omit-when-empty ----------------------


def test_field_status_serializes_compact_without_source_object_with_source():
    assert _field_status_to_json(FieldStatus(Status.PLACEHOLDER)) == "PLACEHOLDER"
    assert _field_status_to_json(FieldStatus(Status.FOUND, "datamine")) == {
        "status": "FOUND",
        "source": "datamine",
    }


def test_unannotated_box_emits_no_status_keys():
    # Golden-safety: an unannotated box serializes with no status/circle_status key,
    # so every existing fighter's JSON is byte-identical (proven wholesale by R8).
    out = _hitbox_to_json(Hitbox(circle=Circle(dx=0, dy=0, r=5), damage=1.0, angle=0))
    assert "status" not in out
    assert "circle_status" not in out


def test_velocity_phase_serializes_triple_without_status_object_with():
    plain = VelocityPhase(frame=3, vx=0.0, vy=12.0)
    assert _velocity_phase_to_json(plain) == [3, 0.0, 12.0]  # byte-identical
    tagged = VelocityPhase(frame=3, vx=0.0, vy=12.0, status={"vy": FieldStatus(Status.PLACEHOLDER)})
    out = _velocity_phase_to_json(tagged)
    assert out["frame"] == 3
    assert out["status"] == {"vy": "PLACEHOLDER"}


# --- Round-trip on every carrier (incl. VelocityPhase / LandingSpawn) ----------


def _synthetic_fighter_with_status_everywhere() -> FighterData:
    """A FighterData carrying a status map on ALL five authored dataclasses plus a
    hurt circle — the carriers Birky's shipped exemplar doesn't all annotate."""
    hitbox = Hitbox(
        circle=Circle(
            dx=0,
            dy=10,
            r=12,
            status={"r": FieldStatus(Status.FOUND, "datamine"), "dx": FieldStatus(Status.PLACEHOLDER)},
        ),
        damage=6.0,
        angle=270,
        status={"damage": FieldStatus(Status.PLACEHOLDER), "angle": FieldStatus(Status.DIVERGENCE)},
    )
    spawn = LandingSpawn(
        hitboxes=(
            Hitbox(
                circle=Circle(dx=0, dy=10, r=8, status={"r": FieldStatus(Status.GUESS)}),
                damage=5.0,
                angle=45,
                status={"damage": FieldStatus(Status.TUNED)},
            ),
        ),
        speed=8.0,
        lifetime=20,
        status={"speed": FieldStatus(Status.PLACEHOLDER, "playtest")},
    )
    move = MoveData(
        name="synthetic",
        in_air=True,
        startup=2,
        active=2,
        recovery=40,
        hitboxes=(hitbox,),
        velocity_phases=(VelocityPhase(frame=38, vx=0.0, vy=12.0, status={"vy": FieldStatus(Status.PLACEHOLDER)}),),
        landing_spawn=spawn,
        status={"startup": FieldStatus(Status.FOUND, "datamine")},
    )
    hurt = Hurtbox(circles=(Circle(dx=0, dy=0, r=10, status={"r": FieldStatus(Status.FOUND, "datamine")}),))
    return FighterData(hurtbox=hurt, moves={"up_b": move})


def test_status_survives_serialize_reload_on_every_carrier():
    fd = _synthetic_fighter_with_status_everywhere()
    # dict -> json.dumps -> json.loads -> hydrate, the real write/reload cycle.
    reloaded = _fighter_from_json(json.loads(json.dumps(fighter_to_json(fd, "synthetic"))))
    assert reloaded == fd


def test_shipped_birky_round_trips_with_status():
    # The exemplar file specifically: on-disk bytes hydrate back to the oracle,
    # status maps included (R8 covers this in aggregate; asserted here explicitly).
    assert load_fighter_data("birky") == BIRKY_FIGHTER_DATA
