"""Per-fighter rolling input-history buffer (#21, regridded #875).

Pure, pygame-free. Records the last up-to-``INPUT_HISTORY_FRAMES`` raw input
frames a player produced. Each frame stores, per mapped control, whether it was
*pressed* this frame (the rising edge, ``InputFrame.pressed``) or merely *held*
(down but not a fresh edge, ``InputFrame.held``). Keeping per-frame press-vs-held
marks — instead of #21's press-edge-only joined glyphs — lets the HUD grid tell a
same-frame combo from a sequential press and from a held-while-pressed one (#875:
``A+↑`` same frame vs ``A`` then ``↑`` vs hold-``A``-then-press-``↑`` were
indistinguishable on the old one-line strip). Directions are ABSOLUTE — ``→``
always means physical right, independent of fighter facing.

The HUD render (``render_battle.draw_input_history``) and the Options
``show_input_history`` toggle consume this; the buffer itself owns no pygame.
"""

INPUT_HISTORY_FRAMES = 16  # grid width: most-recent this-many frames (newest on the right)

# Per-control mark for one frame. PRESSED (rising edge) outranks HELD when a key
# is both — a fresh key is in ``.held`` too, but the grid should show its edge.
PRESSED = "pressed"
HELD = "held"

# control-name -> glyph, in canonical row order (directions before buttons).
# ``frame_marks`` and the grid render walk this list, so rows are always ordered
# the same way regardless of set iteration order.
_GLYPHS = (
    ("up", "↑"),
    ("down", "↓"),
    ("left", "←"),
    ("right", "→"),
    ("attack", "A"),
    ("special", "B"),
    ("shield", "S"),
)


def frame_marks(pressed, held, controls):
    """Map one frame's keycodes to ``{control-name: PRESSED | HELD}``.

    ``pressed`` / ``held`` are sets of pygame keycodes (``InputFrame.pressed`` /
    ``.held``); ``controls`` maps control-name -> keycode (a fighter's ``controls``
    dict). A control in ``pressed`` marks ``PRESSED`` (the rising edge wins even
    though a fresh key is in ``held`` too); a control only in ``held`` marks
    ``HELD``. Controls with no activity are absent. Returns ``{}`` for an idle
    frame.
    """
    marks = {}
    for name, _glyph in _GLYPHS:
        code = controls.get(name)
        if code is None:
            continue
        if code in pressed:
            marks[name] = PRESSED
        elif code in held:
            marks[name] = HELD
    return marks


class InputHistory:
    """A rolling window of the last N frames' per-control marks (oldest->newest)."""

    def __init__(self, frames=INPUT_HISTORY_FRAMES):
        self._n = frames
        self._frames = []  # list of {control-name: PRESSED | HELD}, oldest -> newest

    def record(self, pressed, held, controls):
        """Append this frame's marks; drop the oldest once the window is full.

        Idle frames (no mapped control down) are recorded as empty ``{}`` columns
        so a gap between presses stays visible in the grid.
        """
        self._frames.append(frame_marks(pressed, held, controls))
        if len(self._frames) > self._n:
            del self._frames[0]

    def frames(self):
        """The recorded frames' marks, oldest -> newest."""
        return list(self._frames)
