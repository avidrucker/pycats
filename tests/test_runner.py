# tests/test_runner.py
from pycats.sim.runner import run_battle


def test_runner_is_deterministic():
    a = run_battle(backend="legacy", frames=120)
    b = run_battle(backend="legacy", frames=120)
    assert a == b


def test_runner_produces_one_snapshot_per_frame():
    snaps = run_battle(backend="legacy", frames=80)
    assert len(snaps) == 80


def test_runner_runs_statechart_backend():
    snaps = run_battle(backend="statechart", frames=80)
    assert len(snaps) == 80


# --- Task 6: new snapshot field tests ---

def test_snapshot_player_tuple_ends_with_defensive_status_and_move_frame():
    """Per-player tuple must end with defensive_status (str) and move_frame (int)."""
    snaps = run_battle(backend="legacy", frames=10)
    players, _atk, _phase, _winner = snaps[0]
    for p in players:
        # last two fields: defensive_status (str), move_frame (int)
        defensive_status = p[-2]
        move_frame = p[-1]
        assert isinstance(defensive_status, str), (
            f"expected str for defensive_status, got {type(defensive_status)}: {defensive_status!r}"
        )
        assert defensive_status in ("vulnerable", "intangible"), (
            f"unexpected defensive_status value: {defensive_status!r}"
        )
        assert isinstance(move_frame, int), (
            f"expected int for move_frame, got {type(move_frame)}: {move_frame!r}"
        )


def test_snapshot_attack_tuple_ends_with_hitbox_circle():
    """Per-attack tuples must end with hit_cx, hit_cy, hit_r (float or int)."""
    from pycats.sim.input_script import compile_timeline, COMBAT_SCRIPT
    from pycats.sim.runner import KEYMAPS
    frame_inputs = compile_timeline(COMBAT_SCRIPT, KEYMAPS)
    # Run enough frames that attacks actually appear
    snaps = run_battle(backend="legacy", frames=len(frame_inputs), frame_inputs=frame_inputs)
    # Find a snap where an attack is active
    attack_snap = None
    for s in snaps:
        _players, atk, _phase, _winner = s
        if atk:
            attack_snap = atk
            break
    assert attack_snap is not None, "No attacks appeared during COMBAT_SCRIPT run"
    for a in attack_snap:
        # Existing fields: (rect.x, rect.y, frames_left, owner_name, active)
        # New fields: hit_cx, hit_cy, hit_r  at indices -3, -2, -1
        assert len(a) == 8, f"expected 8-field attack tuple, got {len(a)}: {a}"
        hit_cx, hit_cy, hit_r = a[-3], a[-2], a[-1]
        assert isinstance(hit_cx, (int, float)), f"hit_cx not numeric: {hit_cx!r}"
        assert isinstance(hit_cy, (int, float)), f"hit_cy not numeric: {hit_cy!r}"
        assert isinstance(hit_r, (int, float)), f"hit_r not numeric: {hit_r!r}"
        assert hit_r > 0, f"hit_r should be positive, got {hit_r}"


def test_default_backend_is_statechart():
    """run_battle() with no backend arg must use statechart (deterministic)."""
    a = run_battle(frames=120)
    b = run_battle(frames=120)
    assert a == b, "default-backend run_battle() is not deterministic"
    # Must match explicit statechart run on same frames
    c = run_battle(backend="statechart", frames=120)
    assert a == c, "default run_battle() does not match explicit statechart run"
