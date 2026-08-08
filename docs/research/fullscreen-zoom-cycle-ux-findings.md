# F10 fullscreen-zoom cycle UX — findings & ruling (#88)

> Why some F10 presses produce no visible change in fullscreen, and what to do
> about it. Companion to #85 (introduced the clamp + cycle) and #89 (zoom toast).
> Confidence: high — root cause read directly from the code and confirmed by
> computing the per-monitor outcomes with `display.fit_scale`/`clamp_scale`.
> Date: 2026-06-25. Code as of `main` @ 31fbf45.

## Question

Reported on #88: in fullscreen, some F10 presses don't visibly change the game
size (on a 1080p monitor, presses 4 and 5 look identical to press 3, then press 6
wraps to the smallest). Is it a bug, and should the cycle change?

## Root cause — intended, not a logic defect

`FULLSCREEN_ZOOM_PRESETS = ("fit", 1.0, 1.5, 2.0, 2.5)` and each numeric preset is
passed through `display.clamp_scale` so `base * scale` never exceeds the monitor —
the no-crop guarantee from #85 (the whole stage + KO/blast bounds stay visible).
When several presets clamp to the **same** achievable scale, those F10 steps render
identically. The code is doing exactly what it was designed to do; the cycle just
walks a fixed 5-entry list that has **monitor-dependent duplicates**.

## How bad, per monitor (computed)

Distinct achievable scales = `{fit_scale} ∪ {clamp(p) for p in 1,1.5,2,2.5}`:

| Monitor | fit | clamped presets | distinct sizes | F10 presses today | dead presses |
|---|---|---|---|---|---|
| 1920×1080 | 2.0 | 1.0, 1.5, 2.0, **2.0** | 1.0, 1.5, 2.0 | 5 | **2** |
| 2560×1440 | 2.0 | 1.0, 1.5, 2.0, 2.5 | 1.0, 1.5, 2.0, 2.5 | 5 | **1** |
| 3840×2160 | 4.0 | 1.0, 1.5, 2.0, 2.5 | 1.0, 1.5, 2.0, 2.5, 4.0 | 5 | 0 |
| 1366×768 | 1.0 | 1.0, 1.42, 1.42, 1.42 | 1.0, 1.42 | 5 | **3** |
| 1280×720 | 1.0 | 1.0, 1.33, 1.33, 1.33 | 1.0, 1.33 | 5 | **3** |

Every common monitor except 4K has at least one dead press; small laptops have
three. So this is a real, widespread UX wart — the reporter's expectation ("a
visible change every press") is reasonable.

## Options considered

1. **Leave as-is + rely on the #89 toast.** Cheapest (already shipped). The toast
   makes the *number* update even when the size doesn't, so no press is fully
   "dead." But it does **not** meet the stated expectation of a *visible size
   change* every press — three of five steps still look identical on a laptop.
2. **Dedupe the cycle per-monitor (RECOMMENDED).** At fullscreen entry, compute
   the distinct achievable scales (table above), sorted ascending, and have F10
   cycle *that* list. Every press then changes the rendered size. Keeps no-crop
   untouched (it's built from the same clamp). Small, contained change.
3. **Drop "fit" when it equals a numeric preset.** A partial version of (2) — only
   removes the fit/2× collision, not the 2.5×→2× one. Half-measure; (2) subsumes it.
4. **Continuous zoom / true "fill" option.** Bigger redesign (out of scope) — note
   it as a possible future: on 1440p the largest discrete option (2.5×) still
   leaves a border because true fill would be 2.667×.

## Ruling

**Adopt option 2 — dedupe to distinct achievable scales per monitor.** Combined
with the #89 toast (kept), every F10 press produces a visibly distinct size and
shows its value. The no-crop guarantee is preserved (the list is derived from the
existing `clamp_scale`/`fit_scale`).

Label guidance for the DEV ticket: label the **largest** achievable entry "Fit"
(it represents "as large as fits", whether that's a clean integer like 2× on 1080p
or a clamped fractional like 1.42× on a 1366-wide laptop), and label the smaller
clean presets by their numeric value (`1×`, `1.5×`, …). Exact label/format details
are the DEV ticket's call; this doc fixes the *behaviour* (cycle distinct sizes).

## Follow-on

Filed **#92** to implement a pure `display.achievable_zoom_scales(display_size)`
helper and rewire the fullscreen F10 cycle onto it. Option 4 (true continuous
"fill") is explicitly **not** filed — record it here as a possible future if
discrete steps ever feel insufficient.
