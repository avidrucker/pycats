"""Selectable cat-face render styles (#108). The cycle/label logic is pure; the
render helper is exercised headlessly (returns a sized Surface or None)."""
import pygame

from pycats import cat_faces


def test_cycle_face_style_wraps_through_all_styles():
    seen = []
    idx = 0
    for _ in range(len(cat_faces.FACE_STYLES)):
        seen.append(idx)
        idx = cat_faces.cycle_face_style(idx)
    assert seen == list(range(len(cat_faces.FACE_STYLES)))
    assert idx == 0  # wrapped back to the start


def test_face_style_label_is_bounds_safe():
    assert cat_faces.face_style_label(cat_faces.PRIMITIVES) == "primitives"
    assert cat_faces.face_style_label(cat_faces.SIDEWAYS) == "sideways"
    assert cat_faces.face_style_label(999) == "primitives"  # out of range -> default


def test_ink_for_contrasts_with_the_body():
    assert cat_faces.ink_for((255, 160, 64))[0] < 60   # light cat -> dark ink
    assert cat_faces.ink_for((20, 20, 20))[0] > 200     # dark (void) cat -> light ink


def test_render_face_primitives_and_unknown_are_none():
    assert cat_faces.render_face(cat_faces.PRIMITIVES, True, (255, 160, 64)) is None
    assert cat_faces.render_face(999, True, (255, 160, 64)) is None


def test_render_face_front_kaomoji_returns_sized_surface():
    pygame.init()
    pygame.display.set_mode((1, 1))
    surf = cat_faces.render_face(cat_faces.FRONT, True, (255, 160, 64))
    assert surf is not None
    assert surf.get_width() == cat_faces._FACE_W  # scaled to the face width


def test_render_face_sideways_flips_with_facing():
    pygame.init()
    pygame.display.set_mode((1, 1))
    right = cat_faces.render_face(cat_faces.SIDEWAYS, True, (255, 160, 64))
    left = cat_faces.render_face(cat_faces.SIDEWAYS, False, (255, 160, 64))
    assert right is not None and left is not None
    assert right.get_size() == left.get_size()  # same glyph, mirrored
