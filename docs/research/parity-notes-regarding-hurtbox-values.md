# Parity notes: hitbox/hurtbox POSITION values (`dx`/`dy`) — the fidelity ceiling

**Ticket:** #310 (research) · **Paired with:** #309 (zone-anchor, shipped the flagged
values) · **Builds on:** #120 (Smash units & sources), ADR-0003 (tuning provenance),
#224 (OS decompilation catalogue, closed), #192 (guessed-value tracker).

> Terminology: this doc says "hitbox positions" throughout. The same reasoning applies
> to hurtbox circle offsets (`characters/*.py` `Hurtbox(circles=...)`) — both are
> body-relative `Circle(dx, dy)` offsets, so the ceiling below is identical for both.

## TL;DR verdict

**Combat *scalars* reach exact Project M parity; hitbox/hurtbox *positions* do not, and
cannot without rebuilding PM's model/skeleton/camera pipeline inside a 2-D game.** The
achievable ceiling for positions is **proportional parity** (same body-relative zone and
same relative reach ordering), which is exactly what #309's `zone_dy` anchor encodes.
Positions are therefore a **"playtest / feel" provenance category**, not an
"unresolved-research" one — distinct from the datamined scalars.

This is **not** a gap in effort. It is a property of the coordinate systems.

## Why scalars are faithful but positions are not

| Quantity | PM/Brawl source | pycats target | Faithful? |
|---|---|---|---|
| damage %, base knockback, knockback growth, launch angle, weight, frame timings | datamined **dimensionless / engine-native integers**; the knockback *formula* is itself datamined (#120) | copied raw | **Yes — exact** |
| hitbox/hurtbox **position** (`dx`/`dy`) | a **bone-relative 3-D offset**: "X units from bone *N*, at animation-frame *F*," in abstract world units | pixels from a 2-D rectangle's top-left | **No — not a lookup** |

A scalar like `KBG = 100` means the same thing in any reimplementation, so it transfers
losslessly. A position is **not a number in a shared coordinate system** — it is a
*mapping* that would have to be constructed, and the mapping is missing two links.

### Missing link 1 — no skeleton (the bone→body gap)

PM/Brawl hitboxes hang off a **bone** on a rigged 3-D model. Each hitbox stores a bone
id plus an `(x, y, z)` offset *from that bone*, and the bone itself **moves every
animation frame**. rukaidata exposes the bone-relative offset and the bone id — but not
where the bone *is* in world/screen space at a given frame. Recovering that needs the
character's **skeleton + per-frame bone transforms** (a Brawl model dump via
`brawllib_rs` or equivalent).

pycats has **no skeleton at all** — fighters are rectangles with drawn cat features, not
rigged models. So "offset from bone *N*" has nothing to attach to. This is the step we
approximate by eye when we author `Circle(dx, dy)`.

### Missing link 2 — no fixed unit→pixel scale (#120's wall)

