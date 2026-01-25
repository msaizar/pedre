"""Base class for PathfindingManager."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    from collections import deque

    import arcade


class PathfindingBaseManager(BaseSystem, ABC):
    """Base class for PathfindingManager."""

    role = "pathfinding_manager"

    @abstractmethod
    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_tile_x: int,
        end_tile_y: int,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Find a path using A* pathfinding with automatic retry logic."""
        ...
