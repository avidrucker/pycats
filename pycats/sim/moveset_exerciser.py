"""Computer-driven moveset exerciser (#1203).

Drive every canonical move of every roster character through the REAL input seam
(`Player.handle_actions`) and report which canonical moves never activate — so an
unimplemented or unwired move surfaces as a printed line instead of going
unnoticed in play.

Run it::

    python -m pycats.sim.moveset_exerciser

It prints, per character, the canonical move keys that do not activate (with a
readable gloss) plus a per-character and total tally.

Design (the three things the ticket pins):

  1. The move-key list is DERIVED from `move_select` — the single source. We walk
     ``direction × ground/air × A/B/smash`` through `select_move_key` and collect
     one representative input context per canonical key. There is no hand-copied
     second catalog to drift.

  2. "Missing" = the canonical move does not activate when its input is driven —
     checked against the CANONICAL key, never `resolve_move_key` (which falls back:
     a missing ``usmash`` resolves to ``ftilt``/the ``attack`` alias, an undefined
     special resolves to ``None``). Driving a fallback activates a DIFFERENT move
     object than the canonical one, so the canonical key still reads missing.

  3. Detection is driven, not a static ``.moves``-dict read: `probe_move` presses
     the input through `handle_actions` and observes activation three ways — the
     MoveClock started the canonical `MoveData` (normal / recovery / a charged
     smash after it fires), the fighter began CHARGING the canonical key
     (`pending_charge_key`), or a counter special armed its detect stance
     (`counter_timer`; Narz's down-B never runs on the clock).

Input encoding note: the DIRECTION is HELD (not freshly pressed) and the BUTTON is
pressed. A freshly-pressed ``up`` is a jump and a freshly-pressed left/right can
arm a dash — holding the direction and pressing only the button reproduces a real
tilt/smash input and reaches the attack seam cleanly.

Out of scope (see the ticket): move *correctness* (hitbox/damage/knockback values
— that is the per-move authoring epic #1117 and the datamine wayfinder #1147), the
hollow-move / present-but-empty check, any change to `resolve_move_key`'s
fallback, and rendering. This is a headless terminal diagnostic.
"""

from __future__ import annotations

import os
import sys

from ..characters.roster import ARCHETYPE_ROSTER
from ..combat.data import FighterData, load_fighter_data
from ..combat.move_select import select_move_key

# Direction tokens select_move_key understands, in select precedence order.
_DIRECTIONS = ("neutral", "up", "down", "forward", "back")


def canonical_contexts() -> dict[str, tuple[str, str | None, bool]]:
    """Map each canonical move key -> one representative input context that
    `select_move_key` maps TO it: ``(button, direction_token_or_None, on_ground)``
    where button is ``"attack"`` / ``"special"`` / ``"smash"`` and the direction
    token is ``None`` for neutral. Derived by walking `move_select`, so the key set
    is exactly what the seam can select — no second copy.

    ``forward``/``back`` collapse to ``ftilt`` on the ground (Smash has no b-tilt),
    so the first context to yield a key wins; ground normals are visited before
    aerials, then specials, then smashes.
    """
    contexts: dict[str, tuple[str, str | None, bool]] = {}
    for on_ground in (True, False):
        for direction in _DIRECTIONS:
            key = select_move_key(direction, on_ground, is_special=False, is_smash=False)
            contexts.setdefault(key, ("attack", _dir_token(direction), on_ground))
    for direction in _DIRECTIONS:
        key = select_move_key(direction, on_ground=True, is_special=True, is_smash=False)
        contexts.setdefault(key, ("special", _dir_token(direction), True))
    for direction in _DIRECTIONS:  # smashes are ground-only
        key = select_move_key(direction, on_ground=True, is_special=False, is_smash=True)
        contexts.setdefault(key, ("smash", _dir_token(direction), True))
    return contexts


def _dir_token(direction: str) -> str | None:
    """Neutral holds no arrow; every other token holds one."""
    return None if direction == "neutral" else direction


# Which control-map action holds each direction token (facing right: forward =
# right, back = left). The exerciser always builds a right-facing fighter.
_ARROW_ACTION = {"up": "up", "down": "down", "forward": "right", "back": "left"}

# Readable gloss for the report — generated from the context, not a hand catalog.
_SLOT = {"attack_ground": "tilt", "attack_air": "aerial", "special": "special", "smash": "smash"}


