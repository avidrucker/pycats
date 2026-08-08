# Per-frame HUD/shell readout census — key churn + safe display-precision reduction (#1289)

> Child A (RESEARCH) of the #1288 epic. Surfaces the facts the ARCHITECT child (B)
> needs to design the display-precision change: which per-frame readouts mint
> high-cardinality text-cache keys, how much a 1-dp display cut saves, the
> pure-display vs sim-state boundary per readout, and whether a shared format seam
> exists.
>
> Inputs:
> - Code: `hud_rows` / `hud_emphasis_rows` / `draw_shell_chrome` in
>   `pycats/render/hud.py`; `render_text` / `render_text_simple` /
>   `render_text_mixed` in `pycats/ui/text_utils.py`; `InputFrame.__str__` in
>   `pycats/core/input.py`; `LivePresenter._draw_overlay` in
>   `pycats/sim/presenters.py`; `SHIELD_MAX_HP` / `SHIELD_DRAIN_PER_FRAME` in
>   `pycats/config/physics.py`; `fighter.shield_hp` setter in
>   `pycats/entities/fighter.py`.
> - Oracle: `tests/test_shell_chrome.py` (mirrors `draw_shell_chrome`'s FPS format).
> - Prior: #1282 §Q1/§5 (the churn census that motivated the epic); #1288 (owner
>   decision: FPS `x.x` display, 2-dp internal; determinism boundary).
> - Date: 2026-08-07
>
> **No decision here** — that is child B. This is findings only.

## TL;DR

- **One dominant per-frame filler: `FPS: {fps:.2f}`** — pure shell display, drawn
  unconditionally every playing frame. A 1-dp display (`x.x`) cuts its distinct-key
  count by **exactly 10×** per unit of FPS spread. This is the whole point of the
  epic and the only clear win.
- **`Shield HP: {shield_hp}` is a weaker candidate than the epic framing suggests.**
  The per-frame *drain* (0.2 from a max of 50) already yields **1-dp strings**
  (50.0, 49.8, 49.6, …) — ~250 distinct over a full drain, *not* 2-dp churn. The
  only 2-dp keys come from **damage absorption** (`shield_hp -= atk.damage`, a 2-dp
  hit value), which is occasional, not per-frame. So a 1-dp display cut helps Shield
  HP much less than FPS, and it is **sim state** (render-layer rounding only).
- **A second per-frame high-cardinality readout the epic didn't name:**
  `frame_input.__str__()` (the debug-input chrome, `draw_shell_chrome`) prints the
  raw held/pressed/released **keycode sets**. High cardinality, but it is *not*
  decimal-formatted, so a precision cut does not apply to it. Flagged for
  completeness; out of the epic's lever.
- **No shared *format* seam exists.** Every readout is an inline f-string at its
  call site; `render_text*` is a *render* seam (it takes an already-formatted
  string), not a format seam. Child B chooses between a new shared display-format
  helper vs per-call edits — there is nothing to hook today.
- **No sim/combat golden depends on any of these display strings.** The one place
  the FPS format is duplicated is `tests/test_shell_chrome.py`, a re-computing
  *oracle* (not a frozen image) that mirrors `f"FPS: {fps:.2f}"`; it must be edited
  in lockstep when C changes the format, but it will not "break" as a golden.

## Q1 — Census of per-frame HUD/shell readouts

Every string below is rebuilt and re-submitted to the text cache each frame during
play. "Cardinality" is the count of distinct cache keys the source value can mint.

| Readout (source) | Format | Source value | Change rate | Cardinality | Precision-cut candidate? |
|---|---|---|---|---|---|
| **FPS** — `draw_shell_chrome`, `hud.py` | `FPS: {fps:.2f}` | `clock.get_fps()` (rolling avg) | **every frame, unconditional** | **high** (~100/FPS-unit of spread) | **YES — the primary target** |
| **Shield HP** — `hud_rows`, `hud.py` | `Shield HP: {shield_hp}` | `fighter.shield_hp` = `round(…,2)` | every frame **while shielding** | medium; **drain is already 1-dp** (~250/full drain), 2-dp only on hits | partial (sim state; small win) |
| **Damage %** — `hud_emphasis_rows`, `hud.py` | `Damage: {int(percent)}%` | `fighter.percent` | changes on hits, sweeps upward | 0–~999 per stock | **NO — already `int`** |
| **Debug input** — `draw_shell_chrome`, `hud.py` | `frame_input.__str__()` | `InputFrame` held/pressed/released **sets** | every input change | high (set-of-keycodes repr) | **NO — not decimal-formatted** |
| Jumps — `hud_rows` | `{n} jump(s) left` | `jumps_remaining` | rare | ~3 | no |
| FSM / Movement — `hud_rows` | `FSM: {state}` / `Movement: {state}` | `Player.state` | per state change | bounded set (~8) | no |
| Shield Attempting — `hud_rows` | `… {Yes/No}` | `shield_attempting` | per toggle | 2 | no |
| Lives — `hud_emphasis_rows` | `Lives: {n}` | `fighter.lives` | per KO | ~4 | no |
| Static chrome — `draw_shell_chrome` / `draw_pause_hint` | fullscreen hint, `P: Pause Game`, ESC hint | constants / `is_fullscreen` | near-static | 2–3 | no — these are the still-visible keys the cache churn evicts |

