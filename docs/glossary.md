# Glossary

The single place to look up a PM/Smash mechanics term or a pycats project term.
Entries are **one-line definitions + a pointer** to the authoritative doc — the
linked doc owns the full description, this page just indexes it (so the two can't
drift; same principle as [ADR-0003](./adr/0003-tuning-data-provenance-and-drift-guard.md)).

Sections mirror the [PM mechanics reference](./pm-reference/00-overview.md) sub-domains,
plus a final section for pycats-specific project terms. When a term here appears in a
doc or ticket, it carries the meaning recorded below.

> Convention: most mechanics are described **qualitatively**; PM-specific *numbers*
> (frame data, magnitudes) are sourced per-character/version in the linked doc, not here.

---

## Knockback, hitstun & launch

| Term | Meaning | Reference |
|---|---|---|
| **knockback (KB)** | Dimensionless launch magnitude from the Melee-onward formula shared by Brawl/PM. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#knockback-magnitude) |
| **BKB** (base knockback) | A hitbox's knockback floor at 0% damage. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#knockback-magnitude) |
| **KBG** (knockback growth) | How fast a hitbox's knockback scales with the target's percent. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#knockback-magnitude) |
| **WDSK** (weight-dependent set knockback) | Set-knockback that ignores victim percent but still scales with weight + KBG/BKB. | [moveset](./pm-reference/moveset-and-frame-data.md) |
| **weight** | The only defender attribute in the KB formula; heavier launches less. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#knockback-magnitude) |
| **hitstun** | KB-scaled frames the victim cannot act after the hitlag freeze ends. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#hitstun) |
| **hitlag** (freeze frames) | Impact-pause freezing both fighters before knockback applies. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#hitlag-freeze-frames) |
| **crouch-cancel** | Crouching when hit scales down hitlag (×0.67) and knockback — a defensive option. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#hitlag-freeze-frames) |
| **launch velocity & decay** | Initial launch speed (KB×0.03) bled off ~0.051/frame until it reaches zero. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#launch-velocity--per-frame-decay) |
| **DI** (Directional Influence) | Holding a direction rotates the launch trajectory without changing its magnitude. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#di--sdi) |
| **SDI** (Smash DI) | Rapid stick inputs during hitlag nudge the victim's position to escape multi-hits. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#di--sdi) |
| **Sakurai angle** (361) | Angle sentinel: airborne-fixed, grounded scales flat→max with KB (weak grounded hits stay flat). | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#launch-angles--sentinels) |
| **autolink angles** (365/366) | Angles that scale with attacker motion to keep multi-hit moves connecting. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#launch-angles--sentinels) |

## Hitboxes, priority & moves

