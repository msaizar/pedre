"""Base class for InputManager."""

from abc import ABC, abstractmethod

from pedre.systems.base import BaseSystem


class InputBaseManager(BaseSystem, ABC):
    """Base class for InputManager."""

    role = "input_manager"

    @abstractmethod
    def get_movement_vector(self) -> tuple[float, float]:
        """Calculate normalized movement vector from currently pressed keys."""
        ...
