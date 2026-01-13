"""Particle effects system for visual polish.

This module provides a lightweight particle system for adding visual feedback and
atmosphere to the game. Particles are small, temporary visual effects that enhance
player interactions, NPC behaviors, and world events.

The particle system consists of:
- Particle: Individual particle data including position, velocity, and visual properties
- ParticleManager: System for creating, updating, and rendering particles

The manager provides several pre-configured particle effects:
- Hearts: Romantic/affection effects that float upward
- Sparkles: Quick bursts for interactions and discoveries
- Trail: Subtle movement trails for the player
- Burst: Dramatic explosions for reveals and events

Particles automatically fade out over their lifetime and are removed when expired.
The system uses simple physics including gravity simulation for realistic movement.

Example usage:
    # Create manager
    particle_manager = ParticleManager()

    # Emit effects
    particle_manager.emit_hearts(player_x, player_y)
    particle_manager.emit_sparkles(chest_x, chest_y, color=(255, 215, 0))

    # Update and render each frame
    particle_manager.update(delta_time)
    particle_manager.draw()

    # Toggle effects on/off
    particle_manager.toggle()
"""

import math
from dataclasses import dataclass
from random import Random

import arcade


@dataclass
class Particle:
    """Individual particle state.

    Represents a single particle with position, motion, and visual properties.
    Particles are short-lived visual effects that move according to their velocity
    and are affected by gravity. They can optionally fade out over their lifetime.

    The particle system updates position each frame based on velocity, applies
    downward gravity acceleration, and automatically removes particles when their
    age exceeds their lifetime.

    Attributes:
        x: Current X position in screen coordinates.
        y: Current Y position in screen coordinates.
        velocity_x: Horizontal velocity in pixels per second.
        velocity_y: Vertical velocity in pixels per second.
        lifetime: Total lifetime in seconds before particle expires.
        age: Current age in seconds (starts at 0.0).
        color: RGBA color tuple (red, green, blue, alpha) with values 0-255.
        size: Particle radius in pixels.
        fade: Whether particle alpha should fade to 0 over lifetime.
    """

    x: float
    y: float
    velocity_x: float
    velocity_y: float
    lifetime: float
    age: float = 0.0
    color: tuple[int, int, int, int] = (255, 255, 255, 255)
    size: float = 4.0
    fade: bool = True


