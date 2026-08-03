# pycats/render/__init__.py
"""The battle render package (#900, child 3 of #833): the former 1400-line
`render_battle.py` split into focused submodules —

  - `body`   — the cat sprite composite, its per-look cache, silhouette ring, idle
               breathing, and the Verlet-tail renderer;
  - `tint`   — per-frame body-flash overlay selection + blending;
  - `status` — the dizzy-star / timer-bar / grabs-left drawing;
  - `hud`    — the battle HUD, controls, input-history, and shell chrome;
  - `debug`  — the hit/hurtbox debug overlay;
  - `battle` — the top-level `render_battle` / `render_attacks` draw entry points.

The pure (pygame-free) status model — `timer_bar_specs`, `grabs_left_dots`, and the
`STATUS_SOURCES` table — moved down to `pycats.systems.status_model`.

This `__init__` re-exports the full former `render_battle` surface (public names
plus the privates and module-level caches that tests and the render-isolation
fixture reach into), so `from pycats.render import X` and the thin
`pycats/render_battle.py` shim both expose exactly what the module did before.
"""

# Public names (star-import skips underscore-prefixed names) --------------------
# The pure status model, re-surfaced so `render.timer_bar_specs` etc. resolve as
# they did when these lived in render_battle.
from ..systems.status_model import (  # noqa: F401
    _GETUP_ATTACK_FRAMES,
    _SHIELD_RECENCY_KEY,
    CHARGE_BAR_COLOR,
    DIZZY_BAR_COLOR,
    DOWN_BAR_COLOR,
    INTANGIBLE_BAR_COLOR,
    LOCKOUT_BAR_COLOR,
    RECHARGE_BAR_COLOR,
    SHIELD_BAR_COLOR,
    STATUS_SOURCES,
    StatusSource,
    TimerBar,
    _bar_for,
    _intangible_remaining_max,
    _secs,
    grabs_left_dots,
    timer_bar_specs,
)
from .battle import *  # noqa: F401,F403

# Private names + module-level caches the test suite / render_isolation reach into.
from .battle import _CROUCH_ANIM_RATE, _attack_surface  # noqa: F401
from .body import *  # noqa: F401,F403
from .body import (  # noqa: F401
    _BODY_PAD_BOT,
    _BODY_PAD_TOP,
    _BODY_PAD_X,
    _IDLE_BREATH_PERIOD_FRAMES,
    _NALIO_BREATHS_PER_LOOP,
    _NALIO_WAIT1_LOOP_FRAMES,
    _body_cache,
    _body_cache_key,
    _body_layers_cache,
    _cat_body_layers,
    _cat_body_surface,
    _CatShim,
    _dilated_silhouette,
    _draw_body_features,
    _tail_outline_cache,
    _tail_seg_cache,
)
from .debug import *  # noqa: F401,F403
from .debug import _active_hurtbox  # noqa: F401
from .hud import *  # noqa: F401,F403
from .status import *  # noqa: F401,F403
from .status import _STAR_HALO, _star_points  # noqa: F401
from .tint import *  # noqa: F401,F403
from .tint import _blend  # noqa: F401
