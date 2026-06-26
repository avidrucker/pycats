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
from pycats.combat.geometry import circles_overlap, resolve_circle


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
    for atk in list(attacks):  # copy to allow safe removal
        if not atk.active:
            continue

        for defender in players:
            # Skip if defender is invulnerable, is dead, or is the owner of the attack
            if (
                defender.fighter.invulnerable or not defender.fighter.is_alive or defender is atk.owner
            ):  # no self-hit
                continue

            # Resolve defender hurtbox circles to absolute coordinates.
            # Origin convention: rect top-left (rect.x, rect.y).
            resolved_hurtbox = [
                resolve_circle(c, defender.rect.x, defender.rect.y,
                               defender.fighter.facing_right, defender.rect.width)
                for c in defender.fighter_data.hurtbox.circles
            ]

            if circles_overlap(atk.hit_cx, atk.hit_cy, atk.hit_r, resolved_hurtbox):
                defender.fighter.receive_hit(atk)
                atk.owner.fighter.record_hit_landed()  # Track successful hit
                if atk.disappear_on_hit:
                    atk.kill()
                else:
                    atk.active = False  # only one hit allowed
                break  # break after first hit to avoid multiple hits in one frame
