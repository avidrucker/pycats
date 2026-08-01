# tests/test_golden.py
"""Golden-snapshot regression oracle for the statechart engine.

Three deterministic scenarios are recorded:
- default:     200 frames with the default timeline
- combat:      COMBAT_SCRIPT inputs + 240-frame tail
- two_npc:     attacker (P1) vs follower (P2), both controller-driven (#58)

Each test calls check_or_update(name, snaps) which compares the serialized
snapshots against tests/golden/<name>.json AND a small reviewable semantic digest
in tests/golden/<name>.summary.json.  Set PYCATS_UPDATE_GOLDENS=1 to (re)record
them — but a regen must be REVIEWED, not rubber-stamped: see
tests/golden/REGEN_PROTOCOL.md (S4).
"""

import random

from pycats.sim.controllers import AttackerController, FollowerController
from pycats.sim.input_script import COMBAT_SCRIPT, compile_timeline
from pycats.sim.runner import KEYMAPS, run_battle
from tests.golden_util import check_or_update

# ---- scenario constants ----
DEFAULT_FRAMES = 200
COMBAT_TAIL = 240
TWO_NPC_FRAMES = 600


def test_golden_default():
    """200-frame default timeline produces a stable golden snapshot.

    Phase 2b (#696): runs Nalio vs Nalio — the first named-cat mechanics flip. The
    scenario passes chars explicitly here (not via the global no-char default, which
    stays the placeholder cat until a later golden-neutral slice); the `character`
    field in the digest reads nalio/nalio.
    """
    snaps = run_battle(frames=DEFAULT_FRAMES, p1_char="nalio", p2_char="nalio")
    assert len(snaps) == DEFAULT_FRAMES
    check_or_update("default", snaps)


def _run_combat():
    # Nalio (P1) vs Birky (P2): COMBAT_SCRIPT racks Birky with in-place jabs then lands a
    # fully-charged forward-smash for a legitimate side-blast KO (#588). The default cat
    # has no fsmash, so the KO needs these characters.
    frame_inputs = compile_timeline(COMBAT_SCRIPT, KEYMAPS)
    frames = len(frame_inputs) + COMBAT_TAIL
    snaps = run_battle(frames=frames, frame_inputs=frame_inputs, p1_char="nalio", p2_char="birky")
    assert len(snaps) == frames
    return snaps


def test_golden_combat():
    """COMBAT_SCRIPT + tail: hurt and ko are exercised via a fully-charged smash KO
    (Nalio fsmashes Birky off the side, ~69%→88%); stable golden. Post-#475 the KO is a
    real knockback launch, not the removed ledge-hang self-destruct (#588). Percents
    rose from ~66→86 when #599 corrected the smash to PM's weaker 1.3671×/59f."""
    snaps = _run_combat()
    all_states = {p[1] for snap in snaps for p in snap[0]}
    assert "hurt" in all_states, f"'hurt' never reached; states={sorted(all_states)}"
    assert "ko" in all_states, f"'ko' never reached; states={sorted(all_states)}"
    check_or_update("combat", snaps)


def test_golden_two_npc():
    """Dual-controller battle (#58): attacker (P1) vs follower (P2), BOTH players
    driven via controllers=. Locks the dual-controller path against a golden.
    """
    # #166: fixed seed pinned at the live two-NPC golden (neither archetype draws
    # rng today, so the snapshot is unchanged — this makes the contract explicit).
    a = AttackerController(attacker_num=1, rng=random.Random(0))
    f = FollowerController(attacker_num=2, rng=random.Random(0))
    snaps = run_battle(frames=TWO_NPC_FRAMES, controllers=(a, f))
    assert len(snaps) == TWO_NPC_FRAMES

    # emergent: both players are actually driven (pre-contact window, input-only)
    p1x = [s[0][0][2] for s in snaps[:20]]
    p2x = [s[0][1][2] for s in snaps[:20]]
    assert len(set(p1x)) > 1, "P1 stayed idle in the 2-NPC battle"
    assert len(set(p2x)) > 1, "P2 stayed idle in the 2-NPC battle"

    check_or_update("two_npc", snaps)