class ParticleManager:
    """Manages particle effects and visual polish.

    The ParticleManager coordinates creation, updating, and rendering of particle effects
    throughout the game. It maintains a list of active particles and provides methods for
    emitting different types of effects.

    The manager handles:
    - Creating particles with randomized properties for natural variation
    - Updating particle positions and ages each frame
    - Applying physics (velocity, gravity) to particles
    - Fading and removing expired particles
    - Rendering all active particles

    Particles can be toggled on/off globally for performance or player preference. When
    disabled, no particles are rendered and no new particles are created.

    Each particle effect type (hearts, sparkles, trail, burst) has pre-tuned parameters
    for velocity ranges, lifetimes, colors, and sizes that create distinct visual effects.

    Integration with actions:
    - EmitParticlesAction can trigger effects from scripts
    - RevealNPCsAction emits gold burst particles when NPCs appear
    - Various game systems emit particles for player feedback

    Attributes:
        particles: List of currently active particles.
        enabled: Whether particle effects are active.
    """

    def __init__(self) -> None:
        """Initialize the particle manager.

        Creates an empty particle list and enables the particle system. The manager
        uses its own random number generator for particle properties to ensure
        consistent behavior independent of other game randomness.
        """
        self.particles: list[Particle] = []
        self.enabled = True
        self._rng = Random()  # noqa: S311 - Non-cryptographic RNG for particle effects

    def emit_hearts(
        self,
        x: float,
        y: float,
        count: int = 10,
        *,
        color: tuple[int, int, int] = (255, 105, 180),  # Hot pink
    ) -> None:
        """Emit heart particles for romantic or affectionate moments.

        Creates particles that float upward with slight outward spread, typically used
        during romantic dialogues or when NPCs show affection. The particles are larger
        than other types and use a gentle upward trajectory.

        Each particle is given random position offsets, velocities, and lifetimes to
        create natural variation. The particles fade out as they age and are affected
        by gravity.

        Common uses:
        - Romantic NPC dialogues
        - Player interactions with loved NPCs
        - Triggered by EmitParticlesAction with particle_type="hearts"

        Args:
            x: X position to emit from (world coordinates).
            y: Y position to emit from (world coordinates).
            count: Number of particles to emit (default 10).
            color: RGB color tuple (default hot pink 255, 105, 180).
        """
        if not self.enabled:
            return

        for _ in range(count):
            # Random upward and outward velocity
            angle = self._rng.uniform(-30, 30)  # Mostly upward with some spread
            speed = self._rng.uniform(30, 60)

            velocity_x = math.sin(math.radians(angle)) * speed
            velocity_y = math.cos(math.radians(angle)) * speed

            particle = Particle(
                x=x + self._rng.uniform(-10, 10),
                y=y + self._rng.uniform(-10, 10),
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                lifetime=self._rng.uniform(1.0, 2.0),
                color=(color[0], color[1], color[2], 255),
                size=self._rng.uniform(6.0, 10.0),
                fade=True,
            )
            self.particles.append(particle)

    def emit_sparkles(
        self,
        x: float,
        y: float,
        count: int = 15,
        *,
        color: tuple[int, int, int] = (255, 255, 100),  # Yellow
    ) -> None:
        """Emit sparkle particles for interactions and discoveries.

        Creates small, fast-moving particles that burst outward in all directions,
        typically used when the player interacts with objects or discovers items.
        The particles have shorter lifetimes than hearts and move more dynamically.

        The outward burst pattern creates a satisfying "pop" effect that provides
        immediate visual feedback for player actions.

        Common uses:
        - Object interactions (chests, doors, switches)
        - Item pickups and discoveries
        - General interaction feedback
        - Triggered by EmitParticlesAction with particle_type="sparkles"

        Args:
            x: X position to emit from (world coordinates).
            y: Y position to emit from (world coordinates).
            count: Number of particles to emit (default 15).
            color: RGB color tuple (default yellow 255, 255, 100).
        """
        if not self.enabled:
            return

        for _ in range(count):
            # Random outward velocity in all directions
            angle = self._rng.uniform(0, 360)
            speed = self._rng.uniform(40, 80)

            velocity_x = math.cos(math.radians(angle)) * speed
            velocity_y = math.sin(math.radians(angle)) * speed

            particle = Particle(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                lifetime=self._rng.uniform(0.5, 1.0),
                color=(color[0], color[1], color[2], 255),
                size=self._rng.uniform(2.0, 4.0),
                fade=True,
            )
            self.particles.append(particle)

    def emit_trail(
        self,
        x: float,
        y: float,
        count: int = 3,
        *,
        color: tuple[int, int, int] = (200, 200, 255),  # Light blue
    ) -> None:
        """Emit subtle trail particles for player movement.

        Creates small, semi-transparent particles with low velocities and short lifetimes,
        designed to leave a subtle visual trail behind the player as they move. The effect
        is intentionally understated to add visual interest without being distracting.

        Trail particles start semi-transparent and fade quickly. They're emitted with
        small random offsets and low velocities, creating a gentle dissipating effect.

        This effect is typically called continuously during player movement, with only
        a few particles emitted per call to keep the performance impact minimal.

        Common uses:
        - Player movement feedback
        - Continuous visual trail effect
        - Subtle motion indication

        Args:
            x: X position to emit from (world coordinates, typically player position).
            y: Y position to emit from (world coordinates, typically player position).
            count: Number of particles to emit per call (default 3, kept low for continuous use).
            color: RGB color tuple (default light blue 200, 200, 255).
        """
        if not self.enabled:
            return

        for _ in range(count):
            particle = Particle(
                x=x + self._rng.uniform(-5, 5),
                y=y + self._rng.uniform(-5, 5),
                velocity_x=self._rng.uniform(-10, 10),
                velocity_y=self._rng.uniform(-10, 10),
                lifetime=self._rng.uniform(0.3, 0.6),
                color=(color[0], color[1], color[2], 128),  # Start semi-transparent
                size=self._rng.uniform(2.0, 3.0),
                fade=True,
            )
            self.particles.append(particle)

    def emit_burst(
        self,
        x: float,
        y: float,
        count: int = 20,
        *,
        color: tuple[int, int, int] = (255, 200, 0),  # Orange
    ) -> None:
        """Emit burst particles for dramatic events and reveals.

        Creates a large number of particles that explode outward at high speeds,
        designed for dramatic moments like NPC reveals, quest completions, or
        significant game events. The particles are larger and faster than sparkles,
        creating a more pronounced explosion effect.

        The high-speed radial burst creates maximum visual impact. Particles are
        larger and live longer than sparkles, making the effect more prominent.

        Common uses:
        - NPC reveals (RevealNPCsAction uses gold burst)
        - Quest completion moments
        - Major event triggers
        - Dramatic reveals and discoveries
        - Triggered by EmitParticlesAction with particle_type="burst"

        Args:
            x: X position to emit from (world coordinates).
            y: Y position to emit from (world coordinates).
            count: Number of particles to emit (default 20 for dramatic effect).
            color: RGB color tuple (default orange 255, 200, 0).
        """
        if not self.enabled:
            return

        for _ in range(count):
            # Strong outward burst
            angle = self._rng.uniform(0, 360)
            speed = self._rng.uniform(80, 150)

            velocity_x = math.cos(math.radians(angle)) * speed
            velocity_y = math.sin(math.radians(angle)) * speed

            particle = Particle(
                x=x,
                y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                lifetime=self._rng.uniform(0.8, 1.5),
                color=(color[0], color[1], color[2], 255),
                size=self._rng.uniform(4.0, 8.0),
                fade=True,
            )
            self.particles.append(particle)

    def update(self, delta_time: float) -> None:
        """Update all active particles.

        Updates particle ages, positions, and velocities for the current frame. This
        method should be called once per frame, typically in the game view's update loop.

        The update process:
        1. Ages all particles by delta_time
        2. Removes particles that have exceeded their lifetime
        3. Updates positions based on current velocities
        4. Applies downward gravity acceleration to all particles

        Gravity simulation (50 pixels/second² downward) makes particles follow realistic
        arcs rather than straight-line motion, adding visual polish to all effects.

        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        # Update particle positions and age
        for particle in self.particles[:]:  # Copy list to allow removal during iteration
            particle.age += delta_time

            # Remove dead particles
            if particle.age >= particle.lifetime:
                self.particles.remove(particle)
                continue

            # Update position
            particle.x += particle.velocity_x * delta_time
            particle.y += particle.velocity_y * delta_time

            # Apply gravity (slight downward acceleration for realism)
            particle.velocity_y -= 50 * delta_time

    def draw(self) -> None:
        """Draw all active particles.

        Renders each particle as a filled circle with appropriate color and alpha.
        This method should be called once per frame during the game view's draw loop,
        typically after drawing the game world but before UI elements.

        Particles with fade=True have their alpha calculated based on remaining lifetime,
        creating a smooth fade-out effect as they age. The final alpha is computed by
        multiplying the particle's base alpha by its remaining life ratio.

        When the particle system is disabled, this method returns immediately without
        rendering anything.
        """
        if not self.enabled:
            return

        for particle in self.particles:
            # Calculate alpha based on lifetime if fading
            if particle.fade:
                life_ratio = 1.0 - (particle.age / particle.lifetime)
                alpha = int(particle.color[3] * life_ratio)
            else:
                alpha = particle.color[3]

            # Draw particle as a circle
            color_with_alpha = (particle.color[0], particle.color[1], particle.color[2], alpha)

            arcade.draw_circle_filled(
                particle.x,
                particle.y,
                particle.size,
                color_with_alpha,
            )

    def clear(self) -> None:
        """Clear all active particles.

        Immediately removes all particles from the system. This is useful for:
        - Scene transitions where particles should not carry over
        - Resetting visual state
        - Cleanup when disabling the particle system

        Called automatically by toggle() when disabling particle effects.
        """
        self.particles.clear()

    def toggle(self) -> bool:
        """Toggle particle effects on/off.

        Switches the particle system between enabled and disabled states. When
        disabling, all active particles are immediately cleared to prevent them
        from lingering on screen.

        When disabled:
        - No new particles are created (emit methods return immediately)
        - No particles are rendered (draw returns immediately)
        - All existing particles are cleared

        When enabled:
        - Normal particle creation and rendering resumes

        This is useful for:
        - Performance optimization on slower systems
        - Player preference settings
        - Debugging without visual clutter

        Returns:
            New enabled state (True if now enabled, False if now disabled).
        """
        self.enabled = not self.enabled
        if not self.enabled:
            self.clear()
        return self.enabled

    def get_particle_count(self) -> int:
        """Get the current number of active particles.

        Returns the count of particles currently being updated and rendered.
        This is useful for:
        - Performance monitoring and debugging
        - Visual effect intensity tracking
        - Diagnostic information display

        Returns:
            Number of active particles currently in the system.
        """
        return len(self.particles)
