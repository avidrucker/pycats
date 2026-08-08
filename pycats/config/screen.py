"""Screen dimensions + framerate — the foundational constants every other config
submodule (stage geometry, render positions) derives from. No sibling imports."""

SCREEN_WIDTH, SCREEN_HEIGHT = 960, 540
FPS = 60


def tick_fps(speed: float) -> int:
    """Display tick target at `speed`. 0.5 -> 30 (each frame dwells ~2x as long on
    screen), 0.25 -> 15. Clamped to >= 1. Slow-motion is presentation-only: the sim is
    fixed-timestep (#166/#80), so this paces the DISPLAY of already-computed frames and
    never the sim itself. Shared by the sim presenters (#351) and the live game (#932)."""
    return max(1, round(FPS * speed))
