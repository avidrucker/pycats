"""Selectable cat-face render styles (#108/#114). The cycle/label logic is pure;
the render helper is exercised headlessly (returns a sized Surface or None).

#114 retired the kaomoji/emoji glyph styles (sideways `ᓚᘏᗢ`, front `(=^･ω･^=)`,
emoji `🐱`) and replaced them with the pure-ASCII #110 heads: a profile head
(flipped per facing) and a 3/4 head, drawn by a multi-line monospace block
renderer that falls back to primitives when no monospace font is available.
"""
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


def test_face_styles_are_exactly_primitives_profile_34():
    # #114 acceptance: no kaomoji/emoji styles remain in the cycle or in code.
    assert cat_faces.FACE_STYLES == ("primitives", "profile", "3/4")
    for retired in ("SIDEWAYS", "FRONT", "EMOJI"):
        assert not hasattr(cat_faces, retired), f"{retired} should be gone (#114)"


def test_face_style_label_is_bounds_safe():
    assert cat_faces.face_style_label(cat_faces.PRIMITIVES) == "primitives"
    assert cat_faces.face_style_label(cat_faces.ASCII_PROFILE) == "profile"
    assert cat_faces.face_style_label(cat_faces.ASCII_34) == "3/4"
    assert cat_faces.face_style_label(999) == "primitives"  # out of range -> default


def test_ink_for_contrasts_with_the_body():
    assert cat_faces.ink_for((255, 160, 64))[0] < 60   # light cat -> dark ink
    assert cat_faces.ink_for((20, 20, 20))[0] > 200     # dark (void) cat -> light ink


def test_render_face_primitives_and_unknown_are_none():
    assert cat_faces.render_face(cat_faces.PRIMITIVES, True, (255, 160, 64)) is None
    assert cat_faces.render_face(999, True, (255, 160, 64)) is None


def test_render_face_profile_returns_sized_surface():
    pygame.init()
    pygame.display.set_mode((1, 1))
    surf = cat_faces.render_face(cat_faces.ASCII_PROFILE, True, (255, 160, 64))
    assert surf is not None
    assert surf.get_width() == cat_faces._FACE_W  # scaled to the face width


def test_render_face_34_returns_sized_surface():
    pygame.init()
    pygame.display.set_mode((1, 1))
    surf = cat_faces.render_face(cat_faces.ASCII_34, True, (255, 160, 64))
    assert surf is not None
    assert surf.get_width() == cat_faces._FACE_W


def test_render_face_profile_flips_with_facing():
    pygame.init()
    pygame.display.set_mode((1, 1))
    right = cat_faces.render_face(cat_faces.ASCII_PROFILE, True, (255, 160, 64))
    left = cat_faces.render_face(cat_faces.ASCII_PROFILE, False, (255, 160, 64))
    assert right is not None and left is not None
    assert right.get_size() == left.get_size()  # same head, mirrored
    # The flip must actually mirror pixels — not just return the same surface.
    assert pygame.image.tobytes(right, "RGBA") != pygame.image.tobytes(left, "RGBA")


def test_render_face_34_does_not_flip_with_facing():
    pygame.init()
    pygame.display.set_mode((1, 1))
    right = cat_faces.render_face(cat_faces.ASCII_34, True, (255, 160, 64))
    left = cat_faces.render_face(cat_faces.ASCII_34, False, (255, 160, 64))
    assert pygame.image.tobytes(right, "RGBA") == pygame.image.tobytes(left, "RGBA")


def test_render_face_falls_back_to_primitives_without_a_monospace_font(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    # No monospace font available -> render_face returns None -> caller draws
    # the primitive face (#114 acceptance).
    monkeypatch.setattr(cat_faces, "_mono_font", lambda size: None)
    assert cat_faces.render_face(cat_faces.ASCII_PROFILE, True, (255, 160, 64)) is None
    assert cat_faces.render_face(cat_faces.ASCII_34, True, (255, 160, 64)) is None
