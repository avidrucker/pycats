# ROUNDS v1 — draft screen: layout + draw rule (design spec)

**Status:** Accepted — 2026-08-03. Resolves the **ROUNDS Mode v1 wayfinder map** (#1096)
prototype ticket **#1103** ("minimal draft screen — pick-1-of-5 UI + its statechart slot").
Epic #347.

This is the **UI + draw-mechanics** detail for the draft screen. The *statechart slot* it sits
in is owned by **ADR-0015** (the dedicated `draft` FSM state, pip-score inline, loser picks /
winner waits, both ready-up, per-round rebuild) and is **not** re-decided here. Pixel-exact
styling is downstream build work; this spec fixes the layout shape, the interaction, and the
card-draw rule a DEV child (#347) builds from.

## Context

Grounding, read from source / prior rulings 2026-08-03:

- **Statechart (ADR-0015):** the draft is a dedicated ROUNDS between-point FSM state; the
  point-loser drafts 1-of-5; the winner waits; the pip-score renders **inline** on this screen
  (no separate point-results state); both players ready-up before the per-point rebuild via
  `create_from_selection` / `build_fighter` (the ADR-0014 recompute boundary).
- **Format (#1098):** a match is scored in **points**, **first-to-5**; the **loser drafts 1**
  per point; **both players draft 1 starting card** at match start.
- **Card pool (#1101):** the 9 buildable v1 cards — Phoenix `+stock`, Chase `+speed`,
  Springs `+jump`, Compact `−body`, Glass Cannon `+dmg/−weight`, Metal `+weight/−speed`,
  Bruiser `+KBG/−dmg`, Long Arms `+reach`, Floaty `−gravity`. (Leech + Empower are slotted but
  their effect shapes are riders — not in the v1 draw pool until their shapes land.)
- **Seeding (#1099):** the draft must ride its **own** seeded RNG stream (independent of the
  per-controller sim RNG) so match-running goldens stay reproducible; the exact seam call is a
  downstream fact #1099 documents.
- **Tempo (premortem #1076 §6, failure #4):** a slow modal draft kills ROUNDS' fast
  pick→counterpick loop. Every choice below favours speed.

## Decisions

### 1. Scope — this ticket owns the draw rule *and* the layout
The screen renders the drawn cards, so the two are one decision. The draw rule is small and
lives here (not a separate downstream ticket).

### 2. Draw rule
Each draft samples **up to 5 distinct valid cards** from the 9-card pool, off the **draft's own
seeded stream** (#1099). **Valid pool** = *(all stackable cards)* + *(once-only cards the player
does not already own)*.
- **Never show on-screen duplicates** — the 5 slots are always distinct cards.
- **Show fewer than 5** when the valid pool is smaller than 5 (no padding). With 8 stackable
  cards this rarely fires (valid pool stays ≥ 8), but the rule is the defined behaviour.

### 3. Stackability (per-card)
A card is **stackable** (can be re-offered / held ×N) unless marked once-only. A once-only card
drops out of that player's valid pool once owned.

| Card | Stackable? |
|---|---|
| Phoenix, Springs, Chase, Compact, Glass Cannon, Bruiser, Long Arms, Floaty | ✅ stack |
| **Metal** | ❌ once-only |

Stacking *magnitude/balance* math (does holding Chase ×3 snowball?) is **out of v1 scope** —
deferred to post-v1 balancing (#1156). This spec only fixes which cards may be re-offered.

### 4. Card face
Placeholder large **emoji / ASCII glyph** + **name** + **effect line(s)** (both signs shown for
trade cards, e.g. Glass Cannon `+dmg / −weight`) + an **`(own ×N)`** tag when the player already
holds it. Text-render only — no art pipeline in v1. Glyphs are placeholders, swappable later
(🔥 Phoenix · 💨 Chase · 🦿 Springs · 🤏 Compact · 💥 Glass Cannon · ⚙️ Metal · 🥊 Bruiser ·
🦾 Long Arms · 🎈 Floaty).

### 5. Layout
A **horizontal row of 5** cards, a cursor highlight on the selected card, **←/→** to move.

### 6. Selection
**One button commits immediately** — no confirm modal. **No draft timer** in v1 (local hotseat;
a stall is a social problem, not a design one). A misclick costs one card in a first-to-5 match
and the player drafts again next point — acceptable for the tempo win.

### 7. Display around the choosing
- **Pip-score top-center, inline** — both players' pips toward first-to-5 (doubles as the
  point-result feedback: the loser's point loss shows as the opponent's filled pip).
- **Both players' owned-card strips** shown (so stacking + "what does my opponent hold" is
  legible — the info that makes the pick a decision).

### 8. Advance (exit to next point)
The loser's pick is **revealed to both players** (drops into the owned strip), then **each player
taps ready** → rebuild → next point. This is ADR-0015's "both ready-up"; the reveal is the moment
the winner learns what they now face (counterplay). A tap is not a modal — tempo holds.

### 9. Starting draft (match start)
A **coin flip** picks who drafts first; **sequential** (one row + one cursor at a time). Each
player picks 1 from their **own independent batch of 5** (batches drawn separately, so both may
be offered — and take — the same card). Each ends with 1 starter card → point 1. Reuses the same
single-row screen with a "P_ picks first (coin flip)" header.

## Prototype (ASCII mockup)

Placeholder art; exact spacing/pixels are downstream build detail.

**Between-point draft (P1 won the point; P2 drafts):**
```
        ┌──────────────  ROUNDS  ──────────────┐
        │  P1  ●●●○○      P2  ●●○○○   (first to 5)│
        └───────────────────────────────────────┘
                  P2 — pick a card

  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
  │  💨   │ ┃  💥   ┃ │  🎈   │ │  🦿   │ │  ⚙️   │
  │ CHASE │ ┃GLASS  ┃ │FLOATY │ │SPRINGS│ │ METAL │
  │+move  │ ┃CANNON ┃ │−grav  │ │+1 jump│ │+weight│
  │ speed │ ┃+dmg   ┃ │       │ │       │ │−speed │
  │       │ ┃−weight┃ │       │ │(own×1)│ │       │
  └───────┘ ┗━━━━━━━┛ └───────┘ └───────┘ └───────┘
              ▲ ←/→ move · ATTACK to pick

  P2 build: 🦿×1 🥊×1          P1 build: 💨×2 🤏×1
```

**Reveal + ready beat (after the pick):**
```
      P2 drafted  💥 GLASS CANNON  (+dmg, −weight)

  P1 build: 💨×2 🤏×1      P2 build: 🦿×1 🥊×1 💥×1

           P1 [ READY ]      P2 [ READY ]
              press ATTACK to ready up
```

**Starting draft (coin flip → P2 first; then P1's turn with its own fresh batch):**
```
        ┌──────────────  ROUNDS  ──────────────┐
        │  P1  ○○○○○      P2  ○○○○○   (first to 5)│
        └───────────────────────────────────────┘
          Starting draft — P2 picks first (coin flip)

  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
  │  ⚙️   │ │  🔥   │ │  🦾   │ │  🤏   │ │  🥊   │
  │ METAL │ │PHOENIX│ │LONG   │ │COMPACT│ │BRUISER│
  │+weight│ │+1     │ │ ARMS  │ │−body  │ │+KBgrow│
  │−speed │ │ stock │ │+reach │ │ size  │ │−dmg   │
  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

## Consequences / downstream (v1 build scope — #347 children, filed one-at-a-time)

- Build the `draft` screen (row-of-5 render + cursor + owned strips + inline pip-score) in the
  ADR-0015 FSM state; both render branches (`ScreenStateManager.render` +
  `screen_render.py::render_active_screen`) must be wired to avoid the documented not-drawn bug.
- Implement the seeded draw (`sample` up to 5 distinct valid cards) on the #1099 draft stream.
- The card-face emoji glyphs are placeholders; an art/legibility pass is later polish.
- The starting-draft coin flip must also ride a seeded stream so goldens stay reproducible.

## References

- Map #1096 (ROUNDS Mode v1 wayfinder map) · epic #347.
- #1103 (this ticket) · #1098 (format params) · #1099 (seeding contract) · #1101 (starter card
  set) · #1156 (post-v1 balancing — stacking magnitude).
- ADR-0015 (screen-flow: the draft's statechart slot) · ADR-0014 (per-round recompute) ·
  ADR-0013 (fighter-seam contract).
- `docs/research/2026-08-02-rounds-x-pm-fit-premortem-findings.md` §6 (tempo, failure #4).
- Source touched downstream: `pycats/shell/screen_manager.py`,
  `pycats/shell/screen_render.py`, `pycats/screens/`, `pycats/loadout/build_fighter.py`.
