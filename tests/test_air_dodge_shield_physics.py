#!/usr/bin/env python3
"""Test script to check if air dodging while holding shield causes physics issues."""

import pygame as pg
from pycats.entities.player import Player
from pycats.entities.platform import Platform
from pycats.core.input import InputFrame

# Initialize pygame
pg.init()

# Create test environment
platforms = [
    Platform(pg.Rect(300, 400, 200, 30), True),  # Thin platform
    Platform(pg.Rect(100, 300, 200, 30), False), # Thick platform
]

# Create player in air
controls = {'left': pg.K_a, 'right': pg.K_d, 'up': pg.K_w, 'down': pg.K_s, 'shield': pg.K_q, 'attack': pg.K_e}
player = Player(400, 250, controls, (255, 160, 64), (255, 255, 255), "TestCat")

print("=== Testing Air Dodge + Shield Physics Issue ===")
print(f"Initial: pos={player.rect.center}, on_ground={player.on_ground}, vel={player.vel}")

# Step 1: Let player fall a bit to ensure they're clearly in air
for i in range(3):
    fall_frame = InputFrame(held=set(), pressed=set(), released=set())
    player.update(fall_frame, platforms, pg.sprite.Group())
    
print(f"After falling: pos={player.rect.center}, on_ground={player.on_ground}, vel={player.vel}")

# Step 2: Air dodge while holding shield (the problematic case)
air_dodge_shield_frame = InputFrame(
    held={pg.K_q},  # Shield held
    pressed={pg.K_q},  # Shield just pressed (triggers air dodge)
    released=set()
)

player.update(air_dodge_shield_frame, platforms, pg.sprite.Group())
print(f"After air dodge + shield: state={player.fsm.state}, spot_dodge_flag={player.spot_dodge_shield_held}, vel={player.vel}")

# Step 3: Continue holding shield for several frames to see physics behavior
continue_shield_frame = InputFrame(
    held={pg.K_q},  # Keep holding shield
    pressed=set(),  # No new presses
    released=set()
)

print("\n--- Physics during air dodge + shield ---")
for frame in range(1, 8):
    prev_vel = player.vel.copy()
    player.update(continue_shield_frame, platforms, pg.sprite.Group())
    
    print(f"Frame {frame}: state={player.fsm.state}, pos={player.rect.center}, vel={player.vel}, gravity_change={player.vel.y - prev_vel.y:.1f}")
    
    # Check if gravity is being applied (velocity should increase by ~1 each frame)
    gravity_applied = abs(player.vel.y - prev_vel.y) > 0.5
    
    if not gravity_applied and player.fsm.state == "dodge":
        print(f"  ⚠️  WARNING: Gravity not being applied! This suggests air dodge is using spot dodge physics.")
    elif gravity_applied:
        print(f"  ✅ Gravity applied normally")

print(f"\nFinal result: spot_dodge_flag={player.spot_dodge_shield_held}")

# Step 4: Test comparison - ground spot dodge (should NOT have gravity)
print("\n=== Comparison: Ground Spot Dodge (should not have gravity) ===")
player2 = Player(400, 370, controls, (90, 90, 90), (255, 255, 255), "GroundCat")

# Settle on platform
settle_frame = InputFrame(held=set(), pressed=set(), released=set())
player2.update(settle_frame, platforms, pg.sprite.Group())
print(f"Ground player settled: pos={player2.rect.center}, on_ground={player2.on_ground}")

# Ground spot dodge (shield + down)
ground_spot_frame = InputFrame(
    held={pg.K_q, pg.K_s},  # Shield and down held
    pressed={pg.K_q, pg.K_s},  # Both just pressed
    released=set()
)

player2.update(ground_spot_frame, platforms, pg.sprite.Group())
print(f"After ground spot dodge: state={player2.fsm.state}, spot_dodge_flag={player2.spot_dodge_shield_held}")

for frame in range(1, 4):
    prev_vel2 = player2.vel.copy()
    player2.update(continue_shield_frame, platforms, pg.sprite.Group())
    
    gravity_applied2 = abs(player2.vel.y - prev_vel2.y) > 0.5
    print(f"Ground Frame {frame}: vel={player2.vel}, gravity_applied={gravity_applied2}")

pg.quit()
