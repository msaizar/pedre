"""Base class for PathfindingPlugin."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.plugins.base import BasePlugin

if TYPE_CHECKING:
    from collections import deque

    import arcade


class PathfindingBasePlugin(BasePlugin, ABC):
    """Base class for PathfindingPlugin."""

    role = "pathfinding_plugin"

    @abstractmethod
    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Find a path using A* pathfinding with automatic retry logic."""
        ...
