# Fighter buff mechanics — catalog (PM 3.6 / Brawl / Melee / meleelight)

Findings doc for #1106. Enumerates the distinct ways a fighter/player/character can be
**buffed** — temporarily or persistently strengthened — across the four reference systems.
A "buff" here = more effective HP (heal / lower damage %), defensive advantage (armor,
invincibility, intangibility, reflection), movement/jump gain, increased offensive output,
or a relative advantage from weakening everyone else.

**Scope:** enumerate the *mechanics* with a one-line effect + one primary quote each.
Exact magnitudes / durations / engine constants are **out of scope** (a follow-on thorough
ticket if wanted). Deciding whether pycats implements any of these is also out of scope.

## How to read the game columns

| Mark | Meaning |
|------|---------|
| ✓ | Present, confirmed by the cited primary source. |
| ✓ᴵ | **Inference, not separately sourced.** PM 3.6 is a Brawl mod, so Brawl's item/engine surface exists in it; but competitive PM typically runs items-off and no PM 3.6 primary was found confirming per-item behavior. Treat as `GUESS` pending a PM/PMDT primary. |
| — | Absent in that game per the source. |

## Sourcing caveats (read before citing this doc)

- **Primary source is SmashWiki** (served from **`ssbwiki.com`** — `smashwiki.org` does not
  resolve). Every quote below is verbatim from the linked page. SmashWiki is a strong
  community primary for item/mechanic definitions, but it is **not a PMDT changelog**.
- **The PM 3.6 armor rework** (below) rests on SmashWiki's *Project M* page, **not** a PMDT
  primary patch-notes document — a search for a primary PM 3.6 changelog returned only
  landing pages. Flagged for a human to source if it becomes decision-bearing.
- **"Hyper armor" is not a SmashWiki term.** The Armor page distinguishes only *armor*
  (knockback-based / limited) from *super armor* (infinite knockback resistance). The
  ticket seed's "hyperarmor" maps to **super armor**; no distinct "hyper armor" quote exists,
  so none is invented.
- **The Lucario aura *meter/charge* system is likely Project+ (post-3.6, ~2019), not PM 3.6.**
  Only the Brawl-style damage-scaling aura is confirmed as the 3.6-era baseline (see row).
- **Series-context items out of the four scope games** (Fairy Bottle, Little Mac's KO
  Uppercut armor, Wario Chomp heal-by-eating) are listed under *Series context* at the end,
  not in the main catalog — they debuted in SSB4/Ultimate.
- **meleelight** implements dodge/ledge/tech **intangibility** frames (`intangibleTimer`,
  `executeIntangibility`, `airdodgeIntangible`) but has **no item-buff system** (no metal /
  star / bunny / heal item). So it is a primary source only for the *intangibility* mechanic.

---

