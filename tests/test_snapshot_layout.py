"""#322 / B-b — the golden snapshot is self-describing (PlayerSnap namedtuple).

Drift guard: PlayerSnap's field names must map to runner.snapshot()'s real field
POSITIONS. It asserts known frame-0 semantic values *by name*, so reordering or
inserting a field in snapshot() (without matching PlayerSnap) reds this — the
named accessor can't silently read the wrong slot.
"""


from pycats.config import INITIAL_LIVES  # noqa: E402
from pycats.sim.runner import PlayerSnap, run_battle  # noqa: E402


def test_playersnap_names_map_to_real_snapshot_field_positions():
    snaps = run_battle(frames=1)
    part = snaps[0][0][0]  # frame 0, player parts, player 0
    assert len(PlayerSnap._fields) == len(part), "PlayerSnap width != snapshot part width"

    ps = PlayerSnap(*part)
    # Named fields must carry the right TYPE + known frame-0 value. If a field were
    # reordered in snapshot(), one of these names would read the wrong slot (e.g.
    # `state` would be an int, or `lives` would be a state string) and red.
    assert ps.name == "P1"
    assert isinstance(ps.state, str)
    assert ps.lives == INITIAL_LIVES
    assert ps.is_alive is True
    assert ps.percent == 0
    assert isinstance(ps.on_ground, bool)
    assert isinstance(ps.facing_right, bool)
