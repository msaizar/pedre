"""Base class for PhysicsManager."""

from pedre.systems.base import BaseSystem


class PhysicsBaseManager(BaseSystem):
    """Base class for PhysicsManager."""

    def invalidate(self) -> None:
        """Mark physics engine for recreation on next update."""
        return
