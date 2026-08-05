# PM 3.6 buff-mechanics — PMDT primary-source hunt

Findings doc for **#1108** (first child of tracker #1107), seeded by #1106's catalog
(`docs/research/fighter-buffs-findings.md`). The catalog sourced everything from SmashWiki and
marked two fact-classes as ungrounded in a PM primary:

1. **PM 3.6 item behavior** — every item row marked `✓ᴵ` (inference: "PM is a Brawl mod, so the
   item exists in-engine"), with no PM primary confirming per-item presence/behavior.
2. **The PM 3.6 armor rework** — the catalog's armor note (4-move infinite-armor whitelist;
   "knockback-based armor" threshold; visual overlays) came from SmashWiki's *Project M* page,
   **not** a PMDT changelog.

This ticket hunts a **PM/PMDT primary** for both and reports, per fact, whether the primary
**confirms / refutes / can't-confirm** the #1106 inference — and which `✓ᴵ` marks can be upgraded.

---

## Bottom line

- **The armor rework is grounded in a first-party PMDT primary.** The **Demo 2.6b changelist**
  (PMBR, Smashboards, Aug 2013) states the rework verbatim: armor **standardized via knockback as
  Light / Medium / Heavy**, with **color overlays that get more opaque for stronger armor**. This
  **CONFIRMS** both the catalog's "knockback-based armor" claim and the "more opaque overlay =
  stronger" detail (SmashWiki was faithfully paraphrasing this PMBR sentence), and **dates the
  rework to the Demo 2.6b era (2013)**. The one fragment still *not* in any PMDT primary is the
  specific **4-move "infinite-armor whitelist"** (Ike Eruption / Ganondorf Flame Choke / grab
  armor) — 2.6b speaks only of Light/Med/Heavy and is silent on an infinite-armor whitelist, so
  that stays **SmashWiki-only, can't-confirm**.
- **The item roster stays inferred — and is partly refuted.** The official PM 3.6 Full Changelist
  has **no Items section**, so per-item presence/behavior in 3.6 is **can't-confirm
  (changelog-silent)**. But the **Demo 2.5b changelist** (PMBR, 2013) explicitly says **Super Star
  (Starman), Timer, and Superspicy Curry were non-functional and demoted to stickers** — a
  first-party **REFUTATION** of the catalog's "behaves as in Brawl" inference for those three (at
  least in the Demo era). So those `✓ᴵ` marks should carry a "known-broken in PM Demo" flag, not
  become `✓`. The remaining items stay `✓ᴵ`. One first-party 3.6 line confirms only that an item
  *system* functions (Giga can grab/use items).
- **Net:** the armor rework upgrades from SmashWiki to first-party PMDT (with the whitelist carved
  out as still-unsourced); the item inferences hold, with three items actively refuted for the
  Demo era.

---

## Access note — blocked sources (flagged per the ticket's blocked-source rule)

The true first-party primaries (official `projectmgame.com` changelists) **survive only in web
archives** — the live `projectmgame.com` now redirects to `projectplusgame.com` and its changelist
pages are gone (TLS cert also expired). The in-session `WebFetch` tool **refuses `web.archive.org`,
`archive.ph`, and `smashboards.com` (403)** outright. First-party text was obtained by running
**`curl` against the Wayback Machine from Bash** (`…/web/<snapshot>id_/http://projectmgame.com/…`),
which works where WebFetch does not — and re-verified by hand for the quotes below.

