"""Base class for ParticleManager."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pedre.systems.base import BaseSystem


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


class ParticleBaseManager(BaseSystem, ABC):
    """Manages particle effects and visual polish."""

    role = "particle_manager"

    @abstractmethod
    def emit_hearts(
        self,
        x: float,
        y: float,
        count: int = 10,
        *,
        color: tuple[int, int, int] = (255, 105, 180),  # Hot pink
    ) -> None:
        """Emit heart particles for romantic or affectionate moments."""
        ...

    @abstractmethod
    def emit_sparkles(
        self,
        x: float,
        y: float,
        count: int = 15,
        *,
        color: tuple[int, int, int] = (255, 255, 100),  # Yellow
    ) -> None:
        """Emit sparkle particles for interactions and discoveries."""
        ...

    @abstractmethod
    def emit_burst(
        self,
        x: float,
        y: float,
        count: int = 20,
        *,
        color: tuple[int, int, int] = (255, 200, 0),  # Orange
    ) -> None:
        """Emit burst particles for dramatic events and reveals."""
        ...
