# Cat faces via emoji / ASCII / kaomoji — research + experiment findings (#103)

> Should pycats draw cat **faces** with emoji / ASCII / kaomoji instead of (or as
> well as) the current pygame primitives? Online survey + an empirical pygame
> render test on this machine. Read-only research + a throwaway prototype.
> Confidence: high for the empirical results (measured here); the survey is
> standard reference material. Date: 2026-06-25. Code @ 01ac2d8.
> Experiment: `repros/cat-faces-103/` (gitignored) — re-run with the command at
> the bottom; sample PNGs are saved there.

## TL;DR

- **Color emoji works in pygame here — overturning the common "you can't" advice.**
  `pygame.font` (SDL_ttf **2.24.0**, pygame-ce 2.5.7) renders 🐱 (NotoColorEmoji)
  in **full colour** directly — no PIL/freetype workaround needed. (The widely
  repeated "SDL_ttf can't do colour emoji" is true only of *older* SDL_ttf.)
- **But colour emoji has fixed art** — every cat would look like Noto's one 🐱,
  **killing the per-character colour identity** (calico/tabby/void are currently
  distinguished by colour). And it's a **hard font dependency** (no NotoColorEmoji
  → tofu) at a **fixed 136×128 strike** (must downscale to the ~40px body).
- **Kaomoji is the sweet spot for an expressive face:** `(=^･ω･^=)` etc. render
  with any font, are **monochrome but tintable** — so they *keep each cat's
  colour* — are tiny, dependency-free, and have a rich vocabulary that maps
  naturally to fighter **states** (idle/hurt/dizzy/KO).
