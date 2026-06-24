# pycats/entities/tail.py

import math
from typing import List, Tuple
import pygame as pg  # type: ignore
from ..config import (
    FPS,
    TAIL_SEGMENTS,
    TAIL_SEGMENT_LENGTH,
    TAIL_SEGMENT_WIDTH,
    TAIL_BASE_OFFSET_X,
    TAIL_BASE_OFFSET_Y,
    TAIL_ANCHOR_FLIP_STEP,
    TAIL_WAVE_AMPLITUDE,
    TAIL_WAVE_FREQUENCY,
    TAIL_FOLLOW_STRENGTH,
    TAIL_DAMPING,
    TAIL_UPDATE_FREQUENCY,
    TAIL_SHAPE_UPDATE_HZ,
    TAIL_MIN_MOVEMENT_THRESHOLD,
    TAIL_DRAG_STRENGTH,
    TAIL_GRAVITY_EFFECT,
    TAIL_GRAVITY_DROOP,
    TAIL_MOMENTUM_DECAY,
    TAIL_MAX_BEND_ANGLE,
    TAIL_VELOCITY_SENSITIVITY,
    TAPER_MODIFER,
)


class TailSegment:
    """A single segment of the tail with position and angle."""

    def __init__(self, x: float, y: float, angle: float = 0):
        self.x = x
        self.y = y
        self.angle = angle  # In radians
        self.target_angle = angle
        self.velocity_x = 0
        self.velocity_y = 0

    def update_with_drag(
        self,
        target_x,
        target_y,
        player_vel,
        follow_strength,
        damping,
        is_base_segment=False,
    ):
        # Calculate basic following behavior
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > TAIL_MIN_MOVEMENT_THRESHOLD:
            # Calculate base target angle
            base_angle = math.atan2(dy, dx)

            # Add velocity-based drag effect
            if not is_base_segment:
                # Drag effect: tail lags behind movement direction
                velocity_magnitude = math.sqrt(player_vel.x**2 + player_vel.y**2)
                if velocity_magnitude > 0.5:  # Only apply drag if moving significantly
                    # Velocity angle (direction of movement)
                    vel_angle = math.atan2(player_vel.y, player_vel.x)

                    # Tail should lag opposite to movement direction
                    drag_angle = vel_angle + math.pi  # Opposite direction

                    # Mix base angle with drag angle based on velocity
                    drag_influence = min(
                        velocity_magnitude * TAIL_VELOCITY_SENSITIVITY, 1.0
                    )
                    drag_influence *= TAIL_DRAG_STRENGTH

                    # Interpolate between base angle and drag angle
                    self.target_angle = self.lerp_angle(
                        base_angle, drag_angle, drag_influence
                    )

                    # Add gravity effect when falling
                    if player_vel.y > 2:  # Falling
                        gravity_angle = math.pi / 2  # Downward
                        gravity_influence = min(
                            player_vel.y * 0.05, TAIL_GRAVITY_EFFECT
                        )
                        self.target_angle = self.lerp_angle(
                            self.target_angle, gravity_angle, gravity_influence
                        )
                else:
                    self.target_angle = base_angle
            else:
                self.target_angle = base_angle

            # Limit extreme bending
            angle_diff = self.target_angle - self.angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # Clamp the angle difference to prevent extreme bends
            max_change = TAIL_MAX_BEND_ANGLE * follow_strength
            angle_diff = max(-max_change, min(max_change, angle_diff))

            # Smooth angle transition
            self.angle += angle_diff * follow_strength

        # Apply momentum-based position updates
        target_vel_x = (target_x - self.x) * follow_strength
        target_vel_y = (target_y - self.y) * follow_strength

        # Apply drag to velocity
        self.velocity_x = self.velocity_x * TAIL_MOMENTUM_DECAY + target_vel_x * (
            1 - TAIL_MOMENTUM_DECAY
        )
        self.velocity_y = self.velocity_y * TAIL_MOMENTUM_DECAY + target_vel_y * (
            1 - TAIL_MOMENTUM_DECAY
        )

        # Update position based on velocity
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Maintain proper distance from target
        actual_distance = math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2)
        if actual_distance > TAIL_SEGMENT_LENGTH * 1.5:  # Too far, snap closer
            direction_x = (target_x - self.x) / actual_distance
            direction_y = (target_y - self.y) / actual_distance
            self.x = target_x - direction_x * TAIL_SEGMENT_LENGTH
            self.y = target_y - direction_y * TAIL_SEGMENT_LENGTH

    def lerp_angle(self, angle1, angle2, t):
        """Linear interpolation between two angles, handling wraparound"""
        diff = angle2 - angle1
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return angle1 + diff * t

    def update_position(self, parent_x: float, parent_y: float, length: float):
        """Update position based on parent segment and current angle."""
        self.x = parent_x + math.cos(self.angle) * length
        self.y = parent_y + math.sin(self.angle) * length