## 1. Healing / damage-reduction (item)

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Heart Container | ✓ | ✓ | ✓ᴵ | Large heal — fully clears damage (Melee); heals up to 100% (Brawl) | [Heart Container](https://www.ssbwiki.com/Heart_Container) |
| Maxim Tomato | ✓ | ✓ | ✓ᴵ | Heals 50 percentage points of damage | [Maxim Tomato](https://www.ssbwiki.com/Maxim_Tomato) |
| Food | ✓ | ✓ | ✓ᴵ | Recovers a small amount of damage per piece | [Food](https://www.ssbwiki.com/Food) |

## 2. Defensive / armor

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Super armor (infinite knockback resistance) | ✓ | ✓ | ✓ | No flinch / no knockback from a hitbox (still takes damage) | [Armor](https://www.ssbwiki.com/Armor) |
| Knockback-based armor (threshold) | ✓ | ✓ | ✓ | Armor holds only if incoming knockback is below a threshold; PM 3.6 restricts *infinite* armor to a whitelist and converts most armored moves to this | [Armor](https://www.ssbwiki.com/Armor) · [Project M](https://www.ssbwiki.com/Project_M) |
| Metal Box (metalization) | ✓ | ✓ | ✓ᴵ | Turns fighter metal: heavier, high knockback resistance, faster fall | [Metal Box](https://www.ssbwiki.com/Metal_Box) |
| Franklin Badge | — | ✓ | ✓ᴵ | Reflects incoming projectiles back at attackers | [Franklin Badge](https://www.ssbwiki.com/Franklin_Badge) |
| Cloaking Device | ✓ | — | — | Turns user invisible and immune to damage (hitstun/knockback still apply) | [Cloaking Device](https://www.ssbwiki.com/Cloaking_Device) |
| Yoshi armored double jump (move-intrinsic) | ✓ | ✓ | ✓ᴵ | Yoshi's midair jump grants knockback armor during its early frames | [Yoshi (SSBM)](https://www.ssbwiki.com/Yoshi_(SSBM)) |

## 3. Invincibility / intangibility (state)

The distinction is precise and easy to get wrong — see quotes below.

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Super Star (Starman) — item | ✓ | ✓ | ✓ᴵ | Temporary full invincibility to all attacks | [Super Star](https://www.ssbwiki.com/Super_Star) |
| Invincibility (state) | ✓ | ✓ | ✓ | Hurtbox can't be damaged, but attacker still gets hitlag (respawn platform, item startup) | [Invincibility](https://www.ssbwiki.com/Invincibility) |
| Intangibility (state) | ✓ | ✓ | ✓ | Hurtbox isn't hit at all — no damage, no knockback, **and no attacker hitlag**; used for dodges/ledge/tech | [Intangibility](https://www.ssbwiki.com/Intangibility) · meleelight `executeIntangibility` |

## 4. Movement / jump (item)

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Bunny Hood | ✓ | ✓ | ✓ᴵ | Faster movement and much higher jumps | [Bunny Hood](https://www.ssbwiki.com/Bunny_Hood) |
| Screw Attack (item) | ✓ | ✓ | ✓ᴵ | Alters first/second jumps to mimic Samus's Screw Attack (jump boost + attack) | [Screw Attack (item)](https://www.ssbwiki.com/Screw_Attack_(item)) |

## 5. Offensive self-buff

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Super Mushroom (grow) | ✓ | ✓ | ✓ᴵ | Grows fighter + hit/hurtboxes: bigger, heavier, stronger, more range | [Super Mushroom](https://www.ssbwiki.com/Super_Mushroom) |
| Superspicy Curry | — | ✓ | ✓ᴵ | User continuously spews damaging flames (~13s) | [Superspicy Curry](https://www.ssbwiki.com/Superspicy_Curry) |
| Lucario Aura (damage-scaling) | — | ✓ | ✓ᴵ | Move power scales with own damage %: weaker low, stronger high. **3.6 baseline = damage-scaling; the aura *meter* is likely Project+, not 3.6.** | [Aura](https://www.ssbwiki.com/Aura) |
| Warp Star (borderline) | ✓ | ✓ | ✓ᴵ | Launch/attack item, not a persistent strengthening buff — included for completeness | [Warp Star](https://www.ssbwiki.com/Warp_Star) |

## 6. Relative buff (weaken everyone else)

Not a direct strengthening of the user, but a net advantage — included because the effect is
"the user is now stronger relative to the field."

| Buff | Melee | Brawl | PM 3.6 | Effect | Source |
|------|:---:|:---:|:---:|--------|--------|
| Lightning | — | ✓ | ✓ᴵ | Shrinks all *other* fighters (weaker, lighter, take more knockback). **Not** a self-grow buff — that framing is wrong | [Lightning](https://www.ssbwiki.com/Lightning) |
| Timer | — | ✓ | ✓ᴵ | Slows all fighters except the user to 1/4 speed | [Timer](https://www.ssbwiki.com/Timer) |

---

## Verbatim primary quotes

Each entry above, one verbatim sentence from its cited page.

- **Heart Container:** "However, it now only heals a total of 100%." (Brawl figure; Melee fully clears damage.)
- **Maxim Tomato:** "Maxim Tomatoes cure 50 percentage points of your accumulated damage."
- **Food:** "Food (たべもの, Food) is an item that, when used, recovers a small amount of the user's damage."
- **Super armor:** "When a character has super armor, or infinite knockback resistance, they will not flinch nor take any knockback when attacked by a harmful hitbox."
- **Knockback-based armor (PM 3.6):** "Infinite armor is now only reserved for Ike's fully charged Eruption, all of Bowser's smash attacks (when charged a certain time), Ganondorf's Flame Choke right before the explosion, and 'grab armor.' Armor for other moves that have it is given knockback-based armor; if an attack's knockback is lower than the specified amount of an armor, no knockback is inflicted, but if it is higher, knockback will be regularly inflicted as usual." (SmashWiki *Project M* page — **not** a PMDT primary.)
- **Metal Box:** "The Metal Box transforms the player's fighter who breaks it into a Metal fighter."
- **Franklin Badge:** "Reflects projectiles." (Brawl instruction manual, quoted on page.)
- **Cloaking Device:** "The Cloaking Device turns the user invisible."
- **Yoshi armored double jump:** "Yoshi also has very unique mechanics, such as an armored double jump, which he can use to escape disadvantage or bait opposing attacks and make them unsafe on hit."
- **Super Star:** "This item makes you invulnerable to all attacks for a short period of time."
- **Invincibility:** "Invincibility is a state where a hurtbox cannot be attacked or damaged."
- **Intangibility:** "Intangibility is a state in which a hurtbox will not be hit by attacks at all." / "Unlike invincibility, intangibility does not cause hitlag to attackers since the intangible character is not physically hit." (meleelight corroborates: `intangibleTimer` / `executeIntangibility` on dodge, ledge, tech, get-up, shield-break moves.)
- **Bunny Hood:** "Once picked up, a character will become quicker and can jump much higher."
- **Screw Attack (item):** "When held, the item alters a character's first and second jumps (leaving any further jumps they may have unchanged), changing them to mimic Samus's up special move, also named the Screw Attack."
- **Super Mushroom:** "Makes the fighter, and their hitboxes and hurtboxes, bigger."
- **Superspicy Curry:** "Upon consumption of the Superspicy Curry, the user will continuously have flames erupting from their mouth in an up-and-down flame pattern for thirteen seconds."
- **Lucario Aura:** "It modifies the damage and knockback of Lucario's moves based on its current damage percentage, weakening them at low percents and strengthening them at high percents."
- **Warp Star:** "When picked up, the Warp Star sends a player flying off into the sky and crashing back down into the stage with an explosion that deals 22% damage and high knockback."
- **Lightning:** "When used, it will shrink every other fighter to tiny size, similar to the effect of the Poison Mushroom, reducing their attack power to 0.7x, making them lighter, and increase the amount of knockback that they take."
- **Timer:** "When the Timer is grabbed, all characters except for the character who grabbed it will be slowed down to 1/4 of their normal speed, regardless of the gameplay speed."

## Series context (out of the four scope games — not part of the catalog)

Debuted in SSB4/Ultimate; listed so a future reader doesn't re-research them as PM/Brawl/Melee buffs:

- **Fairy Bottle** — heals 100% but only if the user is already ≥100% (SSB4+). Source: [Fairy Bottle](https://www.ssbwiki.com/Fairy_Bottle).
- **Little Mac — KO Uppercut** — a charged unblockable punch with brief super armor (frames 8–9), SSB4/Ultimate. Source: [KO Uppercut](https://www.ssbwiki.com/KO_Uppercut).
- **Wario — Chomp heal-by-eating** — eating items heals Wario 1% each, SSB4/Ultimate only (not Brawl/PM). Source: [Chomp](https://www.ssbwiki.com/Chomp).

## Open follow-ups (tracked by #1107)

Filed one at a time under the tracker #1107:

1. **Datamine magnitudes/durations** for each buff (metal weight/fall multipliers, Bunny Hood
   jump/speed factors, invincibility frame counts, super-armor knockback thresholds) — the
   "thorough" scope this ticket deferred. Sources: brawllib_rs / meleelight / OpenSA. *(tracker
   thread B — not yet filed.)*
2. **Confirm PM 3.6 item behavior from a PM/PMDT primary** — the ✓ᴵ inference marks should
   become ✓ or — once sourced. *(→ #1108, filed.)*
3. **Source the PM 3.6 armor rework from a PMDT primary changelog** (currently SmashWiki only).
   *(→ #1108, filed — same PMDT-primary hunt as #2.)*
4. **Resolve the Lucario aura-meter question** — is the charge/meter system PM 3.6 or Project+?
   *(tracker thread C — not yet filed.)*

## Refs

Canon baseline: PM 3.6 (`docs/project-m-parity.md`). Router: `docs/mechanics-index.md`.
meleelight mirror: intangibility-frame source. Ticket: #1106.
