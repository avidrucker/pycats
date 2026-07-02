# Findings: Project M menu interface — layout, navigation, architecture (#115)

> A bounded research spike mapping Project M's full menu interface so pycats can
> design its screen system + **main-menu Options sub-menu (#116)** against a
> known-good reference, and record where we deliberately diverge. Read-only;
> deliverable is this doc + a short list of design decisions for #116. **No
> production code.**
>
> Sources (cited inline, confidence noted): SmashWiki
> [Project M](https://www.ssbwiki.com/Project_M),
> [Rules](https://www.ssbwiki.com/Rules),
> [Pause](https://www.ssbwiki.com/Pause),
> [Character selection screen](https://www.ssbwiki.com/Character_selection_screen),
> [Versus Mode](https://www.ssbwiki.com/Versus_Mode); and
> [Project+ Features](https://projectplusgame.com/features) (PM's community
> successor — used for the *settings architecture* section, flagged as such).
> Date: 2026-06-26. Ticket #115; informs tracker #116; relates #18, #97 (screen
> system), #99 (parity doc), #111 (status-bar toggle), #95 (settings persistence).
> pycats grounded against `pycats/screen_manager.py`, `pycats/settings.py`,
> `pycats/config.py` (HEAD `f8ecb73`).

## 0. Headline finding (read this first)

**Project M has no single "Options/Settings" screen.** Unlike a modern menu-driven
game, PM (and Brawl/Melee before it) spreads configuration across *context-embedded*
surfaces:

1. the per-match **Rules** menu (game type, time/stock, items, team attack, stage
   pick method, + an unlockable "More Rules" block of toggles);
2. settings **embedded on the Character Select Screen** (controls, tags, port colour
   — heavily so in Project+);
3. settings **embedded on the Stage Select Screen** (hazards, presets, music);
4. a developer-flavoured **Code Menu** for visual/debug toggles (Project+: hitboxes,
   hitstun display, camera lock — reached by a button chord, not a menu item);
5. most of which is **per-session**, not globally persisted.

**Implication for pycats:** our planned **consolidated** main-menu Options sub-menu
(#116) — one screen that gathers display + gameplay-HUD toggles and *persists them as
defaults* via `settings.py` — is itself a **deliberate divergence from PM's
distributed, mostly-ephemeral model.** That is fine (we are a small 1v1 trainer, not
a tournament platform), but it means PM gives us *content* to borrow (which toggles
exist, sensible defaults, confirm/cancel conventions) far more than *structure* to
copy. Record the divergence in the parity doc (#99).

## 1. Screen / menu hierarchy & transitions

PM keeps Brawl's foundational menu tree and renames the competitive bits
([Project M](https://www.ssbwiki.com/Project_M)). Observed flow (confidence: high for
shape, medium for exact labels):

```
Title / "Press Start"
└─ Main Menu
   ├─ Solo
   │  ├─ Training            (PM: default / first solo option)
   │  ├─ Fight!              (PM rename of Brawl "Brawl"/standard match)
   │  ├─ Events, Classic, All-Star, Stadium, Subspace Emissary (kept from Brawl)
   │  └─ Special Versus      (PM rename of "Special Brawl"; Stamina/Stock variants)
   ├─ Group / Versus
   │  ├─ → Rules            (match settings; see §5)
   │  ├─ → Character Select (CSS; see §3) ──→ Stage Select (SSS; see §4) ──→ Match
   │  ├─ Rotation, Tourney, Special, Names
   │  └─ (Project+) Codes    (re-enable the Code Menu; see §7)
   ├─ Vault / Data / Options-ish (Brawl "Options": controls, sound, deflicker, …)
   └─ (online / extras)
   In-match:  Match ──(Start)──> Pause overlay (see §6) ──> Resume / Quit
```

Key transition facts:
- **Group → Rules and Character Select are siblings**, both reached from the Group
  sub-menu; rules can *also* be tweaked from the CSS in Brawl ("where the player may
  sometimes make changes to the rules",
  [CSS](https://www.ssbwiki.com/Character_selection_screen)).
- **CSS → SSS → Match** is the canonical pre-match pipeline. Back/cancel (B) steps up
  one level at each screen.
- PM swaps **Impact font** + a **Melee-like art style** into the menus
  ([Project M](https://www.ssbwiki.com/Project_M)).

## 2. Main menu & modes (PM specifics)

| Item | Detail | Confidence |
|---|---|---|
| Mode renames | "Brawl"→**Fight!**, "Special Brawl"→**Special Versus**, other "Brawl"→**Smash** | explicit |
| Solo default | **Training** is the first/default Solo option | explicit |
| Versus defaults | **4 stock, 8-min timer, Team Attack ON** (Melee-competitive) | explicit |
| Everything unlocked | all characters + stages available from the start | explicit |
| Single-player Versus | a *time* match with infinite time can be started solo | explicit |
| In-match HUD | timer moved to **top-center** (Brawl had top-right) | explicit |

## 3. Character Select Screen (CSS)

- **Melee-like redesign**, altered fonts; independent icons for transforming
  characters (Zelda/Sheik, Samus/ZSS) ([Project M](https://www.ssbwiki.com/Project_M)).
- Per-player cursors; **Random** icon for random character
  ([CSS](https://www.ssbwiki.com/Character_selection_screen)).
- **Project+ embeds a lot of settings here** (confidence: high, but Project+ not PM):
  costume scroll (hold `L`/`R`), secret costumes (`R`/`Z`), **port colour swap** (12
  choices via `L`/`R` over a tag), **tag/name entry**, and a **controls editor**
  (`Y` in tag entry: C-stick = Tilt/Charge/Taunt/Attack, UCF shield-dropping)
  ([Project+](https://projectplusgame.com/features)).

**Takeaway for pycats:** PM/Project+ treat the CSS as the natural home for
*per-player* config (character, colour, controls, tag). pycats already does
character + (implicitly) colour on `char_select`. Controls remapping, if we ever add
it, belongs there — **not** in the global Options sub-menu.

## 4. Stage Select Screen (SSS)

- **Revamped layout**: stage icons in a rectangular grid at the bottom, the selected
  stage shown large at the top, multiple pages, PM background
  ([Project M](https://www.ssbwiki.com/Project_M)).
- **Stage striking** built in via `X` (Full Set).
- Stage-pick *method* is a Rules setting: **Choose / Random / Turns / Ordered /
  Loser's Pick** ([Rules](https://www.ssbwiki.com/Rules)).
- Project+ embeds **hazard toggle** (`Z`, icon frame colour = on/off), **layout
  presets** (`L`/`R`: Legal/PMBR/Proposed/regional/All), **alternate stages**
  (hold `L`/`R`/`Z`), **music select** (`Y`)
  ([Project+](https://projectplusgame.com/features)).

pycats has no stage system today; out of scope, but the SSS confirms the same pattern
— **toggles live on the screen they affect**, surfaced by a face button + a colour cue.

## 5. Rules menu — the closest thing to "settings"

Brawl's Versus **Rules** menu, inherited by PM
([Rules](https://www.ssbwiki.com/Rules)):

| Setting | Range / values | Default | Notes |
|---|---|---|---|
| Game type | Time / Stock / Coin | Stock (PM Versus) | PM Versus default 4-stock |
| Time limit | 1–99 min / infinite | 2:00 (Brawl) | |
| Stock count | 1–99 | 3 (Brawl) / 4 (PM) | |
| Handicap | 0–300% / Auto | off | PM Special Versus replaces with **Stock Control 1–30** |
| Damage ratio | 0.5–2.0 | 1.0 | knockback scaling |
| Team Attack | on / off | off (PM Versus: **on**) | friendly fire |
| Items | None / Low / Medium / High (+ item switch) | — | |
| Stage select | Choose / Random / Turns / Ordered / Loser's Pick | — | |

**"More Rules"** (unlocked after 200 KOs in Brawl — PM unlocks freely): **Stock time
limit, Pause on/off, Score display, Damage gauge visibility, SD penalty, Random-stage
customization** ([Rules](https://www.ssbwiki.com/Rules)).

**Two of these map straight onto pycats settings:** *Pause on/off* and *Damage gauge
visibility* are exactly the kind of HUD/behaviour toggles our Options sub-menu (#116)
will hold — but in PM they are **per-match rules**, not persisted defaults.

## 6. Pause menu ([Pause](https://www.ssbwiki.com/Pause))

- Triggered by **Start**; freezes all action until unpaused. Confidence: high.
- Lets a player **resume** or **abandon/quit** the match (button combo to quit).
- **Camera/snapshot mode** while paused: pan, zoom (`X`/`Y`), switch focus character
  (`L`/`R`) — Brawl adds snapshots. (pycats has no camera; out of scope.)
- **Pause can be disabled** via the Versus rules (tournament standard).

pycats already has a `pause` FSM state + `pause_menu` (Resume / view stats / return to
menu). PM parity here is essentially met; the only borrowable idea is "pause can be
turned off" — a possible future Options toggle, not requested now.

## 7. Where settings actually live + persistence

| Surface | What it holds | Persistence | Source |
|---|---|---|---|
| **Rules** menu | match type, time/stock, items, team-attack, stage method, +More-Rules toggles | per-session (resets) | [Rules](https://www.ssbwiki.com/Rules) |
| **CSS** | character, costume, **port colour, tag/name, controls** | tags stored; rest session/per-port | [Project+](https://projectplusgame.com/features) |
| **SSS** | hazards, layout preset, alternates, music | "session-based adjustments" (not clearly global) | [Project+](https://projectplusgame.com/features) |
| **Code Menu** (`L+R+D-Down`) | **visual/debug toggles**: hitboxes, hitstun, body-collision, ledge boxes, camera lock, big-head | toggled live; re-enable via *Versus → Codes* | [Project+](https://projectplusgame.com/features) |
| **Versus settings** | input buffer (3-frame) | per-session | [Project+](https://projectplusgame.com/features) |
| Brawl **Options** | controls, sound, rumble, deflicker, language | persisted to save | Brawl (general) |

**Architecture notes:**
- Settings are **modal-embedded**, not centralized. The only *global, persisted*
  bucket in stock Smash is the system **Options** (sound/controls/video-ish) — small.
- The **Code Menu is the spiritual home of "show/hide a visual overlay" toggles**
  (hitboxes, hitstun numbers). pycats' **status-timer-bars toggle (#111)** is exactly
  this kind of thing — a *visual-debug/aid overlay*, not a gameplay rule.
- Persistence is mostly **per-session**; PM does not generally save your match-rule
  tweaks as permanent defaults the way pycats' `settings.py` (#95) saves display prefs.

## 8. Input & navigation conventions (Smash/PM)

| Convention | Behaviour | Confidence |
|---|---|---|
| Confirm | **A** | high |
| Back / cancel | **B** (steps up one screen) | high |
| Pause / advance results | **Start** | high (Pause/Results pages) |
| Cursor | D-pad / control stick; per-player cursors on CSS | high |
| Secondary actions | face buttons in-context (`X` strike, `Y` music/controls, `Z` hazards) | high (Project+) |
| State cue via **colour** | e.g. SSS icon frame Orange=on / Blue=off | high (Project+) |
| Hold-to-act | hold `L`/`R`/`Z` for alternates; (pycats already uses hold-B-to-menu, hold-ESC #113) | high |

**Borrow for pycats Options sub-menu:** A=confirm, B=back-one-level, left/right or
up/down to move between toggles, and a **colour/extra cue** for on-vs-off state.

## 9. PM → pycats mapping (feeds #99 and #116)

| PM concept | pycats today | Verdict |
|---|---|---|
| Distributed, context-embedded settings | (none yet) | **Diverge:** pycats builds *one consolidated* Options sub-menu (#116) |
| Per-session rules, not saved | `settings.py` persists display prefs (#95) | **Diverge:** pycats *persists* toggles as defaults |
| Code Menu visual toggles (hitbox/hitstun overlays) | status-timer bars toggle `SHOW_STATUS_TIMER_BARS` (#111) | **Map:** our HUD toggles ≈ PM's Code-Menu overlays |
| Rules: Pause on/off, Damage-gauge visibility | possible future Options toggles | **Map (later):** same idea, but persisted |
| CSS-embedded controls/colour/tag | `char_select` (character; colour implicit) | **Map:** per-player config belongs on char-select, not Options |
| Stage select method / SSS toggles | no stages | **N/A** (out of scope) |
| Confirm=A / Back=B / Start | screen FSM input (`screen_manager.py`) | **Map:** adopt the same convention for Options nav |
| Pause menu (Resume/Quit, pause-off) | `pause` state + `pause_menu` | **Met** (pause-off is a future toggle) |

## 10. Design decisions surfaced for the Options sub-menu (#116)

1. **Consolidated vs embedded:** pycats deliberately picks a **single Options
   sub-menu** (divergence from PM). Accept and document in #99.
2. **Two flavours of setting** will coexist there and should be visually grouped:
   - **Display/system** (zoom, fullscreen) — already persisted via `settings.py`.
   - **Gameplay-HUD overlays** (status-timer bars #111, future: hitbox/damage display)
     — PM treats these as Code-Menu/visual toggles; pycats should still persist them.
3. **Persist everything** the menu changes (PM doesn't; we do — it's our value-add as
   a trainer). Route every change through `settings.save(...)` + a live update.
4. **Nav convention:** A = confirm/toggle, B = back one level, up/down to move, with
   an explicit on/off cue (PM uses colour) — mirror `screen_manager.py`'s FSM input.
5. **Keep per-player config OFF the Options screen:** PM/Project+ put controls,
   colour, and tags on the **CSS**. If pycats adds controls remapping, it goes on
   `char_select`, not Options.
6. **"Pause off" and "hide damage"** are PM-attested toggles we could add later — note
   as candidates, do not file yet (lazy decomposition; #116 lists current scope).

## 11. Gaps & confidence

- **No authoritative single PM "menu map" exists**; this is reconstructed from
  SmashWiki + the Project+ feature list. Mode *labels* and exact sub-menu ordering are
  medium-confidence; the *patterns* (embedded settings, A/B nav, per-session rules)
  are high-confidence and corroborated across sources.
- **Project+ ≠ Project M.** The settings-architecture detail in §3/§4/§7 is from
  Project+ (the successor) and is flagged at each use. It is the best available proxy
  for "how the PM lineage organizes settings," but a purist PM 3.6 audit would differ
  in the Code Menu specifics.
- **No video capture was analyzed**; a follow-up could verify exact Options/Rules
  screen ordering from gameplay footage if higher fidelity is ever needed.
