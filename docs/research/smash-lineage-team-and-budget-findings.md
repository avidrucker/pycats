# Team size + budget of the Smash lineage — findings

**Ticket:** #1084 · **Role:** RESEARCH · **area:docs** · **Date:** 2026-08-04 · **Agent:** ELDERBERRY

Context-gathering only — no pycats code/design change. Figures are cited to primary
(dev interviews, Iwata Asks) or secondary (retrospectives, wikis) sources, each with a
confidence label. Where a hard number does not exist, a sourced range is given and marked
an estimate.

---

## TL;DR

- **The retail Smash games scaled ~10× per generation in headcount** while dev *duration*
  stayed short: SSB64 ≈ a dozen people, Melee ≈ 50+, Brawl ≈ 100 full-time / ~700 credited.
- **No official dollar budget has ever been published for any Smash title.** Any cost figure
  is a modelled estimate (headcount × duration × a per-developer cost proxy), not a sourced
  number — labelled as such below.
- **Project M** was an unpaid community effort (PMDT) with no fixed headcount, members across
  10+ countries, run ~2010–2015 (~5 years) until the team stood down.
- **Modern AAA** (the class these were, for their era) runs 200–1,000+ people over 3–6 years,
  with a ~$100M development floor — useful only as an outer bound; the classic Smash teams were
  an order of magnitude smaller than a 2020s AAA team.

---

## Per-title summary

| Title (year) | People | Duration | Confidence | Primary source |
|---|---|---|---|---|
| **SSB 64** (1999) | seed ~3 → grew to ~10–15 | ~1–1.5 yr (prototype Sep 1997; JP release Jan 21 1999) | team **medium** (secondary); duration **high** | shmuplations 1999 interview; Wikipedia |
| **Melee** (2001) | 50+ (by E3 2001) | ~13 months (autumn 2000 → Oct 31 2001 build; JP release Nov 21 2001) | team **medium** (single snapshot); duration **high** | SourceGaming timeline; Wikipedia |
| **Brawl** (2008) | ~100 full-time / ~700 credited | ~2 yr 3 mo (Oct 2005 → JP release Jan 31 2008) | **high** (primary Iwata Asks) | Iwata Asks Vol. 1 §3 |
| **Project M** (2011–2015) | no fixed count; ~10 named project leads + volunteers from 10+ countries | ~5 yr active (early 2010 → first demo Feb 7 2011 → ceased Dec 1 2015) | structure **high**; headcount **low** (no figure) | Wikipedia; SmashWiki |

Dollar budget for all four: **not publicly disclosed** — see *Budget note* below.

---

## Per-title detail

### Super Smash Bros. (N64, 1999) — HAL Laboratory

