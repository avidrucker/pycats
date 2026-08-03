# Directional kaomoji cat faces (sideways + 3/4) — findings (#105)

> Follow-up to #103: pycats fighters face each other, so a glyph face must convey
> direction. Online survey + a pygame mirroring experiment. Read-only research +
> throwaway prototype (`repros/dir-faces-105/`, gitignored).
> Confidence: high for the empirical results (measured here). Date: 2026-06-25.

## TL;DR

- **Sideways/profile is solved cleanly.** `ᓚᘏᗢ` renders as a side-on cat **facing
  right** (head/ears `ᗢ` right, tail `ᓚ` left). To get the **left-facing** variant,
  **don't mirror the text — flip the rendered *surface*** (`pygame.transform.flip
  (surf, True, False)`). Verified: the flip produces a clean left-facing cat.
- So per fighter: **P1 (faces right) = as-authored, P2 (faces left) = flipped** →
  they look at each other. Tintable (renders in each cat's colour).
- **Font dependency:** the profile glyphs are Canadian Aboriginal Syllabics; here
  they render via **Noto Sans Canadian Aboriginal**. Needs a probe + fallback like
  `text_utils._find_unicode_font` already does.
- **3/4 view is the real gap.** Standard kaomoji don't do "slightly toward camera
  + slightly turned." The current **primitives already do a pseudo-3/4** (the eye
  is offset toward `facing_right` in `draw_eye`), so 3/4 is best left to primitives
  or a hybrid — not pure kaomoji.

## Why surface-flip, not text-mirror

Mirroring a kaomoji by reversing the string + swapping mirror-pair chars (`( )`,
`< >`, `/ \`, `d b`) fails for glyphs with **no mirror partner** (the syllabics
`ᓚ ᘏ ᗢ` have none). Flipping the *rendered surface* is glyph-agnostic and exact —
and it's the same horizontal-flip pycats already uses conceptually for facing. So:
render the right-facing profile once, `transform.flip` for left. (Tint is applied
at render, so the flip preserves colour.)

## Empirical results (this machine)

pygame-ce 2.5.7, rendered at 40px, tinted `(255,160,64)`. All via
**notosanscanadianaboriginal** (covers the syllabics + falls back for the rest):

| Candidate | Glyph | Reads as | Result |
|---|---|---|---|
| profile cat | `ᓚᘏᗢ` | side cat, **faces right** | OK, 95×55 → flip = clean left-facer |
| profile + tail | `₍^. .^₎⟆` | side cat w/ tail | OK, 180×55 |
| paws (front-ish) | `/ᐠ｡ꞈ｡ᐟ\` | front | OK |
| control (front) | `(=･ω･=)` | front | OK |

Samples in `repros/dir-faces-105/` — `syllabic_cat_R.png` (right-facing) and
`syllabic_cat_L.png` (surface-mirrored left-facing) confirm the technique.

## Catalogue

**Sideways profile (author facing-right, flip for left):**
- `ᓚᘏᗢ` — cleanest minimal side cat (recommended).
- `₍^. .^₎⟆` — side cat with a visible tail.
- `🐈` / `🐈‍⬛` — colour-emoji side profile (fixed art, see #103 tradeoffs).

**3/4 / front (no clean directional text):** `(=^･ω･^=)`, `/ᐠ｡ꞈ｡ᐟ\`,
`ฅ^•ﻌ•^ฅ`. These read straight-on; there is no widely-recognised kaomoji that
reads as a 3/4 turn.

Sources: [emojicombos — cat symbol text (ᓚᘏᗢ)](https://emojicombos.com/cat-symbol-text),
[emojicombos — kaomoji cat](https://emojicombos.com/kaomoji-cat),
[emojicombos — cat](https://emojicombos.com/cat).

## Recommendation

- **Pure-sideways kaomoji face skin is viable and clean:** render `ᓚᘏᗢ`
  (tinted per cat), use `transform.flip` to orient by `facing_right`, so the two
  fighters face each other. Gate on a Canadian-Aboriginal-capable font probe with
  a fallback to primitives.
- **For 3/4, keep the primitives** — they already lean the eye toward facing and
  carry the per-character colour/animation a static glyph can't. A "3/4 kaomoji"
  isn't a real thing; don't force it. If a turned look is wanted beyond the
  primitive eye-offset, it's a custom small bitmap, not standard kaomoji.
- This still belongs as an **opt-in skin** (#103 / #16), default staying
  primitives so render tests stay green; render-only, sim goldens unaffected (#80).

## Follow-on (not filed here)

- DEV: profile-kaomoji face skin using render-once + `transform.flip` per facing,
  tinted, font-probe-gated.
- The live **per-player face-toggle test key** (filed separately so faces can be
  compared in-game).

Refs: #103 (kaomoji skin), #16 (skins), `render_battle.draw_eye` facing logic,
`text_utils` font probe, #80 (render-only / golden isolation).
