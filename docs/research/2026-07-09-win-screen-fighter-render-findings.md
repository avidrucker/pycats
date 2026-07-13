# Win-screen fighter rendering — cat-draw seam findings

**Ticket:** #736 (RESEARCH, bounded spike) · **Scopes:** #728 (DEV — render both fighters on the win screen) · **Next:** architect design pass, then #728 implements.
**Date:** 2026-07-09 · **Agent:** banana

## Headline

**The position-decouple seam #728 needs already exists.** `render_battle._cat_body_surface(p)`
returns a fighter's whole body — ring + fill + stripes + face + name — baked onto a single
padded `SRCALPHA` surface with a **virtual rect** (via `_CatShim`), fully independent of the
fighter's battle `rect` and the camera. Blitting that surface at any `(x, y)` on any surface
draws the cat. Every input it needs is already present on the `Player` objects the win screen
holds (`self.winner` / `self.loser`). So the "draw a cat at an arbitrary point" primitive is
**not net-new work** — it is how the body-composite cache already renders off-field.

What remains for #728 is therefore **not** "build a decoupled draw path" but four smaller
decisions (tint/facing neutralization, scale, placement, and whether to promote the private
`_cat_body_surface` to a public seam), plus the net-new crown + dim overlay. Those are the
architect's forks — see "Decisions I am NOT making".

---

## Q1 — Inputs & coupling (static appearance vs battle-only state)

The cat-draw path splits into two entry styles:

- **Live, on-field draw** — `draw_eye(surface, p)`, `draw_cat_features(surface, p)`,
  `draw_stripes(surface, p)` read the fighter's **real screen position** straight from
  `p.rect` (`p.rect.top`, `.centerx`, `.right`/`.left` gated on `p.facing_right`). These are
  battle-coordinate-coupled and are **not** what the win screen should call directly.
- **Composite draw** — `_draw_body_features(p, face_style)` builds a fresh padded `SRCALPHA`
  surface and hands the same `draw_*` helpers a **`_CatShim`** whose `rect` is a *virtual*
  `pygame.Rect(_BODY_PAD_X, _BODY_PAD_TOP, w, h)` inside that surface. Position-independent by
  construction. `_cat_body_surface` / `_cat_body_layers` wrap it with the silhouette ring +
  name and cache the result.

Inputs the composite reads from the `Player`, sorted:

| Input | Source on `Player` | Kind |
|---|---|---|
| body size `(w, h)` | `p.fighter.stand_size` | static appearance (per archetype) |
| facing | `p.fighter.facing_right` | **battle-derived** (last-faced direction) |
| body colour | `p.char_color` | static |
| eye colour | `p.eye_color` | static |
| stripe colour | `p.stripe_color` | static |
| slot id / accent | `p.char_name` (`"P1"`/`"P2"`) → `slot_accent_color` | static (seat) |
| name label | `p.nickname or p.char_name` | static |
| face style | passed arg, default `cat_faces.PRIMITIVES` | static |
| flash tint | `active_tint(p)` → reads `p.fighter` timers | **battle-only live state** |
| feature outline | `char_color == eye_color == stripe_color` (placeholder) | static (derived) |

**Confirmed present:** `pycats/entities/player.py` exposes `self.fighter`, `char_color`,
`eye_color`, `stripe_color`, `char_name`, `nickname`, and `identity` (`PlayerIdentity.number`,
1 == P1). `Player.rect` is a property delegating to `fighter.rect`. So the win screen's
existing `winner`/`loser` carry everything the composite needs.

**The only two battle-derived inputs are `facing` and `tint`** — both bake into the composite
and both are the substance of the neutralization decision below.

## Q2 — Position decoupling (the seam)

Three options, with tradeoffs:

- **(a) Reuse `_cat_body_surface(p)` and blit at `(x, y)`.** *Recommended.* Near-zero new
  code, exercises the exact tested composite path, honours per-archetype size and the slot
  ring. Blast radius on battle rendering: none (read-only reuse). Caveats: it is **private**
  (`_`-prefixed) — calling it from `win_screen` couples across a private boundary (see the
  promote-to-public fork), and it bakes `facing`/`tint` (see neutralization fork).
- **(b) Extract a public "draw body at point" helper** that `_draw_body_features` and the new
  caller share. Cleaner seam, but it is a refactor of a cached, parity-guarded subsystem
  (`_body_cache` / render-parity oracle) — larger blast radius and test cost than #728 itself.
  Better as a **follow-up refactor ticket** than folded into the screen slice.
- **(c) Win-screen-local re-implementation** (draw body onto a local surface in `win_screen`).
  Avoids touching `render_battle`, but duplicates the body-composition logic and will drift
  from the real fighter look — rejected as a maintenance liability.

**Recommendation for the architect:** ship #728 on **(a)** — reuse the composite — and, if the
private-boundary coupling is judged worth removing, do **(b)** as a *separate* one-line-public
wrapper (`cat_body_surface(p)` delegating to `_cat_body_surface`) rather than a deeper
extraction. Do not choose (c).

## Q3 — Cache interaction

`_body_cache` / `_body_layers_cache` are keyed by `_body_cache_key`: `char_color`,
`stripe_color`, `eye_color`, `char_name`, `nickname`, `facing_right`, **`body_tint(p)`**,
`face_style`, `(w, h)`, `slot_accent_color`. Implications:

- Reusing the cache on the win screen is **safe and beneficial** — same key ⇒ same surface as
  in battle. No new key needed.
