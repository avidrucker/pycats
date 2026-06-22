# tests/test_smoke.py
def test_imports_headless():
    import pygame
    import statecharts
    surf = pygame.Surface((10, 10))
    assert surf.get_size() == (10, 10)
    assert hasattr(statecharts, "Session")
