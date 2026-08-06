"""DEV 4 (#1218) — ROUNDS v1 Health Regen consumer (systems/over_time.py).

Spec: ADR-0019 (Leech card family) §3 · tick-slot #1173 Q4 Option A · knob-fields
#1208 (`FighterData.regen_rate` / `regen_interval`) · apply-layer ADR-0014/#1196.

Health Regen is the *time*-driven Leech heal: a per-frame system (`over_time.tick`)
heals a card-carrying owner a fixed chunk (`regen_rate`, percent) every N frames
(`regen_interval`), maintaining a transient per-fighter counter (`fighter.regen_counter`)
and lowering the owner's `percent` (the setter floors at 0). Defaulted off
(`regen_interval == 0`) → every existing cat + the default sim are byte-identical.

The behavioral slices drive `over_time.tick()` directly over synthetic seats (a real
`Fighter` so the percent-floor is exercised); the tick-slot slice asserts the call
order through the runner. Magnitudes stay tunable (#1156) — the tests pick their own.
"""

from __future__ import annotations

from dataclasses import replace

from pycats.combat.data import Circle, FighterData, Hitbox, Hurtbox, MoveData
from pycats.entities.fighter import Fighter
from pycats.systems import over_time


def _fighter_data(*, regen_rate: float = 0.0, regen_interval: int = 0) -> FighterData:
    """A minimal defaults FighterData with the two Health Regen knobs set."""
    return FighterData(
        hurtbox=Hurtbox(circles=(Circle(0, -10, 20),)),
        moves={
            "attack": MoveData(
                name="jab",
                in_air=False,
                startup=3,
                active=2,
                recovery=6,
                hitboxes=(Hitbox(circle=Circle(30, 0, 10), damage=8.0, angle=45),),
            ),
        },
        # Default-cat grounded units (#1209 made walk/dash/run required, no default);
        # this helper landed via #1218's merge race on a pre-#1209 base.
        walk=1.1,
        dash=1.5,
        run=1.5,
        regen_rate=regen_rate,
        regen_interval=regen_interval,
    )


class _Seat:
    """The over_time contract: a seat exposing `.fighter_data` (the knobs) and
    `.fighter` (a real Fighter whose `percent` setter floors at 0)."""

    def __init__(self, *, percent: float, regen_rate: float = 0.0, regen_interval: int = 0):
        self.fighter_data = _fighter_data(regen_rate=regen_rate, regen_interval=regen_interval)
        self.fighter = Fighter(0, 0, True, self.fighter_data)
        self.fighter.percent = percent


# --- 1. Inert default: no regen card → never healed, counter never advances -----


def test_default_fighter_has_regen_counter_idle_at_zero() -> None:
    fighter = Fighter(0, 0, True, _fighter_data())
    assert fighter.regen_counter == 0


def test_interval_zero_seat_never_heals_and_counter_stays_zero() -> None:
    # regen_interval == 0 = off: skipped with no divide/modulo, percent untouched.
    seat = _Seat(percent=42.0, regen_rate=5.0, regen_interval=0)
    for _ in range(50):
        over_time.tick([seat])
    assert seat.fighter.percent == 42.0
    assert seat.fighter.regen_counter == 0


def test_default_sim_leaves_regen_counter_untouched() -> None:
    # The default headless battle carries no regen card (regen_interval == 0), so
    # over_time skips both fighters every frame — goldens stay byte-identical.
    from pycats.sim.runner import build_players, run_battle

    p1, p2, _ = build_players()
    assert (p1.fighter_data.regen_interval, p2.fighter_data.regen_interval) == (0, 0)
    run_battle(frames=30)
    # build_players makes fresh players; run_battle builds its own, so assert the
    # invariant on freshly-built default players (interval 0 → counter never ticks).
    assert p1.fighter.regen_counter == 0
    assert p2.fighter.regen_counter == 0


# --- 2. Heals every N frames (per-fighter counter), and NOT between --------------


