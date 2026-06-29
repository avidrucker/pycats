# Menus & game flow — PM mechanics reference

> The **front-end**: how a match is set up (character select, stage select,
> rules), the screen flow around it, and the results screen after. This doc owns
> the *front-end + match-flow* model; in-match fighter behaviour is the combat/state
> docs, stage *geometry* is [stages-and-environment](./stages-and-environment.md)
> (stage *select* is here), and pycats' own screen implementation lives in the
> footer. Part of the [PM mechanics reference](./00-overview.md)
> ([epic #147](https://github.com/avidrucker/pycats/issues/147)); PM 3.6.

**Audience:** a contributor — human or agent — about to implement or modify menus,
screen flow, or match settings. Reference depth, not a tutorial; assumes the
[00-overview](./00-overview.md) conventions.

## Headline: PM has no single "Options" screen

Unlike a modern menu-driven game, PM (and Brawl/Melee before it) **spreads
configuration across context-embedded surfaces**, most of it **per-session, not
globally persisted**:

1. the per-match **Rules** menu (game type, time/stock, items, team attack, stage-pick method, + a "More Rules" toggle block);
2. settings **embedded on the Character Select Screen** (controls, tags, port colour);
3. settings **embedded on the Stage Select Screen** (hazards, music, presets);
4. a developer-flavoured **Code Menu** (visual/debug toggles — hitboxes, hitstun display, camera lock — reached by a button chord in Project+), not a menu item.

There is no consolidated "Settings" page to mirror — a port has to *decide* whether
to follow PM's distributed model or consolidate (see the pycats divergence in the
footer).

## Screen flow

The canonical loop:

```
title → main menu → mode (Versus/…) → Character Select (CSS) → Stage Select
      → MATCH → Results → (rematch ↺ to CSS, or back to menu)
```

Pausing mid-match opens a **pause menu** (resume / retry / quit), itself a small
settings surface.

## Character Select Screen (CSS)

- Each player picks a **character** and a **costume/port colour**; players **ready
  up** before the match starts.
- **Team / handicap / tag** toggles live here; PM (and especially Project+) embeds
  a lot of per-player config on the CSS.
- Cosmetic costume/skin selection is the CSS hook a port plugs character art into
  (in pycats, the cat-skin feature [#16](https://github.com/avidrucker/pycats/issues/16)/[#127](https://github.com/avidrucker/pycats/issues/127)).

## Stage Select

- Pick from the **legal stage list** (hazardless/legal versions for competitive
  play), plus **random**; competitive sets often use **stage striking**.
- Stage-embedded settings (hazards on/off, music) live here.
- *Which* stages exist and their grabbable-edge geometry is
  [stages-and-environment](./stages-and-environment.md); this is the *selection*.

## Match / ruleset settings

The **Rules** menu defines how a match starts and ends:

- **Game type:** **stock** (N lives — the tournament standard), **time** (most KOs
  in a time limit), or **stamina** (HP-based).
- **Time limit**, **team attack**, **handicap**, **items** (frequency/set —
  tournament: off; see [items](./00-overview.md)).
- A match **ends** when a stock/time/stamina condition resolves — and a "KO" is a
  fighter crossing a blast line ([stages-and-environment](./stages-and-environment.md)
  / [combat-knockback-hitstun](./combat-knockback-hitstun.md)). Stock = lose all
  lives; time = highest KO count; the result feeds the results screen.

## Results screen

After the match: **placement + stats** (KOs, falls, damage, etc.), a winner
declaration, then **advance** — typically a single button press to rematch (back to
CSS) or return to the menu.

## Debug / feature menus

PM/Project+ expose developer toggles via a **Code Menu** (button-chord) —
hitbox/hurtbox display, hitstun/​frame display, camera lock, infinite-shield, etc.
Useful as a model for a port's training/debug overlay.

## Brawl / Melee / PM deltas

- **PM/Project+ add CSS + debug features** (more port config, the Code Menu)
  on top of Brawl's front-end.
- **Distributed, ephemeral settings** is a family trait (Melee→Brawl→PM); the
  modern "one Settings screen, persisted" pattern is *not* how PM works.
- Ruleset *values* (default time, stock count) are competitive-convention, not
  engine constants.

## Sources

- [`docs/research/project-m-menu-architecture.md`](../research/project-m-menu-architecture.md) — PM's full menu interface: layout, navigation, the distributed-settings finding (#115).
- [`docs/research/screen-flow-statecharts-port-findings.md`](../research/screen-flow-statecharts-port-findings.md) — pycats' screen-flow architecture + the statecharts-port question.
- SmashWiki — [Rules](https://www.ssbwiki.com/Rules), [Character selection screen](https://www.ssbwiki.com/Character_selection_screen), [Versus Mode](https://www.ssbwiki.com/Versus_Mode), [Pause](https://www.ssbwiki.com/Pause).
- Stage geometry: [stages-and-environment](./stages-and-environment.md); match-end KO: [combat-knockback-hitstun](./combat-knockback-hitstun.md). Conventions: [00-overview](./00-overview.md).

## pycats status

Implemented:
- **Screen flow** — title → menu → battle (as a game state) → win/results, via the
  screen manager / FSM ([#18](https://github.com/avidrucker/pycats/issues/18); the statecharts-port question is [#100](https://github.com/avidrucker/pycats/issues/100)). Title is "Cat Fight" ([#17](https://github.com/avidrucker/pycats/issues/17)).
- **Character select** ([#16](https://github.com/avidrucker/pycats/issues/16)); **results/win screen** with stats.
- **Match engine** — stock-based `in_play` / `match_over` (`systems/match_engine.py`); a KO = blast-line crossing.
- **A consolidated main-menu Options sub-menu** ([#121](https://github.com/avidrucker/pycats/issues/121) shipped; tracker [#116](https://github.com/avidrucker/pycats/issues/116)) gathering display + HUD toggles (e.g. the status-timer bar [#111](https://github.com/avidrucker/pycats/issues/111)), with the hold-ESC-to-quit option.

**Deliberate divergences (logged at [#99](https://github.com/avidrucker/pycats/issues/99)):**
- **Consolidated, persisted Options** vs PM's distributed, mostly-ephemeral settings — pycats is a small 1v1 trainer, so one Options screen that persists defaults (`settings.py`) is intentional, **not** PM-faithful.
- **Rematch needs both players to confirm** (both-press-A + 2 s grace) vs PM's single-press advance — fixes [#10](https://github.com/avidrucker/pycats/issues/10) (the mashed killing-blow skipping the stats screen); see [#11](https://github.com/avidrucker/pycats/issues/11). This is the seed entry of the parity doc.

**Deferred:** full PM **CSS** (costumes/tags/teams/handicap), **stage select** (single static stage today → [stages-and-environment](./stages-and-environment.md)), a **ruleset-config UI** (stock/time/items toggles), and a **debug/Code menu**. Open questions: [#24](https://github.com/avidrucker/pycats/issues/24).
