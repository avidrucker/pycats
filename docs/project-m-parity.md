# Project M feature-parity differences

Where **pycats deliberately differs from Project M / the Smash lineage**, and where it
currently diverges with convergence planned. These are design decisions (or known
gaps), not bugs — but with no single home they read as bugs to a fresh reader and get
re-investigated from scratch (cf. the #7 / #10 churn). This file is that home.

**Relationship to the PM reference (#147):** the `docs/pm-reference/` set (epic #147)
documents the Project M *baseline* — how PM behaves. **This** doc records where pycats
*departs* from that baseline. The reference docs' "pycats status" footers link here.

## How to add an entry

Append a `###` entry in the same shape — keep it short, link the deciding issue, and
set an honest **Status**:

- **Intentional** — a ratified, deliberate divergence we intend to keep.
- **Current gap — convergence planned (#N)** — pycats differs today, but matching PM is
  tracked as future work.

```
### <Short divergence title>
- **pycats:** <what pycats does>
- **Project M:** <what PM does>
- **Why / status:** Intentional — <rationale>.   (or: Current gap — convergence planned (#N).)
- **Refs:** #N, #M, <file/commit>
```

---

## Divergences

### Rematch / play-again advance requires both players to confirm
- **pycats:** Leaving the win/results screen back to character-select requires **both
  players to press "A"** (both-confirm), with a ~2-second input grace window.
- **Project M:** Advances past the results screen on a **single** button press
  (Start/A by one player).
- **Why / status:** **Intentional.** The both-confirm + grace window fixes #10, where
  the still-mashed killing-blow attack key instantly skipped the stats screen before
  either player could read it.
- **Refs:** #10 (`6cd883a`), #11.

### Consolidated main-menu Options sub-menu
- **pycats:** A **single consolidated Options screen** off the main menu holds the
  global display + HUD-overlay settings, persisted via `settings.py`. Per-player config
  (controls / colour / tag) stays PM-faithful on the character-select screen.
- **Project M:** Has **no single Options screen** — settings are distributed and
  context-embedded (Rules menu, CSS, stage select, a Code-Menu overlay) and mostly
  per-session rather than persisted.
- **Why / status:** **Intentional** (ratified, permanent). pycats is a small 1v1
  trainer; one place + persistence is the value-add. Decision recorded in #122; PM-model
  analysis in `docs/research/project-m-menu-architecture.md` §10.
- **Refs:** #116, #121, #122.

### Status-effect count-down bars (HUD overlay)
- **pycats:** Draws an optional count-down bar above a fighter for timed status effects
  (shield, shield-break stun). On by default; toggleable in the Options sub-menu.
- **Project M:** Shows **no such bar** — shield size and stun are read from the
  animation, not an explicit gauge.
- **Why / status:** **Intentional.** A trainer-friendly readability aid; treated like a
  Project+ Code-Menu visual overlay, and made toggleable so it can be turned off for
  PM-faithful practice.
- **Refs:** #111, #121 (toggle), #122.

### Air dodge preserves momentum and has no helpless state
- **pycats:** Air dodge **preserves all momentum** (Brawl-style), applies a
  non-canonical *additive* horizontal nudge on a directional dodge, has **no
  helpless / special-fall** state, and returns straight to `fall` when the 14-frame
  dodge timer expires — a Brawl/Melee hybrid matching neither game.
- **Project M:** Uses the **Melee-style** air dodge — halts/replaces momentum with a
  directional burst and drops the fighter into a **helpless / special-fall** state
  (the basis of wavedashing).
- **Why / status:** **Current gap — convergence planned (#184).** Research #23 confirmed
  this isn't a bug to bless or revert (a bare `vel.y = 0` would be PM-wrong too — halt
  without helpless); the PM-faithful air dodge is a feature, deferred as #184.
- **Refs:** #23 (`docs/research/air-dodge-vertical-momentum-findings.md`), #184, #24.
