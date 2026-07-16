# Cat liveliness — reference-games survey (#742)

**Ticket:** #742 (RESEARCH · `area:display`) · **Agent:** DRAGONFRUIT · **Date:** 2026-07-15
**Question:** pycats draws each fighter as a plain colored rectangle, which reads as a static
block at rest. How do shipped games with rectangular / blocky character shapes make those
shapes read as *alive*? This is a design-inspiration survey — prior art only, no pycats
render-pipeline mapping and no prototype (both deliberately deferred; the human chose the
minimal-survey depth).

**In-family context:** one specific technique is already scoped — #567 (DEV, post-v1: idle
breathing animation) and #741 (RESEARCH: breathing cycle duration / timing). This survey maps
the wider design space those sit inside; it does **not** re-spec breathing.

---

## TL;DR

A rectangle reads as alive through four distinct channels, and the strongest reference games
lean on more than one:

1. **Idle-motion** — it moves a little even when doing nothing (breathe, blink, fidget).
2. **Movement-motion** — it deforms and orients with its motion (squash/stretch, lean, rotate).
3. **Impact/event accents** — the world reacts to it (dust, shake, freeze-frame, trails).
4. **Character accent** — a minimal identity cue (eyes/face, differentiated color, framing).

The recurring lesson across every source: **when the character shape is deliberately minimal,
the aliveness budget moves off the sprite and into motion, reaction, and framing.** HAL said it
plainly for BoxBoy — a simple design means you invest in *animation variety*, not detail.

---

## The reference games

Six exemplars, chosen for genuinely rectangular / blocky silhouettes (candidate list from the
ticket, narrowed to the clearest cases).

### 1. Thomas Was Alone (Mike Bithell, 2012) — rectangles that act through *feel* + framing

The characters are literally colored rectangles (Mondrian was a stated visual inspiration). Two
liveliness channels, and notably **neither is sprite animation**:

- **Differentiated movement feel as personality.** Each rectangle's *shape, speed, and jump
  height* define its character — a tall floaty one, a small quick one, a heavy slow one. You read
  personality from *how it moves*, before any narration.
- **Narrative framing.** A narrator (Danny Wallace, BAFTA-winning performance) supplies names,
  interiority, and humor. The rectangles never animate a face — the framing does the emotional
  work.

**Take for pycats:** the archetypes' already-differentiated movement parameters (speed, jump,
weight) *are themselves* a liveliness channel — the same lever Thomas Was Alone leans on hardest.
Distinct per-cat feel makes each box read as a distinct creature even before we add any motion
polish. (Framing/narration is out of scope for a fighting game, but the movement-feel point
transfers directly.)

### 2. BoxBoy! (HAL Laboratory, 2015) — a square + eyes + relentless animation variety

Qbby is a black square with two small feet and two eyes. HAL's own account (Siliconera interview
with director Yasuhiro Mukae) is the cleanest statement of the whole survey's thesis:

- **Eyes were added for a functional reason first** — "so you can see which direction he's
  pointed" — and turn out to carry most of the character read.
- **Simple design → invest in animation variety:** *"the secret to how vibrant Qbby looks lies in
  all the variations to his movements. He's got a simple design, so we added a lot of variation to
  his animation to complement that."*
- **Idle + reaction animations do the personality work:** "the things he does when the player
  isn't controlling him," "the way he expresses joy after finishing a stage," a "shocked face when
  he hits a sprite," and a focusing expression when creating blocks.

**Take for pycats:** two cheap, high-leverage ideas — (a) a **minimal face / eyes** that also
communicates facing direction, and (b) **contextual reaction animations** (a hit reaction, a KO
reaction, an idle fidget) rather than one static idle. This is the survey's single best template
for "make a box a character."

### 3. Downwell (Ojiro Fumoto, 2015) — juice on a blocky, 3-color sprite

A tiny blocky protagonist in a high-contrast 3-color palette. Its liveliness is almost entirely
**event feedback / juice**: screen shake on impact, particle bursts (muzzle flash from the
gunboots, debris), brief hit-stop / freeze-frames on kills, and heavy recoil. Fumoto's GDC talk
"Polishing the Boots" documents the one-mechanic-polished-hard philosophy.

**Take for pycats:** impact accents (screen shake, land/hit particles, hit-stop) make a plain
sprite feel like it has weight and consequence — directly applicable to landings and attack
connects.

### 4. Super Meat Boy (Team Meat, 2010) — squash/stretch + trails on a rounded cube

Meat Boy is a small dark-red cube. Its feel is defined by **squash-and-stretch** — "squelching,
sticky jumps" that deform the body to suggest mass and momentum — plus **motion/blood trails**
that leave a visible arc of where it's been, and springy easing on wall-slides and jumps.

**Take for pycats:** squash-on-land / stretch-on-jump-launch is the highest-recognition motion
technique for a box, and a short motion trail on fast movement (dash, launch) reads as speed.

### 5. Geometry Dash (RobTop / Robert Topala, 2013) — rotation as momentum

In cube mode the avatar is a square icon that **rotates continuously as it moves and flips on
each jump**. A spinning square reads as having momentum and life where a static one reads as a
tile. Cheap: it's a single continuous transform.

**Take for pycats:** a subtle tilt/rotation coupled to horizontal velocity (lean into a run,
rotate through an aerial) is a low-cost way to make the box feel like it has inertia. (Full
continuous spin is too much for a fighter, but velocity-coupled lean is the transferable idea.)

