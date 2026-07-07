# Design spec — the DDD/hexagonal skin / character / selection model

**Ticket:** #675 (Child 2 of the epic **#672**) · **Role:** ARCHITECT · **Date:** 2026-07-06 (GRAPE)
**Status:** design/spec — **no code**. Formalizes the #673 findings ([`2026-07-06-skin-char-decomplect.md`](./research/2026-07-06-skin-char-decomplect.md)) into an implementable model + a Phase-1/2/3 child breakdown. DP1/DP2 land **proposed — pending sign-off**.

## TL;DR

- New pure package **`pycats/domain/`** holds four value objects — `Skin`, `Character`, `Selection`, `PlayerIdentity` (3 seams) — plus two registries, two resolvers, and one port. It imports **no pygame / sim / UI**.
- **Two independent resolvers** compose in one port: `build_fighter(Selection) -> BuiltFighter(fighter_data, skin)`. Mechanics (`fighter_data_of`) and cosmetics (`palette_of`) never touch each other — skin-cycling stays cost-free on the data side.
- **`char_name` dies**, split into three prefixed seams — `PlayerNumberSlot` (identity/win-attribution), `PlayerTeamColor` (HUD accent), `PlayerName` (label; absorbs `nickname` #478). Each of its ~8 real consumers repoints to exactly one seam.
- **The placeholder becomes a normal non-selectable `(Character, Skin)`** — absent from the two registries — deleting both `if key == "testcat"` special-cases *and* the `_NEUTRAL` fallback.
- **DP1** (placeholder exact gray) and **DP2** (`PlayerSnap` identity field) are surfaced with a recommendation each, pending human sign-off.
- Nine refactor children enumerated across three phases (golden-neutral → golden-flip → cleanup); filed one at a time downstream.

---

## 1. Domain module layout + value-object shapes

**Decision:** a new package **`pycats/domain/`**, not an extension of `characters/` — because `characters/` already reaches into `palettes` / pygame-adjacent code, so a fresh package is the only place the "no pygame / sim / UI import" invariant can be *enforced* (an import-lint test asserts it; see §Verification). Colors are `RGB = tuple[int, int, int]` at the boundary, matching today's palette dicts.

| Module | Contents |
|---|---|
| `domain/skin.py` | `Skin` (frozen dataclass) + `Skin.from_palette_dict(key, d)` / `.to_palette_dict()` migration adapters |
| `domain/character.py` | `Character` (frozen dataclass) |
| `domain/selection.py` | `Selection`, `BuiltFighter` (NamedTuples) |
| `domain/player_identity.py` | `PlayerNumberSlot`, `PlayerTeamColor`, `PlayerName`, `PlayerIdentity` |
| `domain/placeholder.py` | `PLACEHOLDER_CHARACTER`, `PLACEHOLDER_SKIN` |
| `domain/registry.py` | `CHARACTERS: dict[str, Character]`, `SKINS: dict[str, Skin]`, `resolve_selection(char_key, skin_key) -> Selection` |
| `domain/resolvers.py` | `fighter_data_of(Character) -> FighterData`, `palette_of(Skin) -> Skin` |
| `domain/build_fighter.py` | `build_fighter(Selection) -> BuiltFighter` (the port) |

Value-object shapes (mirroring the real palette dict + `FighterData` dataclass found in the grounding):

```python
# domain/skin.py
RGB = tuple[int, int, int]

@dataclass(frozen=True)
class Skin:
    key: str            # "calico", "ghost", … ; the placeholder is "placeholder"
    name: str           # display "Calico"
    color: RGB
    stripe_color: RGB
    eye_color: RGB
    description: str = ""

    @classmethod
    def from_palette_dict(cls, key, d):        # migration bridge from load_palettes()
        return cls(key, d["name"], d["color"], d["stripe_color"], d["eye_color"], d.get("description", ""))

    def to_palette_dict(self):                 # feed adapters that still want the dict
        return {"name": self.name, "color": self.color, "stripe_color": self.stripe_color,
                "eye_color": self.eye_color, "description": self.description}
```

```python
# domain/character.py
@dataclass(frozen=True)
class Character:
    key: str            # the MECHANICS key load_fighter_data knows: "nalio"/"birky"/"narz"/"testcat"
    name: str           # display "Nalio"
    default_skin_key: str   # a Skin.key — the skin worn until a player cycles it (#650)
```

`FighterData` is **not** embedded in `Character` (see Rejected alternatives) — it is resolved lazily by `fighter_data_of`, keeping `Character` a small pure identity value and keeping combat-data import out of the value object.

---

## 2. Resolver + port signatures

**Decision:** two resolvers stay independent; the port composes them and always returns both halves (headless runs simply ignore the skin).

```python
# domain/resolvers.py
def fighter_data_of(character: Character) -> FighterData:
    return load_fighter_data(character.key)     # combat/data.py, un-overloaded — key is explicit now

def palette_of(skin: Skin) -> Skin:
    return skin                                  # near-identity: Skin IS the cosmetic value
```

```python
# domain/selection.py
class Selection(NamedTuple):
    character: Character
    skin: Skin

class BuiltFighter(NamedTuple):
    fighter_data: FighterData
    skin: Skin

# domain/build_fighter.py  (the one seam both sim + live call)
def build_fighter(selection: Selection) -> BuiltFighter:
    return BuiltFighter(fighter_data_of(selection.character), palette_of(selection.skin))
```

`palette_of` is deliberately trivial today — its value is that cosmetics resolution now has **one** name, replacing the two hand-synced paths (`palette_for` live vs `CAT_CHARACTERS` in sim). The Match adapter reads `built.skin.color / .eye_color / .stripe_color` to construct the `Player` sprite (§3), so no consumer indexes a palette dict by string anymore.

`build_fighter` has **no `if` on the key** — the placeholder flows through it like any other Selection (§4).

---

## 3. The `Player` 3-seam representation

Today `Player.__init__(x, y, controls, color, eye_color, char_name, facing_right, fighter_data)` overloads `char_name` as data-key (via `fighter_data or load_fighter_data(char_name)`), label, win-attribution id, and accent selector. Split it into three **prefixed** seams.

**Naming rule (load-bearing):** every seam keeps its `Player…` prefix — `PlayerNumberSlot`, `PlayerTeamColor`, `PlayerName` — never the bare `Name` / `Color` / `Slot`. Bare names would shadow builtins, pygame symbols, or existing domain terms (`Player.char_color`, `Skin.name`). The spec and all downstream code use the prefixed names throughout.

```python
# domain/player_identity.py
class PlayerNumberSlot(int): ...              # 1 or 2 (v1); the stable identity + win-attribution key

class PlayerTeamColor(Enum):
    RED = "red"                               # → P1_UI_COLOR accent
    BLUE = "blue"                             # → P2_UI_COLOR accent
    # v-next: GREEN, YELLOW

class PlayerName(str): ...                    # "P1"/"P2" by default; absorbs today's nickname (#478)

class PlayerIdentity(NamedTuple):
    number: PlayerNumberSlot
    team_color: PlayerTeamColor
    name: PlayerName

    @classmethod
    def for_slot(cls, n):                     # the v1 defaults: color + name derive FROM number
        return cls(PlayerNumberSlot(n),
                   PlayerTeamColor.RED if n == 1 else PlayerTeamColor.BLUE,
                   PlayerName(f"P{n}"))
```

Number is primary; `team_color` and `name` *default from* it but stay independently overridable (a future nickname sets `name` only; a team mode sets `team_color` only). `Player` gains a `PlayerIdentity` and (Phase 1) keeps a transitional `char_name` **property** returning `identity.name`, so nothing breaks before consumers move.

**Consumer repoint map** (from the grounding — each goes to exactly one seam):

| Consumer (file:function) | Uses char_name as… | Repoints to |
|---|---|---|
| `render_battle.slot_accent_color` | accent (`== "P1"`) | **PlayerTeamColor** (→ P1/P2_UI_COLOR) |
| `render_battle.draw_player_name` | label (`nickname or char_name`) | **PlayerName** |
| `render_battle._CatSpec` + body-cache key | label / cache identity | **PlayerName** |
| `stats_print.format_stats_data` | win-attribution (`== "P1"`) | **PlayerNumberSlot** (`== 1`) |
| `stats_print.format_winner_announcement` | label (`f"{char_name} Wins!"`) | **PlayerName** |
| `sim/presenters` HUD lines (×2) | label | **PlayerName** |
| `sim/runner.snapshot` (`PlayerSnap.name`, attack owner tag) | snapshot row-key / win-attribution | **PlayerNumberSlot** → slot string (see DP2) |
| `entities/fighter_input` dev-log breadcrumb (`characters/{char_name.lower()}_cat.py`) | **MECHANICS key** (data-file path!) | **`Selection.character.key`** |

The last row is the smoking gun for the root braid: a dev breadcrumb builds a *source-file path* out of `char_name`, only correct when `char_name` happens to equal the character key. Post-split it reads `character.key` — the seam that actually means "which fighter data."

---

## 4. The placeholder as a normal non-selectable `(Character, Skin)`

**Decision:** define one `PLACEHOLDER_CHARACTER` + one `PLACEHOLDER_SKIN`, **absent** from the `CHARACTERS` / `SKINS` registries. "Doesn't use the regular palette" = **not a member of the selectable registries**, never a render bypass.

```python
# domain/placeholder.py
PLACEHOLDER_CHARACTER = Character(key="testcat", name="Test", default_skin_key="placeholder")
PLACEHOLDER_SKIN      = Skin(key="placeholder", name="Test",
                             color=(128, 128, 128), stripe_color=(96, 96, 96),
                             eye_color=(64, 64, 64), description="unselectable fixture")   # DP1 values
```

`resolve_selection(char_key, skin_key)` (the driving-adapter entry point) does the one lookup:

```python
def resolve_selection(char_key, skin_key=None) -> Selection:
    character = CHARACTERS.get(char_key, PLACEHOLDER_CHARACTER)
    skin_key  = skin_key or character.default_skin_key
    skin      = SKINS.get(skin_key, PLACEHOLDER_SKIN)
    return Selection(character, skin)
```

This single fallthrough **replaces all three** of today's key-special-cases: the `if key == "testcat"` in `load_fighter_data`, the `if key == "testcat"` in `palette_for`, and the `_NEUTRAL` unknown-key branch. `build_fighter(resolve_selection("bogus"))` yields the gray placeholder in **both** halves coherently — `fighter_data_of` → `load_fighter_data("testcat")` → `DEFAULT_FIGHTER_DATA`; `palette_of` → the gray `Skin` — so a typo is *visibly* the placeholder, never silently a real cat (this is exactly the #630/#647 ruling, now expressed with zero special-cases).

`CHARACTERS` is built from `ARCHETYPE_ROSTER` + `ARCHETYPE_NAME` + `ARCHETYPE_DEFAULT_SKIN`; `SKINS` from `load_palettes()`. The placeholder is constructed directly, never inserted into either — so char-select can never land on it.

---

## 5. Phase-1/2/3 refactor children (enumerated — filed one at a time downstream)

**Phase 1 — introduce the domain + rewire through it, golden-NEUTRAL (no regen).**

- **1a — Add `pycats/domain/` (pure), fully unit-tested, unwired.** Ships all §1–§4 types + registries + resolvers + port + placeholder, with unit tests (incl. the no-pygame import-lint). Touches no consumer. *Golden posture: none touched.*
- **1b — Rewire `build_players` + `create_from_selection` through `build_fighter`.** Keep today's exact selections (sim = calico/tabby skins + default-cat data + P1/P2; live = selected archetype+skin + P1/P2), constructing `Player` from `BuiltFighter` + `PlayerIdentity.for_slot(n)`. *Golden posture: byte-identical — existing goldens + `test_battle_screen_render` are the proof; no regen.*
- **1c — Repoint the `char_name` consumers onto the seams** behind the transitional `char_name` property (accent→team_color, win-attribution→number, snapshot→slot). *Golden posture: byte-identical; no regen.*

**Phase 2 — migrate sims to named Selections, golden-FLIPPING (regen, author ≠ reviewer).**

- **2a — Add the `character` field to `PlayerSnap` + `summarize()` (DP2).** Row-key stays the slot; `character` rides alongside. *Golden posture: schema addition — regen once, review the sidecar diff.*
- **2b — Point `default` scenario Selections at real Characters** (Nalio vs Nalio, pinned #557). *Golden posture: flip; regen `default.json`; author ≠ reviewer.*
- **2c — Same for `full_match`**, then **2d — `two_npc`**, one child each. (`combat.json` already uses Nalio/Birky data.) *Golden posture: flip per scenario.*

**Phase 3 — phase out the shim + cleanup.**

- **3a — Rename `CAT_CHARACTERS → SKINS`; drop `ARCHETYPE_PALETTE` + `_NEUTRAL`; remove the transitional `char_name` property.** *Golden posture: neutral (mechanical rename).*
- **3b — Rename the `DEFAULT_FIGHTER_DATA` constant + sweep stale "default cat" narration** (the old #634 scope). *Golden posture: neutral.*

Each child carries its own acceptance; 2b–2d are gated on DP2, and any placeholder-value change is gated on DP1.

---

## Decision points — proposed, pending sign-off

### DP1 — PlaceholderSkin exact values (game-designer)
**Recommendation: keep #636's shipped tri-tone gray** — `color (128,128,128)`, `stripe (96,96,96)`, `eye (64,64,64)`. Rationale: it already ships, is tested, and the achromatic-but-*distinct* eyes/stripes are what make the fixture legible against the dark stage (the #546 outline basis) while still reading as "not a named cat." A single flat uniform gray (all three = `128`) satisfies the "flat pure gray" wording but flattens the stripe/eye separation #636 deliberately added. **This is a cosmetic value → a game-designer call (RULES → Changing values); I propose keep-tri-tone but defer.** The refactor is value-agnostic: `PLACEHOLDER_SKIN` is a single literal, changeable in one line whichever way DP1 rules.

### DP2 — Snapshot identity field (golden-reviewer)
**Recommendation: row-key stays the slot** — `PlayerNumberSlot` → `"P1"`/`"P2"` remains `PlayerSnap.name`, so `summarize()`'s name-keying and any `p[0] == "P2"` row filters are untouched — **and add a separate `character` field** (holding `Character.key`, e.g. `"nalio"`) to `PlayerSnap` immediately after `name`, in Phase 2a. This makes goldens reflect the real fighter without reshaping the row key. Confirm the exact field position + `summarize()` surface with the golden reviewer before 2a regen.

---

## Rejected alternatives

- **Fuse `fighter_data_of` + `palette_of` into one `resolve(Selection)`** — rejected: skin-cycling (#650) changes cosmetics with zero data change; one function re-braids the two concerns the whole epic exists to separate.
- **Embed `FighterData` inside `Character`** — rejected: bloats a pure identity value and drags combat-data import into the domain value; the resolver keeps identity small and data lazy.
- **Keep `char_name` as the snapshot row-key while also naming the character** — rejected: that keeps slot-identity and character-identity on one field; DP2 gives them separate fields.
- **Make the placeholder a render bypass / special-case in `draw`** — rejected: that *is* today's braid; a normal non-selectable `(Character, Skin)` needs zero special-cases.
- **Put the domain types inside `characters/`** — rejected: `characters/` already imports palettes; only a fresh `domain/` lets the no-pygame invariant be import-linted.

---

## The three #673 open questions — answered

1. **PlaceholderSkin exact values** → DP1 (proposed keep-tri-tone, pending game-designer).
2. **Snapshot identity field** → DP2 (proposed slot row-key + new `character` field, pending golden-reviewer).
3. **`Character` naming collision** (`CAT_CHARACTERS` *means skins*) → resolved: the domain identity type is `Character`; the skin registry is `SKINS`; `CAT_CHARACTERS` is renamed to `SKINS` and retired in Phase 3a, so the collision never coexists in-tree.

---

## Verification (for the refactor children, not this doc)

- **Domain purity:** a unit test asserts `import pycats.domain.*` pulls in **no** `pygame` (walk `sys.modules` after a fresh import, or scan the AST) — the enforceable form of "no pygame / sim / UI."
- **Phase 1 (each child):** `SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest -q` fully green with **`git diff tests/golden/` empty** and `test_battle_screen_render` byte-equality green.
- **Phase 2 (per scenario):** regen via `PYCATS_UPDATE_GOLDENS=1 …`, review the `.summary.json` sidecar field-by-field per `tests/golden/REGEN_PROTOCOL.md`, author ≠ reviewer sign-off.
- **Phase 3:** grep shows no `CAT_CHARACTERS` / `ARCHETYPE_PALETTE` / `_NEUTRAL` / transitional-`char_name` references; suite green.

## Refs

Epic **#672**; #673 findings `docs/research/2026-07-06-skin-char-decomplect.md`; #647 audit `docs/research/2026-07-06-default-test-cat-audit.md`. Grounded in: `entities/player.py` (`Player.__init__`, `char_name`, `nickname`), `combat/data.py` (`load_fighter_data`, `FighterData`), `characters/palettes.py` (`load_palettes`), `characters/og_skins.py` (`OG_SKINS`), `config.py` (`CAT_CHARACTERS` re-export), `characters/roster.py` (`palette_for`, `ARCHETYPE_*`, `_NEUTRAL`, `_TESTCAT`), `sim/runner.py` (`build_players`, `snapshot`, `PlayerSnap`), `battle_screen.py` (`create_from_selection`), `char_select.py` (`get_selected_characters`/`get_selected_palettes`), `render_battle.py` (`slot_accent_color`, `draw_player_name`), `stats_print.py`, `sim/presenters`, `tests/golden_util.py` (`summarize`). Prior: #636 (testcat gray), #591 (testcat name), #478 (nickname), #650 (skin cycle), #557 (Nalio pin). Role: ARCHITECT.