- Because the key includes `body_tint(p)`, a **calm** fighter (tint None) and a **flashing**
  one are different cache entries. If the win screen renders while the loser's fighter still
  carries a live hurt/stun tint, it will fetch (and cache) a *flashing* composite — see Q-tint.
- **Do not cache a scaled surface.** If Q4 scaling is applied, scale the *fetched* surface at
  blit time; never bake scale into the cached composite (it would poison the battle cache).

## Q4 — Scale

The composite is battle-native size (`stand_size` + `_BODY_PAD_*`). Whether that reads well on
the win screen is a **visual-design** call for the architect. If scaling is wanted, apply
`pygame.transform.scale`/`smoothscale` to the surface returned by `_cat_body_surface` at blit
time (cheap, local, cache-safe per Q3). No scaling hook is needed inside `render_battle`.

## Q5 — Crown + dim primitives

- **Yellow crown (triangles + rectangles):** no existing "crown" helper. But `YELLOW =
  (255, 255, 0)` is defined in `config.py`, and the polygon-vertex idiom is established
  (`_star_points` + `pygame.draw.polygon` in `draw_dizzy_stars`; ear triangles in
  `draw_cat_features`). The crown is **net-new but trivial**: a `pygame.draw.polygon` per
  triangle + `pygame.draw.rect` for the band, positioned over the winner's cat-head region.
- **25%-black dim overlay:** no dedicated helper, but the `pygame.Surface(size,
  pygame.SRCALPHA)` + fill + blit idiom is pervasive (`_dilated_silhouette`,
  `_draw_body_features`, `SHIELD_FILL_ALPHA = 100`). The loser dim is the same idiom: a
  SRCALPHA surface filled `(0, 0, 0, ~64)` (25% of 255 ≈ 64) blitted over the loser's cat
  region. **Net-new but idiomatic.**

Neither is a blocker; both are a handful of `pygame.draw` / blit calls.

## Q6 — Placement constraints

`WinScreenManager.render` lays the screen out **top-down** by `y_offset`, all horizontally
**centered on `SCREEN_WIDTH // 2`**:

1. winner announcement (`y = WIN_SCREEN_PADDING`)
2. final-stocks line
3. "Game Statistics" header
4. stats table — centered, `total_width ≈ stat_col(180) + 2·player_col(100) + 2·spacing(20)`
   ≈ **420 px wide**, with red/blue confirmation boxes drawn around the P1/P2 columns
5. instructions / confirmation-status line

The horizontal **margins left and right of the ~420px centered table are the natural empty
regions** for the two cats (P1 in the left margin, P2 in the right), which also matches #728's
seat-fixed left/right requirement. Vertical room below the instructions is a secondary option.
The architect picks exact coordinates; the constraint to honour is **do not overlap the stats
table or its confirmation boxes**.

**Seat seam for #728's left/right + winner colouring:** the file already keys the winner colour
off `self.winner.identity.number == 1` (P1), and `render_battle.slot_accent_color` keys off
`p.char_name == "P1"`. #728's horizontal placement must key off the **seat** (`identity.number`
/ `char_name`), **not** winner/loser — that is the one invariant its test should guard.

---

## Tint/facing neutralization (surfaced sub-fork, for the architect)

The two battle-derived composite inputs need a ruling before #728 is implemented:

- **Tint:** `active_tint(p)` reads `p.fighter` hurt/stun/dodge timers. At match end the loser
  was just KO'd; if any such timer is still live when the win screen renders, the composite
  flashes (red/yellow/white) instead of showing the calm body. #728 almost certainly wants a
  **calm** portrait. Options: render through a path that forces `tint=None`, or confirm the
  fighters are guaranteed calm at win-screen entry. Needs a decision + a guard.
- **Facing:** the composite bakes `fighter.facing_right` (last-faced direction). #728 says P1
  left / P2 right but is silent on which way each cat *faces*. If a deterministic facing is
  wanted (e.g. facing inward toward each other, or both forward), the implementer must set
  facing on the render input or flip the surface — otherwise the cats face wherever they
  happened to be looking when the match ended (non-deterministic, and a test-flakiness risk).

## ROI for #728

- Decouple work: **~0** — the composite seam exists; reuse `_cat_body_surface` + blit.
- Net-new: crown (a few polygons + a rect), loser dim (one SRCALPHA blit), placement math,
  and the tint/facing neutralization. All local to `win_screen.py`.
- Estimate stands at ~60m for #728, contingent on the architect settling the four forks below
  so the implementer isn't deciding them mid-courier.

## Decisions I am NOT making (hand-off to the architect pass)

1. **Seam choice** — reuse private `_cat_body_surface` (a) vs. promote a public wrapper (b).
   (Recommendation: (a), optionally + a one-line public wrapper; not (c).)
2. **Tint & facing neutralization** — how the win-screen portrait forces a calm, deterministic
   render (the sub-fork above). This is the highest-risk unspecified item.
3. **Scale** — battle-native size vs. a scale factor, and its value.
4. **Placement coordinates** — exact cat positions in the side margins (or below), and the
   winner-raised vertical offset magnitude.
5. **Crown geometry & overlay alpha** — exact triangle/rect layout and the dim alpha (25% ≈ 64
   is the spec, but exact value is the designer's).
6. **Extract-now-vs-defer** — whether the public-wrapper/extraction (b) is done now or filed as
   a follow-up refactor ticket.

Items 1, 2, and 6 are coupled (the seam decision drives the neutralization surface and the
extraction question); the architect should resolve them together first, then 3–5.
