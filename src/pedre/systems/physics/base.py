"""Base class for PhysicsManager."""

from abc import ABC, abstractmethod

from pedre.systems.base import BaseSystem


class PhysicsBaseManager(BaseSystem, ABC):
    """Base class for PhysicsManager."""

    role = "physics_manager"

    @abstractmethod
    def invalidate(self) -> None:
        """Mark physics engine for recreation on next update."""
        return
