"""Base class for InputPlugin."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class InputBasePlugin(BasePlugin, ABC):
    """Base class for InputPlugin."""

    role = "input_plugin"

    @abstractmethod
    def get_movement_vector(self, delta_time: float) -> tuple[float, float]:
        """Calculate normalized movement vector from currently pressed keys.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        ...
