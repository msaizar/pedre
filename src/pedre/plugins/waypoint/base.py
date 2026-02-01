"""Base class for WaypointManager."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class WaypointBaseManager(BasePlugin, ABC):
    """Base class for WaypointManager."""

    role = "waypoint_manager"

    @abstractmethod
    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        """Get waypoints."""
        ...
