"""Options 'Input History' toggle retired (#1328).

Shipped in #21 as a persisted, default-ON toggle mirroring show_status_timer_bars, then
made a battle no-op in #1319 when dev_hud became the sole battle-HUD driver. #1328 removes
the persisted key, the runtime accessor, and the Options row entirely. The input-history
grid itself still renders as part of the dev HUD (gated on dev_hud); its capture + render
are covered by test_input_history_capture / test_input_history_render.

Able-to-fail: re-add the setting / accessor / row and each assertion below flips.
"""

import pygame  # noqa: E402

from pycats.screens.options_menu import ROW_DESCRIPTIONS, OptionsMenu  # noqa: E402
from pycats.storage import runtime_settings, settings  # noqa: E402

_P1 = dict(
    left=pygame.K_a,
    right=pygame.K_d,
    up=pygame.K_w,
    down=pygame.K_s,
    attack=pygame.K_v,
    special=pygame.K_c,
    shield=pygame.K_x,
)
_P2 = dict(
    left=pygame.K_LEFT,
    right=pygame.K_RIGHT,
    up=pygame.K_UP,
    down=pygame.K_DOWN,
    attack=pygame.K_PERIOD,
    special=pygame.K_SLASH,
    shield=pygame.K_RSHIFT,
)


def test_show_input_history_setting_retired():
    assert "show_input_history" not in settings.defaults()
    assert not hasattr(runtime_settings, "show_input_history")


def test_input_history_row_absent_from_options():
    m = OptionsMenu(_P1, _P2)
    assert "input_history" not in m.rows
    assert "input_history" not in ROW_DESCRIPTIONS
