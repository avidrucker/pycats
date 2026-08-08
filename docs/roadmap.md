# pycats roadmap — v1 vs post-v1

The release line, at a glance. **The `v1` and `post-v1`/`deferred` GitHub labels are the source of
truth; this file is generated from them** (regen commands at the bottom) — so a new issue is v1-or-not
by its label, not by memory, and the two halves can't silently drift. Subsumes the earlier
`v1-scope.md` + `post-v1-features-scope.md` plan (#560 / #457).

## Definition of v1

**v1 ships when every open `v1`-labelled issue is closed.** v1 is a playable local-multiplayer,
Project-M-flavoured fighter:

- **All 5 archetype cats** (Nalio/Marth/Kirby/DK/Fox lineage) with working movesets;
- **Core movement** — walk/dash/run, jumps, ledge, respawn;
- **Core defense** — shield + spot/roll/air dodge (incl. the CPU's reactive spot-dodge);
- **Full CPU** — the Lv1-9 difficulty ladder;
- **The captioned showcase demo** + playback controls;
- **Flow** — char-select → battle → win; keyboard controls; hit/hurtbox overlay OFF for release.

Deferred to **post-v1**: player profiles / custom keybindings / stats, attack-visual juice, menu/UX &
HUD polish, alt skins, a changelog screen, and 2nd-(GameCube)-controller support.

## What's NOT on this roadmap

Research / decision / spike / tracker / docs tickets carry **neither** label — they're the machinery
that scopes/decides/documents the features below, tracked via their parent feature's links, not as
roadmap line-items.

---

## ✅ In v1  (`v1` label — 24 open)

- **Entities / movement** (4): #267 · #388 · #475 · #482
- **Combat / fighters** (7): #117 · #142 · #228 · #231 · #261 · #294 · #363
- **Screens / flow** (1): #18
- **Display / HUD** (5): #241 · #336 · #506 · #531 · #547
- **Demo / showcase** (7): #308 · #421 · #428 · #430 · #431 · #514 · #515

## 🕒 Deferred — post-v1  (`post-v1` or `deferred` label — 22 open)

- **Entities / movement** (1): #400
- **Combat / fighters** (2): #51 · #347
- **Screens / flow** (12): #20 · #127 · #134 · #361 · #391 · #438 · #441 · #442 · #460 · #479 · #544 · #548
- **Display / HUD** (6): #125 · #217 · #550 · #551 · #558 · #567
- **Demo / showcase** (1): #508

<details><summary>Full list with titles</summary>


**v1:**

- #18 — Scope & complete the screen system (manager + transitions)
- #117 — Epic: 5 cat fighters playing as Project M archetypes (Mario/Marth/Kirby/DK/Fox)
- #142 — Epic: Phase 2 — Moveset (move-selection seam + Nalio's full kit, data-driven)
- #228 — Epic: Birky — Kirby-archetype cat fighter (floaty featherweight)
- #231 — Epic: CPU difficulty levels (Lv1-9) + named-character match setup → runnable Lv5-vs-Lv9 Nalio sim
- #241 — DEV: revert hit/hurtbox overlay back to default OFF before release
- #261 — Tracker: Birky's remaining non-data work — engine prerequisites (fast-fall, specials mechanics, selectability)
- #267 — Epic: PM ledge mechanics — v1 follow-ups (deferred from #14)
- #294 — Epic: Narz — Marth-archetype cat fighter (disjointed swordfighter)
- #308 — Epic: Nalio-vs-Birky feature-showcase demo — captioned, choreographed, recorded
- #336 — DEV: respawn countdown indicator — seconds-to-respawn near the player's stock/damage HUD (split from #334)
- #363 — DEV: reactive spot-dodge — in-place evade as an alternative defensive option (deferred from #338)
- #388 — Epic: implement the basic walk/dash/run movement layer (per #374 design)
- #421 — Expand the showcase — add a ledge-recovery beat (get up from the hang onto the stage)
- #428 — Showcase: add an aerials beat — Nalio's fair/uair/dair off a jump
- #430 — Showcase: add a defensive-options beat — spot-dodge + air-dodge (alongside the shown roll)
- #431 — Showcase: add ledge-getup variants — roll / attack / jump getup (beyond neutral)
- #475 — DEV: remove the ledge-hang auto-drop timeout (LEDGE_HANG_FRAMES) — PM has no hang timer
- #482 — Epic: full-PM respawn model — revival platform + respawn invincibility + grounded spawn (per #480)
- #506 — DEV(entities): respawn invincibility — intangible window on respawn (slice 1 of #482)
- #514 — DEV: any key ends a caption pause early — interruptible timed dwell (demo/sim playback)
- #515 — DEV: hold Escape ~2s to exit demo/sim playback (replaces tap-Esc)
- #531 — DEV(display): give ledge-invuln its own INVULN timer bar — one STATUS_SOURCES entry (closes the #513 drift)
- #547 — DEV: ASCII fallback for arrow/marker glyphs in render_text_mixed (no more "?")

**deferred:**

- #20 — Add hold-B-to-menu circular progress indicator
- #51 — Research (BLOCKED by #38): consecutive-hits off-stage launch — tuning/spec, deferred until base combat phases land
- #125 — Epic: Nalio attack VISUALS — per-move animation + FX (claw/fist juice)
- #127 — Epic: alt skin / colour-palette selection per character (archive OG cats → palettes → CSS picker)
- #134 — No in-app way to see recent changes — versioning/changelog screen is missing
- #217 — DEV: cat-paw primitives at Nalio's hitbox positions — make attacks visibly land (#125)
- #347 — Epic (deferred): 'Rounds Mode' — ROUNDS-style power-up card drafts between fights
- #361 — DEV: menu activation feedback — press-pop on confirm + invalid-press cue (#332)
- #391 — DEV: color menu toggle buttons by state — ON=green, OFF=red, non-binary=yellow
- #400 — DEV: a hit on a vulnerable ledge-hanger deals damage but no knockback — should knock them off (post-V1, #267)
- #438 — Epic: user profiles & custom keybindings
- #441 — DEV: player profiles — nickname (≤4 chars) + profiles/ JSON + nickname above the fighter + associated keybindings
- #442 — DEV: stats logging for players with saved profiles
- #460 — feat(screens): dedicated end-of-battle stats screen subsuming win_screen
- #479 — DEV: player-profile create/select UI in char-select — nickname entry + keybinding set, apply on start
- #508 — DEV (post-v1): skip-to-next-section in demo/sim playback — fast-forward gameplay to the next caption
- #544 — Epic: a11y/UX polish — follow-ups from the #346 menu/prompt/text audit
- #548 — DEV: parallel terminology for Options toggle labels
- #550 — DEV: HUD visual hierarchy — emphasize Damage/Lives, demote the rest
- #551 — DEV: background-independent HUD legibility — text shadow or backplate
- #558 — Epic (deferred, post-v1): PM-faithful invincibility blink/flicker — research + cost/benefit assessment
- #567 — feat(render): subtle idle-stance breathing animation so cats read as alive

</details>

---

## Regenerate (labels are the source of truth)

```bash
gh issue list --state open --label v1        --json number,title,labels   # the In-v1 set
gh issue list --state open --label post-v1   --json number,title,labels   # deferred (feature parks)
gh issue list --state open --label deferred  --json number,title,labels   # deferred (phase-gated)
```

To move an item across the line, change its label — then regenerate this file. Related: parity progress
lives in `docs/project-m-parity.md`; PM mechanics register in `docs/project-m-rules-by-category.md`.
