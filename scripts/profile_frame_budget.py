"""Headed-frame CPU budget + cost-localization harness for #1077 (RESEARCH).

Measures the per-phase per-frame CPU cost of the live BATTLE render, plus a
cProfile attribution of the render phase, across a render-stressing scenario
matrix. Deterministic (seeded AttackerControllers, fixed-timestep sim), so runs
are comparable.

IMPORTANT — what this does and does NOT measure:
  * Runs under SDL_VIDEODRIVER=dummy: every draw call, blit, font.render, and
    per-frame Surface alloc EXECUTES identically to a real window, so the RENDER
    (CPU) phase is faithful. What is NOT captured: DisplayManager.present() cost
    (the scale-blit + pygame.display.flip()/vsync), which only exists with a real
    display. Window-size / fullscreen cost lives ENTIRELY in present() because the
    game draws to a fixed 960x540 logical surface and present() scales it. So the
    numbers below are a resolution-INDEPENDENT CPU-render budget; the headed
    present/flip delta must be measured on a real display (see the findings doc).

Phases timed (perf_counter, ms): SIM = BattleScreen.step; RENDER = battle.render
+ draw_shell_chrome + render_esc_quit_progress (exactly render_active_screen's
"playing" branch). PRESENT (scale-blit) is benchmarked separately.

Two modes:
  * default (no arg): HEADLESS under SDL dummy — the render-CPU scenario matrix,
    cProfile attribution, render_attacks(N), and the present scale-blit CPU bench.
  * --headed: opens a REAL window (needs a display) and measures the true per-frame
    wall time (sim + render + scale + flip) at windowed-1x / windowed-2x / fullscreen,
    plus a direct vsync-on/off flip probe. This is the piece dummy cannot measure.

Usage:
  <main-venv-python> profile_frame_budget.py            # headless suite
  <main-venv-python> profile_frame_budget.py --headed   # opens real windows
"""

# ruff: noqa: E402  — SDL_VIDEODRIVER must be set before `import pygame`, so the
# env-setup block below intentionally precedes the module imports.
import os
import sys

HEADED = "--headed" in sys.argv
if not HEADED:
    # Headless suite: force dummy so every draw/blit/font.render still EXECUTES
    # identically to a real window, but no display is opened. --headed must NOT
    # set this — it needs the real SDL video driver.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import cProfile
import io
import pstats
import time
from statistics import mean

import pygame

from pycats.config import SCREEN_HEIGHT, SCREEN_WIDTH
from pycats.core.input import InputFrame, merge_frames
from pycats.entities.stages import DEFAULT_PLAYER_STAGE
from pycats.render_battle import draw_shell_chrome
from pycats.screens.battle_screen import BattleScreen
from pycats.shell.app import P1_KEYS, P2_KEYS
from pycats.sim.controllers import AttackerController
from pycats.storage import runtime_settings

EMPTY = InputFrame(held=set(), pressed=set(), released=set())


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = min(len(sorted_vals) - 1, int(round((p / 100.0) * (len(sorted_vals) - 1))))
    return sorted_vals[k]


def new_battle(p1="nalio", p2="birky"):
    b = BattleScreen(P1_KEYS, P2_KEYS)
    b.create_from_selection(p1, p2)
    return b


def make_inputs(mode, ledges):
    """Return a callable(frame, battle, platforms) -> merged InputFrame."""
    if mode == "idle":
        return lambda f, b, plats: EMPTY
    if mode == "combat":
        c1 = AttackerController(attacker_num=1)
        c2 = AttackerController(attacker_num=2)
        return lambda f, b, plats: merge_frames(
            [
                c1(b.player1, b.player2, f, b.attacks, ledges),
                c2(b.player1, b.player2, f, b.attacks, ledges),
            ]
        )
    if mode == "combat_specials":
        # enable ranged specials (fireballs / projectiles) to stress render_attacks
        moves = frozenset({"jab", "tilts", "aerials", "specials"})
        c1 = AttackerController(attacker_num=1, enabled_moves=moves)
        c2 = AttackerController(attacker_num=2, enabled_moves=moves)
        return lambda f, b, plats: merge_frames(
            [
                c1(b.player1, b.player2, f, b.attacks, ledges),
                c2(b.player1, b.player2, f, b.attacks, ledges),
            ]
        )
    raise ValueError(mode)


def render_playing(battle, surface, platforms, frame_input, fps):
    # Exactly the live "playing" render branch: battle.render + shell chrome.
    battle.render(surface, platforms)
    draw_shell_chrome(surface, fps, False, frame_input)