- **Recommendation:** if pursued, do it as **selectable face skins** (ties into
  #16), not a wholesale replacement — keep primitives as the default so existing
  render tests stay green. Lead with a **tintable kaomoji skin** (expressive,
  per-character colour, works everywhere); offer a **colour-emoji skin** as a
  flashier option gated on a NotoColorEmoji-present check (the `text_utils` font
  probe already exists). Render-only → sim goldens unaffected (#80).

## Empirical results (measured on this machine)

Linux Mint · pygame-ce 2.5.7 · SDL_ttf 2.24.0 · PIL 12.2 · NotoColorEmoji installed.
Verdict = distinct-colour count of the rendered glyph (`repros/cat-faces-103/experiment.py`):

| Approach | Result | Notes |
|---|---|---|
| `pygame.font.Font(NotoColorEmoji, 109)` → 🐱 | **COLOUR** (54 colours), 136×128 | Works directly! Fixed strike size — downscale to body size. |
| `pygame.font.SysFont("notocoloremoji")` → 🐱 | **COLOUR** (54 colours) | Same, via SysFont. |
| PIL `embedded_color=True` → pygame Surface | **COLOUR**, 123×110 | The documented fallback; needed only on older SDL_ttf. |
| `DejaVuSans.render("(=^.^=)", (255,160,64))` | **MONOCHROME**, tinted | Kaomoji renders fine and **takes any colour** → per-cat tint. |
| `DejaVuSans.render("/\\_/\\", …)` | MONOCHROME, tinted | ASCII works too. |

Sample renders (in `repros/cat-faces-103/`): `01_pygame_notocoloremoji_109.png`
(a crisp full-colour 🐱), `03_pil_notocoloremoji.png`, `04_kaomoji.png` (orange-
tinted `(=^.^=)`).

## Online survey — ways to "draw" a cat face

### Unicode cat emoji (colour, fixed art)
Face set with built-in expressions: 🐱 😺 😸 😹 😻 😼 😽 🙀 😿 😾 — plus 🐈 🐈‍⬛.
Expression is *baked into each codepoint* (😺 smiling, 🙀 weary/shocked, 😾 pouting,
😿 crying), so a state→emoji map is natural but the art style is whatever the
system emoji font dictates.

### Kaomoji / Japanese cat emoticons (text, tintable)
Rich, expression-organised, all plain text characters:
- Neutral/happy: `(=^･ω･^=)` · `(=^‥^=)` · `ฅ^•ﻌ•^ฅ` · `/ᐠ｡ꞈ｡ᐟ\` · `ᓚᘏᗢ` · `^ↀᴥↀ^`
- Pleased/love: `(=^･ｪ･^=)` · `(=^‥^=)♡` · `ฅ^≧∇≦^ฅ`
- Angry/attack: `(=｀ω´=)` · `(=ↀωↀ=)` · `(=ＴェＴ=)`
- Hurt/sad: `(=;ェ;=)` · `(╥ω╥)` · `(=ｘェｘ=)`
- Dizzy/KO: `(=ﾟ□ﾟ=)` · `(@ω@)` · `(×﹏×)` · `(= _ =)`

### Multi-line ASCII cat art
`/\_/\`, `( o.o )`, `> ^ <` style block art — charming but tall (multi-line),
harder to fit a 40×60 body and to animate; better for a logo/splash than a live
fighter face.

Sources: [emojicombos — cat kaomoji](https://emojicombos.com/cat-kaomoji),
[japaneseemoticons.org cat collection](https://japaneseemoticons.org/collection-of-kaomoji-cats/),
[kaomojikuma cats](https://kaomojikuma.com/kaomoji-animals-japanese-emoticons/kaomoji-cats/),
[fancytexty cat kaomoji](https://fancytexty.com/cat-face-kaomojis-list/);
pygame colour-emoji background: [pygame.font docs](https://www.pygame.org/docs/ref/font.html),
[jdhao — colour emoji in Python](https://jdhao.github.io/2022/04/03/add_color_emoji_to_image_in_python/).

## Tradeoffs

| | Colour emoji 🐱 | Kaomoji `(=^･ω･^=)` | Primitives (current) |
|---|---|---|---|
| Visual polish | Highest (full colour art) | Cute, minimalist | Custom, "simple shapes" |
| **Per-character colour identity** | **Lost** (one fixed art) | **Kept** (tint per cat) | Kept |
| Expression set | Fixed emoji per state | Huge, free-form per state | Hand-coded |
| Dependency | **NotoColorEmoji required** (else tofu) | None (any font) | None |
| Sizing | Fixed 136×128 strike → downscale | Any size | Native |
| Animation (facing flip, whiskers, tail) | None (static glyph) | None (static glyph) | Full (already animated) |
| Effort | Low (+ font/fallback handling) | Low | Already built |

## Recommendation

If a change is pursued, do it as **opt-in face skins**, not a default replacement:

1. **Kaomoji face skin (lead candidate).** Tintable to each cat's colour, works on
   any machine, expressive. Map fighter **states** → kaomoji:
   idle `(=^･ω･^=)` · attack `(=｀ω´=)` · hurt `(=;ェ;=)` · dizzy `(@ω@)` (#12) ·
   KO `(×﹏×)`. Render the face glyph where `draw_eye`/`draw_cat_features` draw now;
   keep primitive ears/body/tail (hybrid) or go face-only.
2. **Colour-emoji skin (flashier option).** Gate on a NotoColorEmoji-present check
   (reuse `text_utils._find_unicode_font`), downscale the 136×128 strike to the
   face area, fall back to kaomoji/primitives when absent. Accept the loss of
   per-cat colour (or only offer it for a "default cat").
3. **Keep primitives as the default** so the existing render tests
   (`test_render_battle`, `test_render_isolation`, `test_render_cache`) stay green;
   skins are selectable via #16 (character-skin selection). Sim goldens are
   render-only-unaffected (#80).

**Do not** make emoji the default or a hard dependency, and **do not** drop the
primitives (they carry the per-character colour and the animation the glyphs can't).

## Suggested follow-on (file one at a time, per RULES — not filed here)

- DEV: a **tintable kaomoji face skin** with a state→face map, selectable via #16.
- (optional) DEV: a **colour-emoji skin** gated on font presence, downscaled, with
  fallback.

Recorded as candidates; nothing filed yet (no go-ahead). Refs: #16 (skins), #75
(Appearance port), #12/#13 (states), `text_utils` unicode-font probe, #80
(render-only / golden isolation).
