# Working with fonts in pygame (pycats)

A contributor guide to the font/text stack: how to use it **correctly, effectively, and
performantly**, and the gotchas that have already bitten us so we don't regress. Every
claim points at a code landmark you can open.

The whole stack funnels through one module — **`pycats/text_utils.py`** — and one process-
wide singleton, **`text_renderer = TextRenderer()`**. Sizes come from one place —
**`pycats/config.py`** — and are scaled at one chokepoint. Learn those three facts and the
rest follows.

---

## 1. Font sizes live in one place

Every UI/HUD text size is a named constant in the **"font sizes (single source, #344)"**
block of `pycats/config.py` — `GAME_HUD_FONT_SIZE`, `HUD_EMPHASIS_SIZE`,
`STATUS_BAR_SECONDS_SIZE`, `STATUS_BAR_LABEL_SIZE`, `TEXT_PROBE_SIZE` — alongside the
per-screen families (`WIN_SCREEN_*_SIZE`, `CHAR_SELECT_*_SIZE`, `MAIN_MENU_*_SIZE`). The
point of one home is that a size change — and the global font-scale scalar (§2) — has a
single chokepoint.

- **Do** add a new size as a named constant in that block and import it.
- **Don't** hardcode a size literal at a render call site. (`draw_hud` learned this in #550:
  the emphasized-row size is `config.HUD_EMPHASIS_SIZE`, not a `36` in `render_battle.py`.)

