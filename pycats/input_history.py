"""Per-fighter rolling input-history buffer (#21).

Pure, pygame-free. Records the last up-to-``INPUT_HISTORY_MAX`` raw input
events a player pressed, each entry auto-expiring ``INPUT_HISTORY_TTL_FRAMES``
frames after it was logged. Fed on the *press-edge* (``InputFrame.pressed``,
not ``held``) so holding a key does not re-log; simultaneous new-presses in one
frame join into a single entry (e.g. up+attack -> ``"↑A"``). Directions are
ABSOLUTE — ``→`` always means physical right, independent of fighter facing.

The HUD render (``render_battle.draw_input_history``) and the Options
``show_input_history`` toggle consume this; the buffer itself owns no pygame.
"""

from pycats.config import FPS

INPUT_HISTORY_MAX = 10
INPUT_HISTORY_TTL_FRAMES = 5 * FPS  # entries disappear 5s after they were logged
INPUT_HISTORY_SEP = " · "  # between-entry separator on the HUD strip

# control-name -> glyph, in canonical join order (directions before buttons).
# ``glyphs_for_frame`` walks this list, so a frame's joined entry is always
# ordered the same way regardless of set iteration order.
_GLYPHS = (
    ("up", "↑"),
    ("down", "↓"),
    ("left", "←"),
    ("right", "→"),
    ("attack", "A"),
    ("special", "B"),
    ("shield", "S"),
)


def glyphs_for_frame(pressed, controls):
    """Map this frame's just-pressed keycodes to a joined glyph string.

    ``pressed`` is a set of pygame keycodes (``InputFrame.pressed``);
    ``controls`` maps control-name -> keycode (a fighter's ``controls`` dict).
    Returns ``""`` when no relevant control was newly pressed this frame.
    """
    out = []
    for name, glyph in _GLYPHS:
        code = controls.get(name)
        if code is not None and code in pressed:
            out.append(glyph)
    return "".join(out)


def format_line(label, entries, sep=INPUT_HISTORY_SEP):
    """The HUD strip text: ``"<label> Inputs: <e0> · <e1> · ..."`` (oldest->newest).

    Pure so the wording is unit-testable; the pixel draw is golden-covered.
    """
    return f"{label} Inputs: " + sep.join(entries)


class InputHistory:
    """A capped, per-entry-TTL ring of recent input glyph strings."""

    def __init__(self, max_entries=INPUT_HISTORY_MAX, ttl_frames=INPUT_HISTORY_TTL_FRAMES):
        self._max = max_entries
        self._ttl = ttl_frames
        self._entries = []  # list of [glyphs, remaining_frames]

    def push(self, glyphs):
        """Append a fresh entry (full TTL); no-op on empty. Caps at max, oldest out."""
        if not glyphs:
            return
        self._entries.append([glyphs, self._ttl])
        if len(self._entries) > self._max:
            del self._entries[0]

    def tick(self, frames=1):
        """Age every entry; drop those whose TTL has run out."""
        for entry in self._entries:
            entry[1] -= frames
        self._entries = [e for e in self._entries if e[1] > 0]

    def record(self, pressed, controls):
        """One frame: age existing entries, then push this frame's new presses.

        Ticks first so a freshly-pushed entry keeps its full TTL this frame.
        """
        self.tick()
        self.push(glyphs_for_frame(pressed, controls))

    def entries(self):
        """Current glyph strings, oldest -> newest."""
        return [entry[0] for entry in self._entries]
