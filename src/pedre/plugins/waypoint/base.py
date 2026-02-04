"""Base class for WaypointPlugin."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class WaypointBasePlugin(BasePlugin, ABC):
    """Base class for WaypointPlugin."""

    role = "waypoint_plugin"

    @abstractmethod
    def get_waypoints(self) -> dict[str, tuple[float, float]]:
        """Get waypoints as a dictionary mapping names to (pixel_x, pixel_y) coordinates."""
        ...