| Term | Meaning | Reference |
|---|---|---|
| **hitbox** | Damaging collision shape on a swung limb, active only during a move's active frames. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#the-hitbox--hurtbox-model) |
| **hurtbox** | The vulnerable body region where a hit can connect. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#the-hitbox--hurtbox-model) |
| **capsule** (swept hitbox) | Stretched swept-circle hitbox so fast limbs don't tunnel between frames. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#the-hitbox--hurtbox-model) |
| **intangibility** | A state with no hurtbox interaction (dodges, ledge/respawn invincibility). | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#the-hitbox--hurtbox-model) |
| **sweetspot / sourspot** | The strong tip hitbox vs the weaker near-body hitbox on one move. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#multi-hitbox-moves--hitbox-id-priority) |
| **one-connect rule** | A move hits a given fighter only once per use. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#multi-hitbox-moves--hitbox-id-priority) |
| **hitbox-id priority** | Among a move's overlapping boxes, the lowest id (highest priority) applies. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#multi-hitbox-moves--hitbox-id-priority) |
| **clank / priority** | Deterministic rule resolving two opposing ground hitboxes that overlap the same frame. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#clank--priority-between-opposing-attacks) |
| **priority range** (9%) | Damage within 9% cancels both attacks; a >9% gap lets the stronger continue. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#clank--priority-between-opposing-attacks) |
| **transcendent priority** | Per-move flag letting an attack pass through without clanking. | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#clank--priority-between-opposing-attacks) |
| **stale-move negation** | Repeating a move weakens its damage/knockback until refreshed (a ~9-move staleness queue). | [hitboxes-priority](./pm-reference/combat-hitboxes-priority.md#stale-move-negation) |
| **startup / active / recovery** | A move's frames before / during / after its hitboxes are present. | [moveset](./pm-reference/moveset-and-frame-data.md#per-move-frame-data-fields) |
| **IASA** | "Interruptible as soon as" — frame letting you act early during recovery. | [moveset](./pm-reference/moveset-and-frame-data.md#per-move-frame-data-fields) |
| **landing lag / autocancel** | Endlag for landing mid-aerial; autocancel windows are frames where landing has none. | [moveset](./pm-reference/moveset-and-frame-data.md#per-move-frame-data-fields) |
| **rehit-rate** | Frames between re-hits of the same target by a looping multi-hit move. | [moveset](./pm-reference/moveset-and-frame-data.md#per-move-frame-data-fields) |
| **normals / smashes / aerials / specials** | The move taxonomy: A-ground attacks / chargeable KO attacks / A-air attacks / B-moves. | [moveset](./pm-reference/moveset-and-frame-data.md#move-taxonomy) |
| **projectile** | A separate spawned entity with its own position, velocity, and lifetime. | [moveset](./pm-reference/moveset-and-frame-data.md#projectiles) |

## Movement & tech

| Term | Meaning | Reference |
|---|---|---|
| **walk / run** | Analog grounded stroll (fully actionable) vs holding the dash direction past the initial window. | [movement-and-tech](./pm-reference/movement-and-tech.md#ground-movement) |
| **initial dash / dash-dance / foxtrot** | The dash burst, rapidly reversing within it, and repeatedly re-dashing forward. | [movement-and-tech](./pm-reference/movement-and-tech.md#ground-movement) |
| **pivot** | Frame-perfect turnaround at dash end to attack with momentum. | [movement-and-tech](./pm-reference/movement-and-tech.md#ground-movement) |
| **jumpsquat** | Grounded startup frames before leaving the ground. | [movement-and-tech](./pm-reference/movement-and-tech.md#jumps) |
| **jump-cancel (JC)** | Cancelling grab/up-smash/up-B out of jumpsquat. | [movement-and-tech](./pm-reference/movement-and-tech.md#jumps) |
| **short hop / full hop** | Quick press = low hop; held press = full-height jump. | [movement-and-tech](./pm-reference/movement-and-tech.md#jumps) |
| **double jump / DJC** | A mid-air jump; double-jump cancel uses an aerial to cut its rise short. | [movement-and-tech](./pm-reference/movement-and-tech.md#jumps) |
| **fast-fall** | Tap down past the jump apex to snap to a faster terminal fall speed. | [movement-and-tech](./pm-reference/movement-and-tech.md#air-movement) |
| **air drift / momentum carry** | Horizontal air control; velocity carries between ground and air. | [movement-and-tech](./pm-reference/movement-and-tech.md#air-movement) |
| **wavedash** | Air-dodging diagonally into the ground for an instant ground slide. | [movement-and-tech](./pm-reference/movement-and-tech.md#pm-signature-tech) |
| **waveland** | The grounded slide + landing lag a wavedash resolves into on contact. | [movement-and-tech](./pm-reference/movement-and-tech.md#pm-signature-tech) |
| **L-cancel** | A shield press before landing halves an aerial's landing lag. | [movement-and-tech](./pm-reference/movement-and-tech.md#pm-signature-tech) |

## Defense — shield & dodge

| Term | Meaning | Reference |
|---|---|---|
| **shield** | A bubble that blocks hits at the cost of shield HP; geometry (not HP) decides blocking. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#shield) |
| **shield poke** | A hit reaching an exposed hurtbox without touching the shrunken bubble. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#shield) |
| **shieldstun** | Frames locked in shield after a block: `floor(damage × 0.345)`. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#shield) |
| **shield break → dizzy** | Shield HP hitting 0 breaks the shield, launching then dizzy-stunning the fighter. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#shield) |
| **out-of-shield (OOS)** | Acting directly from shield (jump/grab/dodge/drop) without a full release. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#shield) |
| **powershield / parry** | A tightly-timed shield press that negates shieldstun and reflects projectiles. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#powershield--parry) |
| **spot dodge** | A grounded in-place dodge granting intangibility. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#dodges) |
| **roll** | A grounded dodge that travels a set distance and turns you around. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#dodges) |
| **air dodge** | A single airborne directional dodge; the input that feeds wavedash in PM. | [defense-shield-dodge](./pm-reference/defense-shield-dodge.md#dodges) |

## Grabs & throws

| Term | Meaning | Reference |
|---|---|---|
| **standing / dash / pivot grab** | Grab from idle / while running (more endlag) / turning around to cover behind a dash. | [grabs-throws](./pm-reference/grabs-throws.md#the-grab) |
| **OOS grab** | A dedicated grab straight from shield — a primary block punish. | [grabs-throws](./pm-reference/grabs-throws.md#the-grab) |
| **grab hold** | Holding a grabbed opponent; max duration scales inversely with their damage. | [grabs-throws](./pm-reference/grabs-throws.md#grab-hold) |
| **pummel** | Repeated taps dealing minor damage to a held opponent. | [grabs-throws](./pm-reference/grabs-throws.md#pummel) |
| **throw** | A directional commit launching the held opponent (forward/back/up/down). | [grabs-throws](./pm-reference/grabs-throws.md#throws) |
| **grab release / mash-out** | Grab ending without a throw; the grabbed fighter mashes inputs to escape sooner. | [grabs-throws](./pm-reference/grabs-throws.md#release--mash-out) |
| **grab/attack/shield triangle** | Neutral RPS: grab beats shield, shield beats attack, spacing beats grab. | [grabs-throws](./pm-reference/grabs-throws.md) |

## Fighter states

| Term | Meaning | Reference |
|---|---|---|
| **action state** | One enumerated action a fighter occupies at a time (with an orthogonal tangibility flag). | [fighter-states](./pm-reference/fighter-states.md#the-model) |
| **subaction** | The animation driven by an action, in a separate ID namespace. | [fighter-states](./pm-reference/fighter-states.md#the-model) |
| **tangibility** | The vulnerable / intangible / armored flag set by the current state. | [fighter-states](./pm-reference/fighter-states.md#the-model) |
| **helpless / special-fall** | An actionless airborne state after up-B/airdodge, until landing. | [fighter-states](./pm-reference/fighter-states.md#state-categories) |
| **tumble** | A high-knockback flailing state; can be teched or DI'd. | [fighter-states](./pm-reference/fighter-states.md#state-categories) |
| **knockdown / prone** | Lying on the ground after a hard launch. | [fighter-states](./pm-reference/fighter-states.md#state-categories) |
| **getup** | Options to rise from knockdown (neutral / roll / attack). | [fighter-states](./pm-reference/fighter-states.md#state-categories) |
| **tech** | A well-timed press avoiding knockdown on impact (see also wall/ground teching). | [fighter-states](./pm-reference/fighter-states.md#state-categories) |
| **dizzy / stun** (shield-break) | An input-locked helpless state after a broken shield. | [fighter-states](./pm-reference/fighter-states.md#state-categories) |

## Ledge & edge

| Term | Meaning | Reference |
|---|---|---|
| **ledge sweetspot** | The catch region where a fighter snaps onto a grabbable edge. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#grabbing-the-ledge) |
| **ledge-hang** | The hang state holding the ledge, with ledge intangibility. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#ledge-hang--intangibility) |
| **ledge intangibility** | The invincibility burst on grab that decays with repeated grabs (curbs stalling). | [ledge-mechanics](./pm-reference/ledge-mechanics.md#ledge-hang--intangibility) |
| **neutral getup** | Climb onto the stage from the ledge; slow and punishable at high percent. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#getup-options) |
| **ledge roll** | Roll onto the stage past the edge; vulnerable during the roll. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#getup-options) |
| **ledge attack** | Climb with a hitbox to clear the close-edge space. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#getup-options) |
| **ledge jump** | Jump from the hang into an aerial or further recovery. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#getup-options) |
| **ledge drop / re-recover** | Drop from the ledge, then double-jump or aerial back to reposition. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#dropping-off--re-recovering) |
| **edgeguarding** | Attacking or denying a recovering opponent off-stage. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#edgeguarding-edge-hog--trump) |
| **edge-hog** | Occupying the ledge yourself so the opponent can't grab it. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#edgeguarding-edge-hog--trump) |
| **ledge-trump** | Grabbing a ledge an opponent holds, knocking them off into a vulnerable state. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#edgeguarding-edge-hog--trump) |
| **the "2-frame"** | The brief vulnerability window as an opponent grabs the ledge; a well-timed hit catches it. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#edgeguarding-edge-hog--trump) |
| **teching** (wall/ground) | A right-timed press cancelling a wall/ceiling/ground bounce. | [ledge-mechanics](./pm-reference/ledge-mechanics.md#teching) |
| **ledge-hang (pycats v1)** | Implemented ledge-hang: auto-grab solid edges, getup/drop/timeout, one-occupant lockout. | [ledge §pycats status](./pm-reference/ledge-mechanics.md#pycats-status) |

## Stages & environment

| Term | Meaning | Reference |
|---|---|---|
| **main platform / floor** | The solid ground fighters stand on; its ends are grabbable ledges. | [stages-and-environment](./pm-reference/stages-and-environment.md#stage-anatomy) |
| **ledges (grabbable edges)** | Grabbable main-stage edges; pass-through platforms are **not** grabbable. | [stages-and-environment](./pm-reference/stages-and-environment.md#stage-anatomy) |
| **solid platform** | A platform that collides from all sides. | [stages-and-environment](./pm-reference/stages-and-environment.md#platform-types) |
| **pass-through / drop-through platform** | Collides only from above; press down to drop through. | [stages-and-environment](./pm-reference/stages-and-environment.md#platform-types) |
| **blast zone / blast line** | The four off-screen boundaries; crossing one is a KO. | [stages-and-environment](./pm-reference/stages-and-environment.md#blast-zones) |
| **KO** | A fighter launched far enough to cross a blast line. | [stages-and-environment](./pm-reference/stages-and-environment.md#blast-zones) |
| **dynamic camera** | Zoom/pan keeping all live fighters framed; no fixed unit→pixel scale. | [stages-and-environment](./pm-reference/stages-and-environment.md#camera) |

## Conventions & project / repo terms

| Term | Meaning | Reference |
|---|---|---|
| **Project M (PM) / PM 3.6** | The community Brawl mod (Melee-leaning) and the canonical version pycats sources from. | [overview](./pm-reference/00-overview.md#what-project-m-is) |
| **60 Hz fixed timestep** | The game is locked to 60 FPS — one simulation tick per displayed frame. | [overview](./pm-reference/00-overview.md#conventions-every-reference-doc-follows) |
| **integer frames** | All frame data is whole-frame counts under the fixed-60Hz clock. | [overview](./pm-reference/00-overview.md#conventions-every-reference-doc-follows) |
| **PX_PER_UNIT** | pycats maps one PM spatial unit to ~5.4 pixels (combat numbers entered raw, then scaled). | [overview](./pm-reference/00-overview.md#conventions-every-reference-doc-follows) |
| **angle sentinel** | A special angle code (e.g. 361, 365/366) interpreted by a rule, not as literal degrees. | [knockback-hitstun](./pm-reference/combat-knockback-hitstun.md#launch-angles--sentinels) |
| **archetype** | A pycats cat that *plays as* a Project M character (e.g. Nalio ≈ the PM Mario archetype). | [project-m-parity](./project-m-parity.md) |
| **golden** | A recorded per-frame baseline the deterministic sim is checked against byte-for-byte. | [REGEN_PROTOCOL](../tests/golden/REGEN_PROTOCOL.md) |
| **parity** | Two implementations producing byte-identical output (the now-retired legacy-vs-statechart guard). | [ADR-0002](./adr/0002-dual-backend-endgame.md) |
| **deterministic** | Same inputs → same outputs every frame (no RNG, no wall-clock); required for golden/parity safety. | [CONTEXT.md](../CONTEXT.md) |
| **stochastic** | Involves randomness (RNG-driven) — the opposite of deterministic. pycats controllers must be RNG-free, which is why Smash's stochastic CPU AI can't be copied directly. | [npc-behaviors](./research/2026-06-25-npc-behaviors-and-dual-controller.md) |
| **fleet / claim** | The multi-agent workflow; an agent claims a ticket via `pmtools claim <issue> --as <fruit>`. | [RULES.md](../RULES.md) |

---

*Adding a term?* Put it under the section matching its sub-domain, keep the definition to
one line, and link the **authoritative** doc (don't restate its prose here). New mechanics
*descriptions* belong in the relevant [`pm-reference`](./pm-reference/00-overview.md) doc.
