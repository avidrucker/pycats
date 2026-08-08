# Roster completion assessment — Nalio / Birky / Narz (#561)

**Ticket:** #561 (research spike; parent tracker #566). **Role:** RESEARCH. **Date:** 2026-07-05. **Agent:** DRAGONFRUIT.
**Box:** ~90m breadth spike — a cross-cat completion matrix + a prioritized, classified, routed gap list. *Assessment only — follow-ups are proposed, NOT filed.*

---

## Headline

**All three cats are complete on ground normals, aerials, and smashes.** The gaps are concentrated in three places, in priority order:

1. **Specials** — Nalio has 1 of 4 (neutral-B fireball); **Birky and Narz have zero**. The dispatch hook exists; the *moves* (and several of their *mechanics*) do not.
2. **Recovery (up-B) + fast-fall + grabs/throws** — **missing engine mechanics**, not just missing data. Recovery is the most v1-critical (you cannot get back to stage without it).
3. **Value sourcing** — uneven: Nalio pinned (#557), Narz cited (#290), Birky still #229 guesses (blocked on a Kirby decision).

Nothing here is a *regression* — the roster is a partial-but-correct implementation. This is a "what's left to build" map, not a bug list.

---

## Matrix 1 — move coverage

Legend: ✓ present · ✓ᵃ present via the legacy `"attack"` alias · ✗ missing · ⚙ engine-shared (not per-cat data)

| Move slot | Nalio | Birky | Narz | Notes |
|---|:--:|:--:|:--:|---|
| jab | ✓ | ✓ | ✓ | |
| ftilt | ✓ | ✓ | ✓ | fwd/back both → ftilt (Smash has no b-tilt) |
| utilt | ✓ | ✓ | ✓ | |
| dtilt | ✓ᵃ | ✓ᵃ | ✓ | Nalio/Birky store dtilt under the legacy `"attack"` alias; Narz uses the canonical `"dtilt"` key — a naming-debt, **not** a functional gap |
| dash-attack | ✗ | ✗ | ✗ | dispatch slot reserved ("+ dash later", `move_select.py`) but unwired; no data on any cat |
| nair / fair / bair / uair / dair | ✓ | ✓ | ✓ | **all aerials complete on all three** |
| fsmash / usmash / dsmash | ✓ | ✓ | ✓ | **all smashes complete on all three** (chargeable) |
| **neutral-B** | ✓ (fireball) | ✗ | ✗ | |
| **side-B** | ✗ | ✗ | ✗ | undefined special = silent no-op (no fallback) |
| **up-B (recovery)** | ✗ | ✗ | ✗ | **nobody has a recovery move** — see engine gap below |
| **down-B** | ✗ | ✗ | ✗ | |
| grab + pummel + throws | ✗ | ✗ | ✗ | **engine-absent** (TODO-only: `attack.py:13-21`, `player.py:25-29,86-87`) |
| getup-attack | ⚙ | ⚙ | ⚙ | wake-up move exists as a **shared engine mechanic** (`getup_attack_timer`, `fighter_chart.py:290`), not per-cat data |
| ledge-attack | ⚙ | ⚙ | ⚙ | part of the shared ledge system (#291/#311), not per-cat move data |

**Reading:** the entire normals/aerials/smash kit is done. The move gaps are **specials** (9 of 12 special slots empty across the roster) and **dash-attack** (all three).

## Matrix 2 — movement / physics value sourcing

Legend: **FOUND** sourced+cited · **CITED** cited to a spec, exact canon TBD · **GUESS** unsourced · **DEFAULT** rides the config global (itself Mario-calibrated)

| Attribute | Nalio | Birky | Narz |
|---|---|---|---|
| weight | 100 **FOUND** (Mario) | 70 **GUESS** (#229) | 87 **CITED** (#290) |
| gravity | 0.5 **FOUND** (#557) | 0.42 **GUESS**, blocked on decision | 0.45 **CITED** (#290) |
| max_fall_speed | 13 **FOUND** (#557; config DIVERGENCE) | 12 **GUESS**, blocked | 13 **DEFAULT** (intentional "match Mario", #290 comment) |
| move_speed | **DEFAULT** (config = Mario FOUND #384; not explicitly pinned) | 5 **GUESS** | **DEFAULT** (intentional match, #290) |
| max_jumps | **DEFAULT** | 6 **GUESS** | **DEFAULT** (intentional match, #290) |
| jump_vel | **DEFAULT** (config = Mario FOUND) | -11 **GUESS** | -12 **CITED** (#290) |

**Reading:** Nalio best (pinned, #557). Narz respectable — cited to the #290 Marth spec with the unspecified attributes *intentionally* defaulted to Mario (a documented posture, not an accident); the open question is only whether #290's numbers are PM-Marth-canonical. Birky is all #229 proportional guesses and is **blocked** on the Brawl-vs-PM3.6 Kirby decision (#528 follow-up #3).

## Matrix 3 — identity / render parity

| Aspect | State |
|---|---|
| Palette | ✓ parity — each cat has a distinct default (`calico`/`ghost`/`void`, `roster.py`) |
| Display name / select tile | ✓ parity (`ARCHETYPE_NAME`) |
| Body / face / silhouette | ⚠ **shared render path** — `render_battle.draw_cat_features` + `cat_faces` draw the *same* cat body/face for all three, differentiated **only by palette** (color/stripe/eye). No per-archetype silhouette. Acceptable for v1 (they're distinguishable); distinct bodies are post-v1 polish. |

---

## Gap classification + routing (per #530)

| Gap | Kind | Route (#530) | v1? | Priority |
|---|---|---|:--:|:--:|
| **Up-B / special-recovery mechanic** | **ENGINE** (missing) | spike → ARC → DEV | **v1** | **1 — highest** |
| Fast-fall | ENGINE (missing) | ARC/DEV (#261 item 1, #229) | v1 (Kirby/Marth feel) | 2 |
| Specials authoring — simple (hitbox/projectile) | DATA (hook ready) | DEV per cat | v1 (≥1–2 signature each) | 3 |
| Specials authoring — mechanic-gated (Narz counter down-B, Birky Stone/transform, side-B tether/command) | ENGINE + DATA | spike → ARC → DEV | mixed | 4 |
| Grab / pummel / throws system | ENGINE (fully absent) | spike → ARC → DEV | **human call** (large; v1 vs early-post-v1) | 5 |
| Birky fall re-pin | DATA | **decision → DEV** (blocked #528 fu#3) | v1 | 6 |
| Narz fall-value confirm | research/confirm → DEV pin | DEV (like #557) | v1 (low) | 7 |
| Dtilt `"attack"`-alias cleanup (Nalio/Birky → canonical `"dtilt"`) | refactor | DEV (tiny) | post-v1 housekeeping | 8 |
| Dash-attack (wire slot + data) | ENGINE + DATA | ARC/DEV | post-v1 | 9 |
| Per-archetype silhouettes | render | DEV | post-v1 polish | 10 |

**v1 line is a judgment call — flagged for the human (per #530: when in doubt, kick to Avi + #387 post-v1 scope).** My recommendation: v1 = recovery + fast-fall + ≥1–2 signature specials per cat + Birky fall pin. Grabs/throws and dash-attack lean post-v1 unless you want full PM-neutral at v1.

## Proposed follow-ups (listed, NOT filed — one at a time under #566)

1. **Up-B / special-recovery ENGINE mechanic** — spike-first (generalize #261 item 2 beyond Birky; likely reuse #184 special-fall/helpless). *No existing ticket* — highest-value gap. → #566 cluster B.
2. **Fast-fall ENGINE mechanic** — #261 item 1 / #229. → #566 cluster C.
3. **Per-cat specials tracker** — child DEVs for the simple specials (data-ready) + spikes for the mechanic-gated ones (counter, transform, tether). Several blocked on (1). → #566 cluster A.
4. **Grab/throw/pummel ENGINE system** — spike-first; v1-vs-post-v1 is a human decision. → #566 cluster E.
5. **Birky fall re-pin** — decision→DEV, blocked on #528 fu#3 (already identified).
6. **Narz fall-value confirm+pin** — verify #290 numbers are PM-Marth-canonical, then pin like #557. → #566 cluster D.
7. **Dtilt alias cleanup** — Nalio/Birky dtilt to the canonical key (tiny refactor). Housekeeping.

## Method / limits
- Grounded in the code: `characters/{nalio,birky,narz}_cat.py`, `combat/move_select.py` (dispatch + `"attack"` alias semantics), `combat/data.py` (defaults), `combat/provenance.py` (config sourcing), `entities/attack.py` + `entities/player.py` (grab TODOs), `fighter_chart.py` (getup-attack state), `render_battle.py` + `cat_faces` (shared render), `roster.py` (identity).
- Not exhaustively deep per cat (breadth spike, per the overrun fallback): individual special *move designs* and exact PM value confirmations are deferred to the routed follow-ups.

## Refs
Parent tracker **#566**; per-cat epics **#142/#228/#294**; engine-prereq tracker **#261**; value routing **#530**; fall physics **#528** + Nalio pin **#557**; special-fall/helpless **#184**; Narz spec **#290**; roster epic **#117**; post-v1 scope **#387**.
