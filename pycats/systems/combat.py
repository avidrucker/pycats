"""
Collision & hit-resolution system.

Task 5: hit detection uses circle geometry.
  - Each Attack carries an absolute hitbox circle (hit_cx, hit_cy, hit_r),
    resolved from the move's Hitbox.circle at spawn time.
  - Each defender's Hurtbox.circles are resolved to absolute coordinates via
    resolve_circle() using the defender's rect top-left as origin and their
    facing direction.
  - circles_overlap() tests the hitbox circle against all resolved hurtbox
    circles.  All other guards (invulnerable, is_alive, self-hit) are unchanged.
"""

from pycats.combat.geometry import circle_overlap, circles_overlap, resolve_circle
from pycats.config import CLANK_PRIORITY_RANGE


def _attacks_overlap(a, b) -> bool:
    """True if any resolved hitbox circle of attack a overlaps any of attack b.

    Multi-hitbox aware (#130): walks a.resolved / b.resolved; legacy/stub attacks
    without `resolved` fall back to their single (hit_cx, hit_cy, hit_r) circle.
    """
    a_circles = getattr(a, "resolved", None) or [(a.hit_cx, a.hit_cy, a.hit_r, None)]
    b_circles = getattr(b, "resolved", None) or [(b.hit_cx, b.hit_cy, b.hit_r, None)]
    for acx, acy, ar, _ in a_circles:
        for bcx, bcy, br, _ in b_circles:
            if circle_overlap(acx, acy, ar, bcx, bcy, br):
                return True
    return False


def _clank_strength(atk) -> float:
    """The attack's representative damage for the priority comparison — its
    strongest box (#130 multi-hitbox). Falls back to atk.damage for stubs."""
    boxes = getattr(atk, "hitboxes", None)
    if boxes:
        return max(hb.damage for hb in boxes)
    return getattr(atk, "damage", 0.0)


def _negate(atk):
    """End a clanked hitbox for the frame (no rebound state/freeze yet — #38)."""
    if atk.disappear_on_hit:
        atk.kill()
    else:
        atk.active = False


def _resolve_clanks(attacks):
    """#38 4c: opposing-hitbox clank/priority. Run BEFORE attack->defender so a
    clanked hitbox neither connects nor survives the frame.

    Pairs of active, GROUND (non-air — aerials don't clank, SmashWiki) hitboxes
    owned by different fighters that overlap are resolved by the 9% priority
    range (config.CLANK_PRIORITY_RANGE): within range both end; otherwise the
    stronger continues and the weaker ends.
    """
    live = [a for a in attacks if a.active and not getattr(a, "in_air", False)]
    for i, a in enumerate(live):
        if not a.active:
            continue
        for b in live[i + 1 :]:
            if not b.active or b.owner is a.owner:
                continue
            if not _attacks_overlap(a, b):
                continue
            da, db = _clank_strength(a), _clank_strength(b)
            if abs(da - db) <= CLANK_PRIORITY_RANGE:
                _negate(a)
                _negate(b)
            elif da > db:
                _negate(b)
            else:
                _negate(a)
            if not a.active:
                break  # a is gone; move on to the next attacker


def process_hits(players, attacks):
    """
    Detect Attack→Player collisions and apply damage.

    • Attack never hurts its owner.
    • Dead / respawning players are ignored.
    • Hit detection: circle geometry (atk.hit_cx/hit_cy/hit_r vs resolved
      defender hurtbox circles — NOT rect overlap).
    • If attack hits:
        - If disappear_on_hit: kill()
        - Else: deactivate, but keep visible
    """
    # #38 4c: resolve opposing-hitbox clanks first, so a clanked hitbox neither
    # connects this frame nor survives to the attack->defender pass below.
    _resolve_clanks(attacks)

    for atk in list(attacks):  # copy to allow safe removal
        # #213: a looping attack stays active between hits but is dormant while its
        # rehit cooldown drains. Defensive getattr — stub attacks have no timer.
        if not atk.active or getattr(atk, "_rehit_timer", 0) > 0:
            continue

        # #130: an attack may carry MULTIPLE hitbox circles (multi-hitbox move),
        # in priority order. atk.resolved is the priority-ordered list of
        # (cx, cy, r, box); legacy/stub attacks without it fall back to their
        # single (hit_cx, hit_cy, hit_r) circle (box == atk, which carries the
        # same damage/angle/knockback attrs).
        boxes = getattr(atk, "resolved", None)
        if not boxes:
            boxes = [(atk.hit_cx, atk.hit_cy, atk.hit_r, atk)]

        for defender in players:
            # Skip if defender is invulnerable, is dead, or is the owner of the attack
            if defender.fighter.invulnerable or not defender.fighter.is_alive or defender is atk.owner:  # no self-hit
                continue

            # Resolve defender hurtbox circles to absolute coordinates.
            # Origin convention: rect top-left (rect.x, rect.y). A crouching
            # defender uses its lower/shorter crouch hurtbox (#124), so high
            # attacks whiff — relative to the (resized) crouch rect. Read state
            # defensively (#137): process_hits must not assume the full Player
            # surface — a defender without `.state` (the minimal combat contract)
            # is simply treated as not crouching, mirroring the `resolved` getattr
            # fallback above.
            hurtbox = defender.fighter_data.hurtbox
            d_state = getattr(defender, "state", None)
            if d_state == "crouch" and getattr(defender.fighter, "crouch_hurtbox", None) is not None:
                hurtbox = defender.fighter.crouch_hurtbox
            elif d_state == "prone" and getattr(defender.fighter, "prone_hurtbox", None) is not None:
                # Prone lowers the hurtbox further (#173) so high attacks whiff
                # over a downed fighter, exactly as crouch does.
                hurtbox = defender.fighter.prone_hurtbox
            resolved_hurtbox = [
                resolve_circle(c, defender.rect.x, defender.rect.y, defender.fighter.facing_right, defender.rect.width)
                for c in hurtbox.circles
            ]

            # First box (priority order) that overlaps this defender wins — a
            # single move-instance hits a given target at most once.
            hit_box = next(
                (box for (cx, cy, r, box) in boxes if circles_overlap(cx, cy, r, resolved_hurtbox)),
                None,
            )
            if hit_box is not None:
                # Apply the connecting box's params so receive_hit reads the box
                # that actually landed (no-op when box is the attack itself).
                atk.damage = hit_box.damage
                atk.angle = hit_box.angle
                atk.base_knockback = hit_box.base_knockback
                atk.knockback_growth = hit_box.knockback_growth
                atk.set_knockback = getattr(hit_box, "set_knockback", None)  # WDSK (#211)
                # Crouch-cancel (#135/#283): pass the crouch fact in (reusing the
                # d_state already computed for hurtbox selection) so the domain rule
                # doesn't read the adapter's FSM state label.
                defender.fighter.receive_hit(atk, is_crouching=(d_state == "crouch"))
                atk.owner.fighter.record_hit_landed()  # Track successful hit
                if getattr(atk, "rehit_rate", None) is not None:
                    # #213 looping multi-hit: stay active, just go on cooldown so
                    # the same target is re-hit once rehit_rate frames pass.
                    atk._rehit_timer = atk.rehit_rate
                elif atk.disappear_on_hit:
                    atk.kill()
                else:
                    atk.active = False  # only one hit allowed
                break  # break after first hit to avoid multiple hits in one frame
