"""Idle `wait` MoveData on every authored cat (#1105, Decision A #1104).

Idle is a first-class `MoveData` so it flows through the standard move pipeline (the editor
move cycle / timeline / scrubber / reference-GIF layer, and eventual game render) exactly
like every attack — no bespoke idle mechanism. The `wait` move carries **no hitboxes**
(idle has no active window; the posture-shared stand hurtbox already covers it, #1082), and
its frame length is the PM `Wait1` idle-subaction LOOP length, datamined per source via
brawllib_rs (env #614, same pipeline as #753's Mario 51):

    nalio -> Mario Wait1 = 51    birky -> Kirby Wait1 = 111
    narz  -> Marth Wait1 = 71    gnok  -> DK    Wait1 = 141   (all FOUND, not guessed)

Able-to-fail: drop the `wait` move from any authored cat, give it a hitbox, or set a wrong
loop length, and the matching parametrized case goes red.
"""

import pytest

from pycats.characters.roster import ARCHETYPE_ROSTER
from pycats.combat.data import load_fighter_data

# PM `Wait1` idle-loop frame lengths, brawllib_rs datamine (FOUND): nalio->Mario,
# birky->Kirby, narz->Marth, gnok->DK. Keep in sync with each cat's `characters/data/<cat>.json`.
# (#1137: birky/narz values + labels were transposed at #1105 — Kirby=111, Marth=71.)
_WAIT1_LOOP = {"nalio": 51, "birky": 111, "narz": 71, "gnok": 141}


@pytest.mark.parametrize("cat", ARCHETYPE_ROSTER)
def test_authored_cat_has_wait_idle_move(cat):
    moves = load_fighter_data(cat).moves
    assert "wait" in moves, f"{cat} is missing the idle `wait` MoveData (#1105)"
    wait = moves["wait"]
    # No active hitbox window — idle is a rest loop; the stand hurtbox covers it (#1082).
    assert wait.hitboxes == (), f"{cat} idle `wait` must carry no hitboxes"
    assert wait.hurtbox is None, f"{cat} idle `wait` must use the posture stand hurtbox"
    # Frame length is the datamined Wait1 loop (modeled as recovery; startup=active=0).
    total = wait.startup + wait.active + wait.recovery
    assert total == _WAIT1_LOOP[cat], f"{cat} idle `wait` loop length {total} != datamined Wait1 {_WAIT1_LOOP[cat]}"


def test_wait_covers_every_authored_cat():
    # A future authored cat added to ARCHETYPE_ROSTER without a `wait` move fails here.
    assert set(ARCHETYPE_ROSTER) == set(_WAIT1_LOOP)
