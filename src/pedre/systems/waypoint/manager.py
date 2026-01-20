"""Waypoint management system."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    import arcade

    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class WaypointManager(BaseSystem):
    """Manages waypoints loaded from Tiled maps.

    Waypoints are named positions in the map used for:
    - Player spawn points
    - NPC spawn points
    - Script-triggered teleportation
    """

    name: ClassVar[str] = "waypoint"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize waypoint manager."""
        self.waypoints: dict[str, tuple[float, float]] = {}

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize waypoint manager."""

    def load_from_tiled(
        self,
        tile_map: arcade.TileMap,
        arcade_scene: arcade.Scene,
        context: GameContext,
        settings: GameSettings,
    ) -> None:
        """Load waypoints from Tiled map object layer."""
        self.waypoints = {}

        waypoint_layer = tile_map.object_lists.get("Waypoints")
        if not waypoint_layer:
            logger.debug("No Waypoints layer found in map")
            return

        for waypoint in waypoint_layer:
            if waypoint.name:
                x = float(waypoint.shape[0])
                y = float(waypoint.shape[1])
                tile_x = int(x // settings.tile_size)
                tile_y = int(y // settings.tile_size)
                self.waypoints[waypoint.name] = (tile_x, tile_y)
                logger.debug(
                    "Loaded waypoint '%s' at pixel (%.1f, %.1f) -> tile (%d, %d)",
                    waypoint.name,
                    x,
                    y,
                    tile_x,
                    tile_y,
                )

        # Update context for backward compatibility
        context.waypoints = self.waypoints
        logger.info("Loaded %d waypoints", len(self.waypoints))

    def get_waypoint(self, name: str) -> tuple[float, float] | None:
        """Get waypoint position by name.

        Args:
            name: Waypoint name.

        Returns:
            Tuple of (tile_x, tile_y) or None if not found.
        """
        return self.waypoints.get(name)