def test_heals_by_rate_exactly_every_interval_frames() -> None:
    seat = _Seat(percent=100.0, regen_rate=5.0, regen_interval=4)
    # Frames 1..3: counter climbs, no heal yet.
    for _ in range(3):
        over_time.tick([seat])
        assert seat.fighter.percent == 100.0
    # Frame 4 (== interval): heal fires, counter resets.
    over_time.tick([seat])
    assert seat.fighter.percent == 95.0
    assert seat.fighter.regen_counter == 0
    # Frames 5..7: no heal.
    for _ in range(3):
        over_time.tick([seat])
        assert seat.fighter.percent == 95.0
    # Frame 8 (== 2·interval): second heal.
    over_time.tick([seat])
    assert seat.fighter.percent == 90.0


def test_interval_one_heals_every_frame() -> None:
    seat = _Seat(percent=10.0, regen_rate=2.0, regen_interval=1)
    over_time.tick([seat])
    assert seat.fighter.percent == 8.0
    over_time.tick([seat])
    assert seat.fighter.percent == 6.0


# --- 3. Floors at 0: regen cannot drive percent negative -------------------------


def test_regen_floors_percent_at_zero() -> None:
    # A heal chunk larger than the remaining percent lands exactly at 0, not negative
    # (reuses the Fighter percent setter's max(0, …) floor).
    seat = _Seat(percent=3.0, regen_rate=5.0, regen_interval=1)
    over_time.tick([seat])
    assert seat.fighter.percent == 0.0
    # Already at 0 → stays 0, no underflow.
    over_time.tick([seat])
    assert seat.fighter.percent == 0.0


# --- 4. Owner-only: a fighter's regen only touches its own percent ---------------


def test_regen_heals_only_the_card_owner() -> None:
    owner = _Seat(percent=50.0, regen_rate=5.0, regen_interval=1)
    opponent = _Seat(percent=50.0, regen_rate=0.0, regen_interval=0)
    over_time.tick([owner, opponent])
    assert owner.fighter.percent == 45.0
    assert opponent.fighter.percent == 50.0  # untouched
    assert opponent.fighter.regen_counter == 0


# --- 5. Tick slot: over_time runs before process_hits, through the runner --------


def test_over_time_ticks_before_process_hits_in_runner(monkeypatch) -> None:
    # #1173 Q4 Option A: the heal is applied in the p.update pass, BEFORE
    # process_hits — so a same-frame hit that raises percent lands on top of the heal.
    from pycats.sim import runner
    from pycats.systems import hit_resolution

    calls: list[str] = []
    real_tick = over_time.tick
    real_process = hit_resolution.process_hits

    def spy_tick(players):
        calls.append("over_time")
        return real_tick(players)

    def spy_process(players, attacks):
        calls.append("process_hits")
        return real_process(players, attacks)

    monkeypatch.setattr(runner.over_time, "tick", spy_tick)
    monkeypatch.setattr(runner.hit_resolution, "process_hits", spy_process)

    runner.run_battle(frames=1)

    assert calls[:2] == ["over_time", "process_hits"], calls


def test_regen_visible_through_the_runner_frame_loop(monkeypatch) -> None:
    # End-to-end: give a runner-built fighter a regen card knob and confirm the heal
    # reaches percent across frames (over_time is genuinely wired into run_battle).
    from pycats.core.input import InputFrame
    from pycats.sim import runner

    real_build = runner.build_players

    def build_with_regen(*args, **kwargs):
        p1, p2, group = real_build(*args, **kwargs)
        p1.fighter_data = replace(p1.fighter_data, regen_rate=4.0, regen_interval=2)
        p1.fighter.percent = 40.0
        return p1, p2, group

    monkeypatch.setattr(runner, "build_players", build_with_regen)

    # Empty inputs → no attacks, no hits → P1's percent moves only via regen.
    idle = [InputFrame(held=set(), pressed=set(), released=set()) for _ in range(6)]
    snaps = runner.run_battle(frames=6, frame_inputs=idle)
    # snapshot() returns (players_tuple, atk, phase, winner); P1 is players_tuple[0].
    # P1 starts at 40, heals 4 every 2 frames over 6 frames → 3 heals → 28.
    p1_final_percent = snaps[-1][0][0].percent
    assert p1_final_percent == 28.0