The **Demo 2.5b / 2.6b full changelogs** (Smashboards threads) — the home of the *original* armor
rework statement — 403'd / CAPTCHA'd the in-session fetch. **Avi retrieved these two OPs by hand**
and supplied their text; the armor-rework and item-sticker quotes below come from them. That closes
the one gap the automated sweep could not. (Remaining un-retrieved: a first-party statement of the
*infinite-armor 4-move whitelist* — it is in neither the Demo OPs nor the 3.0/3.5/3.6 changelists,
so it may be SmashWiki's own synthesis; see §1 Claim 1.)

**Primaries reached** (official PMDT, via Wayback `curl`; snapshots noted):

| Source | Snapshot / route | Status |
|--------|------------------|--------|
| **Demo 2.6b changelist** (Smashboards `…/project-m-demo-2-6b-released-changelist-up.340142/`) | retrieved by Avi | **reached** — source of the armor-rework quote (§1) |
| **Demo 2.5b changelist** (Smashboards `…/project-m-demo-2-5b-released.332135/`) | retrieved by Avi | **reached** — source of the item-sticker quote (§2) |
| PM 3.6 Full Changelist (`projectmgame.com/…/project-m-3-6-full-changelist`) | Wayback `20150817001217` | reached; re-verified in this session |
| PM 3.5 Changelist + "3.5 System Changes" blogpost | Wayback `20150120100739` / archived | reached; no armor rework |
| PM 3.0 Changelist (`…/project-m-3-0-changelist`) | Wayback `20131213045700` | reached; tiered armor already assumed |
| PM 3.0 Released thread (PMDT dev "Strong Badam", Dec 9 2013) | Wayback `20250405081302` | reached; reproduces official 3.0 log |
| SmashWiki *Project M* (fan source, uncited — but paraphrases the 2.6b OP) | — | reached; the framing #1106 quoted |

Local `~/Documents/Study/reference/Project-M-CC/` (#664) was also checked: the `codes-3_6.txt` GCT
mirror holds **only Gecko/ASM engine codes** (Alternate Stage Loader, Clone Engine, Custom CSS,
Usage Storage Engine…) — no armor PSA and no item roster, so it is silent on both. Its
`changelist-3_61.png` (official PMDT 3.6.1 changelist, Dec 20 2015) corroborates armor-as-per-move
(see §1). Project-M-CC is a *Community-Complete* build off the **leaked 3.6.1 dev build** — a
derivative — but `codes-3_6.txt` is documented as a 1:1 mirror of vanilla `RSBE01.gct`.

---

## §1 — Armor rework

### Claim 1 — "Infinite armor reserved for a 4-move whitelist (Ike full Eruption, Bowser charged smashes, Ganondorf Flame Choke pre-explosion, grab armor)"

**Verdict: CAN'T-CONFIRM (the specific whitelist is SmashWiki-only; it appears in no PMDT primary
reached, including the Demo 2.6b OP).** One fragment — Bowser's charge-scaled smash armor — **is**
first-party confirmed. But no PMDT primary contains "infinite armor is now only reserved for…" or
names Ike Eruption / Ganondorf Flame Choke / grab armor as a whitelist: the Demo 2.6b rework
statement speaks only of Light/Medium/Heavy, and a grep of the first-party 3.6 changelist for
`eruption`, `flame choke`, `grab armor`, `infinite armor`, `knockback-based` returns **zero hits**.
The whitelist may be SmashWiki's own later synthesis (or drawn from a source not reached); treat it
as unconfirmed until a PMDT primary names those four moves.

First-party (PM 3.6 Full Changelist, snapshot `20150817001217`, Bowser):
> "All Smashes have Light Armor while charging."
> "Charge time now determines how strong the Smash's corresponding armor is. Scales from Light
> Armor (no charge) to Super Armor (full charge)."

This confirms the "Bowser's smash attacks (when charged a certain time)" fragment — but names
"Super Armor," not "infinite armor," and says nothing of the other three whitelist members.

### Claim 2 — "Other armored moves converted to knockback-based armor"

**Verdict: CONFIRMED (first-party).** The Demo 2.6b changelist states the standardization verbatim,
in the "General Character, Gameplay Mechanics, and Additions" section:
> "All Armor has been standardized via knockback as Light, Medium, or Heavy."

This is the PMDT-primary grounding for the catalog's "knockback-based armor" claim. The
per-character sections corroborate the sweep — armor is a per-move property PMDT retuned across the
cast to fit the standard:
> "Bowser's Armor matched to the Project M standard of Light, Medium, and Heavy Armor." (Demo 2.6b)
> "Squirtle's Armor system was streamlined to match the new Project M standard of Light, Medium and
> Heavy Armor." (Demo 2.6b)
> "Down B Super Armor replaced with Heavy Armor." (Pit, Demo 2.6b — old infinite/super armor being
> converted into the new knockback tiers)

The "numeric threshold" phrasing is SmashWiki's gloss, but the *mechanism* it glosses — armor
graded by knockback into Light/Medium/Heavy — is exactly what the primary states.

### Claim 3 — "Color/visual overlays added to indicate armor state, more opaque = stronger"

**Verdict: CONFIRMED (first-party), including the 'more opaque = stronger' detail.** The Demo 2.6b
changelist states it directly:
> "There are color indicators for the characters that have armor during their moves, such as Red for
> Bowser and Blue for Squirtle, with more opaque overlays generally indicating stronger armor."

This is verbatim what SmashWiki paraphrases — so SmashWiki's "uncited" armor passage was faithfully
restating this PMBR sentence. Corroborated by the 3.6 changelist's per-move "Armor Indicator" edits
("Down Tilt - Armor Indicator added for light armor"; "Adjusted Armor indicator to match") and by
Squirtle's 2.6b line ("flashes blue when he has Medium Armor").

### Claim 4 — "Which PM version introduced the rework?"

**Verdict: RESOLVED to the Demo 2.6b era (Aug 2013).** The rework's *introducing statement* is the
Demo 2.6b "General … Gameplay Mechanics" line above ("All Armor has been standardized via
knockback…"), authored by PMBR. Consistent with this, the 2.6b→3.0 changelist already treats tiered
armor as an assumed baseline (only per-character tweaks, e.g. Ike "Aerial Up B no longer has medium
armor…"), and 3.5/3.6 continue to retune it move-by-move. So the system is **introduced in Demo
2.6b and evolves through 3.6**; PM 3.6 (the pycats baseline) inherits it.

---

## §2 — Item roster (the 13 buff items)

**Verdict split:**
- **Super Star (Starman), Timer, Superspicy Curry — REFUTED for the Demo era (first-party).** The
  Demo 2.5b changelist (PMBR, 2013) states plainly:
  > "Timer, Starman, and curry are stickers due to still not working properly"

  These three items were **non-functional in PM and demoted to trophies/stickers** — so the #1106
  "behaves as in Brawl" inference is **wrong for the Demo era**. Whether they were ever restored by
  3.6 is not stated anywhere reached (the 3.6 changelist is silent), so the safe status is
  **"known-broken in PM Demo; unconfirmed for 3.6"** — not `✓`. This also corroborates the
  Curry→"Turbo" replacement the item sweep found on SmashWiki (a broken Curry is why it was
  replaced).
- **The other 10 items (Heart Container, Maxim Tomato, Food, Metal Box, Franklin Badge, Bunny
  Hood, Screw Attack item, Super Mushroom, Warp Star, Lightning): CAN'T-CONFIRM
  (changelog-silent).**

The official PM 3.6 Full Changelist (re-fetched first-party this session) has **no Items section**;
its headings are Costumes & Aesthetics, Misc, Music & Sound Effects, Stages, and one section per
character. No buff item is named. This silence is the *expected* result — PM changelists document
character/stage/aesthetic changes, and PM competitive play runs items off — and it means the #1106
`✓ᴵ` inference stance is accurate for the 10 silent items: **do not upgrade any to PM-confirmed on
the changelist.**

The one first-party item sentence (PM 3.6 Full Changelist, Misc):
> "Giga can now grab items, and use most of them."

This confirms an item *system* functions in PM 3.6 (there are items for Giga to grab and use) — a
mild upgrade of "does PM 3.6 have a working item system at all?" from inference to
**first-party-confirmed: yes** — but says nothing about any specific item's presence or behavior.

**Item toggle default (sub-question C):** not-found in any primary. No PMDT document reached states
whether PM ships items on or off out of the box; the items-off norm is a competitive **ruleset
convention**, not a confirmed game default.

**Superspicy Curry — refutation now first-party.** The catalog's Curry row (flames for ~13s)
describes the *Brawl* item. The Demo 2.5b changelist shows curry was **non-functional in PM**
("...curry are stickers due to still not working properly"), and SmashWiki adds that PM replaced it
with a "Turbo" item in v3.0. So the Curry row is **wrong for PM** — the exact 3.6 behavior (Turbo?
absent?) still needs a datamine (thread B), but "flames as in Brawl" is refuted.

---

## §3 — Which #1106 `✓ᴵ` marks can be upgraded (the deliverable)

| #1106 row | This ticket's verdict | Mark action |
|-----------|----------------------|-------------|
| Super Star (Starman), Timer (items) | **REFUTED for Demo era** (2.5b: "stickers…not working properly") | Change `✓ᴵ` → **flag "known-broken in PM Demo; unconfirmed for 3.6"** (not `✓`, not a clean `—`). |
| Superspicy Curry (item) | **REFUTED** (2.5b sticker + SmashWiki v3.0 "Turbo" replacement) | Change `✓ᴵ` → **"broken in Demo; replaced by 'Turbo' per SmashWiki; 3.6 behavior needs datamine"** — the "flames as in Brawl" effect is wrong. |
| Other 10 item rows (§2) | can't-confirm — changelog-silent | **Stay `✓ᴵ`.** None upgrade. Add a note: "PM 3.6 changelist is silent; presence is a Brawl-base inference (#1108)." |
| Super armor / knockback-based armor rows (PM-specific note) | **CONFIRMED first-party** (Demo 2.6b: knockback-standardized Light/Med/Heavy + opacity-scaled overlays; version = 2.6b); **only the 4-move infinite-armor whitelist stays can't-confirm** | **Upgrade the source:** replace the SmashWiki citation with the **Demo 2.6b changelist** primary quote; keep the PMDT **Light/Medium/Heavy** vocabulary + color overlays. Mark the specific 4-move infinite-armor whitelist as **SmashWiki-only, unconfirmed by any PMDT primary**. |

Applying these edits to `fighter-buffs-findings.md` is the trivial downstream follow-up the #1108
scope explicitly defers (not done here).

---

## §4 — Follow-ups surfaced (for tracker #1107)

- **Infinite-armor 4-move whitelist (residual gap):** no PMDT primary reached names Ike Eruption /
  Ganondorf Flame Choke / grab armor as an infinite-armor whitelist — it may be SmashWiki's own
  synthesis. If it becomes decision-bearing, the route is a PM 3.6 codeset/PSA datamine of those
  specific moves (or a SmashWiki citation-chase), not the changelogs (which are silent on it).
- **Curry→"Turbo" / item 3.6 status (thread B / datamine):** Starman/Timer/Curry were broken in the
  Demo era; whether 3.6 restored them (or what Curry became) needs a PM 3.6 item-config datamine —
  the changelist can't answer it.
- **Item toggle default (thread B / datamine):** whether PM ships items on/off is only answerable
  from PM's game config, not the changelog.
- The `✓ᴵ`-mark edits in §3 are a trivial catalog-cleanup follow-up (not this ticket).

## Refs

Parent: #1107 (tracker). Seed: #1106 (`docs/research/fighter-buffs-findings.md`). Canon baseline:
PM 3.6 (`docs/project-m-parity.md`). Source map: `docs/pm-reference/where-to-find-source-data.md`,
`docs/pm-reference/items.md`. Local PM primary: `~/Documents/Study/reference/Project-M-CC/` (#664).
Router: `docs/mechanics-index.md`.
