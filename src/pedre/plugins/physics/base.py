"""Base class for PhysicsPlugin."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class PhysicsBasePlugin(BasePlugin, ABC):
    """Base class for PhysicsPlugin."""

    role = "physics_plugin"

    @abstractmethod
    def invalidate(self) -> None:
        """Mark physics engine for recreation on next update."""
        return