class Tail:
    """Multi-segment tail with inverse kinematics and wave motion."""

    def __init__(self, player_ref):
        self.player = player_ref
        self.segments: List[TailSegment] = []
        self.time = 0.0  # For wave animation
        self.frame_counter = 0

        # Shape (physics) is recomputed at TAIL_SHAPE_UPDATE_HZ; between those
        # frames the whole tail is translated to follow the player every frame.
        self._shape_interval = max(1, round(FPS / TAIL_SHAPE_UPDATE_HZ))
        self._last_base: Tuple[float, float] | None = None
        # Eased horizontal anchor offset (#3): tracks the facing-based target
        # offset but moves at most TAIL_ANCHOR_FLIP_STEP px/frame, so a facing
        # flip slides the tail base to the other hip instead of teleporting
        # 2*TAIL_BASE_OFFSET_X in a single frame (which the cheap-follow path
        # would otherwise propagate to the whole tail as a snap).
        self._anchor_offset_x = (
            -TAIL_BASE_OFFSET_X if self.player.facing_right else TAIL_BASE_OFFSET_X
        )
        # Cache of rotated segment surfaces, keyed by (width, angle_degrees).
        # char_color is constant per player, so colour is not part of the key.
        self._seg_cache: dict = {}

        # Initialize segments
        for i in range(TAIL_SEGMENTS):
            # Start with segments pointing horizontally backward
            angle = math.pi if self.player.facing_right else 0
            segment = TailSegment(0, 0, angle)
            self.segments.append(segment)

    def update(self, dt: float = 1.0):
        """Update tail physics and animation.

        The expensive inverse-kinematics/wave recompute runs only every
        ``_shape_interval`` frames (TAIL_SHAPE_UPDATE_HZ times per second). On
        the in-between frames the tail still tracks the player: every segment is
        translated by the player's base-point movement, so it stays attached at
        the full frame rate without rerunning any physics.
        """
        self.time += dt * 0.5  # Slower time progression for gentler animation
        self.frame_counter += 1

        # Get player base position for tail attachment
        base_x, base_y = self._get_tail_base_position()

        if self._last_base is None or self.frame_counter % self._shape_interval == 0:
            # Full shape recompute (root + IK + apply), at TAIL_SHAPE_UPDATE_HZ.
            self._update_root_segment(base_x, base_y)
            for i in range(1, len(self.segments)):
                self._update_segment(i)
            self._apply_positions(base_x, base_y)
        else:
            # Cheap follow: rigidly translate the frozen shape with the player.
            dx = base_x - self._last_base[0]
            dy = base_y - self._last_base[1]
            if dx or dy:
                for seg in self.segments:
                    seg.x += dx
                    seg.y += dy

        # Issue #4: keep the (now gravity-drooping) tail out of solid platforms.
        # Runs on both paths and is cheap (segments x platforms).
        self._resolve_platform_collisions()

        self._last_base = (base_x, base_y)

    def _get_tail_base_position(self) -> Tuple[float, float]:
        """Get the attachment point of the tail on the player.

        Issue #3: the target offset flips sign with facing, but we ease the
        actual anchor toward it at TAIL_ANCHOR_FLIP_STEP px/frame so a turn does
        not teleport the base (and, via the cheap-follow path, the whole tail)
        2*TAIL_BASE_OFFSET_X px in one frame.
        """
        target_offset = (
            TAIL_BASE_OFFSET_X if not self.player.facing_right else -TAIL_BASE_OFFSET_X
        )
        delta = target_offset - self._anchor_offset_x
        if delta > TAIL_ANCHOR_FLIP_STEP:
            delta = TAIL_ANCHOR_FLIP_STEP
        elif delta < -TAIL_ANCHOR_FLIP_STEP:
            delta = -TAIL_ANCHOR_FLIP_STEP
        self._anchor_offset_x += delta
        base_x = self.player.rect.centerx + self._anchor_offset_x
        base_y = self.player.rect.bottom - TAIL_BASE_OFFSET_Y
        return base_x, base_y

    def _update_root_segment(self, base_x: float, base_y: float):
        """Update the first segment to respond to player movement and idle animation."""
        root = self.segments[0]

        # Base angle depends on facing direction
        base_angle = math.pi if self.player.facing_right else 0

        # Add movement influence with much more gradual response
        movement_influence = 0
        if hasattr(self.player, "vel"):
            # Very gentle tail response to movement
            velocity_magnitude = math.sqrt(
                self.player.vel.x**2 + self.player.vel.y**2
            )

            if velocity_magnitude > 0.1:  # Only respond to significant movement
                # Tail drags behind movement direction with heavy damping
                movement_angle = math.atan2(self.player.vel.y, self.player.vel.x)
                drag_angle = movement_angle + math.pi  # Opposite to movement

                # Very gentle influence based on velocity
                influence_strength = min(
                    velocity_magnitude * TAIL_VELOCITY_SENSITIVITY, 0.3
                )
                movement_influence = math.sin(drag_angle) * influence_strength * 0.5

        # Add state-specific behaviors with much gentler effects
        state_influence = 0
        if self.player.state == "jump":
            # Very subtle upward curve during jump
            state_influence = -0.1 if self.player.facing_right else 0.1
        elif self.player.state == "fall":
            # Gentle trailing during fall with gravity effect
            gravity_pull = 0.15
            horizontal_drag = 0.1 if self.player.facing_right else -0.1
            state_influence = gravity_pull + horizontal_drag
        elif self.player.state == "dodge":
            # More pronounced movement during dodge but still controlled
            movement_influence *= 1.5

        # Enhanced idle wave motion for more lifelike movement
        wave_offset = 0
        if self.player.state == "idle" or (
            self.player.on_ground and abs(self.player.vel.x) < 0.5
        ):
            # Multiple wave components for more natural motion
            primary_wave = (
                math.sin(self.time * TAIL_WAVE_FREQUENCY) * TAIL_WAVE_AMPLITUDE
            )
            secondary_wave = (
                math.sin(self.time * TAIL_WAVE_FREQUENCY * 0.7 + 1.2)
                * TAIL_WAVE_AMPLITUDE
                * 0.3
            )
            wave_offset = primary_wave + secondary_wave

        # Combine influences with much gentler blending
        target_adjustment = movement_influence + state_influence + wave_offset
        root.target_angle = (
            base_angle + target_adjustment * 0.5
        )  # Further dampen the effect

        # Much slower, smoother angle transition
        angle_diff = root.target_angle - root.angle
        # Normalize angle difference to [-pi, pi]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Very conservative responsiveness
        responsiveness = TAIL_FOLLOW_STRENGTH * 0.6  # Even slower than config value

        # Use a simple angle velocity for the root segment
        if not hasattr(root, "angle_velocity"):
            root.angle_velocity = 0.0

        # Apply very gentle acceleration
        root.angle_velocity += angle_diff * responsiveness
        root.angle_velocity *= TAIL_DAMPING

        # Clamp velocity to prevent sudden movements
        max_velocity = 0.05  # Very small maximum velocity
        root.angle_velocity = max(-max_velocity, min(max_velocity, root.angle_velocity))

        root.angle += root.angle_velocity

    def _update_segment(self, index: int):
        """Update a tail segment using inverse kinematics with fluid motion."""
        current = self.segments[index]
        parent = self.segments[index - 1]

        # Calculate desired position based on parent
        desired_x = parent.x + math.cos(parent.angle) * TAIL_SEGMENT_LENGTH
        desired_y = parent.y + math.sin(parent.angle) * TAIL_SEGMENT_LENGTH

        # Calculate angle to point toward desired position
        dx = desired_x - current.x
        dy = desired_y - current.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > TAIL_MIN_MOVEMENT_THRESHOLD:
            current.target_angle = math.atan2(dy, dx)

        # Issue #4: gravity droop. Pull this segment's target angle toward
        # straight down (+y is down in screen space), progressively stronger
        # toward the tip, so the tail hangs and settles under gravity instead of
        # sticking straight out / curling up. The angle_velocity smoothing below
        # makes this ease in gradually (natural settling).
        gravity_angle = math.pi / 2
        gravity_influence = TAIL_GRAVITY_DROOP * (index / len(self.segments))
        current.target_angle = current.lerp_angle(
            current.target_angle, gravity_angle, gravity_influence
        )

        # Add progressive lag - segments further down move more slowly
        lag_factor = 1.0 - (index / len(self.segments)) * 0.5  # Progressively more lag
        follow_strength = (
            TAIL_FOLLOW_STRENGTH * lag_factor * 0.5
        )  # Much slower following

        # Add some wave propagation down the tail with much gentler effect
        wave_propagation = (
            math.sin(self.time * TAIL_WAVE_FREQUENCY + index * 0.3)
            * TAIL_WAVE_AMPLITUDE
            * 0.1
        )

        # Calculate angle difference with smooth following
        angle_diff = current.target_angle - current.angle
        # Normalize angle difference
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Use angle velocity for each segment with progressive damping
        if not hasattr(current, "angle_velocity"):
            current.angle_velocity = 0.0

        # Progressive damping - segments further down are more damped
        segment_damping = TAIL_DAMPING + (index / len(self.segments)) * 0.05
        segment_damping = min(segment_damping, 0.98)  # Cap at very high damping

        # Very gentle acceleration with wave influence
        acceleration = (angle_diff * follow_strength) + (wave_propagation * 0.01)
        current.angle_velocity += acceleration
        current.angle_velocity *= segment_damping

        # Clamp velocity to prevent sudden movements
        max_velocity = 0.03 * lag_factor  # Progressively smaller max velocity
        current.angle_velocity = max(
            -max_velocity, min(max_velocity, current.angle_velocity)
        )

        current.angle += current.angle_velocity

    def _apply_positions(self, base_x: float, base_y: float):
        """Apply final positions to all segments based on their angles."""
        # First segment starts at base
        if self.segments:
            self.segments[0].x = base_x
            self.segments[0].y = base_y

        # Each subsequent segment follows the previous
        for i in range(1, len(self.segments)):
            parent = self.segments[i - 1]
            current = self.segments[i]
            current.update_position(parent.x, parent.y, TAIL_SEGMENT_LENGTH)

    def _resolve_platform_collisions(self):
        """Issue #4: push tail segments out of SOLID (thick) platforms.

        The tail now droops under gravity, so it would otherwise sink through the
        ground it rests on. Thin platforms are pass-through (like the player), so
        only thick platforms collide. Each penetrating segment is pushed to the
        nearest platform edge (shallowest-penetration axis) — for a tail drooping
        onto a floor that is the top surface, so the tail rests on the platform.
        """
        platforms = getattr(self.player, "platforms", None)
        if not platforms:
            return
        for plat in platforms:
            if getattr(plat, "thin", False):
                continue  # tail passes through thin platforms
            r = plat.rect
            left, right, top, bottom = r.left, r.right, r.top, r.bottom
            for seg in self.segments:
                if left <= seg.x <= right and top <= seg.y <= bottom:
                    # inside the solid rect — exit along the shallowest axis
                    d_top = seg.y - top
                    d_bottom = bottom - seg.y
                    d_left = seg.x - left
                    d_right = right - seg.x
                    m = min(d_top, d_bottom, d_left, d_right)
                    if m == d_top:
                        seg.y = top
                    elif m == d_bottom:
                        seg.y = bottom
                    elif m == d_left:
                        seg.x = left
                    else:
                        seg.x = right

    def draw(self, screen):
        """Draw the tail segments as rectangles.

        Rotated segment surfaces are cached by (width, integer angle°). Only a
        handful of distinct widths exist (the taper is small), so after warm-up
        this is almost entirely cache hits + blits, avoiding a per-segment
        Surface allocation and transform.rotate every frame.
        """
        cache = self._seg_cache
        color = self.player.char_color
        length = TAIL_SEGMENT_LENGTH
        n = len(self.segments)
        blit = screen.blit
        for i, segment in enumerate(self.segments):
            # Taper the width towards the tip
            width = int(TAIL_SEGMENT_WIDTH * (1.0 - (i / n) * TAPER_MODIFER))
            deg = int(round(-math.degrees(segment.angle))) % 360
            key = (width, deg)
            surf = cache.get(key)
            if surf is None:
                base = pg.Surface((length, width), pg.SRCALPHA)
                base.fill(color)
                surf = pg.transform.rotate(base, deg)
                cache[key] = surf
            rect = surf.get_rect()
            rect.center = (int(segment.x), int(segment.y))
            blit(surf, rect)
