"""Base class for PathfindingManager."""

from typing import TYPE_CHECKING

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade


class PathfindingBaseManager(BaseSystem):
    """Base class for PathfindingManager."""

    def set_wall_list(self, wall_list: arcade.SpriteList) -> None:
        """Set the wall list for collision detection."""
        return