def _ensure_pygame():
    """Import pygame under headless SDL drivers and init it once. Kept lazy so
    importing this module never forces a display."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame as pg

    if not pg.get_init():
        pg.init()
    return pg


def probe_move(character: str, key: str, *, fighter_data: FighterData | None = None) -> bool:
    """Drive ``character``'s input for canonical ``key`` once through
    `Player.handle_actions` and return whether that canonical move activated.

    ``fighter_data`` overrides the loaded kit (used to prove detection is driven —
    unwire a move and it stops activating). A key absent from the kit can never
    activate (specials have no fallback; a fallback move is a different object), so
    it returns False.
    """
    pg = _ensure_pygame()
    from ..config import P1_COLOR, WHITE
    from ..core.input import InputFrame
    from ..entities.player import Player

    button, dir_token, on_ground = canonical_contexts()[key]
    fd = fighter_data if fighter_data is not None else load_fighter_data(character)

    controls = {
        "left": pg.K_a,
        "right": pg.K_d,
        "up": pg.K_w,
        "down": pg.K_s,
        "shield": pg.K_q,
        "attack": pg.K_e,
        "special": pg.K_c,
        "smash": pg.K_x,
    }
    player = Player(
        x=100,
        y=100,
        controls=controls,
        color=P1_COLOR,
        eye_color=WHITE,
        char_name=character,
        facing_right=True,
        fighter_data=fd,
    )
    player.fighter.on_ground = on_ground

    button_code = controls[button]
    held = {button_code}
    if dir_token is not None:
        held.add(controls[_ARROW_ACTION[dir_token]])
    frame = InputFrame(held=set(held), pressed={button_code}, released=set())
    player.handle_actions(frame, pg.sprite.Group())

    return _activated(player, key)


def _activated(player, key: str) -> bool:
    """True when driving the input committed the CANONICAL move. Three activation
    paths: the MoveClock is running the canonical MoveData; the fighter began
    charging the canonical key (smashes / chargeable specials); or a counter
    special armed its detect stance (it never runs on the clock)."""
    move = player.fighter_data.moves.get(key)
    if move is None:
        return False
    if player._clock.move is move:  # normal / recovery / a smash after full charge fires
        return True
    if getattr(player.fighter, "pending_charge_key", None) == key:  # charging the canonical move
        return True
    if getattr(move, "is_counter", False) and getattr(player.fighter, "counter_timer", 0) > 0:
        return True
    return False


def missing_moves(character: str, *, fighter_data: FighterData | None = None) -> list[str]:
    """The canonical move keys that do not activate for ``character``, sorted."""
    fd = fighter_data if fighter_data is not None else load_fighter_data(character)
    missing = [key for key in canonical_contexts() if not probe_move(character, key, fighter_data=fd)]
    return sorted(missing)


def exercise(roster=ARCHETYPE_ROSTER) -> dict[str, list[str]]:
    """Run the exerciser over the whole roster -> ``{character: [missing keys]}``."""
    return {name: missing_moves(name) for name in roster}


def _gloss(key: str) -> str:
    """A readable name for a canonical key, generated from its input context
    (e.g. ``side_b`` -> "forward special", ``dtilt`` -> "down tilt")."""
    button, dir_token, on_ground = canonical_contexts()[key]
    if key == "jab":
        return "jab"
    if button == "attack":
        slot = _SLOT["attack_ground" if on_ground else "attack_air"]
    else:
        slot = _SLOT[button]
    direction = dir_token or "neutral"
    return f"{direction} {slot}"


def format_report(results: dict[str, list[str]]) -> str:
    """A terminal report: one line per character listing its missing moves with a
    gloss, plus a per-character and total tally. A complete kit prints a clean line.
    """
    lines: list[str] = []
    total = 0
    for name in results:
        missing = results[name]
        total += len(missing)
        if missing:
            listed = ", ".join(f"{key} ({_gloss(key)})" for key in missing)
            lines.append(f"{name}: missing {len(missing)} — {listed}")
        else:
            lines.append(f"{name}: complete kit — no missing moves")
    lines.append(f"total missing across {len(results)} characters: {total}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Print the moveset report for the whole roster. Returns 0 (the report is a
    diagnostic — a nonzero exit is reserved for a future strict mode)."""
    _ensure_pygame()
    results = exercise()
    print(format_report(results))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