### 6. VVVVVV (Terry Cavanagh, 2010) — a blocky sprite whose face carries it

Captain Viridian is a small blocky pixel figure with a permanent smiley face and little legs that
shuffle when walking. Reinforces BoxBoy's lesson from a different studio: **a face on a simple
shape is disproportionately effective**, and a small walk-cycle shuffle sells motion cheaply.

---

## Taxonomy — the design space, grouped

| Channel | What it is | Techniques observed | Seen in |
|---|---|---|---|
| **Idle-motion** | Motion while doing nothing | breathing bob, blink, idle fidget / "un-controlled" animation, gentle sway | BoxBoy (idle animations); pycats #567/#741 (breathing) |
| **Movement-motion** | Deform/orient with motion | squash-&-stretch, lean/tilt into direction, rotation coupled to velocity, differentiated speed/jump *feel*, anticipation & overshoot easing | Super Meat Boy, Geometry Dash, Thomas Was Alone |
| **Impact / event accent** | The world reacts to the character | landing dust, screen shake, hit-stop / freeze-frame, motion trails / afterimages, recoil, reaction faces | Downwell, Super Meat Boy, BoxBoy (reaction faces) |
| **Character accent** | Non-motion identity cue | minimal face / eyes (doubles as facing indicator), differentiated color, narrative framing | BoxBoy, VVVVVV, Thomas Was Alone |

**Foundational grounding** (why these work): the four channels are applications of the classic
**12 principles of animation** (squash-&-stretch, anticipation, follow-through/overlap; Thomas &
Johnston, *The Illusion of Life*) and of **game feel** as documented in Steve Swink's *Game Feel*
(2008) and the widely-circulated **"Juice it or lose it"** talk (Martin Jonasson & Petri Purho,
GDC Europe 2012), which demonstrates layering exactly these accents onto a flat block game to
transform its feel.

---

## Candidate follow-ups (technique → possible future ticket)

Downstream work only — **filed one-at-a-time and only on an explicit go-ahead** (this ticket does
not file them). Ordered roughly by recognition-per-effort:

1. **Idle breathing bob** — *already scoped* as #567 / #741. Listed for completeness; no new
   ticket.
2. **Squash-on-land / stretch-on-launch** — highest-recognition motion technique for a box
   (Super Meat Boy). Render-only, layered over existing FSM states.
3. **Velocity-coupled lean/tilt** — small rotation into run/aerial direction (Geometry Dash's
   idea, dialed down). Cheap continuous transform.
4. **Landing dust / hit particle accent** — impact feedback on land + attack-connect (Downwell).
5. **Minimal eyes / face accent** — doubles as a facing-direction indicator (BoxBoy, VVVVVV). The
   biggest "box → character" lever, but a larger visual-identity decision — likely wants a design
   sign-off, not just a DEV ticket.
6. **Contextual reaction animation** — a distinct hit / KO / victory reaction rather than one
   static pose (BoxBoy).
7. **Hit-stop / freeze-frame + screen shake on heavy hits** — game-feel juice; verify against what
   the combat renderer already does before filing.

A "next depth tier" for #742 itself (deferred here) would map each of these to pycats'
`render_battle.py` / entities FSM — which are cheap given our rect-drawing vs. which need new
state — and estimate them. That mapping is the natural moderate-depth successor if the direction
is worth pursuing.

---

## Sources

- Thomas Was Alone — [Wikipedia](https://en.wikipedia.org/wiki/Thomas_Was_Alone) (Mondrian
  inspiration; shape/speed/jump-height define personality; Danny Wallace narration, BAFTA).
- BoxBoy! — [Siliconera: "The Art Of Making A Square Come Alive"](https://www.siliconera.com/art-making-square-come-alive-behind-scenes-hal-laboratorys-boxboy/)
  (Mukae interview: eyes for facing, animation variety, idle + reaction animations) and
  [Wikipedia](https://en.wikipedia.org/wiki/BoxBoy!_(video_game)).
- Downwell — [Wikipedia](https://en.wikipedia.org/wiki/Downwell_(video_game)) and Ojiro Fumoto's
  GDC talk ["Polishing the Boots — Designing 'Downwell' Around One Key Mechanic"](https://gdcvault.com/play/1023533/Polishing-the-Boots-Designing-Downwell).
- Super Meat Boy (Team Meat, 2010) — squash/stretch feel, motion trails (direct observation +
  general game-feel coverage).
- Geometry Dash — [Wikipedia](https://en.wikipedia.org/wiki/Geometry_Dash) (cube rotates/flips on
  jump; inspired by The Impossible Game / Super Meat Boy / Bit.Trip Runner).
- VVVVVV (Terry Cavanagh, 2010) — face + walk-shuffle on a blocky sprite (direct observation).
- Foundational: ["Juice it or lose it" — Martin Jonasson & Petri Purho, GDC Europe 2012](https://www.youtube.com/watch?v=Fy0aCDmgnxg);
  Steve Swink, *Game Feel* (2008); Thomas & Johnston, *The Illusion of Life* (12 principles of
  animation).

*Note on grounding: per-game technique descriptions are from the cited articles/talks plus direct
observation of each game; the BoxBoy and Thomas Was Alone design-intent claims carry verbatim
quotes from the linked sources. No PM-parity or in-repo values are asserted here — this is
external design inspiration, not a sourced game-tuning number.*
