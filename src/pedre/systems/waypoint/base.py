"""Base class for WaypointManager."""

from abc import ABC, abstractmethod

from pedre.systems.base import BaseSystem


class WaypointBaseManager(BaseSystem, ABC):
    """Base class for WaypointManager."""

    role = "waypoint_manager"

    @abstractmethod
    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        """Get waypoints."""
        ...
