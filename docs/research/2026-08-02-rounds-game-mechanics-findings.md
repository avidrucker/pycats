# How does ROUNDS (Landfall Games) actually play? — core loop, card catalog, and why it's fun — findings

**Ticket:** #1075 (RESEARCH · `area:combat`) · **Date:** 2026-08-02 · **Agent:** FIG
**Parent:** #347 (Rounds Mode epic, deferred). **Sibling child:** the ROUNDS×PM fit premortem.
**Deliverable:** this doc. **No pycats spec, no design decisions** — the ROUNDS→pycats mapping belongs to a downstream design/architect child (research never produces a spec). Sources cited inline; every claim is tagged with its evidence grade (below).

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

**The one correction #347 needs up front:** #347's "Proposed mechanics" guessed *"every 2 losses, pick 2 of 6."* The evidence says the loser drafts **after each point conceded** (a point being best-of-~3 kills), and picks **1 card from a pool most walkthroughs put at 5** — i.e. **pick-1-of-5, not pick-2-of-6**, and the cadence is *per point*, not *per two losses*. Both of #347's numbers are off; §2 and §3 give the sourced version. **[Reported]/[Conflict]**

**The biggest evidence gaps (for Avi):** the exact **kills-per-point** and **points-per-match** defaults, and the exact **draft pool size (3 vs 5)** — walkthroughs conflict, and only footage or the live game settles them (§2, §3). None of these block the epic; they're knobs a designer picks anyway.

---

## 2. The core loop, precisely

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

| #347 claim | Evidence says | Verdict |
|---|---|---|
| "every **2 losses**" you draft | You draft after **each point conceded** (a point ≈ best-of-3 kills, so ≈ every 2 *kills* lost) | **Imprecise** — cadence is per-point, not per-two-match-losses. The "2" is really the kills-per-point. |
| "pick **2** cards" | You pick **1** | **Wrong** — one card per draft |
| "of **6**" | Pool is **~5** (3–5 across sources) | **Wrong number** — ~5, not 6 |
| format / catalog "TBD" | 1v1, first-to-~5 points, 65+ card catalog (§4) | **Now grounded** (with the [Gap]s noted) |

---

## 4. The card catalog — grouped by effect family

**Official count: 65+ power-ups. [Official]** Below is a representative, near-complete enumeration compiled from a card-list guide (magicgameworld) cross-checked against the rounds.network rarity guide. Effect text is quoted from the guide; treat exact magnitudes as **[Reported]** (guides can lag balance patches) and stacking behavior as **[Inference]** where noted.

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
| Kills per point | ~2 (best-of-3) | [Conflict] | leading reading; confirm |
| Points per match | ~5 (configurable) | [Conflict]/[Gap] | Steam exposes it as a setting |
| Draft trigger | after each point conceded | [Reported] | loser-only |
| Draft pool size | ~5 (3–5 across sources) | [Conflict] | one card picked |
| Picks per draft | 1 | [Reported] | corrects #347's "2" |
| Card pool size | 65+ | [Official] | the adaptation's catalog-size target |
| Maps | 70+ | [Official] | pycats stage variety analog |
| Card permanence | whole match, stackable | [Reported] | build monotonically grows |
| Power-curve shape | escalating; loser-favored | [Reported]/[Inference] | the rubber band — the load-bearing feel |
| Duel / match duration | — | [Gap] | seconds-scale; clock from footage |
| Stacking math (caps, add vs mult) | mixed, uncapped | [Inference]/[Gap] | resolve empirically before balancing |

---

## 7. Open questions handed downstream (evidence gaps — Avi's call)

1. **Exact kills-per-point and points-per-match defaults** — [Conflict]/[Gap]. Resolvable by one play session or a clear footage clip.
2. **Draft pool size: 3 or 5?** — [Conflict]. Same resolution path.
3. **Stacking formulas & caps** — [Gap]. Only the live game / decompiled values settle additive-vs-multiplicative and any hidden caps; matters once someone balances the pycats catalog.
4. **Duel/match length in seconds** — [Gap]. A quantity #347's pacing decisions need.
5. **Full, patch-current card list with exact magnitudes** — the §4 catalog is representative and guide-sourced; a definitive dump would come from the game files or the (paywalled-to-this-fetch) Fandom `All_Cards` page.

These are **not blockers** — they're knobs a designer chooses anyway. They're logged so the downstream design/architect child (and Avi) can decide how much footage/primary confirmation is worth gathering first.

---

## 8. Scope guard

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
- **[Reference, paywalled to fetch]** Rounds Wiki (Fandom) — Rounds / Cards / Ability cards / All Cards: <https://rounds.fandom.com/wiki/Cards>

*Every quoted string above is reproduced from the cited page as fetched 2026-08-02; card magnitudes may drift with balance patches and should be re-verified against the live game before any number is used to tune a pycats catalog.*