def run_scenario(name, input_mode, *, overlay=False, input_history=True, warmup=180, measure=600):
    runtime_settings.set("show_hitbox_overlay", overlay)
    runtime_settings.set("show_input_history", input_history)

    platforms = DEFAULT_PLAYER_STAGE.build()
    battle = new_battle()
    from pycats.entities.ledge import ledges_from_platforms

    ledges = ledges_from_platforms(platforms)
    driver = make_inputs(input_mode, ledges)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Warm caches (body layers, tail segments, font surfaces) + let combat develop.
    for f in range(warmup):
        fi = driver(f, battle, platforms)
        battle.step(fi, platforms)
        render_playing(battle, surface, platforms, fi, 60.0)

    sim_ms, render_ms = [], []
    max_attacks = 0
    for f in range(warmup, warmup + measure):
        fi = driver(f, battle, platforms)
        t0 = time.perf_counter()
        battle.step(fi, platforms)
        t1 = time.perf_counter()
        render_playing(battle, surface, platforms, fi, 60.0)
        t2 = time.perf_counter()
        sim_ms.append((t1 - t0) * 1000.0)
        render_ms.append((t2 - t1) * 1000.0)
        max_attacks = max(max_attacks, len(battle.attacks))

    r = sorted(render_ms)
    s = sorted(sim_ms)
    return {
        "name": name,
        "frames": measure,
        "max_attacks": max_attacks,
        "render_mean": mean(render_ms),
        "render_p50": pct(r, 50),
        "render_p95": pct(r, 95),
        "render_p99": pct(r, 99),
        "render_worst": r[-1],
        "sim_mean": mean(sim_ms),
        "sim_worst": s[-1],
    }


def fps_of(ms):
    return 1000.0 / ms if ms > 0 else float("inf")


def bench_present_scale():
    """Measure the CPU cost of DisplayManager.present()'s scale-blit —
    display.scale_surface(game_surface, factor) — the MEASURABLE half of the
    headed present cost (the flip/vsync half is display-bound and not here).
    A fresh 960x540 surface scaled to representative window/fullscreen sizes."""
    from pycats.shell import display

    src = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    src.fill((20, 20, 30))
    pygame.draw.circle(src, (200, 120, 80), (480, 270), 120)  # some content to scale
    factors = [1.0, 1.5, 2.0, 2.5, 3.0]
    print("\n=== present() scale-blit CPU (display.scale_surface, 960x540 source) ===")
    print(f"{'scale':>6} {'target':>12} {'mode':>10} {'mean_ms':>8} {'p99_ms':>7} {'fps@p99':>8}")
    for fac in factors:
        mode = display.blit_mode_for(fac)
        # warm
        for _ in range(30):
            display.scale_surface(src, fac)
        times = []
        for _ in range(300):
            t0 = time.perf_counter()
            display.scale_surface(src, fac)
            times.append((time.perf_counter() - t0) * 1000.0)
        times.sort()
        tw, th = int(SCREEN_WIDTH * fac), int(SCREEN_HEIGHT * fac)
        print(
            f"{fac:>6.2f} {f'{tw}x{th}':>12} {mode:>10} {mean(times):>8.3f} "
            f"{pct(times, 99):>7.3f} {fps_of(pct(times, 99)):>8.1f}"
        )


def bench_render_attacks_scaling():
    """render_attacks(N) cost as N projectiles rise — the 'many hitboxes /
    projectiles' scenario the controller-driven combat never reached (max 1
    simultaneous attack). Grabs one REAL spawned attack from combat, then clones
    it N times into the group (each is an independent per-frame _attack_surface
    build + blit, so the clone faithfully measures render_attacks(N))."""
    import copy

    from pycats.render_battle import render_attacks

    platforms = DEFAULT_PLAYER_STAGE.build()
    from pycats.entities.ledge import ledges_from_platforms

    ledges = ledges_from_platforms(platforms)
    battle = new_battle()
    driver = make_inputs("combat", ledges)
    template = None
    for f in range(1200):
        fi = driver(f, battle, platforms)
        battle.step(fi, platforms)
        if len(battle.attacks) >= 1:
            template = next(iter(battle.attacks))
            break
    if template is None:
        print("\n(render_attacks scaling: no attack spawned in 1200 frames — skipped)")
        return

    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    print("\n=== render_attacks(N) CPU — N cloned projectiles (per-frame surface build+blit) ===")
    print(f"{'N':>4} {'mean_ms':>8} {'p99_ms':>7} {'per_attack_us':>13}")
    for n in [0, 1, 4, 8, 16, 32, 64]:
        grp = pygame.sprite.Group()
        for i in range(n):
            c = copy.copy(template)
            c.rect = template.rect.with_center((100 + (i * 13) % 760, 80 + (i * 29) % 380))
            grp.add(c)
        for _ in range(20):
            render_attacks(surface, grp)
        times = []
        for _ in range(300):
            t0 = time.perf_counter()
            render_attacks(surface, grp)
            times.append((time.perf_counter() - t0) * 1000.0)
        times.sort()
        per = (mean(times) * 1000.0 / n) if n else 0.0
        print(f"{n:>4} {mean(times):>8.4f} {pct(times, 99):>7.4f} {per:>13.2f}")


