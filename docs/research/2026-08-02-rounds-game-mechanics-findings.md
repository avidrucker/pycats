# How does ROUNDS (Landfall Games) actually play? — core loop, card catalog, and why it's fun — findings

**Ticket:** #1075 (RESEARCH · `area:combat`) · **Date:** 2026-08-02 · **Agent:** FIG
**Parent:** #347 (Rounds Mode epic, deferred). **Sibling child:** the ROUNDS×PM fit premortem.
**Deliverable:** this doc. **No pycats spec, no design decisions** — the ROUNDS→pycats mapping belongs to a downstream design/architect child (research never produces a spec). Sources cited inline; every claim is tagged with its evidence grade (below).

> **Reconciled 2026-08-02 (follow-up #1085).** §2–§6 below were written from secondary sources because the authoritative Fandom wiki pages returned HTTP 402 to the fetcher. Avi supplied those pages' contents, and **[§8](#8-fandom-wiki-reconciliation-primary-source--1085) is the primary-sourced reconciliation** — it confirms the core-loop numbers, resolves the `[Conflict]` items, corrects several secondary-source errors, and gives the **complete 67-card catalog** with exact stats. Where §8 disagrees with §2–§6, **§8 wins.**

> **Subject.** ROUNDS is the 2021 1v1 rogue-lite dueling shooter by Landfall Games — *not* any physical card game, tabletop "Rounds," or the NFL draft (all of which polluted the searches). Everything here is about the Landfall video game, Steam app `1557740`.

---

## 0. How to read the evidence grades

ROUNDS is **external canon** (not Project M), so there's no `.claude/evidence.json` governance and no Tier-1/2/3 disasm ladder. Instead each claim carries one of:

| Grade | Meaning | Trust |
|---|---|---|
| **[Official]** | Landfall press kit / Steam store page | Highest — the developer's own words |
| **[Reported]** | ≥2 independent walkthroughs/reviews agree | Good, but secondary |
| **[Conflict]** | Sources disagree on the exact number | **Confirm before building on it** |
| **[Inference]** | My reasoning from the above; not stated by a source | Treat as a hypothesis |
| **[Gap]** | No source found; only gameplay footage or the game itself would settle it | Open question for Avi |

**Evidence sufficiency is Avi's call** (per the ticket) — this doc flags what's thin; it does not gate the epic on my own judgment.

---

## 1. TL;DR — the headline answer

**The loop, in one breath:** two stick-figures with noodle arms duel to the death in a small arena. **Whoever loses a point picks a random upgrade card**, so the trailing player steadily out-builds the leader — a self-balancing rubber band that keeps every match tense to the last point. Cards are **permanent for the match and stack**, so builds escalate from "a gun" to absurd combos ("a shotgun-rocket-launcher that shoots heat-seeking bouncy missiles"). **[Official]/[Reported]**

**The four numbers that define it [Official]:** **65+** unique power-ups · **70+** maps · **11.2 million** power-up combinations · **1v1 only** (online + local). Released **2021-04-01**, built in ~5 months by **Wilhelm Nulynd** at Landfall. 96% "Overwhelmingly Positive" over ~26,200 Steam reviews.

**The one correction #347 needs up front:** #347's "Proposed mechanics" guessed *"every 2 losses, pick 2 of 6."* The wiki confirms the loser drafts **after each full point conceded** (a full point = **2 kills**, one half-point per kill), and picks **1 card from a pool of 5** — i.e. **pick-1-of-5, not pick-2-of-6**, and the cadence is *per point*, not *per two match-losses*. Both of #347's numbers are off; §3.1 audits each, now **[Confirmed]** by §8. **[Confirmed]**

**Evidence gaps — status after the #1085 reconciliation:** the **kills-per-point (2)**, **points-per-match (first to 5, configurable)**, **card cap (5)**, and **draft pool size (5)** are now **[Confirmed]** from the primary wiki (§8) — the earlier `[Conflict]`s are resolved. Still open **[Gap]**: exact **duel/match durations in seconds** (no source states them) and the **global stat-stacking formula** (the wiki confirms some specifics — e.g. Trickster self-caps — but no overall add-vs-multiply rule). Neither blocks the epic.

---

## 2. The core loop, precisely

> **Primary-confirmed in [§8](#8-fandom-wiki-reconciliation-primary-source--1085).** The `[Conflict]` grades in this section were resolved by the Fandom wiki: **2 kills = 1 point** (half-point per kill), **loser picks 1 of 5**, **first to 5 points** (round limit configurable in the Steam version), and a **5-card cap**. Read §8 for the verbatim quote.

### 2.1 What a match is made of

ROUNDS nests three layers. Writers (and the game's own UI) reuse the word "round" loosely, which is the root of most of the conflict below. The clearest naming:

| Layer | What ends it | What it's worth |
|---|---|---|
| **Duel** (a single life) | one player dies | a "half-point" / one kill **[Reported]** |
| **Point** (a pip at the top of the screen) | one player wins the required kills | 1 point; **triggers a draft for whoever conceded it** **[Reported]** |
| **Match** | one player reaches the point target | the win **[Reported]** |

- **Kills-per-point:** the most detailed walkthroughs (the official-style Steam "how to play" guide, the *Bits & Pieces* write-up, and the Fandom summary) describe a **best-of-3**: *"each person has to win twice to advance,"* i.e. **first to 2 kills = 1 point**. **[Reported]** One SEO recap (rounds.network) instead says *"one elimination = one point,"* directly contradicting this. **[Conflict]** → treat best-of-3-per-point as the leading reading, but confirm.
- **Points-per-match:** commonly stated as **first to 5 points** (with a hard stop / loss condition around a full card collection), and the **round limit is adjustable in the Steam version**. **[Reported]** *Bits & Pieces* frames it as "best-of-3 across five rounds," which is another wording of the same escalation. **[Conflict]** on the exact default — **[Gap]** on the authoritative number.

### 2.2 What resets vs. what persists

| Between points | Behavior | Grade |
|---|---|---|
| Fighter **health** | resets to full (+ any card HP) | [Reported] |
| Fighter **position** | reset — players respawn on opposite sides of the arena | [Reported] |
| The **arena/map** | can change; there are 70+ maps | [Official] map count; [Inference] on per-point rotation |
| **Cards / build** | **persist for the whole match** — *"once chosen, cards stay with you for the entire match"* | [Reported] |
| **Score (pips)** | persists — it's the match state | [Inference] |

So a point is a clean physical reset (fresh HP, fresh spawn) layered over a **monotonically growing build** — the tension comes from the build gap widening, not from any carried-over damage.

### 2.3 Modes and overtime

- **1v1 only** in the base game — online PvP, local/split-screen PvP, and Remote Play Together. **[Official]** There is **no official 2v2**; the community fills that with mods (e.g. the Thunderstore modding scene). **[Reported]/[Inference]**
- **Sudden death / overtime:** no source describes a distinct overtime state; the match simply ends when the point target is reached. **[Gap]**

---

## 3. The draft, precisely

**When:** immediately **after a point is scored**, before the next point begins. **[Reported]**

**Who:** the **losing player only** — the one who just conceded the point. This is the whole balance engine: *"a choice of cards is granted … following a round that the player did not win (for balance reasons)."* The winner gets nothing that round. **[Reported]** (A popular streamer variant — "the winner earns a card but the **loser** picks which one they're forced to take" — is a self-imposed house rule, **not** the base game. **[Reported]**)

**How many offered / picked:** the loser is shown a **small random hand and picks exactly one**. The pool size is where sources split:
- **5 cards** — the Steam how-to guide, *Bits & Pieces* ("one of five random perk cards"), and the Fandom summary all say five. **[Reported]**
- **3–5 cards** — rounds.network hedges to a range. **[Conflict]**
- → Leading reading: **pick 1 of 5**. Flag for footage confirmation; the exact hand size is a **[Gap]**.

**Permanence & stacking:** picks are **permanent for the match** and **the same card can be taken repeatedly to amplify it** — *"you can select the same card multiple times for amplified effects."* You cannot remove or swap a card once taken. **[Reported]**

**Rarity biases the draft [Reported]** (rounds.network, corroborated by the Fandom card page's rarity description):

| Rarity | Corner marker | Draft frequency | Character |
|---|---|---|---|
| Common | (no color) | most frequent | straightforward stat boosts (Damage Up, Quick Shot, Huge) |
| Uncommon | blue | moderate | unique mechanics (Explosive Bullets, Echo, Leech, Teleport) |
| Rare | magenta/purple | rare | build-defining (Glass Cannon, Demonic Pact, Phoenix, Poison) |

### 3.1 #347's "Proposed mechanics" — audited against evidence

| #347 claim | Evidence says (wiki-confirmed, §8) | Verdict |
|---|---|---|
| "every **2 losses**" you draft | You draft after **each full point conceded**; a full point = **2 kills** (a half-point per kill) | **Imprecise** — cadence is per-point; the "2" is the kills-per-point, not two match-losses. **[Confirmed]** |
| "pick **2** cards" | You pick **1** | **Wrong** — one card per draft. **[Confirmed]** |
| "of **6**" | Pool is **5** | **Wrong number** — 5, not 6. **[Confirmed]** |
| format / catalog "TBD" | 1v1, **first-to-5 points** (configurable), **5-card cap**, **67-card** catalog (§8) | **Now grounded.** **[Confirmed]** |

---

## 4. The card catalog — grouped by effect family

> **Superseded by [§8](#8-fandom-wiki-reconciliation-primary-source--1085) for exact numbers.** This section is the *thematic grouping* (useful for a designer thinking in families). The **complete 67-card table with exact stats and rarity** — plus the specific corrections the primary source forces (e.g. Cold Bullets is a bullet-*slow* card, not a spread; Glass Cannon is Uncommon, not Rare) — lives in §8.4. Use §8 for any number you'll build on.

**Official count: 65+ power-ups [Official]; the wiki enumerates 67 (§8).** Below is a representative, near-complete enumeration compiled from a card-list guide (magicgameworld) cross-checked against the rounds.network rarity guide. Effect text is quoted from the guide; treat exact magnitudes as **[Reported]** (guides can lag balance patches) and stacking behavior as **[Inference]** where noted. **§8 corrects the errors this secondary list carries.**

The design is built on **trade-offs**: almost every offensive card carries a **downside** — more damage/bullets in exchange for **+reload time**, lower per-bullet damage, or lower HP. That tension is the balance backbone (§5).

### 4.1 Damage & projectile modifiers (offense)
- **Glass Cannon** — loads more damage, *a lot lower HP* (the archetypal risk card)
- **Careful Planning** — loads more damage, lower attack speed, +0.5s reload
- **Combine / Wind Up** — big damage, fewer ammo / lower attack speed, +reload
- **Big Bullet** — larger projectiles, +0.25s reload
- **Barrage / Buckshot / Burst / Spray / Cold Bullets** — multi-bullet spreads (+4/+2/+12 ammo, "loads more bullets"), each at *lower per-bullet damage* + reload penalty (shotgun/SMG archetypes)
- **Fastball / Quick Shot / Steady Shot / Fast Forward** — bullet-speed boosts, mixed reload trade-offs
- **Grow** — bullets gain damage the longer they travel
- **Demonic Pact** — removes shooting cooldown, +9 bullets, +splash — but **shooting costs 10 HP** (a downside card)

### 4.2 Bounce / homing / steering (projectile behavior)
- **Ricochet / Mayhem** — +bullet bounces (+2 / +5)
- **Trickster** — bullets deal **+80% damage per bounce**, +2 bounces (bounce-scaling build)
- **Target Bounce** — bullets seek visible targets when bouncing
- **Remote** — steer bullets manually with stick/mouse
- **Drill Ammo / Sneaky** — bullets drill through walls / avoid the ground
- **Thruster** — bullets shove targets on hit

### 4.3 Damage-over-time & lifesteal (attrition)
- **Poison / Parasite / Toxic Cloud** — bullets apply DoT (3–5s); Parasite also adds lifesteal + HP + damage
- **Decay** — damage *dealt to you* is spread over 4s (defensive DoT)
- **Leech / Life Stealer** — lifesteal on hit / when near the enemy
- **Explosive Bullets / Timed Detonation / Toxic Cloud** — on-impact AoE

### 4.4 Movement & tempo (utility)
- **Chase** — +60% move speed *toward* the opponent
- **Taste of Blood** — +50% move speed for 3s after dealing damage
- **Scavenger** — dealing damage reloads your weapon
- **Quick Reload / Tactical Reload** — reload-speed / reload-on-block

### 4.5 Defense, HP & block-triggers (the "on-block" family — a whole mechanic)
Blocking is its own action, and a large card family *triggers effects when you block* (trading a +block-cooldown for the effect):
- **Raw HP:** Huge, Tank, Brawler (+200 HP for 3s after damage), Pristine Perseverance (+400 HP above 90%), Defender, Decay
- **On-block offense:** Bombs Away, Frost Slam, Shock Wave, Static Field, Saw, EMP, Supernova, Overpower (15% max-HP AoE), Radiance (reload-triggered sun waves)
- **On-block control:** Implode / Supernova (pull), Silence, Chilling Presence / Frost Slam (slow), Radar Shot (auto-target)
- **On-block defense/utility:** Echo (delayed second block), Healing Field, Tactical Reload, Shield Charge (dash + free block), Teleport (blink on block), Empower (charged next shot)
- **Survival:** Phoenix (respawn once on death, lower HP)

### 4.6 How effects stack
- **Same card repeated → amplified** (explicit). **[Reported]**
- Guides describe a **mix of additive** (flat +HP, +bullets, +ammo) **and multiplicative** interactions (e.g. Grow's travel-damage compounding with per-bounce Trickster scaling), and note **no hard damage cap** is documented. Exact formulas and caps are **[Gap]** — only the game/footage resolves them. **[Inference]/[Conflict]**
- The interesting design surface is **synergy/anti-synergy**: e.g. many-bounce + per-bounce-damage (Trickster + Ricochet) is a multiplicative engine; Glass Cannon + no-HP block cards is an anti-synergy (you die to a stray hit). **[Inference]**

---

## 5. What makes it fun (design analysis)

Five mechanisms, each tied to a source where possible; the rest labeled inference.

1. **The rubber-band / catch-up loop is the whole game.** Only the *loser* drafts, so power flows to whoever's behind. *"The game balances itself by giving losing players more abilities to catch up … comebacks are always possible and no two matches play out the same way."* The score stays close, so tension stays high to the final point. **[Reported]** This is the single mechanic most worth preserving in any adaptation. **[Inference]**
2. **Forced experimentation via randomness.** You're offered a *random* hand of ~5, so *"you can't pre-plan an optimised build; instead you're pushed into experimentation."* No net-decking, no solved opener — every match improvises. **[Reported]**
3. **Emergent build variety.** 11.2M combinations, and *"tons of novelty in discovering new cards and seeing how they work in combo."* The trade-off design (every buff has a cost) means builds have *shape* (glass-cannon vs. tank-attrition vs. bounce-engine), not just bigger numbers. **[Official] count / [Reported] feel**
4. **Short duel + instant restart = readable escalation.** A duel is over in seconds; the reset is immediate; each point visibly ratchets the build up. Fast failure + fast retry keeps the pick→counterpick "needle swinging." *Bits & Pieces*: *"rapid-fire pick and counterpick as the needle swings one way or the other."* **[Reported]** (Exact duel/match *durations* in seconds are **[Gap]** — no source states them; footage would clock them.)
5. **Run-to-run novelty from a small skill floor.** The base verbs — *move, shoot, jump, block* — are trivial to learn, so all depth is in the cards. *"It's the skill selection that makes this game shine."* Low floor, high novelty ceiling. **[Reported]** 96% positive / "Overwhelmingly Positive" corroborates the appeal at scale. **[Official]**

---

## 6. The numbers a pycats mode-designer would need to pick

Option space only — **no recommendation, no pycats spec** (that's the downstream design child). This is the parameter list §347 would have to fill, with ROUNDS' values as the reference point:

| Parameter | ROUNDS value | Grade | Note for the adaptation designer |
|---|---|---|---|
| Players | 1v1 | [Official] | 2v2 is mods-only; a decision for pycats |
| Kills per point | **2** (half-point per kill) | [Wiki §8] | confirmed |
| Points per match | **5** (configurable) | [Wiki §8] | Steam exposes the round limit as a setting |
| Card cap | **5** cards | [Wiki §8] | caps the catch-up; ≤5 drafts per loser |
| Draft trigger | after each full point conceded | [Wiki §8] | loser-only; both pick a starting card |
| Draft pool size | **5** | [Wiki §8] | one card picked → resolves the 3-vs-5 conflict |
| Picks per draft | 1 | [Wiki §8] | corrects #347's "2" |
| Card pool size | **67** (press kit "65+") | [Wiki §8] / [Official] | the adaptation's catalog-size target |
| Maps | 70+ | [Official] | pycats stage variety analog |
| Card permanence | whole match, stackable | [Wiki §8] | build monotonically grows |
| Power-curve shape | escalating; loser-favored | [Reported]/[Inference] | the rubber band — the feel everything depends on |
| Duel / match duration | — | [Gap] | seconds-scale; clock from footage |
| Stacking math (global add vs mult) | percentage-based; some self-caps (Trickster); on-block ×2 via Echo | [Wiki §8] specifics / [Gap] global rule | resolve same-card stacking empirically before balancing |

---

## 7. Open questions handed downstream (evidence gaps — Avi's call)

Status after the #1085 wiki reconciliation (§8):

1. ~~Exact kills-per-point and points-per-match defaults~~ — **RESOLVED (§8).** 2 kills = 1 point; first to 5 points; round limit configurable; 5-card cap. **[Confirmed]**
2. ~~Draft pool size: 3 or 5?~~ — **RESOLVED (§8).** **5** cards offered, pick 1. **[Confirmed]**
3. **Stacking formulas & caps** — **PARTIALLY RESOLVED.** The wiki confirms specifics (Trickster's per-bounce bonus self-caps at your bounce count; on-block triggers fire per block, so Echo doubles Bombs Away 6→12), and the stat model is percentage-based. But no *global* additive-vs-multiplicative rule is stated — still **[Gap]** for exact same-card stacking math; resolve empirically before balancing a pycats catalog.
4. **Duel/match length in seconds** — still **[Gap].** No source states it; only footage clocks it. A quantity #347's pacing decisions need.
5. ~~Full, patch-current card list with exact magnitudes~~ — **RESOLVED (§8.4):** complete 67-card table with exact stats + rarity, transcribed from the Fandom `All_Cards` page.

Remaining live gaps: **#3 (global stacking math)** and **#4 (durations)** — both empirical, neither a blocker.

---

## 8. Fandom wiki reconciliation (primary source — #1085)

**Added 2026-08-02 via follow-up #1085.** The three authoritative Fandom pages (`rounds.fandom.com` → *Rounds*, *Cards*, *All Cards*) 402'd through the fetch tool during #1075; Avi supplied their contents. This section is the **primary-sourced correction layer** — where it disagrees with §2–§6, it wins. Grade for everything here: **[Wiki]** (Fandom, community-maintained but the definitive public reference; still secondary to the game binary, and card magnitudes track the wiki's last patch, not necessarily the live build).

### 8.1 Core loop — verbatim, and what it confirms

> *"each round consists of both players attempting to kill the other player, causing the survivor to gain a **half-point**. Once a person scores a **full point**, that round of the game ends, and the losing player chooses **one of 5 unique upgrades** … This repeats until one of the players reaches **5 points**, or when a person loses after **collecting 5 cards**. The **round limit can be changed** in the Steam version."* — *Rounds* wiki

This **confirms the §2 leading reading** and resolves every core-loop `[Conflict]`:

| Quantity | Confirmed value | Note |
|---|---|---|
| Kill → score | **half-point per kill** | survivor of a duel gains ½ |
| Point | **2 kills = 1 full point** | reaching a full point ends the "round" and triggers the draft |
| Draft trigger | **loser of the point drafts** | "the losing player chooses" |
| Draft pool | **1 of 5** | resolves the 3-vs-5 conflict → **5** |
| Match win | **first to 5 points** | default; **configurable** ("round limit can be changed") |
| Card cap | **5 cards** | "or when a person loses after collecting 5 cards" — a losing player can hold at most 5, i.e. ≤5 drafts before the match resolves **[Inference on the exact interaction]** |

### 8.2 Cards page — rarity + granting, confirmed

- **Granting:** *"A choice of cards is granted to a player upon the start of the game, or following [a] round that the player did not presently win (for balance reasons)."* → both players pick a **starting card**; thereafter **only the round-loser drafts**. Confirms §3.
- **Rarity markers (corner triangles):** **no color = Common · blue = Uncommon · magenta = Rare.** (Corrects the secondary claim of a "black corner" for Common — it's *no* color.)
- **Color themes** carry mechanical flavor — e.g. the **Violet** family is "damage variation," self (Demonic Pact) or enemy (Parasite), with grim visuals (Decay, Abyssal Countdown).

### 8.3 Synergy — the canonical worked example (confirms multiplicative on-block stacking)

> *"if the player uses … **Bombs Away**, which causes the player to release **6 bombs** nearby when the player blocks, and **Echo**, which causes the player to block twice in succession, these cards synergize to let the player release **12 bombs** whenever they use their block ability."* — *Rounds* wiki

So on-block triggers fire **once per block event**, and Echo's extra block **doubles** every on-block effect — a concrete, multiplicative synergy. It also pins **Bombs Away = 6 bombs** (§4 said only "a bunch").

### 8.4 The complete card catalog (67 cards, exact stats + rarity)

Transcribed from the Fandom *All Cards* page (vanilla install, no mods). This **supersedes §4's representative list.** "Stats" are the flat/percentage modifiers; "Effect" is the special behavior (N/A = pure stat card).

| # | Card | Rarity | Stats | Effect |
|---|---|---|---|---|
| 1 | Abyssal Countdown | Rare | — | Stand still to summon dark powers (continuous block + slight AoE damage + slight pull toward you) |
| 2 | Barrage | Uncommon | +4 bullets, +5 ammo, −70% DMG, +0.25s reload | Fire many bullets at once |
| 3 | Big Bullets | Common | +0.25s reload | Bigger bullets |
| 4 | Bombs Away | Uncommon | +30% HP, +0.25s block CD | Spawn **6** small bombs around you when you block |
| 5 | Bouncy | Uncommon | +2 bounces, +25% DMG, +0.25s reload | Bouncing bullets |
| 6 | Brawler | Uncommon | **+200% HP** for 3s after dealing DMG | (temporary HP surge) |
| 7 | Buckshot | Uncommon | +4 bullets, +5 ammo, −60% DMG, +0.25s reload | Shotgun-style spread |
| 8 | Burst | Common | +2 bullets, +3 ammo, −60% DMG, +0.25s reload | Bullets fired in sequence |
| 9 | Careful Planning | Uncommon | +100% DMG, −150% ATKSPD, +0.5s reload | — |
| 10 | Chase | Uncommon | +30% HP | +60% movement toward opponent (needs line of sight) |
| 11 | Chilling Presence | Rare | +25% HP | Slightly slow nearby enemies |
| 12 | Cold Bullets | Common | **+70% bullet slow**, +0.25s reload | (slows *your* bullets — a control/aim card, **not** a spread) |
| 13 | Combine | Common | +100% DMG, −2 ammo, +0.5s reload | — |
| 14 | Dazzle | Common | +0.25s reload | Bullets stun the opponent multiple times |
| 15 | Decay | Uncommon | +50% HP | Damage done to you is dealt over 4s |
| 16 | Defender | Uncommon | −30% block CD, +30% HP | — |
| 17 | Demonic Pact | Rare | +9 bullets, +2 splash DMG, +0.25s reload | Shooting costs 10 HP; removes shooting cooldown |
| 18 | Drill Ammo | Rare | +7m bullets drill through walls, +0.25s reload | — |
| 19 | Echo | Uncommon | +30% HP, +0.25s block CD | Blocking triggers another, delayed block |
| 20 | EMP | Uncommon | +30% HP, +0.25s block CD | Blocking spawns a ring of slowing projectiles |
| 21 | Empower | Uncommon | +0.25s block CD | Blocking boosts damage+speed of next shot; that shot triggers on-block abilities where it lands |
| 22 | Explosive Bullet | Uncommon | −100% ATKSPD, +0.25s reload | Bullet explodes on impact |
| 23 | Fastball | Common | +250% bullet speed, −50% ATKSPD, +0.25s reload | — |
| 24 | Fast Forward | Common | +100% projectile speed, +30% reload speed | Bullets keep default trajectory |
| 25 | Frost Slam | Common | +30% HP, +0.25s block CD | Slows enemies around you when blocking |
| 26 | Glass Cannon | **Uncommon** | +100% DMG, −100% HP, +0.25s reload | (corrects §3's "Rare" example) |
| 27 | Grow | Uncommon | +0.25s reload | Bullets gain damage over travel time ("shoot into the sky for max damage") |
| 28 | Healing Field | Common | +30% HP, +0.25s block CD | Blocking creates a healing field |
| 29 | Homing | Uncommon | −25% DMG, −50% ATKSPD, +0.25s reload | Bullets home toward visible targets |
| 30 | Huge | Common | +80% HP | (amplifies Overpower's max-HP AoE) |
| 31 | Implode | Uncommon | +50% HP, +0.25s block CD | Blocking pulls enemies toward you |
| 32 | Leech | Common | +75% life steal, +30% HP | — |
| 33 | Lifestealer | Rare | +25% HP | Steal HP from opponent when near |
| 34 | Mayhem | Uncommon | +5 bounces, −15% DMG, +0.5s reload | — |
| 35 | Overpower | Uncommon | +30% HP, +0.25s block CD | Deal 15% of your max HP to enemies around you when blocking |
| 36 | Parasite | Uncommon | +50% life steal, +25% HP, +25% DMG, +0.25s reload | Bullets deal DoT over 5s |
| 37 | Phoenix | Rare | −35% HP | Respawn once on death |
| 38 | Poison | **Common** | +70% DMG, +30% reload speed, −1 bullet | Bullets deal DoT over 3s (corrects §3's "Rare" example) |
| 39 | Pristine Perseverance | Rare | +400% HP when above 90% HP | — |
| 40 | Quick Reload | Uncommon | −70% reload time | — |
| 41 | Quick Shot | Common | +150% bullet speed, +0.25s reload | — |
| 42 | Radar Shot | Uncommon | +30% HP, +0.25s block CD | Blocking scans the area; auto-shoots any enemy found |
| 43 | Radiance | Rare | +30% HP | Spawn damaging sun waves when reloading; rate ramps during reload |
| 44 | Refresh | Rare | — | Get block back when dealing damage (hidden cooldown) |
| 45 | Remote | Rare | −40% bullet speed, +0.25s reload | Steer bullet with right stick / mouse |
| 46 | Ricochet | Uncommon | +2 bounces, +25% ATKSPD, +0.25s reload | Bullets lose half their speed when they bounce |
| 47 | Saw | Rare | +30% HP, +0.25s block CD | Blocking spawns a saw around you for a short while |
| 48 | Scavenger | Uncommon | +0.5s reload | Dealing damage reloads your weapon |
| 49 | Shield Charge | Uncommon | +0.25s block CD | Blocking launches you forward + a second auto-block when the charge ends |
| 50 | Shields Up | Rare | +0.5s reload, +0.5s block CD | Firing your last bullet triggers a block; disables continuous reloading |
| 51 | Shockwave | Uncommon | +50% HP, +0.25s block CD | Blocking pushes enemies away |
| 52 | Silence | Uncommon | +25% HP, +0.25s block CD | Blocking silences nearby enemies |
| 53 | Sneaky | Uncommon | +0.25s reload | Bullets avoid the ground |
| 54 | Spray | Uncommon | +1000% ATKSPD, +12 ammo, −75% DMG, +0.25s reload | — |
| 55 | Static Field | Uncommon | +0.25s block CD | Blocking creates a field that slows and deals damage |
| 56 | Steady Shot | Common | +40% HP, +100% bullet speed, +0.25s reload | — |
| 57 | Supernova | Rare | +50% HP, +0.5s block CD | Blocking spawns a field that pulls enemies in and stuns after a while |
| 58 | Tactical Reload | Rare | +0.25s block CD | Blocking reloads your weapon |
| 59 | Tank | Common | +100% HP, −25% ATKSPD, +0.5s reload | (amplifies Overpower) |
| 60 | Target Bounce | Uncommon | +1 bounce, −20% DMG, +0.25s reload | Bullets aim for visible targets when bouncing |
| 61 | Taste of Blood | Uncommon | +30% life steal | +50% movement speed for 3s after dealing DMG |
| 62 | Teleport | Rare | −30% block CD | Blocking teleports you forward (through objects) |
| 63 | Thruster | Uncommon | +0.25s reload | Bullets have thrusters that push targets |
| 64 | Timed Detonation | Common | −15% DMG, +0.25s reload | Bullets spawn bombs that explode after 0.5s |
| 65 | Toxic Cloud | Rare | −20% ATKSPD, +0.5s reload | Bullets spawn a poison cloud on impact (damage + slow) |
| 66 | Trickster | Rare | +2 bounces, −20% DMG, +0.5s reload | +80% DMG per bounce — **capped at your total bounce count** (does not scale infinitely) |
| 67 | Wind Up | Common | +100% bullet speed, +60% DMG, −100% ATKSPD, +0.5s reload | — |

**Rarity distribution (67 total):** Common ~19 · Uncommon ~31 · Rare ~17 (counted from the table; the wiki's own rarity column is authoritative if a recount differs).

### 8.5 Corrections this primary source forces on §3–§4

| Item | §3/§4 said (secondary) | Wiki says (§8) |
|---|---|---|
| **Cold Bullets** | grouped as a multi-bullet "spread" ("loads more bullets") | **+70% bullet *slow*** — a control card, not a spread. **Clear error corrected.** |
| **Glass Cannon** rarity | Rare (build-definer) | **Uncommon** |
| **Poison** rarity | Rare | **Common** |
| **Grow** rarity | implied Common | **Uncommon** |
| **Brawler** | "+200 HP" (flat) | **+200% HP** (percentage) |
| **Bombs Away** | "a bunch of bombs" | exactly **6** (→ 12 with Echo) |
| **Bouncy, Homing, Refresh** | missing / statless | now catalogued with exact stats |
| **Trickster stacking** | "no hard cap documented" | per-bounce bonus **self-caps** at your bounce count |
| Common corner marker | "black corner" (rounds.network) | **no color** |

None of these change the §5 design analysis or the §6 parameter shape — they sharpen the catalog a pycats designer would port.

---

## 9. Scope guard

Per repo rules, this doc **reports findings + option space only**. It deliberately contains **no** ROUNDS→pycats mapping, **no** modifier-layer or draft-screen design, and **does not re-rule** #347's format open-questions — it surfaces the options and their ROUNDS reference values. The PM/Brawl/Melee *mixing* analysis is the sibling premortem child's job, not this one. Determinism/seeding (#166) is noted only as a constraint the eventual draft must satisfy (the draft is random → it must be seedable), not designed here.

---

## Sources

- **[Official]** ROUNDS press kit — Landfall: <https://landfall.se/rounds-press-kit>
- **[Official]** ROUNDS on Steam (store page, reviews): <https://store.steampowered.com/app/1557740/ROUNDS/>
- **[Reported]** Steam Community "how to play rounds" guide: <https://steamcommunity.com/sharedfiles/filedetails/?id=2914483165>
- **[Reported]** Rounds Fundamentals: Core Mechanics Explained — rounds.network: <https://rounds.network/rounds-fundamentals-core-mechanics-explained/>
- **[Reported]** The Complete Guide to Rounds Card Types and Rarities — rounds.network: <https://rounds.network/the-complete-guide-to-rounds-card-types-and-rarities/>
- **[Reported]** ROUNDS review — rounds.network: <https://rounds.network/rounds-review-my-new-favorite-multiplayer-roguelike/>
- **[Reported]** "You Should Play Rounds" — Bits & Pieces: <https://bitsandpieces.games/2024/02/23/rounds/>
- **[Reported]** ROUNDS – All Cards — Magic Game World (card list + effects): <https://www.magicgameworld.com/rounds-all-cards/>
- **[Wiki — primary reference, contents supplied by Avi under #1085 after the fetch 402'd]** Rounds Wiki (Fandom):
  - *Rounds* (core loop): <https://rounds.fandom.com/wiki/Rounds>
  - *Cards* (rarity + granting): <https://rounds.fandom.com/wiki/Cards>
  - *All Cards* (the 67-card catalog, §8.4): <https://rounds.fandom.com/wiki/All_Cards>

*Every quoted string above is reproduced from the cited page as of 2026-08-02; the §8 wiki content was supplied by Avi (the pages 402'd through the fetch tool). Card magnitudes track the wiki's last-edited patch and should be re-verified against the live game or the game binary before any number is used to tune a pycats catalog.*
