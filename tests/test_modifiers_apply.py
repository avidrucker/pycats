"""ROUNDS v1 modifier apply-layer (DEV 2, #1196; spec ADR-0014).

The apply-layer turns drafted cards into a patched FighterData. These tests drive
each acceptance slice of ADR-0014 through the public surface of
`pycats.loadout.modifiers` (Modifier, card_to_modifiers, apply) and the inert
wiring at `build_fighter`. Cards come from the real catalog (load_cards) so the
tests exercise the authored deltas, not synthetic stand-ins.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
from pycats.combat.units import u
from pycats.loadout.cards import load_cards
from pycats.loadout.modifiers import Modifier, apply, card_to_modifiers


def _baseline() -> FighterData:
    """A minimal FighterData with the default-cat speed units (walk 1.1 → move_speed
    6) + weight=100 / gravity=0.5, plus one move carrying two hitboxes so nested-seam
    scaling has real targets. Speed modifiers scale the raw UNIT (walk/dash/run); the
    shipped px re-derives via u() (#1209, ADR-0011)."""
    return FighterData(
        walk=1.1,
        dash=1.5,
        run=1.5,
        hurtbox=Hurtbox(circles=(Circle(0, -10, 20), Circle(0, 20, 16))),
        moves={
            "attack": MoveData(
                name="jab",
                in_air=False,
                startup=3,
                active=2,
                recovery=6,
                hitboxes=(
                    Hitbox(circle=Circle(30, 0, 10), damage=8.0, angle=45, base_knockback=20.0, knockback_growth=100.0),
                    Hitbox(circle=Circle(40, 0, 12), damage=4.0, angle=80, base_knockback=10.0, knockback_growth=90.0),
                ),
            ),
        },
        stand_size=(60, 80),
    )


def test_card_to_modifiers_derives_one_modifier_per_delta() -> None:
    chase = load_cards()["chase"]
    mods = card_to_modifiers(chase)
    assert mods == [
        Modifier("move_speed", "mult_pct", 20),
        Modifier("dash_speed", "mult_pct", 20),
        Modifier("run_speed", "mult_pct", 20),
    ]


def test_baseline_move_speed_is_six() -> None:
    # Guards the concrete acceptance numbers below: base walk 1.1u derives u(1.1) = 6,
    # the same px the removed MOVE_SPEED global used to hold.
    assert _baseline().move_speed == u(1.1) == 6


def test_apply_no_cards_is_identity() -> None:
    baseline = _baseline()
    assert apply(baseline, ()) is baseline


def test_apply_does_not_mutate_baseline_and_returns_distinct_object() -> None:
    baseline = _baseline()
    before = replace(baseline)  # a snapshot to compare against
    result = apply(baseline, [load_cards()["chase"]])
    assert result is not baseline
    assert baseline == before  # in-place mutation would red this


def test_stocks_delta_is_not_consumed_by_apply() -> None:
    # Phoenix carries only a `stocks` delta (ADR-0013 seam 10, match-level lives).
    # It is OUT of the FighterData apply-layer, so the FighterData is unchanged.
    baseline = _baseline()
    assert apply(baseline, [load_cards()["phoenix"]]) == baseline


def test_single_mult_pct_rounds_int_seam() -> None:
    # Chase: move_speed +20% scales the walk UNIT → u(1.1 × 1.20) = u(1.32) = 7.
    result = apply(_baseline(), [load_cards()["chase"]])
    assert result.move_speed == u(1.1 * 1.20) == 7


def test_compound_same_seam_multiplies_factors_not_percents() -> None:
    # Chase (+20%) + Metal (−15%) on the walk unit → u(1.1 × 1.20 × 0.85) = 6.
    # (This documents the spec's acceptance example; note it does NOT by itself
    # distinguish product from summed percents — 1.1×1.05 also rounds to 6. The
    # distinguishing case is test_two_factors_compound_distinguishable below.)
    cards = load_cards()
    result = apply(_baseline(), [cards["chase"], cards["metal"]])
    assert result.move_speed == u(1.1 * 1.20 * 0.85) == 6


def test_two_factors_compound_distinguishable_from_summed_percents() -> None:
    # Two +50% factors on the walk unit compound to 1.1 × 1.5 × 1.5 = 2.475 →
    # u = 13, which summed percents (1.1 × 2.0 = 2.2 → u = 12) could never produce —
    # this is the test the compound-vs-sum ruling actually hangs on. Synthetic cards
    # keep the base tuning values free to change without touching this invariant.
    from pycats.loadout.cards import Card

    def boost(cid: str) -> Card:
        return Card(id=cid, name=cid, deltas=[dict(seam="move_speed", op="mult_pct", value=50)], stackable=True)

    result = apply(_baseline(), [boost("a"), boost("b")])
    assert result.move_speed == u(1.1 * 1.5 * 1.5) == 13
    assert result.move_speed != u(1.1 * (1 + 0.5 + 0.5))  # 12, the summed-percents answer


def test_mixed_ops_apply_flats_after_the_scaled_base() -> None:
    # Glass Cannon (weight add_n −8) + Metal (weight mult_pct +30) →
    # round(100 × 1.30 − 8) = 122. add_n lands AFTER the scaled base, and the
    # result is order-independent (both cards, either order, give 122).
    cards = load_cards()
    a = apply(_baseline(), [cards["glass_cannon"], cards["metal"]])
    b = apply(_baseline(), [cards["metal"], cards["glass_cannon"]])
    assert a.weight == b.weight == round(100 * 1.30 - 8) == 122


def test_float_seam_gravity_is_not_rounded() -> None:
    # Floaty: gravity −20% → 0.5 × 0.80 = 0.4, preserved (no truncation to 0).
    result = apply(_baseline(), [load_cards()["floaty"]])
    assert result.gravity == pytest.approx(0.5 * 0.80)
    assert result.gravity != round(result.gravity)


def test_add_n_floor_clamps_weight_at_one() -> None:
    # A synthetic add_n that would drive weight below 1 floors at 1 (ADR-0013).
    heavy_negative = Modifier("weight", "add_n", -500)
    from pycats.loadout.cards import Card

    card = Card(id="anvil", name="Anvil", deltas=[dict(seam="weight", op="add_n", value=-500)], stackable=True)
    assert card_to_modifiers(card) == [heavy_negative]
    result = apply(_baseline(), [card])
    assert result.weight == 1


def test_damage_scales_every_hitbox() -> None:
    # Glass Cannon: damage +25% scales EVERY hitbox's damage (float, no round).
    baseline = _baseline()
    result = apply(baseline, [load_cards()["glass_cannon"]])
    got = [hb.damage for hb in result.moves["attack"].hitboxes]
    want = [hb.damage * 1.25 for hb in baseline.moves["attack"].hitboxes]
    assert got == pytest.approx(want)
    assert got == pytest.approx([10.0, 5.0])


def test_reach_scales_every_hitbox_radius_rounded() -> None:
    # Long Arms: reach +20% scales every Hitbox.circle.r (int, round).
    baseline = _baseline()
    result = apply(baseline, [load_cards()["long_arms"]])
    got = [hb.circle.r for hb in result.moves["attack"].hitboxes]
    assert got == [round(10 * 1.20), round(12 * 1.20)] == [12, 14]


def test_knockback_growth_scales_every_hitbox() -> None:
    # Bruiser: knockback_growth +20% (float, no round) on every hitbox; and its
    # damage −12% rides along on the same card.
    baseline = _baseline()
    result = apply(baseline, [load_cards()["bruiser"]])
    kbg = [hb.knockback_growth for hb in result.moves["attack"].hitboxes]
    assert kbg == pytest.approx([100.0 * 1.20, 90.0 * 1.20])
    dmg = [hb.damage for hb in result.moves["attack"].hitboxes]
    assert dmg == pytest.approx([8.0 * 0.88, 4.0 * 0.88])


def test_body_size_scales_stand_size_and_hurtbox() -> None:
    # Compact: body_size −15% scales stand_size and every hurtbox circle (int, round).
    baseline = _baseline()
    result = apply(baseline, [load_cards()["compact"]])
    assert result.stand_size == (round(60 * 0.85), round(80 * 0.85)) == (51, 68)
    got_r = [c.r for c in result.hurtbox.circles]
    assert got_r == [round(20 * 0.85), round(16 * 0.85)] == [17, 14]
    # Offsets scale uniformly about the origin (a body scale, not a radius-only edit).
    assert [c.dy for c in result.hurtbox.circles] == [round(-10 * 0.85), round(20 * 0.85)] == [-8, 17]


def test_deletion_is_reversible_recompute_from_pristine_baseline() -> None:
    # apply is functional, so re-deriving from a subset of cards is exact regardless
    # of a prior apply with the full set (ADR-0014 §3, model C1).
    cards = load_cards()
    baseline = _baseline()
    _ = apply(baseline, [cards["chase"], cards["metal"]])  # the "before deletion" build
    after_delete = apply(baseline, [cards["chase"]])
    fresh = apply(baseline, [cards["chase"]])
    assert after_delete == fresh
    assert after_delete.move_speed == u(1.1 * 1.20) == 7


def test_selection_defaults_to_no_cards() -> None:
    from pycats.loadout.registry import SKINS, character_for
    from pycats.loadout.selection import Selection

    sel = Selection(character_for("nalio"), SKINS["red-blue"])
    assert sel.cards == ()


def test_build_fighter_default_selection_is_byte_identical() -> None:
    # The inert-wiring invariant: apply(fd, ()) returns the baseline object, so a
    # default Selection through build_fighter yields the same FighterData as the
    # bare resolver — sim goldens + render parity stay green.
    from pycats.loadout.build_fighter import build_fighter
    from pycats.loadout.registry import SKINS, character_for
    from pycats.loadout.resolvers import fighter_data_of
    from pycats.loadout.selection import Selection

    # (== not `is`: load_fighter_data hydrates a fresh instance per call, so two
    # resolver calls are equal-but-distinct. apply's same-object inertness is
    # covered by test_apply_no_cards_is_identity.)
    character = character_for("nalio")
    sel = Selection(character, SKINS["red-blue"])
    assert build_fighter(sel).fighter_data == fighter_data_of(character)


def test_build_fighter_applies_drafted_cards() -> None:
    # With a non-empty card list, build_fighter patches the fighter data.
    from pycats.loadout.build_fighter import build_fighter
    from pycats.loadout.registry import SKINS, character_for
    from pycats.loadout.resolvers import fighter_data_of
    from pycats.loadout.selection import Selection

    character = character_for("nalio")
    base = fighter_data_of(character)
    sel = Selection(character, SKINS["red-blue"], cards=(load_cards()["chase"],))
    built = build_fighter(sel).fighter_data
    assert built.move_speed == round(base.move_speed * 1.20)