# ------------------------------------------------------------------ HEADED
def _present_split(dm):
    """Replicate DisplayManager.present()'s body, timing the scale-blit and the
    flip separately (ms). Mirrors the real present exactly minus the zoom toast."""
    from pycats.shell import display

    t0 = time.perf_counter()
    if dm.is_fullscreen:
        dm.display_surface.fill((0, 0, 0))
        dm.display_surface.blit(display.scale_surface(dm.game_surface, dm.scale_factor), (dm.offset_x, dm.offset_y))
    elif dm.game_surface is not dm.screen:
        dm.display_surface.blit(display.scale_surface(dm.game_surface, dm.scale_factor), (0, 0))
    t1 = time.perf_counter()
    pygame.display.flip()
    t2 = time.perf_counter()
    return (t1 - t0) * 1000.0, (t2 - t1) * 1000.0


def _headed_mode(dm, label, *, input_mode="combat", warmup=120, measure=600):
    """Drive a real window one frame at a time (UNCAPPED — no clock.tick, so the
    true achievable per-frame time shows) and time sim / render / scale / flip."""
    from pycats.entities.ledge import ledges_from_platforms

    runtime_settings.set("show_hitbox_overlay", False)
    runtime_settings.set("show_input_history", True)
    platforms = DEFAULT_PLAYER_STAGE.build()
    ledges = ledges_from_platforms(platforms)
    battle = new_battle()
    driver = make_inputs(input_mode, ledges)

    for f in range(warmup):
        fi = driver(f, battle, platforms)
        battle.step(fi, platforms)
        render_playing(battle, dm.render_surface(), platforms, fi, 60.0)
        _present_split(dm)

    sim_ms, ren_ms, scale_ms, flip_ms, total_ms = [], [], [], [], []
    for f in range(warmup, warmup + measure):
        pygame.event.pump()  # keep the WM happy
        fi = driver(f, battle, platforms)
        a = time.perf_counter()
        battle.step(fi, platforms)
        b = time.perf_counter()
        render_playing(battle, dm.render_surface(), platforms, fi, 60.0)
        c = time.perf_counter()
        sc, fl = _present_split(dm)
        sim_ms.append((b - a) * 1000.0)
        ren_ms.append((c - b) * 1000.0)
        scale_ms.append(sc)
        flip_ms.append(fl)
        total_ms.append((b - a) * 1000.0 + (c - b) * 1000.0 + sc + fl)

    def row(name, xs):
        xs = sorted(xs)
        print(
            f"  {name:12} mean {mean(xs):7.3f}  p50 {pct(xs, 50):7.3f}  "
            f"p95 {pct(xs, 95):7.3f}  p99 {pct(xs, 99):7.3f}  worst {xs[-1]:7.3f}"
        )

    print(f"\n--- HEADED: {label} (uncapped, {measure} frames) ---")
    row("sim", sim_ms)
    row("render", ren_ms)
    row("scale-blit", scale_ms)
    row("flip", flip_ms)
    row("TOTAL", total_ms)
    tot = sorted(total_ms)
    print(f"  => achievable fps: mean {1000.0 / mean(tot):6.1f}  p99 {1000.0 / pct(tot, 99):6.1f}")


