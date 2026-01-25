"""Base class for InputManager."""

from pedre.systems.base import BaseSystem


class InputBaseManager(BaseSystem):
    """Base class for InputManager."""

    def get_movement_vector(self) -> tuple[float, float]:
        """Calculate normalized movement vector from currently pressed keys."""
        return (0, 0)
