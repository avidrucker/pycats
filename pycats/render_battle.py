# pycats/render_battle.py
"""Backward-compatible shim (#900, child 3 of #833).

The battle renderer was split into the `pycats.render` package (body / tint /
status / hud / debug / battle) with its pure status model in
`pycats.systems.status_model`. This module re-exports the full former surface so
every existing `from pycats.render_battle import X` and `render_battle.X` keeps
resolving unchanged — including the private helpers and module-level caches the
test suite and the `render_isolation` fixture reach into.

Import from `pycats.render` (or the focused submodules) in new code.
"""

from pycats.render import *  # noqa: F401,F403

# Private names + caches (star-import skips underscore-prefixed names).
from pycats.render import (  # noqa: F401
    _BODY_PAD_BOT,
    _BODY_PAD_TOP,
    _BODY_PAD_X,
    _CROUCH_ANIM_RATE,
    _GETUP_ATTACK_FRAMES,
    _IDLE_BREATH_PERIOD_FRAMES,
    _NALIO_BREATHS_PER_LOOP,
    _NALIO_WAIT1_LOOP_FRAMES,
    _SHIELD_RECENCY_KEY,
    _STAR_HALO,
    _active_hurtbox,
    _attack_surface,
    _attack_surface_cache,
    _attack_surface_key,
    _bar_for,
    _blend,
    _body_cache,
    _body_cache_key,
    _body_layers_cache,
    _body_scaled_cache,
    _build_attack_surface,
    _cat_body_layers,
    _cat_body_layers_scaled,
    _cat_body_surface,
    _CatShim,
    _dilated_silhouette,
    _draw_body_features,
    _intangible_remaining_max,
    _secs,
    _shield_bubble,
    _shield_bubble_cache,
    _star_points,
    _tail_outline_cache,
    _tail_seg_cache,
)