def probe_vsync():
    """Direct answer to the §6 question: does pygame.display.flip() block on the
    monitor refresh? Open a 1920x1080 window with vsync on, then off, and time
    flip() alone. If vsync blocks, mean flip ~= the refresh interval (~16.7ms@60Hz)."""
    print("\n=== VSYNC PROBE: flip() cost at 1920x1080, vsync on vs off ===")
    for vsync in (1, 0):
        try:
            scr = pygame.display.set_mode((1920, 1080), pygame.SCALED, vsync=vsync)
        except pygame.error as e:
            print(f"  vsync={vsync}: set_mode failed ({e})")
            continue
        scr.fill((10, 10, 20))
        for _ in range(30):
            pygame.event.pump()
            pygame.display.flip()
        times = []
        for i in range(180):
            pygame.event.pump()
            scr.fill((10, 10, 20 + (i % 40)))  # force a real change each frame
            t0 = time.perf_counter()
            pygame.display.flip()
            times.append((time.perf_counter() - t0) * 1000.0)
        times.sort()
        print(
            f"  vsync={vsync}: flip mean {mean(times):7.3f}ms  p50 {pct(times, 50):7.3f}  "
            f"p99 {pct(times, 99):7.3f}  (=> {1000.0 / mean(times):6.1f} fps cap)"
        )


def main_headed():
    from pycats.shell.display_manager import DisplayManager

    pygame.init()
    pygame.font.init()
    print(f"real SDL video driver: {pygame.display.get_driver()}")

    # windowed 1x (game_surface IS the window — no scale) then 2x (offscreen + upscale)
    dm = DisplayManager(windowed_scale=1.0, start_fullscreen=False)
    _headed_mode(dm, "windowed 1x (no scale)")
    dm.set_windowed_scale(2.0)
    _headed_mode(dm, "windowed 2x (upscale)")
    # fullscreen (letterboxed magnify at the monitor's largest achievable zoom)
    dm.toggle_fullscreen()
    _headed_mode(dm, f"fullscreen zoom {dm.scale_factor}x")

    probe_vsync()
    pygame.quit()


def main():
    pygame.init()
    pygame.font.init()

    scenarios = [
        ("2cat idle (history on)", "idle", dict()),
        ("2cat idle (history off)", "idle", dict(input_history=False)),
        ("2cat combat", "combat", dict()),
        ("2cat combat + overlay", "combat", dict(overlay=True)),
        ("2cat combat + specials(fireballs)", "combat_specials", dict()),
        ("2cat combat + specials + overlay", "combat_specials", dict(overlay=True)),
    ]

    rows = []
    for name, mode, kw in scenarios:
        rows.append(run_scenario(name, mode, **kw))

    print("\n=== PER-FRAME CPU BUDGET (ms) — render phase, SDL dummy (no present/flip) ===")
    print(
        f"{'scenario':42} {'atk':>3} {'r_mean':>7} {'r_p50':>6} {'r_p95':>6} "
        f"{'r_p99':>6} {'r_wrst':>7} {'fps@p99':>8} {'sim_mn':>7}"
    )
    for x in rows:
        print(
            f"{x['name']:42} {x['max_attacks']:>3} {x['render_mean']:>7.3f} {x['render_p50']:>6.3f} "
            f"{x['render_p95']:>6.3f} {x['render_p99']:>6.3f} {x['render_worst']:>7.3f} "
            f"{fps_of(x['render_p99']):>8.1f} {x['sim_mean']:>7.3f}"
        )
    budget = 1000.0 / 60.0
    print(f"\n60fps frame budget = {budget:.3f} ms (sim+render+present+overhead must fit).")

    # cProfile the render phase of the heaviest CPU scenario.
    print("\n=== cProfile: render phase, '2cat combat + specials + overlay', 600 frames ===")
    runtime_settings.set("show_hitbox_overlay", True)
    runtime_settings.set("show_input_history", True)
    platforms = DEFAULT_PLAYER_STAGE.build()
    from pycats.entities.ledge import ledges_from_platforms

    ledges = ledges_from_platforms(platforms)
    battle = new_battle()
    driver = make_inputs("combat_specials", ledges)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for f in range(180):
        fi = driver(f, battle, platforms)
        battle.step(fi, platforms)
        render_playing(battle, surface, platforms, fi, 60.0)

    prof = cProfile.Profile()
    for f in range(180, 780):
        fi = driver(f, battle, platforms)
        battle.step(fi, platforms)  # stepped OUTSIDE the profiler below
        prof.enable()
        render_playing(battle, surface, platforms, fi, 60.0)
        prof.disable()

    st = io.StringIO()
    ps = pstats.Stats(prof, stream=st).sort_stats("tottime")
    ps.print_stats(28)
    print(st.getvalue())

    bench_render_attacks_scaling()
    bench_present_scale()


if __name__ == "__main__":
    if HEADED:
        main_headed()
    else:
        main()
