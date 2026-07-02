"""Per-fighter rolling input-history buffer (#21).

Pure, pygame-free logic: records the last up-to-10 raw input events a player
pressed (on the press-edge), each entry decaying 5s (300 frames @ 60 FPS) after
it was logged. Simultaneous new-presses in one frame join into a single entry
(e.g. up+attack -> "↑A"). Directions are ABSOLUTE (right always = physical
right, independent of facing). The HUD render + Options toggle are exercised
elsewhere (test_battle_screen_render / a runtime_settings toggle test).
"""
from pycats.input_history import (
    InputHistory,
    glyphs_for_frame,
    format_line,
    INPUT_HISTORY_MAX,
    INPUT_HISTORY_TTL_FRAMES,
)

# A minimal controls dict shaped like game.P1_KEYS (name -> pygame keycode).
CONTROLS = {
    "left": 1,
    "right": 2,
    "up": 3,
    "down": 4,
    "attack": 5,
    "special": 6,
    "shield": 7,
}


# --------------------------------------------------------------------------- #
# glyphs_for_frame — keycode set + controls -> joined glyph string
# --------------------------------------------------------------------------- #
def test_glyphs_single_direction():
    assert glyphs_for_frame({3}, CONTROLS) == "↑"


def test_glyphs_single_button():
    assert glyphs_for_frame({5}, CONTROLS) == "A"
    assert glyphs_for_frame({6}, CONTROLS) == "B"
    assert glyphs_for_frame({7}, CONTROLS) == "S"


def test_glyphs_absolute_arrows():
    assert glyphs_for_frame({1}, CONTROLS) == "←"
    assert glyphs_for_frame({2}, CONTROLS) == "→"
    assert glyphs_for_frame({4}, CONTROLS) == "↓"


def test_glyphs_simultaneous_join_in_canonical_order():
    # up + attack pressed the same frame -> one joined entry, direction first
    assert glyphs_for_frame({3, 5}, CONTROLS) == "↑A"
    # order is stable regardless of set iteration: down + special + shield
    assert glyphs_for_frame({6, 4, 7}, CONTROLS) == "↓BS"


def test_glyphs_empty_when_no_relevant_press():
    assert glyphs_for_frame(set(), CONTROLS) == ""


def test_glyphs_ignores_keys_outside_controls():
    # keycode 99 belongs to the other player / unrelated key
    assert glyphs_for_frame({99}, CONTROLS) == ""
    assert glyphs_for_frame({99, 5}, CONTROLS) == "A"


# --------------------------------------------------------------------------- #
# InputHistory — ring buffer with per-entry TTL
# --------------------------------------------------------------------------- #
def test_push_records_oldest_to_newest():
    h = InputHistory()
    h.push("↑")
    h.push("A")
    assert h.entries() == ["↑", "A"]


def test_push_ignores_empty():
    h = InputHistory()
    h.push("")
    assert h.entries() == []


def test_cap_drops_oldest_beyond_max():
    h = InputHistory(max_entries=3)
    for g in ["1", "2", "3", "4"]:
        h.push(g)
    assert h.entries() == ["2", "3", "4"]


def test_tick_expires_entry_after_ttl():
    h = InputHistory(ttl_frames=3)
    h.push("A")
    h.tick()  # 2 left
    h.tick()  # 1 left
    assert h.entries() == ["A"]
    h.tick()  # 0 -> expired
    assert h.entries() == []


def test_record_ticks_existing_then_pushes_fresh():
    h = InputHistory(ttl_frames=2)
    h.record({5}, CONTROLS)          # frame 1: push "A" (ttl 2)
    h.record(set(), CONTROLS)        # frame 2: tick A -> 1, no new press
    assert h.entries() == ["A"]
    h.record(set(), CONTROLS)        # frame 3: tick A -> 0, expired
    assert h.entries() == []


def test_record_fresh_entry_survives_full_ttl():
    h = InputHistory(ttl_frames=2)
    h.record({5}, CONTROLS)          # push "A" this frame; not decremented same frame
    assert h.entries() == ["A"]


def test_config_constants_wired():
    from pycats.config import FPS
    assert INPUT_HISTORY_TTL_FRAMES == 5 * FPS
    assert INPUT_HISTORY_MAX == 10


# --------------------------------------------------------------------------- #
# format_line — presentation string (pure; the pixel draw is golden-covered)
# --------------------------------------------------------------------------- #
def test_format_line_joins_entries_with_separator():
    assert format_line("P1", ["↑", "A", "↑A"]) == "P1 Inputs: ↑ · A · ↑A"


def test_format_line_empty_buffer():
    assert format_line("P2", []) == "P2 Inputs: "
