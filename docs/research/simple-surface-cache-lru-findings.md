# `_simple_surface_cache` wholesale-clear — does it have the #1267 hitch, and is LRU warranted? (#1282)

> Confirms whether the second text-render surface cache (`render_text_simple`,
> hotspot B4) has the periodic-recompose problem #1267 fixed on the mixed cache
> (`_compose_mixed`, B5), and whether the identical LRU eviction is a warranted,
> safe fix.
>
> Inputs:
> - Code: `render_text_simple` + `_simple_surface_cache` in `pycats/ui/text_utils.py`;
>   HUD string builders in `pycats/render/hud.py`; `fighter.py` (shield-HP format).
> - Prior art: #1267 (merged LRU fix for the mixed cache); #1263 (added the simple
>   cache, B4); #1247 (measured B4 at 12.8 render calls/frame);
>   `docs/research/2026-08-05-loop-profile-measured-hotspots.md` (B4/B5 basis).
> - Date: 2026-08-05
>
> **Verdict: confirmed + warranted, at low priority.** The wholesale clear
> reproduces the #1267 mechanism, the fix transfers mechanically 1:1, and there is
> no blocking reason against it — but the cache fills *slower* than the mixed cache
> did, so this is a consistency / cheap-correctness fix, not a fix for a frequent
> hitch. Follow-up DEV ticket: **#1287**.

## 1. Caller census — what flows through the simple cache

`render_text_simple` (`pycats/ui/text_utils.py`) is fed from three seams:

- `render_text_mixed` **delegates** to it whenever no unicode font is selected
  (`text_utils.py:331`).
- The module-level `render_text(...)` wrapper (`text_utils.py:726`) routes straight
  through it.
- Direct calls from `menu_widgets.py`, `options_menu.py`, `text_entry.py` (menu /
  options chrome).

The **in-battle HUD** reaches the simple cache via the `render_text(...)` wrapper, so
the #1263/#1282 premise that damage %, lives, FPS, etc. rasterise on this path is
accurate. The `TextRenderer` instance is process-lived and the cache is **never reset
between screens**, so distinct keys accumulate across the whole session (menus + every
match); the 1024 cap is a *session*-level threshold, not per-match.

## 2. Q1 — Does the cap-clear reproduce the #1267 hitch? YES (mechanism), slower fill.

Dynamic strings minted on this path during play, by key cardinality:

| String (source) | Cardinality | When | Filler? |
|---|---|---|---|
| `FPS: {fps:.2f}` (`hud.py:292`, `clock.get_fps()`) | up to ~1000 (2-decimal float) | **every frame during play, unconditional** | dominant |
| `Shield HP: {shield_hp}` (`hud.py:99`; `fighter.py:682` `round(...,2)`) | high (2-decimal float) | **every frame while shielding / regenerating** | strong |
| `Damage: {int(percent)}%` (`hud.py:111`) | 0→~999 per stock, resets on death | sweeps upward over a match | moderate |
| `{jumps} jump(s) left`, `FSM/Movement: {state}`, `Shield Attempting: Yes/No` | low (bounded sets) | per-frame | negligible |
| `Lives: N`, player label, `P: Pause Game`, F11/F10 hints | static / near-static | per-frame | these are the **still-visible keys the clear drops** |

When the accumulated distinct-key count crosses 1024 **during a match**, `.clear()`
(`text_utils.py:515`) drops every entry — including the ~8–12 still-visible play
strings (Lives / label / pause hint / fullscreen hints / current damage) — which all
re-rasterise the next frame. That is structurally the identical periodic hitch #1267
removed from the mixed cache.

**Fill-rate quantification (caveat).** A headless probe of `clock.get_fps()` under
`SDL_VIDEODRIVER=dummy` produced only **9 distinct `FPS: x.xx` keys over 600 frames
(1.5%/frame)** — an idle loop with no render work keeps frame times near-constant, so
`get_fps()` converges to ~60.00. At that idle rate the FPS string alone needs ~68k
frames (~19 min) to fill the cap. This is a **lower bound**: on a real display each
frame does full scene compositing + a sim step + occasional GC, so measured FPS
variance — and thus the 2-decimal churn — is materially higher, and the damage-sweep +
per-frame `Shield HP:.2f` (while shielding) add to it. The cap is realistically crossed
within a long or multi-match session; it is *not* crossed in a few seconds the way the
mixed-cache churn was. So: same mechanism, **lower frequency** than #1267.

## 3. Q2 — Does the #1267 fix transfer cleanly? YES — mechanically identical.

The simple-cache hit/insert block mirrors the mixed cache exactly:

- `self._simple_surface_cache = {}` → `OrderedDict()` (import already added for #1267)
- on cache hit (`text_utils.py:510`): add `self._simple_surface_cache.move_to_end(key)`
- at cap (`text_utils.py:514-515`): replace `.clear()` with `popitem(last=False)`

The cached surface is only ever blitted (read), never drawn onto — same as the mixed
path — so LRU eviction changes nothing observable. Byte-parity is **already guarded** by
`test_simple_cached_output_is_byte_identical_to_direct_render`. No new behavioural
surface.

## 4. Q3 — Any reason LRU is NOT warranted? No blocking reason; lower urgency than #1267.

The only counter-argument is "the cap is never reached, so it's moot." That is **weaker
here than for the mixed cache** (slower fill) but not true in absolute terms — the cache
is session-lived and does cross 1024 in long / multi-match sessions, at which point the
hitch bites. Because the fix is a pure win (same cost, no downside, no new behaviour)
that mirrors an already-merged sibling and keeps the two caches consistent, it is
warranted — as a **severity:low consistency fix**, not an urgent one.

## 5. Adjacent observation (out of scope for #1287)

The `FPS: {fps:.2f}` and `Shield HP: {shield_hp}` (2-decimal) per-frame keys are
themselves wasteful cache churn: they are the *reason* the cap is approached at all.
Rounding the FPS readout to an int (or 1 decimal) at the source would cut the dominant
filler by ~100× and shrink the cache-pressure problem independently of the eviction
policy. That is a separate optimisation (reduce key cardinality at the source, not the
eviction policy) and a candidate follow-up — flagged here, not filed.

## 6. Decision

Filed **#1287** — *Perf: LRU eviction for `_simple_surface_cache` instead of wholesale
clear* (severity:low, area:cross-cutting, parent #1261) — mirroring #1267, scoped to
`_simple_surface_cache`, with an able-to-fail "still-visible key survives eviction" test.
No code change in this research ticket.