- **Team size.** No primary interview gives a hard headcount. Secondary/community accounts
  describe a very small seed team — Masahiro Sakurai (design, animation, modelling) and
  Satoru Iwata (programming, then HAL's president), plus a sound editor — that grew to roughly
  **10–15** once Nintendo approved use of its mascots. Treat the "3 → 10–15" figure as a
  **secondary estimate** (medium confidence): the 1999 developer interview and Wikipedia name
  key individuals but do not state a total.
- **Scope pressure.** Sakurai, 1999: *"We were only able to include about 60% of what we had
  planned for Super Smash Bros, sadly,"* and the single-player mode was *"created in the very
  last month of the development in a mad rush."* Balancing used HAL's debug team for test
  matches rather than a dedicated QA org.
- **Timeline.** Sakurai built a prototype in **September 1997** (unannounced to Nintendo),
  shown at the end of 1997; the game released in Japan on **January 21, 1999** — roughly a
  year-plus from approval to ship. Duration **high** confidence; exact start of full production
  not pinned.

### Super Smash Bros. Melee (GameCube, 2001) — HAL Laboratory

- **Team size.** *"Over 50 people"* by **E3 2001** (May 17), per the SourceGaming Melee
  development timeline (relayed via David V. Kimball's compilation). This is a **single
  snapshot** near the end of production, not a start-to-finish average — medium confidence, and
  likely an undercount of everyone who touched the project.
- **Duration.** *"In development for 13 months, beginning around autumn 2000"* (Wikipedia); the
  JP/NTSC build was completed **October 31, 2001**, with JP release **November 21, 2001**.
  Duration **high** confidence.
- **Working conditions.** Notoriously severe crunch — Sakurai described the period as
  *"destructive," with no holidays and short weekends*, and later reports have him working
  ~40-hour stretches and being hospitalized after collapsing. Relevant for budgeting: the short
  13-month calendar was bought with extreme overtime, not a large calm team.

### Super Smash Bros. Brawl (Wii, 2008) — Sora Ltd. / ad-hoc team

- **Team size (primary, high confidence).** From **Iwata Asks: Super Smash Bros. Brawl,
  Vol. 1 §3** — Iwata: *"the number of people involved fulltime was roughly 100"*; Sakurai:
  *"Looking at all the staff that appears in the staff credits, it was about 700 people."* The
  **~100 vs ~700** gap is exactly the credits-count-vs-quoted-headcount distinction the ticket
  flags: ~100 is the core full-time team; ~700 is everyone credited (part-time, outsourced,
  borrowed, support).
- **Assembly.** An ad-hoc team, not a standing studio — core staff from **Game Arts**
  (introduced by Miyamoto, after they finished *Grandia III*), plus personnel **borrowed from
  ~19 different developers**, assembled under **Sora Ltd.** in a rented Takadanobaba, Tokyo
  office where Sakurai relocated for the project's duration.
- **Duration.** Development began **October 2005**; released on Wii in Japan **January 31,
  2008** — approximately **2 years 3 months**.

### Project M (Brawl mod, 2011–2015) — PMDT (community)

- **Structure (high confidence).** A **volunteer** mod of Brawl by the **Project M Development
  Team (PMDT)**, formerly the "Project M Back Room." Members spanned **more than ten
  countries**. Named project leaders included SHeLL, Magus, Strong Bad, jiang, Shadic,
  haloedhero, Yeroc, Shanus, cMart, and Warchamp7 (~10 leads) — a distributed, unpaid,
  role-specialized crew rather than a payrolled studio.
- **Headcount (low confidence).** No source gives a total team size or a per-discipline
  breakdown; the volunteer roster fluctuated over the project's life. Report the count as
  **unknown**, not estimated.
- **Timeline.** Work began **early 2010**; first public demo **February 7, 2011**; the PMDT
  announced it would **cease development on December 1, 2015** — roughly **5 years** of active,
  unpaid work. Reach: 3M+ downloads, a 500,000+ player base, sustained tournament use.
- **Relevance to pycats.** Project M is the closest analogue to this project's *labour model* —
  a distributed volunteer effort re-implementing/tuning fighting-game mechanics with no budget —
  but it stood on Brawl's finished engine and assets; it re-tuned, it did not build from zero.

---

## Budget note (dollar figures)

**No official development budget (in currency) has been published for SSB64, Melee, Brawl, or
Project M.** Nintendo does not disclose per-title budgets, and Project M was unpaid volunteer
work with no budget line at all. Any dollar figure for these titles is therefore a **model**,
not a citation. A first-order estimate multiplies headcount × duration × a per-developer cost
proxy — using a commonly-cited **~$10,000/month (~$120,000/year) fully-loaded cost per
developer** (a US 2020s figure; 1999–2008 Japanese costs were lower, so these are upper bounds):

| Title | Rough model (full-time headcount × duration × ~$120k/dev-yr) | Nature |
|---|---|---|
| SSB 64 | ~12 people × ~1.25 yr ≈ **$1.5–2M** order-of-magnitude | **estimate only** — no source |
| Melee | ~50 people × ~1.1 yr ≈ **$6–7M** order-of-magnitude | **estimate only** — no source |
| Brawl | ~100 full-time × ~2.25 yr ≈ **$25–30M** order-of-magnitude | **estimate only** — no source |
| Project M | volunteer — **$0 payroll**; cost was donated time | n/a |

These are deliberately coarse (one significant figure) and use a modern US cost proxy against
1999–2008 Japanese salaries, so they **overstate** the real spend. Use them only for
sense-of-scale, never as sourced budget numbers.

---

## AAA budgeting scale (framing)

So the Smash figures sit in context — how large-studio budgets generally scale (team × months),
from 2020s industry sources:

- **Team size:** a modern AAA title typically involves **200 to 1,000+ people** across
  disciplines; the largest (e.g. Call of Duty) run into the thousands.
- **Duration:** **3 to 6 years** minimum development cycles.
- **Cost floor:** publishers/analysts use **~$100M** as a rough development floor (excluding
  marketing); top-tier releases reach **$100–300M+** all-in. *The Last of Us Part II* (2020) is
  cited around **$220M**.
- **Per-developer cost proxy:** **~$10k/month (~$120k/yr)** fully-loaded per developer (US).

**Calibration takeaway.** Brawl (~100 full-time, ~2.25 yr) was already a large-team effort for
its day but is an **order of magnitude smaller** than a 2020s AAA team, and the classic Smash
titles bought short calendars with heavy crunch rather than large headcount. For a **solo +
AI-augmented** build, the realistic comparison is not the retail teams at all but **Project M's
labour model** — distributed volunteer re-implementation on top of existing mechanics — scoped
down to one person. The retail figures set the *ceiling of ambition* (what a funded team ships in
1–2 years); Project M sets the *floor of feasibility* (what unpaid re-implementation of these
mechanics has actually looked like).

---

## Sources & confidence

| # | Source | Type | Used for |
|---|---|---|---|
| 1 | [Iwata Asks: Super Smash Bros. Brawl, Vol. 1 §3 — "Searching for Office and Staff"](https://www.nintendo.com/en-za/Iwata-Asks/Iwata-Asks-Super-Smash-Bros-Brawl/Iwata-Asks-Super-Smash-Bros-Brawl-Vol-1/3-Searching-for-Office-and-Staff/3-Searching-for-Office-and-Staff-212682.html) | **Primary** (Nintendo interview) | Brawl ~100 full-time / ~700 credited; team assembly |
| 2 | [Super Smash Bros. – 1999 Developer Interview (shmuplations)](https://shmuplations.com/smashbros/) | **Primary** (Sakurai interview) | SSB64 scope pressure, timeline hints |
| 3 | [Super Smash Bros. (video game) — Wikipedia](https://en.wikipedia.org/wiki/Super_Smash_Bros._(video_game)) | Secondary | SSB64 staff names, prototype/release dates |
| 4 | [Super Smash Bros. Melee — Wikipedia](https://en.wikipedia.org/wiki/Super_Smash_Bros._Melee) | Secondary | Melee 13-month duration, crunch |
| 5 | [Everything We Know About Melee's Development (David V. Kimball)](https://davidvkimball.com/posts/everything-we-know-about-super-smash-bros-melees-development) / [SourceGaming Melee timeline](https://sourcegaming.info/2016/09/16/meleetimeline/) | Secondary (retrospective) | Melee "50+ by E3 2001"; start/end dates |
| 6 | [Project M — Wikipedia](https://en.wikipedia.org/wiki/Project_M) / [Project M — SmashWiki](https://www.ssbwiki.com/Project_M) | Secondary | PMDT structure, 10+ countries, 2010–2015 timeline, leads |
| 7 | [AAA cost/team-size framing — 300Mind](https://300mind.studio/blog/cost-to-develop-video-game/), [Innovecs Games](https://www.innovecsgames.com/blog/aaa-game-development-cost/), [Ask a Game Dev (per-dev cost)](https://www.tumblr.com/askagamedev/617925808134242304/how-does-budget-for-a-aaa-game-gets-estimated) | Secondary (industry) | AAA team 200–1,000+, 3–6 yr, ~$100M floor, ~$10k/mo/dev |

**Blocked/paywalled sources:** none — every source above fetched successfully.
**Availability gap (not a blocked source):** no official **dollar budget** exists for any of the
four titles; the currency figures in the *Budget note* are modelled estimates, flagged as such.
Firmer SSB64/Melee headcounts would need a full **credits count** (Mario Wiki / game credits)
rather than the quoted snapshots used here — a follow-up if a hard number is ever required.
