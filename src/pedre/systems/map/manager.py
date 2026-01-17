"""Map management system for loading and processing Tiled maps.

This module provides the MapManager class, which handles the loading of Tiled map files,
extraction of map layers (walls, objects), and orchestration of map data distribution
to other systems (portals, interactive objects).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, cast

import arcade

from pedre.constants import asset_path
from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems import PortalManager
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class MapManager(BaseSystem):
    """Manages map loading and resource extraction.

    Responsibilities:
    - Load Tiled map files (.tmx)
    - Extract collision layers (walls, objects) to sprite lists
    - Extract and manage waypoints
    - Orchestrate loading of map-dependent data for other systems:
        - Portals (PortalManager)
        - Interactive objects (InteractionManager)
        - NPCs (NPCManager)

    Attributes:
        tile_map: The loaded arcade.TileMap instance.
        scene: The arcade.Scene created from the tile map.
        waypoints: Dictionary of waypoints {name: (x, y)} from map object layer.
    """

    name: ClassVar[str] = "map"
    dependencies: ClassVar[list[str]] = ["npc", "portal", "interaction", "player"]

    def __init__(self) -> None:
        """Initialize the map manager."""
        self.tile_map: arcade.TileMap | None = None
        self.scene: arcade.Scene | None = None
        self.waypoints: dict[str, tuple[float, float]] = {}
        self.current_map: str = ""

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize map manager (no map loaded yet)."""

    def load_map(self, map_file: str, context: GameContext, settings: GameSettings) -> None:
        """Load a Tiled map and populate game context and systems.

        Args:
            map_file: Filename of the .tmx map to load (e.g. "map.tmx").
            context: GameContext for updating shared state (wall_list, waypoints).
            settings: GameSettings for resolving asset paths.
        """
        map_path = asset_path(f"maps/{map_file}", settings.assets_handle)
        logger.info("Loading map: %s", map_path)
        self.current_map = map_file

        # 1. Load TileMap and Scene
        self.tile_map = arcade.load_tilemap(map_path, scaling=1.0)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # 2. Extract collision layers
        wall_list = arcade.SpriteList()
        collision_layer_names = ["Walls", "Collision", "Objects"]
        if self.scene:
            for layer_name in collision_layer_names:
                if layer_name in self.scene:
                    for sprite in self.scene[layer_name]:
                        wall_list.append(sprite)

        # Update context with wall list (needed by physics, pathfinding)
        context.wall_list = wall_list

        # 3. Load other components
        self._load_waypoints(settings)
        context.waypoints = self.waypoints

        # 4. Delegate to other systems
        self._load_npcs(context, settings)
        self._load_portals(context)
        self._load_interactive_objects(context)

        # 5. Let PlayerManager spawn player using new map data
        # Note: PlayerManager.setup() might have run earlier with no map.
        # We need to trigger player spawn now that map is loaded.
        player_manager = context.get_system("player")
        if player_manager and hasattr(player_manager, "spawn_player"):
            player_manager.spawn_player(context, settings)

        # 6. Update Pathfinding (needs new wall list)
        pathfinding = context.get_system("pathfinding")
        if pathfinding and hasattr(pathfinding, "set_wall_list"):
            pathfinding.set_wall_list(wall_list)

    def on_draw(self, context: GameContext) -> None:
        """Draw the map scene."""
        if self.scene:
            self.scene.draw()

    def _load_waypoints(self, settings: GameSettings) -> None:
        """Load waypoints from object layer."""
        self.waypoints = {}
        if not self.tile_map:
            return

        waypoint_layer = self.tile_map.object_lists.get("Waypoints")
        if not waypoint_layer:
            return

        for waypoint in waypoint_layer:
            if waypoint.name:
                x = float(waypoint.shape[0])
                y = float(waypoint.shape[1])
                tile_x = int(x // settings.tile_size)
                tile_y = int(y // settings.tile_size)
                self.waypoints[waypoint.name] = (tile_x, tile_y)

    def _load_npcs(self, context: GameContext, settings: GameSettings) -> None:
        """Load NPCs from map and register with NPCManager."""
        # This logic should ideally be in NPCManager, but MapManager orchestrates it.
        # We can pass the object layer or scene to NPCManager.
        npc_manager = context.get_system("npc")
        if not npc_manager:
            return

        if self.scene and "NPCs" in self.scene and hasattr(npc_manager, "load_npcs_from_scene"):
            # We need to convert static sprites to AnimatedNPCs if they have properties
            # Currently GameView._setup_animated_npcs did this.
            # We should move that logic to NPCManager.load_npcs_from_scene(scene, settings)
            npc_manager.load_npcs_from_scene(self.scene, settings, context.wall_list)

        # Also ensure visible NPCs are in the wall_list
        # The load_npcs_from_scene method should handle adding to wall_list if needed (collision).

    def _load_portals(self, context: GameContext) -> None:
        """Load portals from map and register with PortalManager."""
        portal_manager = context.get_system("portal")
        if not portal_manager or not self.tile_map:
            return

        portal_manager.clear()  # Clear old portals

        portal_layer = self.tile_map.object_lists.get("Portals")
        if not portal_layer:
            return

        for portal in portal_layer:
            if not portal.name or not portal.properties or not portal.shape:
                continue

            # Extract shape logic (same as GameView)
            xs: list[float] = []
            ys: list[float] = []

            if isinstance(portal.shape, (list, tuple)) and len(portal.shape) > 0:
                first_elem = portal.shape[0]
                if isinstance(first_elem, (tuple, list)):
                    for p in portal.shape:
                        # the shape p is (x, y)
                        xs.append(float(p[0]))
                        ys.append(float(p[1]))
                else:
                    xs.append(float(portal.shape[0]))
                    ys.append(float(portal.shape[1]))
            else:
                continue

            sprite = arcade.Sprite()
            sprite.center_x = (min(xs) + max(xs)) / 2
            sprite.center_y = (min(ys) + max(ys)) / 2
            sprite.width = max(xs) - min(xs)
            sprite.height = max(ys) - min(ys)

            cast("PortalManager", portal_manager).register_portal(sprite=sprite, name=portal.name)

    def _load_interactive_objects(self, context: GameContext) -> None:
        """Register interactive objects from 'Interactive' layer."""
        interaction_manager = context.get_system("interaction")
        if not interaction_manager or not self.scene:
            return

        interaction_manager.clear()

        if "Interactive" in self.scene:
            for sprite in self.scene["Interactive"]:
                # Get name logic (same as GameView)
                name = None
                if hasattr(sprite, "properties") and sprite.properties:
                    name = sprite.properties.get("name")

                if not name and hasattr(sprite, "name"):
                    name = sprite.name

                if name:
                    interaction_manager.register_object(sprite, name.lower())
