# tests/test_render_battle.py
import pytest
import pygame
import pycats.entities.tail
from pycats.sim.runner import build_stage, build_players
from pycats.render_battle import render_battle

# Re-init font + clear stale render/font caches before each test so a prior
# test's pygame.quit() can't break rendering (#63).
pytestmark = pytest.mark.usefixtures("render_isolation")


def test_render_battle_draws_without_error():
    surface = pygame.Surface((960, 540))
    platforms = build_stage()
    p1, p2, players = build_players()
    # advance one frame so players have valid rects/tails
    from pycats.core.input import InputFrame
    empty = InputFrame(held=set(), pressed=set(), released=set())
    for p in players:
        p.update(empty, platforms, pygame.sprite.Group())
    render_battle(surface, players, platforms)  # must not raise
    assert surface.get_at((0, 0)) is not None


def test_tail_entity_does_not_import_the_render_adapter():
    """#265 (H-a): the render layer is an ADAPTER over the entities; the
    dependency must point adapter→entity, never entity→adapter. `entities/tail.py`
    must not import `render_battle` (it used to, for `tinted`; the tint is now
    passed in by the caller). Able-to-fail: re-adding the import reds this."""
    import ast
    import pathlib

    tail_src = pathlib.Path(pycats.entities.tail.__file__).read_text(encoding="utf-8")
    tree = ast.parse(tail_src)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("render_battle"):
            offenders.append(f"line {node.lineno}: from {'.' * node.level}{node.module} import ...")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("render_battle"):
                    offenders.append(f"line {node.lineno}: import {alias.name}")
    assert offenders == [], (
        "entities/tail.py imports the render adapter (layering inversion, #265):\n"
        + "\n".join(offenders)
    )


def test_platform_renders_thickness_colour_pixels():
    """#317/H-b slice 1: render_battle paints each platform its thickness colour
    (thick (164,113,73) / thin (193,153,112)). Guards the Surface -> draw.rect
    extraction — able-to-fail if the colour mapping or the rect draw is wrong."""
    from pycats.config import SCREEN_WIDTH, SCREEN_HEIGHT
    plats = build_stage()
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf.fill((0, 0, 0))
    render_battle(surf, [], plats)
    thick = next(p for p in plats if not p.thin)
    thin = next(p for p in plats if p.thin)
    assert surf.get_at(thick.rect.center)[:3] == (164, 113, 73)
    assert surf.get_at(thin.rect.center)[:3] == (193, 153, 112)


def test_tail_entity_is_pygame_free():
    """#330/H-b slice 3: with rendering moved to render_battle.render_tail,
    entities/tail.py is pure Verlet sim — it imports no pygame. Able-to-fail:
    re-add `import pygame` and this reds."""
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(pycats.entities.tail.__file__).read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offenders += [a.name for a in node.names if a.name.split(".")[0] == "pygame"]
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pygame":
            offenders.append(node.module)
    assert offenders == [], f"tail.py imports pygame: {offenders}"