Adjacent (not the main game HUD, but same pattern, and instructive): the
standalone **watch/replay** overlay `LivePresenter._draw_overlay`
(`pycats/sim/presenters.py`) already renders **`FPS: {get_fps():.1f} ({cap})`** at
**one decimal** — a 1-dp FPS precedent already living in the tree — plus a per-player
`{name}: {lives} stocks  {int(percent)}%  [{state}]` line. Not the epic's target
(different render path), but confirms `.1f` is already considered acceptable for an
FPS readout here.

## Q2 — Cardinality reduction from a 1-dp FPS display

`clock.get_fps()` is a rolling average that hovers near the cap; `.2f` formatting
mints one key per 0.01 FPS, `.1f` one per 0.1 FPS. **For any FPS spread of *S*
units, `.2f` → up to `100·S` distinct keys, `.1f` → up to `10·S` — a flat 10×
reduction, independent of how wide the spread is.** That matches the epic's ~10×
(≈1000→≈100–200) estimate.

The #1282 headless probe measured only **9 distinct `FPS: x.xx` keys over 600 idle
frames** — an unrealistic floor, because an idle `SDL_VIDEODRIVER=dummy` loop keeps
frame times near-constant so `get_fps()` converges to ~60.00. Under a live display
(full scene compositing + a sim step + occasional GC per frame) the spread widens,
so the `.2f` key count climbs while `.1f` stays ~10× smaller. FPS is the dominant
filler *because* it is the only readout that changes every frame **unconditionally**
(Shield HP only churns while shielding; Damage only on hits).

**Shield HP:** the per-frame drain (`SHIELD_MAX_HP=50`, `SHIELD_DRAIN_PER_FRAME=0.2`)
already produces 1-dp values (`round(50-0.2k, 2)` = 50.0, 49.8, 49.6, …), so a 1-dp
display cut does **not** reduce the drain sequence (~250 keys/full drain) at all — it
only collapses the occasional 2-dp values that damage absorption introduces. Net
Shield-HP win from a display-precision cut is small and conditional; the bigger lever
for Shield-HP cache pressure would be a different one (out of this ticket's scope).

## Q3 — Boundary map (pure-display vs sim-state)

| Readout | Class | Rule for child B/C |
|---|---|---|
| **FPS** | **Pure display** — `clock.get_fps()` is shell/loop state, never fed to the sim | Round freely (the epic's `x.x` display; keep the float internally). No sim/combat golden references it. |
| **Shield HP** | **SIM state** — `fighter.shield_hp` feeds shield mechanics; goldens depend on the *stored value* | **Display-round at the render/format layer only.** Never touch the stored `round(…,2)` value or `SHIELD_*` constants. |
| **Damage %** | SIM-derived, already display-truncated (`int(percent)`) | Display-only; stored `percent` untouched. Not a precision candidate. |
| **Debug input** | Shell/input debug | Pure display; not decimal-formatted — no precision cut applies. |
| Lives / jumps / FSM / Movement / Shield Attempting | SIM-derived, low cardinality | Not precision candidates; leave as-is. |

**Golden check.** No sim/combat golden asserts on the *display string* of any of
these — goldens track sim/frame state, not HUD text. The only format duplication is
`tests/test_shell_chrome.py`, which **re-derives** the expected surface from its own
copy of `f"FPS: {fps:.2f}"` (a faithful oracle, not a frozen PNG). It must be edited
in lockstep with the format change in child C, but it does not constitute a golden
that "breaks" — it is a mirror that has to track. (`tests/test_text_render_cache.py`
uses a literal `"FPS: 60"` string; format-independent.)

## Q4 — Is there a shared format seam?

**No.** Two distinct seam types, and only the wrong one is shared:

- **Render seam (shared, but too late):** all HUD/shell text flows through the
  module-level `render_text(...)` wrapper → `render_text_simple` (or
  `render_text_mixed` → `render_text_simple` when no unicode font). This is a single
  chokepoint, but it receives an **already-formatted string** — the precision
  decision has already happened at the call site. A rule here could not know a token
  was "an FPS float that should be 1-dp".
- **Format seam (does not exist):** each readout is an **inline f-string** built in
  `hud_rows` / `hud_emphasis_rows` / `draw_shell_chrome`. There is no HUD
  number-formatting helper today.

So child B's design choice is real and open:
- **(a) a new shared display-format helper** (e.g. a `fmt_fps()` / general
  `display_round(value, dp)` the call sites adopt) — one place for the rule, but a
  new seam to introduce and route call sites through; or
- **(b) per-call edits** — change `f"FPS: {fps:.2f}"` → `f"FPS: {fps:.1f}"` (and the
  oracle mirror) inline. Minimal, but the rule lives at each call site.

Given the census, only **one** call site (FPS) is a clear target, with Shield HP a
weak, sim-boundaried second — which is evidence B can weigh toward the low-ceremony
per-call option, or toward a helper if it wants the display-round rule documented in
one named place for future readouts.

## Handoff to child B (ARCHITECT)

- Target the FPS readout (`draw_shell_chrome`) as the clear win; decide helper vs
  per-call (Q4).
- If Shield HP is in scope, design it as **render-layer display rounding only**
  (Q3) and note its win is smaller/conditional than FPS (Q2).
- Whatever the format change, C edits `tests/test_shell_chrome.py`'s FPS mirror in
  the same commit (Q3).
- `frame_input.__str__()` is high-cardinality but not a decimal-precision lever —
  out of the epic's scope; flag only.