Even with a bone position in hand, converting world units → pixels needs a constant that
**#120 established does not exist**: Brawl positions are abstract units, the camera zooms
dynamically, and SmashWiki states hitbox sizes are literally *"based on feel."* pycats'
`PX_PER_UNIT ≈ 5.4` (used for *radii*) is itself a **playtest-chosen approximation**, not
a derived value (tracked as #195) — so it cannot serve as a ground-truth position scale.

Two missing links, one of which (#2) is **provably not a fixed number**. That is the hard
wall.

## What "100% parity" would actually require — and why each path stalls

1. **Rebuild the model pipeline (the only route to *proportional* fidelity).** Extract
   each character's skeleton + per-frame bone transforms (`brawllib_rs`), compose with
   rukaidata's bone-relative offsets → hitbox position in model-local space *per frame*,
   then apply **one chosen model→pixel scale + origin per character**. This yields
   positions that sit in the same place *relative to the body* as PM.
   - **Cost:** a full rigging/animation-sampling pipeline for a game that has no rig.
     Disproportionate to a 2-D cat fighter.
   - **Still not pixel-exact:** the final model→pixel scale is a feel choice (link #2
     never closes), so the result is *proportional*, not identical to a PM screenshot.
2. **Even done perfectly, it wouldn't match the *visual*.** A faithful *bone* position
   points at where Kirby's foot is on the Brawl model — not where the rendered *cat's*
   paw is. In a game that does not use PM's models, **hitbox parity ≠ sprite parity**;
   chasing bone-exactness can actively fight the drawn character.
3. **Redefine parity as proportional/relational (recommended).** Accept the reachable
   ceiling: scalars exact, same body-relative **zone** (head / center / feet — which
   #309 already encodes), same **relative reach ordering** between a character's moves.
   This is the parity that governs gameplay feel, and it is the ceiling #120 implies.

## Answers to the ticket's three questions

1. **Is faithful derivation possible at all?** **No, not to pixel fidelity.** It requires
   a skeleton/model dump pycats does not have *and* a unit→pixel scale that #120 shows is
   not a fixed number. Per the ticket's hard-timebox: recovering bone→body needs an
   engine/model dump not in hand → this *confirms* the ceiling; no `brawllib_rs`
   excavation was started.
2. **Do the OS decompilation sources (#224) expose usable relative positions?** They
   crack **engine constants** (scalars, forces, formulas) — which is why *those* are
   faithful — but a hitbox's screen position is still a function of the runtime
   skeleton + camera, which the decomps compute at runtime rather than store as a
   copyable relative pixel value. So they do **not** hand over a better position source
   than rukaidata's bone offsets.
3. **If not derivable, document as "playtest / feel" provenance.** **Yes — this is the
   verdict.** See below.

## Provenance decision (recommendation)

Positions (`dx`/`dy` for both hitboxes and hurtbox circles) are a first-class
**"playtest / feel" provenance category**, on par with FOUND/GUESS/TUNED — **not** a
perpetual "GUESS → to research" item. They are *intentionally* feel-tuned because a
faithful pixel value does not exist to be found.

- **Retire** the "needs research" implication of the `⚠ playtest starting point` markers
  on **positions** — they are done, blessed as feel-provenance. Keep the marker glyph as
  a *"feel-tuned, adjust by playtest"* signal, not a *"faithful value pending"* one.
- **Keep** the research posture only for **scalars** still marked GUESS (those *can* be
  datamined; #192 owns that trail).
- **ADR-0003 is `Proposed`** (human sign-off pending, #226/#233). Do **not** amend it
  here. When it is accepted, register position values with a provenance `status` of
  `"FEEL"` (or fold into `TUNED` with `source: "playtest"`), so the drift-guard treats a
  position change as a feel re-tune, not a citation desync. This is a recommendation for
  the #233 refactor, filed against that ticket's scope.

### Flagged inventory (#309) — disposition

| Location | Values | Disposition |
|---|---|---|
| `pycats/characters/body_zones.py` | `BODY_ZONES` fractions (0.15 / 0.50 / 0.85 / 1.10) | **FEEL — retire "to research."** Body-relative by construction; correct on any body. |
| `pycats/characters/birky_cat.py` | every move's `dy` via `zone_dy(...)`; the `dx` offsets | **FEEL — retire "to research."** Zone + reach ordering match PM proportionally. |
| `pycats/characters/nalio_cat.py`, `narz_cat.py` | move `dx`/`dy` | **FEEL** — adopt the same disposition as each is next touched. |
| all `Hurtbox(circles=...)` offsets | body-relative circle `dx`/`dy` | **FEEL** — same ceiling; body-relative. |

## Consequences

- **No follow-up DEV ticket for "derive faithful positions"** — the derivation is not
  reachable, so filing one would be a puzzle with no solution. The only DEV-shaped
  follow-up is the ADR-0003 provenance-status recommendation, which belongs to the
  already-filed **#233** (blocked on #226), not a new ticket.
- **What *does* improve position quality going forward:** playtest feel + the #309
  zone-anchor scheme (adopt `zone_dy` for the rest of the roster as characters are
  touched), not a datamining pass.
- **Scalars remain the parity lever:** keep sourcing damage/BKB/KBG/angle/weight/frames
  raw from rukaidata/PM3.6 — that is where "accurate PM values" is both achievable and
  worth the effort.

## References

- #309 — zone-anchor hitbox `dy` (shipped the flagged feel values).
- #120 — `docs/research-120-smash-units-and-sources.md` (no fixed unit→pixel mapping).
- #195 — `PX_PER_UNIT` not yet a named constant.
- #224 — open-source decompilation/reimplementation catalogue (closed).
- ADR-0003 — `docs/adr/0003-tuning-data-provenance-and-drift-guard.md` (Proposed).
- #233 — ADR-0003 provenance-registry refactor (blocked on #226 sign-off).
- #192 — guessed-value tracker (owns the scalar research trail).
