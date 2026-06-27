# TIL 2026-06-26 — DRAGONFRUIT

**Context:** A long display/appearance session — shipped the whole resolution/
fullscreen/persistence arc (#82/#85/#88/#89/#92/#95) and a cat-face research+build
thread (#103/#105/#108/#110/#114), then closed the off-pixel research (#80) and
scaffolded the combat "5 PM-archetype cats" epic (#117/#119/#120). The throughline:
**the interesting findings were empirical and counter-intuitive — the web/the
assumption was wrong, and a five-minute experiment on the actual machine was what
settled it.**

---

## 1. Verify capability claims empirically — pygame *does* render colour emoji

**What happened:** For #103 I quoted the well-worn web advice that "SDL_ttf can't
render colour emoji" and planned a PIL/freetype workaround. Then I ran a throwaway
experiment on this machine (`repros/cat-faces-103/`): plain
`pygame.font.Font(NotoColorEmoji, 109).render("🐱")` produced a full-colour cat
face (54 distinct colours). The advice is only true of *older* SDL_ttf; pygame-ce
2.5.7 ships SDL_ttf **2.24.0**, which renders the CBDT/CBLC colour strikes directly.

**What I learned:** "library X can't do Y" is a claim about a *version*, and the
web's consensus lags the version you actually have installed. The experiment cost
a few minutes and overturned the plan.

**The rule:** treat "can't be done" capability claims as version-stamped — verify
against the installed toolchain with a throwaway probe before designing around the
limitation.

---

## 2. To flip directional text-art, flip the *surface*, not the *characters*

**What happened:** Cats face each other, so a glyph face needs a left- and a
right-facing variant (#105, #110). Mirroring the *text* (reverse the string + swap
`( )`, `/ \`, `< >`) breaks on glyphs with no mirror partner — the profile cat
`ᓚᘏᗢ` is Canadian-syllabic with none. `pygame.transform.flip(surf, True, False)` on
the *rendered* surface mirrors geometrically and is glyph-agnostic: the snout `>`
becomes a `<`, ears mirror, tint is preserved. It worked unchanged for a single
kaomoji (#105) *and* a multi-line ASCII head (#110) — handed chars flip correctly
because it's pixels, not characters.

**What I learned:** the hard part of "mirror this text" evaporates if you stop
thinking in characters and mirror the raster. Render once (facing right), flip for
left.

**The rule:** mirror handed text-art by flipping the rendered surface, never by
swapping characters — render the right-facer once and `transform.flip` for the left.

---

## 3. A quantization "limitation" can be load-bearing — the int-truncation is a determinism asset

**What happened:** #80 asked whether to move the sim off pixel coordinates to
"world units." Auditing found the sim is hybrid — float **velocity**
(`Vector2`) but integer **position** (`Rect`) — and `move_rect` does
`rect.x += vel.x` into an *integer*, truncating every frame
(`core/physics.py:31-34`). My first instinct was "that's a limitation." It's the
opposite: the per-frame truncation **quantizes away sub-pixel float drift**, so
replay and the legacy≡statechart parity oracle don't depend on bit-identical
floating point across platforms. Moving to float world-units would *remove* that
safety net, break every golden, and force retuning every hitbox/knockback — for no
gain over the scale-to-fit resolution independence already shipped.

**What I learned:** before "fixing" something that looks like a crude limitation,
check what it's protecting. The integer snap looked like imprecision; it's the
thing that makes the determinism contract cheap.

**The rule:** when a design has a quantization/coarseness that looks like debt,
prove it isn't load-bearing before removing it — here, int positions are *why*
replay/parity survive cross-platform float noise. (Recorded in
`docs/research/off-pixel-coordinates-findings.md`.)

---

## 4. Park render-only state as a dynamic attribute to stay out of another agent's lane

**What happened:** #108 (live face-style toggle) needed a per-fighter `face_style`.
The natural home is the `Player`/`Fighter` entity — but that file is CHERRY's
active D1 worktree (`area:entities`), and #108 is `area:display`. `Player` has no
`__slots__`, so I set `player.face_style` *dynamically from `game.py`* and read it
with `getattr(p, "face_style", PRIMITIVES)` in the renderer. Zero edits to
`entities/`, so no cross-lane collision, and the default-via-`getattr` keeps it
robust.

**What I learned:** "where does this state belong?" has two answers — the
*conceptually* right home and the *collision-safe* home. When they differ because
another agent owns the natural file, a dynamic attribute set from your own lane is
a clean way to keep the change in-lane.

**The rule:** to attach render-only/debug state whose natural home sits in a busy
lane, set it as a dynamic attribute from your own file and read it with a
defaulted `getattr` — don't edit the other lane's file.

---

## 5. An overlay tinted to its background disappears — give it contrast, let the layer beneath own the identity colour

**What happened:** First cut of #108 tinted the kaomoji face to the cat's
`char_color` — and the orange face vanished into the orange body. The body fill
*already* carries the per-character colour identity; the face is an overlay and
needs to *contrast*, not match. Fix: `ink_for(body_color)` — luminance-based dark
ink on light cats, light ink on dark cats.

**What I learned:** when two layers stack, only one of them should own the "brand"
colour. I'd given the colour job to both, so the top layer self-camouflaged.

**The rule:** an overlay must contrast with what's under it; let the lower layer own
the identity colour and pick the overlay's colour for legibility (luminance flip),
not theme.

---

## 6. A research ticket's deliverable is a sourced ruling + the *right* follow-up — which is sometimes no ticket

**What happened:** Two research closes went opposite ways on purpose. #88 (F10
zoom presses with no visible change) → ruling "intended (no-crop clamp), here's the
measured per-monitor dead-press count, fix it" + a scoped DEV ticket #92. #80
(off-pixel) → a firm "don't do it" recommendation and **no** downstream ticket,
because #45 had already deferred the only dependent work (bigger stages/camera);
filing one would have manufactured work with no current need. Same for the combat
epic: I filed the umbrella (#117) and only the *unblocked* prerequisites (#120
units/sources, #119 Mario spec), cross-linked both ways, and left the #38-gated
implementation children unfiled.

**What I learned:** "close the research" doesn't mean "spawn an implementation
ticket." The honest output is a sourced verdict plus exactly the follow-up the
verdict justifies — occasionally zero.

**The rule:** end a research ticket with a sourced ruling and only the follow-ups
it actually warrants; don't file downstream work that nothing currently needs
(RULES.md "a question/suggestion is not authorization to create work").

---

## What landed

| Artifact | Change |
|---|---|
| `pycats/display.py` + `game.py` | windowed-scale presets, in-fullscreen zoom (dedup'd to distinct sizes), zoom toast (#82/#85/#88→#92/#89) |
| `pycats/settings.py` | first persisted user-state — display prefs, stdlib JSON, env-isolated (#95) |
| `pycats/cat_faces.py` + `render_battle.py` | per-player face-style toggle (E/`;`), glyph faces over the body composite (#108) |
| `RULES.md` + `CLAUDE.md` | "Surfacing run/sim commands" rule — full-path run block for runnable changes (#96) |
| `docs/research/*` , `docs/research-findings-*` | off-pixel (#80), emoji/kaomoji (#103), directional kaomoji (#105), ASCII heads (#110), persist-prefs (#86) |

## Open threads

- **#114** — swap #108's kaomoji/emoji styles for the #110 ASCII profile/3-4 heads
  (retire the glyph styles); ready to build.
- **#119 / #120** — Mario archetype spec + Smash-unit/data-source research; both
  unblocked, gated impl waits on the combat core **#38**. Handoff scratch doc at
  `/tmp/handoff-pycats-119-mario-cat-spec.md` (ephemeral).

## Related artifacts

- [TIL 2026-06-25 DRAGONFRUIT](./today-i-learned-2026-06-25-dragonfruit.md) — the verify-first throughline continues here.
- `docs/research/off-pixel-coordinates-findings.md` (#80); `docs/research/pm-framerate-fidelity.md` (PM 60 FPS).
