"""
Collision & hit-resolution system.
"""


def process_hits(players, attacks):
    """
    Detect Attack→Player collisions and apply damage.

    • Attack never hurts its owner.
    • Dead / respawning players are ignored.
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
                defender.invulnerable or not defender.is_alive or defender is atk.owner
            ):  # no self-hit
                continue

            if atk.rect.colliderect(defender.rect):
                defender.receive_hit(atk)
                atk.owner.record_hit_landed()  # Track successful hit
                if atk.disappear_on_hit:
                    atk.kill()
                else:
                    atk.active = False  # only one hit allowed
                break  # break after first hit to avoid multiple hits in one frame