> **Wrinkle worth knowing:** `pycats/render_battle.py` keeps its own `HUD_FONT_SIZE = 24`
> (#415) for the battle-HUD / controls / input-history text, distinct from
> `config.GAME_HUD_FONT_SIZE`. Both are 24; they are not the same constant. When you touch
> HUD text, check which one the call site actually uses.

---

## 2. Every size flows through the scale chokepoint

pycats has a global **font scale** (`small` 0.5 / `standard` 1.0 / `large` 2.0), chosen from
the Options menu. It is applied at exactly one place: **`runtime_settings.scaled_font_size(base)`**,
which returns `max(config.MIN_FONT_PX, round(base * font_scale()))`.

- `standard` (1.0) is an **exact identity** — `round(base * 1.0) == base` — so the default
  render is byte-identical (this is why the font-scale feature is golden-safe, #345).
- `MIN_FONT_PX` (6) clamps a scaled-down size so it never rounds to 0/unreadable.

Both font builders inside `TextRenderer` — **`_get_font(font_name, size)`** and
**`sys_font(name, size)`** — call `scaled_font_size(size)` first, then cache by the
**effective** size. So **any font you obtain through `TextRenderer` scales automatically.**

- **Do** render text through the `TextRenderer` API (see §3) and pass the *authored* size;
  the chokepoint scales it.
- **Don't** build a `pygame.font.Font(None, 24)` (or call `pygame.font.SysFont`) directly at
  a UI call site — that bypasses `scaled_font_size`, so your text won't follow the player's
  Font Size setting and won't honour the `MIN_FONT_PX` clamp. The one deliberate exception is
  face art (§6).

---

## 3. The rendering API (use these, in this order of preference)

All live on the shared `text_renderer` singleton in `pycats/text_utils.py`:

| Call | Use it for |
| --- | --- |
| `render_text(surface, text, pos, size, color, center=, right_align=)` | module-level helper — the common case; computes width and left/center/right-aligns, routing size through `_get_font`. |
| `TextRenderer.render_text_mixed(...)` / `render_mixed_centered(...)` | strings that may contain Unicode (arrows `← ↑ → ↓`, `► ◄`) — see §4. |
| `TextRenderer.render_text_simple(...)` | ASCII-only fast path (also the fallback when no Unicode font is present). |
| `TextRenderer.sys_font(name, size)` | a *cached* `pygame.font.SysFont` when you genuinely need a system font (menu measurement, the fullscreen hint). |

Prefer `render_text` / the mixed helpers over reaching for a raw `pygame.font.Font`.

---

## 4. Mixed / Unicode text: compose once, cache by the *scaled* size

`render_text_mixed` / `render_mixed_centered` support strings that mix a regular font with a
Unicode-capable one. Two rules the implementation bakes in (`_select_mixed_fonts`,
`_compose_mixed`):

- **Compose once, then blit.** Each `(text, size, colour)` is composed to a single SRCALPHA
  surface and cached; the glyphs are non-overlapping side-by-side blits, so blitting the
  composed surface is byte-identical to blitting each glyph (#372).
- **Key the cache by the EFFECTIVE (scaled) size, not the authored one.** Otherwise a live
  font-scale change is served the stale surface composed at the previous scale, and mixed
  text never resizes (#401). `_compose_mixed`'s key is `(text, scaled_font_size(size), colour)`.
- **No Unicode font? Fall back to ASCII.** `_select_mixed_fonts` returns `unicode_font=None`
  when the host has no Unicode face; callers drop to `render_text_simple`. Don't assume a
  Unicode glyph will render.

---

## 5. `SysFont` is expensive — never call it per frame

`pygame.font.SysFont()` is a fontconfig lookup that **builds a new font object every call**
and can **hard-hang on a real display** (#375). `TextRenderer.sys_font` exists precisely to
cache it, keyed by `("sys", name, scaled_size)`, so a steady-state render frame makes **zero**
`SysFont` calls.

- **Do** go through `sys_font` (or `_get_font`) so the font is built once and reused.
- **Don't** call `pygame.font.SysFont` / `pygame.font.Font` inside a render loop.
- **Regression guard:** `tests/test_menu_font_caching.py` asserts a warmed menu render makes
  zero per-frame `SysFont` calls. If you add a menu/HUD render path, keep it cache-warm.

---

## 6. What is deliberately NOT centralized (and why)

Not every font size belongs in the §1 single-source block:

- **`cat_faces._MONO_SIZE` (28)** is a monospace **FACE-art** render size, tuned to the ASCII
  head art and then smoothscaled down to the body size (#110). It is *not* a UI text size and
  must **not** scale with the UI font_scale — so `cat_faces._mono_font` builds its font
  directly via `pygame.font.match_font` + `pygame.font.Font(path, size)` and keeps its own
  `_font_cache`. It returns `None` when the host has no monospace face, and the caller draws
  the primitive face instead.
- **`TEXT_PROBE_SIZE` (16)** is the glyph-support **probe/measurement** size, not a size you
  render user-facing copy at.

If you're tempted to "helpfully" fold these into the single-source block, don't — they are
different concerns that happen to be font sizes.

---

## 7. Test-isolation gotchas (these have bitten)

The font stack is **process-global** (the `text_renderer` singleton and its caches). Two ways
tests break because of that:

### `pygame.quit()` invalidates cached fonts
`pygame.quit()` deinitializes `pygame.font`. Any `Font` cached *before* the quit is now
"Invalid font (font module quit since font created)" on a later cache hit, and a fresh
`pygame.font.Font(None, size)` raises "font not initialized" (#63). **Opt render tests into
the `render_isolation` fixture** (`tests/conftest.py`) — it re-inits font and clears the
render/font caches before each test:

```python
pytestmark = pytest.mark.usefixtures("render_isolation")
```

### The cached-fake leak (#550 → #709) — the subtle one
Monkeypatching a **font factory** (`pygame.font.SysFont` / `Font`) is not enough on its own.
`TextRenderer._get_font` / `sys_font` cache whatever the factory returns in the **shared**
`text_renderer.font_cache` — and that fake object **outlives `monkeypatch`'s revert**, because
the cache holds the object, not the patched function. A later render then reads the fake as a
font and crashes (`unicode_font=_DummyFont` → no `.get_ascent()`), reddening tests in files the
diff never touched, and only on some collection orders.

- **A test that injects a fake font MUST flush the downstream cache in its own teardown:**
  ```python
  finally:
      text_renderer.font_cache.clear()
      text_renderer._mixed_surface_cache.clear()
  ```
  (`tests/test_main_menu_title.py` does exactly this.)
- **Backstop:** the autouse `_no_fake_fonts_leaked` guard in `tests/conftest.py` asserts the
  shared font cache holds only real `pygame.font.Font` objects on teardown — it evicts any
  fake and fails the *polluting* test by name, so you get a pointed error at the source instead
  of a mystified downstream victim.
- **Diagnostic rule of thumb:** a change that reddens tests in files it never touched = a
  leaked global from an earlier test. See RULES.md → *"Never restore a monkeypatched global by
  hand in a test"* (the cached-fake variant).

---

## Do / Don't checklist

**Do**
- Add every UI size to the single-source block in `config.py` (§1).
- Render through `text_renderer` / `render_text`, passing the *authored* size (§2–§3).
- Use `render_text_mixed` for anything with arrows/Unicode; let it fall back to ASCII (§4).
- Warm the font cache once and reuse; keep menu/HUD renders zero-`SysFont`-per-frame (§5).
- Add `render_isolation` to any test that renders (§7).
- Flush `text_renderer` caches in teardown if your test injects a fake font (§7).

**Don't**
- Hardcode a size literal at a call site (§1).
- Build `pygame.font.Font(None, N)` / call `SysFont` directly for UI text — you skip the
  scale chokepoint and (in a loop) the cache (§2, §5).
- Key a mixed-text cache by the authored size — key by the scaled size (§4).
- Fold face-art / probe sizes into the UI single-source block (§6).
- Monkeypatch a font factory without flushing the shared cache afterward (§7).

---

## Landmarks

- `pycats/config.py` — the "font sizes (single source, #344)" block; `FONT_SCALES`, `MIN_FONT_PX`.
- `pycats/runtime_settings.py::scaled_font_size` / `font_scale` — the scale chokepoint (#345).
- `pycats/text_utils.py` — `TextRenderer` (`_get_font`, `sys_font`, `_select_mixed_fonts`,
  `_compose_mixed`, `render_text_mixed`, `render_mixed_centered`, `render_text_simple`) and the
  module-level `render_text` helper + `text_renderer` singleton.
- `pycats/render_battle.py::draw_hud` — HUD text; local `HUD_FONT_SIZE` (#415), emphasized rows (#550).
- `pycats/cat_faces.py` — `_mono_font` / `_MONO_SIZE` / `_font_cache` (the deliberately-non-UI face art).
- `tests/conftest.py` — `render_isolation` (#63) and `_no_fake_fonts_leaked` (#709).
- `tests/test_menu_font_caching.py` — the zero-`SysFont`-per-frame guard (#375).
- RULES.md → *"Never restore a monkeypatched global by hand in a test"* (the cached-fake variant, #550/#709).
