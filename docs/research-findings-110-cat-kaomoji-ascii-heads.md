# Pure-ASCII cat FACE+EARS heads (sideways + 3/4) — findings (#110)

> A cat **head only** (ears + eyes + nose) in **profile** or **3/4**, built purely
> from ASCII/text (multi-line) — no pictorial emoji, no body/tail. Closes the gap
> from #103 (front-only kaomoji) and #105 (full-body side cat `ᓚᘏᗢ`).
> Online survey + a pygame multi-line render + mirror experiment.
> Confidence: high (measured here). Date: 2026-06-26. Experiment:
> `repros/ascii-faces-110/` (gitignored).

## TL;DR

- **Both views are achievable in pure ASCII, face+ears only.** Two designs read
  clearly:
  - **3/4 view:** the classic 3-line cat face.
  - **Profile (sideways):** a 3-line side head facing right; **surface-flip** for
    the left-facer.
- **Multi-line mirroring works via surface flip** (the #105 technique extends to
  ASCII): `/ \ ( ) < >` flip geometrically correct, so **no character-swap is
  needed** — render the right-facer once, `transform.flip` for left.
- **This resolves #105's "3/4 is the gap"**: multi-line ASCII does what a single
  kaomoji glyph could not.
- **Caveat:** the designs are ~3 lines (~90×78 px at a 22px mono font) and must
  downscale into the ~40px face box — legibility at that size is the main risk;
  a 2-line variant or a slightly taller face area may read better.

## The two recommended designs

**3/4 view** (face + ears + nose, slightly toward camera):

```
 /\_/\
( o.o )
  >^<
```

**Profile, facing right** (flip the rendered surface for the left-facing fighter):

```
 /\___
( o   >
 \___>
```

So for two fighters facing in: **P1 (faces right) = as-authored, P2 (faces left)
= `transform.flip`**. Verified in the experiment — the flip turns the snout `>`
into a left-pointing `<` and mirrors the ears/head correctly (`profile_r_c.png`
vs `profile_r_c_FLIP.png`).

## Empirical results (this machine)

- **Monospace font:** `DejaVuSansMono` (linesize 26 at 22px) renders all the box-
  drawing slashes/parens/carets cleanly. Monospace is **required** — proportional
  fonts misalign the columns and the art falls apart.
- **Multi-line render:** split on `\n`, render each line, blit stacked at
  `font.get_linesize()`. Width = widest line.
- **Mirror:** `pygame.transform.flip(block, True, False)` on the *rendered block*
  reads correctly for both designs; **no per-glyph swap** needed.
- **Contrast:** dark ink reads on the orange body swatch — reuse #108's
  `cat_faces.ink_for` (dark ink on light cats, light on dark).
- Samples: `34_mouth.png` (3/4), `profile_r_c.png` / `_FLIP.png` (profile R/L),
  plus other candidates (`profile_r_a/b/d`, `34_classic/eq`).

## 3/4 vs profile — verdict

- **Profile** is the best fit for pycats: the fighters face each other, so a
  side-on head (flipped per `facing_right`) looks like they're squaring up.
- **3/4** is the more universally "cute/legible" cat and is a fine alternative
  (it reads the same flipped, being near-symmetric).
- Either is **face+ears only** (no body/tail), pure ASCII (no emoji), tintable,
  and mirrorable — meeting every constraint in the ticket.

## Recommendation / integration

Add these as new style(s) in the **#108** face-toggle harness (`pycats/cat_faces.py`):
- A multi-line block renderer (render lines, stack at linesize, monospace).
- Styles `ascii_profile` (flip per facing) and `ascii_34`.
- Scale the block to the face width (as #108 already does), in `ink_for` contrast.
- **Tune for legibility at ~40px:** try a larger face box for ASCII styles, or a
  trimmed 2-line variant if 3 lines blur. Font-probe for a monospace with fallback.

Render-only (default stays primitives), so sim/goldens/render-tests are unaffected
(#80). File the DEV slice when wanted (not filed here — no go-ahead).

## Sources

- [ASCII Art Archive — cats](https://www.asciiart.eu/animals/cats)
- [melaniecebula/cat-ascii-faces](https://github.com/melaniecebula/cat-ascii-faces)
- [asciiart.website — cats](https://asciiart.website/cat.php?category_id=32)
- [emojicombos — simple cat ASCII](https://emojicombos.com/simple-cat-ascii)

Refs: #103 (emoji/kaomoji feasibility), #105 (directional, full-body + surface-flip),
#108 (live face-toggle harness this slots into), `cat_faces.ink_for`.
